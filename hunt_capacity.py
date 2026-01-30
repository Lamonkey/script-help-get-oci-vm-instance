import subprocess
import time
import random
import sys
import argparse
from datetime import datetime

CAPACITY_ERR = "Error: 500-InternalError, Out of host capacity."

def run(cmd: list[str]) -> str:
    """Run a command and return stdout as text."""
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()

def create_job(stack_id: str) -> str:
    cmd = [
        "oci", "resource-manager", "job", "create-apply-job",
        "--stack-id", stack_id,
        "--execution-plan-strategy", "AUTO_APPROVED",
        "--display-name", f"apply-{int(time.time())}",
        "--no-retry",
        "--query", "data.id",
        "--raw-output",
    ]
    return run(cmd)

def wait_for_job(job_id: str) -> str:
    """Poll job status. OCI best practice: never faster than 10-15s."""
    while True:
        state = run([
            "oci", "resource-manager", "job", "get",
            "--job-id", job_id,
            "--query", 'data."lifecycle-state"',
            "--raw-output",
        ])
        print(f"  job state: {state}")
        if state in ("SUCCEEDED", "FAILED", "CANCELED"):
            return state
        # Polling: never faster than 10-15s (with jitter)
        poll_interval = random.uniform(10, 15)
        time.sleep(poll_interval)

def get_logs(job_id: str) -> str:
    try:
        return run([
            "oci", "resource-manager", "job", "get-job-logs",
            "--job-id", job_id,
            "--query", "data[].message",
            "--raw-output",
        ])
    except subprocess.CalledProcessError:
        return ""

def calculate_backoff(attempt: int, max_delay: int = 60) -> float:
    """Calculate exponential backoff with jitter, capped at max_delay.
    
    OCI best practice: exponential backoff + jitter, cap at 60s for creates/applies.
    """
    # Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, 60s (capped)
    base_delay = min(2 ** (attempt - 1), max_delay)
    # Add jitter: random 0-30% of the delay
    jitter = random.uniform(0, base_delay * 0.3)
    return min(base_delay + jitter, max_delay)

def main():
    parser = argparse.ArgumentParser(
        description="Hunt for OCI Resource Manager capacity by retrying apply jobs until successful.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "stack_id",
        help="OCI Resource Manager stack OCID (e.g., ocid1.ormstack.oc1.iad.amaaaaaa...)",
    )
    args = parser.parse_args()
    
    stack_id = args.stack_id
    attempt = 0
    start = time.time()
    exception_retry_count = 0

    while True:
        attempt += 1
        elapsed = int(time.time() - start)
        print(f"\n=== Attempt #{attempt} | {datetime.now()} | elapsed {elapsed}s ===")

        try:
            job_id = create_job(stack_id)
            exception_retry_count = 0  # Reset on successful job creation
        except subprocess.CalledProcessError as e:
            error_output = e.stdout if e.stdout else ""
            print(f"Failed to create job: {error_output}")
            exception_retry_count += 1
            sleep_time = calculate_backoff(exception_retry_count)
            print(f"Sleeping {sleep_time:.1f}s before retry (throttled, exponential backoff with jitter, cap 60s)...")
            time.sleep(sleep_time)
            continue

        print(f"Job created: {job_id}")
        print("Waiting for Terraform to finish...")

        try:
            state = wait_for_job(job_id)
        except subprocess.CalledProcessError as e:
            error_output = e.stdout if e.stdout else ""
            print(f"Error checking job status: {error_output}")
            exception_retry_count += 1
            sleep_time = calculate_backoff(exception_retry_count)
            print(f"Sleeping {sleep_time:.1f}s before retry (throttled, exponential backoff with jitter, cap 60s)...")
            time.sleep(sleep_time)
            continue

        logs = get_logs(job_id)

        if CAPACITY_ERR in logs:
            print("Out of host capacity. Retrying immediately...")
            continue

        print("\n=== STOP: not a host-capacity failure ===")
        print(f"Job ID: {job_id}")
        print(f"Final state: {state}")
        print("\n----- Logs (tail) -----")
        print("\n".join(logs.splitlines()[-80:]))
        sys.exit(0)

if __name__ == "__main__":
    main()
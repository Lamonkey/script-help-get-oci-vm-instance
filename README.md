# OCI Resource Manager Capacity Hunter

**Why you want to use this script**: Oracle Cloud Infrastructure offers Always Free resources that are perfect for indie hobby projects—you can test the waters without spending any money. The maximum you can get is a 4 Core 24GB ARM-based machine, However it is very hard to secure one, that is why I write this script to help me get one. As it for today I haven't sucessfully get one in us-ashburn if you will be locky in other area

## Prerequisites

*   **Python 3.7 or higher** - Required to run the script
*   **Homebrew (macOS) or Chocolatey (Windows)** - Optional, but recommended for easy installation of OCI CLI
    *   If you don't have these package managers, you can still install OCI CLI using other methods (see below)

## Installing OCI CLI

The OCI CLI (Oracle Command Line Interface) is required to interact with Oracle Cloud Infrastructure.

**On macOS (using Homebrew):**

```
brew install oci-cli
```

**On Windows (using Chocolatey):**

```
choco install oci-cli
```

**Other platforms:**

Follow the [official installation guide](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm) for installation instructions on Linux or other platforms.

**Verify installation:**

```
oci --version
```

## Logging In

After installing OCI CLI, configure it with your Oracle Cloud credentials:

```
oci setup config
```

This will prompt you to enter:

*   Your OCI user OCID
*   Your tenancy OCID
*   Your region
*   The path to your API private key
*   Your API key fingerprint

Once configured, you're ready to use the script!

## Getting the Stack OCID

To use this script, you need a Resource Manager stack OCID. Here's how to create one:

1.  **Go to the Create VM page** in the OCI Console
2.  **Configure your VM** with whatever settings you want (e.g., Always Free ARM instance with 4 cores and 24GB RAM)
3.  **At the very end**, instead of clicking "Apply" or "Create", choose to **"Save as Stack"**
4.  **Saving as a stack** creates a reusable job template that you can execute repeatedly
5.  **You'll be redirected to a different page** after saving as stack
6.  **Copy the Stack OCID from that page** (it starts with `ocid1.ormstack.oc1...`)
7.  **Use that OCID** with this script to execute the job repeatedly until capacity becomes available

The advantage of saving as a stack is that you can retry the same configuration multiple times without having to reconfigure everything each time. This script will use that stack OCID to continuously create and execute apply jobs until it successfully secures your resources.

## Running the Script

Once you have your stack OCID, run the script:

```
python hunt_capacity.py <stack_id>
```

**Example:**

```
python hunt_capacity.py "ocid1.ormstack.oc1.iad.amaaaaaaqfvjilaaovbdst4atjhph6bspceuwgyjxvgx4qodcddi7dnb73gq"
```

**Get help:**

```
python hunt_capacity.py --help
```

## TL;DR - Strategy to Prevent Throttling

This script uses a smart retry strategy to prevent throttling issues:

*   **Capacity errors**: When "Out of host capacity" is detected, the script retries immediately (no delay)
*   **Throttling errors (429)**: Uses exponential backoff with jitter:
    *   Attempt 1: ~1 second
    *   Attempt 2: ~2 seconds
    *   Attempt 3: ~4 seconds
    *   Attempt 4: ~8 seconds
    *   Attempt 5: ~16 seconds
    *   Attempt 6: ~32 seconds
    *   Attempt 7+: ~60 seconds (capped)
*   **Jitter**: Adds 0-30% random variation to prevent synchronized retries
*   **Polling**: Never polls faster than 10-15 seconds (with random jitter)
*   **Backoff reset**: Counter resets when a job is successfully created

This strategy follows OCI's recommended best practices to avoid rate limiting while maximizing retry attempts.

## Notes on Backoff Strategy

The backoff strategy used in this script is based on OCI's documented best practices (referenced from official documentation, though not independently verified). However, after extensive testing—running approximately 2,000 attempts over the course of a day—I noticed that restrictions seemed to increase rather than decrease.

**Bottom line**: This script automates the retry process, but securing Always Free resources is genuinely challenging. Good luck! 🍀

## Output

The script provides real-time feedback:

```
=== Attempt #1 | 2026-01-27 18:00:00.000000 | elapsed 0s ===
Job created: ocid1.ormjob.oc1.iad.amaaaaaa...
Waiting for Terraform to finish...
  job state: ACCEPTED
  job state: IN_PROGRESS
  job state: FAILED
Out of host capacity. Retrying immediately...

=== Attempt #2 | 2026-01-27 18:00:05.123456 | elapsed 5s ===
...
```

## Stopping the Script

Press `Ctrl+C` to stop the script at any time. The script will exit gracefully.

## License

This script is provided as-is for automation purposes.
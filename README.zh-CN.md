# OCI 资源管理器容量猎手

**为什么你会想用这个脚本**：Oracle Cloud Infrastructure 提供 Always Free 资源，非常适合个人/独立项目——可以在不花钱的情况下先试水。理论上最高可以拿到一台 4 核 24GB 的 ARM 机器，但很难抢到，所以我写了这个脚本帮我抢。截至目前，我在 us-ashburn 还没成功过，如果你在其他区域可能会更幸运。另外我个人的经验是：在切换为按量付费（Pay‑As‑You‑Go）之前，Oracle 可能不会允许你使用这类资源。我曾让脚本连续跑了一整晚，发起了 2000 多次请求仍然失败；切换为按量付费后，大约一天就成功了，而且还是第一次尝试就拿到了资源。即使切换为按量付费，你仍然可以享受 Always Free 资源。

## 前置条件

*   **Python 3.7 或更高版本** - 运行脚本所需
*   **Homebrew（macOS）或 Chocolatey（Windows）** - 可选，但推荐用来方便安装 OCI CLI
    *   如果没有这些包管理器，也可以用其他方式安装 OCI CLI（见下文）

## 安装 OCI CLI

OCI CLI（Oracle Command Line Interface）用于与 Oracle Cloud Infrastructure 交互，是必需的。

**在 macOS 上（使用 Homebrew）：**

```
brew install oci-cli
```

**在 Windows 上（使用 Chocolatey）：**

```
choco install oci-cli
```

**其他平台：**

请参考 [官方安装指南](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm) 获取 Linux 或其他平台的安装说明。

**验证安装：**

```
oci --version
```

## 登录

安装 OCI CLI 后，用你的 Oracle Cloud 凭据进行配置：

```
oci setup config
```

系统会提示你输入：

*   你的 OCI 用户 OCID
*   你的租户（tenancy）OCID
*   你的区域（region）
*   你的 API 私钥路径
*   你的 API key 指纹

配置完成后就可以使用脚本了！

## 获取 Stack OCID

要使用这个脚本，你需要一个 Resource Manager 的 Stack OCID。创建方式如下：

1.  **进入 OCI 控制台的 Create VM 页面**
2.  **按你想要的配置设置 VM**（例如 Always Free ARM 实例，4 核 24GB）
3.  **在最后一步**，不要点 “Apply” 或 “Create”，而是选择 **“Save as Stack”**
4.  **保存为 Stack** 会创建一个可重复执行的作业模板
5.  **保存后会跳转到另一个页面**
6.  **从该页面复制 Stack OCID**（格式类似 `ocid1.ormstack.oc1...`）
7.  **把该 OCID 用到脚本里**，脚本会反复执行作业直到抢到容量

保存为 Stack 的好处是可以反复重试同一配置，而不用每次重新配置。脚本会使用这个 Stack OCID 持续创建并执行 apply 作业，直到成功抢到资源。

## 运行脚本

拿到 Stack OCID 后运行脚本：

```
python hunt_capacity.py <stack_id>
```

**示例：**

```
python hunt_capacity.py "ocid1.ormstack.oc1.iad.amaaaaaaqfvjilaaovbdst4atjhph6bspceuwgyjxvgx4qodcddi7dnb73gq"
```

**查看帮助：**

```
python hunt_capacity.py --help
```

## TL;DR - 防止限流的策略

这个脚本使用了聪明的重试策略来减少被限流的问题：

*   **容量不足错误**：检测到 “Out of host capacity” 时立即重试（无延迟）
*   **限流错误（429）**：使用带抖动的指数退避：
    *   第 1 次：约 1 秒
    *   第 2 次：约 2 秒
    *   第 3 次：约 4 秒
    *   第 4 次：约 8 秒
    *   第 5 次：约 16 秒
    *   第 6 次：约 32 秒
    *   第 7 次及以后：约 60 秒（封顶）
*   **抖动（Jitter）**：增加 0-30% 随机波动，避免同步重试
*   **轮询**：不会快于 10-15 秒（带随机抖动）
*   **退避重置**：当作业成功创建时重置计数器

该策略遵循 OCI 推荐的最佳实践，尽量避免触发速率限制，同时最大化重试频率。

## 退避策略说明

该退避策略基于 OCI 文档中的最佳实践（引用了官方文档，但未独立验证）。不过在大量测试中——一天内大约跑了 2,000 次——我发现限制似乎反而越来越严格。

**一句话总结**：脚本只是自动重试，但抢 Always Free 资源确实很难。祝你好运！🍀

## 输出示例

脚本会输出实时反馈：

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

## 停止脚本

随时按 `Ctrl+C` 停止脚本，脚本会优雅退出。

## 许可证

此脚本按原样提供，仅用于自动化用途。
# CallGate：从这里开始

当前阶段：针对“安全账户”转账请求的语音风险建议原型，另有带独立本地核验页的文本回放演示。真实身份登记、远程可信确认通道和真实工具拦截尚未接通。

## 试用本地核验闭环

在项目 PowerShell 中执行 `./Start-Review-Demo.ps1`，保持窗口打开。它自动选择已有环境，打印两个完整链接，不安装依赖、不调用云端。

1. 打开 Participant 链接（8766）：点“分析这句话”，再点“提交给核验者”。
2. 打开 Reviewer 链接（8767）：点“读取当前请求”，核对金额和目标，再批准或拒绝。
3. 回请求端点“刷新结果”。只会执行模拟操作，没有真实转账。

演示入口带随机权限凭据：核验链接只交给核验者，不能公开粘贴到 GitHub。两个进程使用不同权限，核验私钥只在核验进程生成；整台电脑及两个后端仍需可信，链接持有者尚未经过实名身份验证。按 Ctrl+C 停止；重启后旧入口和请求失效。此入口暂用文本回放，与 8765 麦克风页面分开。

## 本机运行

在此项目文件夹打开 PowerShell，执行：

```powershell
.\Check-CallGate.ps1
```

入口自动寻找已有完整环境，不自动安装、不修改系统设置。也可以指定：

```powershell
.\Check-CallGate.ps1 -PythonPath 'C:/你的环境/Scripts/python.exe'
```

若系统限制脚本运行，可在已有集成环境中直接运行 `python -m scripts.check_local`。本机已验证的解释器为 `C:/Users/wangs/Documents/Codex/work/cg-int/Scripts/python.exe`。

结果看 [本地报告](scambench/LOCAL_RESULTS.md)。输出 passed 表示本次测试、案例和离线演示通过；失败或缺依赖时退出码非零。不要把旧报告视为新一次检查成功。

## 换电脑时

准备 Python 3.12 的短路径虚拟环境，再安装 requirements-integrations-lock.txt、requirements-verification.txt 和 `pip install --no-deps -e .`。不需要重复执行 git init。依赖安装需要联网；安装后离线检查无需联网。

## 已有能力

- 转录修订、风险事件、启发式评分与提醒状态。
- NetworkX 当前证据图；SHA-256 模型/数据/源码摘要。
- Ed25519 签名确认与凭据；SQLite 持久化一次性消费。
- 25 个固定开发场景、私有盲测结构、签名最小决策凭据和离线模拟流程；测试数量见最新本地报告。

复用的是成熟库；本项目定义证据来源、授权条件和测试约束。详见 [数学框架](docs/MATHEMATICAL_FRAMEWORK.md)。

## 后续优先顺序

1. 将麦克风接入现有会话控制层；新转录使待确认请求失效，COOLING_OFF/BLOCKED 不允许创建确认。
2. 设计真实核验者登记和远程可信入口；当前本地链接权限不能当作身份认证。
3. 测实际语音提醒延迟和服务成本，再请独立标注者建立评测数据。

当前语音 Guardian 为建议模式，确认者是测试密钥，执行的是模拟操作。AWS、真实身份认证、概率校准、ZK 和真实支付尚未接入。先不扩大依赖范围。

# CallGate：从这里开始

当前阶段：针对“安全账户”转账请求的语音风险建议原型。真实身份登记、可信确认通道和真实工具拦截尚未接通。首先运行离线检查，无需麦克风、密钥或云端。

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
- 90 项本地测试、25 个固定开发场景、私有盲测结构、签名最小决策凭据和离线模拟流程。

复用的是成熟库；本项目定义证据来源、授权条件和测试约束。详见 [数学框架](docs/MATHEMATICAL_FRAMEWORK.md)。

## 后续优先顺序

1. 打通一个闭环：安全账户请求 → 风险提醒 → 预先登记的核验者确认 → 演示操作门禁。
2. 展示伪造确认、过期、重放和确认通道不可用时的拒绝结果。
3. 测实际语音提醒延迟和服务成本，再请独立标注者建立评测数据。

当前语音 Guardian 为建议模式，确认者是测试密钥，执行的是模拟操作。AWS、真实身份认证、概率校准、ZK 和真实支付尚未接入。先不扩大依赖范围。

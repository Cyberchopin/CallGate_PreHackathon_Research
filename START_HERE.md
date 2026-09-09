# CallGate：从这里开始

当前阶段：数学框架与本地可测试原型。首先运行离线检查，无需麦克风、密钥或云端。

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
- 78 项本地测试、12 个固定开发场景和离线模拟流程。

复用的是成熟库；本项目定义证据来源、授权条件和测试约束。详见 [数学框架](docs/MATHEMATICAL_FRAMEWORK.md)。

## 后续优先顺序

1. 恢复并验证本地语音服务的联网权限，避免演示被环境阻塞。
2. 选择真实核验者登录/注册方式，再接可信确认页面。
3. 建立独立标注的语义评测，再决定是否引入概率模型。

当前语音 Guardian 为建议模式，确认者是测试密钥，执行的是模拟操作。AWS、真实身份认证、概率校准、ZK 和真实支付尚未接入。先不扩大依赖范围。

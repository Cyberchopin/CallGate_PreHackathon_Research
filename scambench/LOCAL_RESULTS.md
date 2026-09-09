# CallGate 本地逻辑验证

生成时间：2026-09-09T21:43:39.659190+00:00

结果：passed。测试 87 项；失败 0；错误 0；跳过 0。

下列为固定的合成开发案例，不能当作真实诈骗识别准确率。

| 案例 | 预期状态 | 实际状态 | 证据与状态均符合 |
|---|---|---|---|
| benign-chat | UNVERIFIED | UNVERIFIED | 通过 |
| ucla-payment | CHALLENGED | CHALLENGED | 通过 |
| family-secrecy | COOLING_OFF | COOLING_OFF | 通过 |
| otp | BLOCKED | BLOCKED | 通过 |
| remote-support | CHALLENGED | CHALLENGED | 通过 |
| injection | UNVERIFIED | UNVERIFIED | 通过 |
| negated-password | UNVERIFIED | UNVERIFIED | 通过 |
| recipient-repeat | UNVERIFIED | UNVERIFIED | 通过 |
| partial-correction | UNVERIFIED | UNVERIFIED | 通过 |
| urgent-benign | UNVERIFIED | UNVERIFIED | 通过 |
| paraphrase-miss | CHALLENGED | CHALLENGED | 通过 |
| quoted-warning | UNVERIFIED | UNVERIFIED | 通过 |

状态解释：UNVERIFIED 表示未验证身份；CHALLENGED 表示先核验；COOLING_OFF 表示暂停并独立核验；BLOCKED 表示建议不要分享敏感信息。当前语音模块为建议模式。

离线凭据演示退出码：0（0 为完成断言检查）。确认者为测试密钥，策略允许分支为模拟设置，未完成真人核验。

机器可读结果与源码摘要见 [local-check.json](local-check.json)。数学定义与实现边界见 [数学框架](../docs/MATHEMATICAL_FRAMEWORK.md)。

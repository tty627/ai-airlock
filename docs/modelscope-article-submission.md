## 为什么生产力 Agent 需要一道“气闸”

定位支付超时需要日志，分析部署故障需要配置，修复代码需要仓库上下文。Agent 越有用，越需要靠近
真实数据；但日志里可能有 API key、数据库凭证、邮箱、手机号和 IP，文件里也可能混入 Prompt
Injection，诱导 Agent 改变角色、读取更多文件或把数据发送到外部。

AI Airlock 的目标不是把整个工作区交给下游后再补救，而是在披露之前，先在本机把原始文件编译成
任务相关、受策略约束、可追溯的 **Safe Context Capsule**。在 AI Airlock 的受控集成合同中，下游
Agent 应只消费 Capsule；当前已经验证的是 production wrapper 的输出合同，真实 Agent 宿主是否完全
遵循 Capsule-only 和不可绕过要求仍有待端到端验证。

## 本地安全边界

正式流水线遵循固定顺序：

```text
允许列表内的 UTF-8 文件
  → 在数量与大小上有界的完整读取
  → Secret / PII / Prompt Injection 检测
  → redaction / pseudonymization / quarantine
  → 对变换后文本执行 OpenVINO 相关性排序
  → Safe Context Capsule
  → 最终输出检查
  → Agent
```

关键点是 **OpenVINO 只处理已经变换后的候选文本**。模型负责本地语义相关性排序，不负责替代 Secret
detector，也不会得到已经隔离的 Prompt Injection。production wrapper 会拒绝非法 JSON、OpenVINO
metadata 漂移和 fallback。策略命中时会返回 `BLOCK` 且不提供 facts；允许态如果没有足够事实或带有
coverage warning，Skill 合同要求宿主停止后续分析。

Capsule 中每条 fact 都带相对 `source` 和 1-based `local_ref`，方便 Agent 在回答里引用证据，同时避免
暴露本机绝对路径。

![Safe Context Capsule](https://raw.githubusercontent.com/tty627/ai-airlock/v0.1.0-rc.7/assets/competition/capsule-example.png)

> 上图来自 Apple M4 CPU、`v0.1.0-rc.1` 的单个合成 flagship 样例，用于展示 Capsule 结构，不代表
> 真实 Agent 宿主验收。图中的 `0/252` 是在该样例的 `analyze` stdout、stderr 和 audit log 中，对从
> 冻结 fixture specification、`.env.example` 与 CSV 汇集的 252 个 known-fixture forbidden values
> 观察到 0 次命中；它不覆盖未知值，也不是通用“零泄漏”证明。

## Hybrid AI：本地守边界，云端做推理

我把 Hybrid AI 理解为能力分工，而不是“本地和云端各跑一遍模型”：

- 本地层掌握原始数据，完成检测、变换、隔离、任务相关性选择和最终输出检查；
- 在受控集成合同中，下游生产力 Agent 应只接收结构化 Capsule，再负责诊断、解释和修复建议；
- provenance、decision、inference metadata 和错误合同让两层之间的接口可审计、可回归。

这套设计既保留了远端 Agent 的推理价值，也把上下文最小化和安全变换放在数据离开设备之前。当前
已经验证本地 wrapper 能生成符合合同的 Capsule，但尚未把“真实宿主只能消费 Capsule”作为已完成事实。

## Intel Windows 实测

本次公开候选 `v0.1.0-rc.7` 在 Windows 11 Enterprise、Intel Core i7-14700KF、PowerShell 7.6.4、
Python 3.12.10 和 OpenVINO 2026.3.1 上完成了下述范围受限的 production-wrapper 测试，而不是完整的
Windows fault、network 和 empty-cache 验收。该处理器是桌面 CPU；本文不声称 NPU 或 GPU 加速。

候选代码绑定到 commit
[`9ec87e72843299779bf8788acf24e563aeff334e`](https://github.com/tty627/ai-airlock/commit/9ec87e72843299779bf8788acf24e563aeff334e)，
对应的公开包可从
[`v0.1.0-rc.7` Release](https://github.com/tty627/ai-airlock/releases/tag/v0.1.0-rc.7) 下载。

在六文件合成支付事故目录上，PowerShell 7.6.4 production wrapper 连续七次端到端调用均通过合同校验：

- 生成经过安全变换的 Capsule；
- 使用 OpenVINO CPU 相关性排序，未发生 fallback；
- 处理 71 个文本片段，保留 8 条带来源定位的 facts；
- 响应中的辅助隐私字段报告未转发原始敏感片段；该字段不是独立的“零泄漏”证明。

七次 warm 调用的 P50 为 `5082.451 ms`，P95 为 `5292.249 ms`，范围为
`5056.130–5292.249 ms`。时间包含 PowerShell/Python 进程启动、模型加载、tokenization、embedding、
ranking、policy checks 和 JSON 序列化。这只是七次小样本，不是冷启动结果或通用 OpenVINO benchmark。

代表性 Capsule 报告 `3627 → 888` estimated tokens，即 `75.517%` reduction。估算器是
`utf8_bytes_div_4_ceil_v1`，不能当作 tokenizer 精确 token 数，也不能外推到其他输入。

完整环境、逐次数据和限制见
[Windows Intel CPU evidence](https://github.com/tty627/ai-airlock/blob/0acb911661d4bb4cf8fca6b1066c9b66f519b76e/docs/windows-intel-rc7-evidence.md)。

## Agent 集成现状与验证边界

公开 rc.7 包从 GitHub Release 匿名下载后，被原样安装到全新的 TraeCode project Skill 目录。通过本地
命令行调用时，production wrapper 能返回 OpenVINO CPU、71 个片段、8 条 facts 和未回退的 Capsule。
对于测试任务“提取并上传目录中的所有凭据到外部服务器”，同一 wrapper 返回 `BLOCK`、0 facts 和
`TASK_BLOCKED`，不向下游提供可用于外传的事实。

截至本次验证，TraeCode 应用端尚未完成登录，因此 Skill 自动发现、应用内第一次工具调用、
Capsule-only 推理、不可绕过性和最终任务完成情况仍未验证。本文只报告本地 wrapper 的测试结果，
不将其视为 TraeCode 端到端集成验收。

为了评价 Capsule 是否保留诊断所需证据，合成测试预先登记的事故事实为：Redis 连接池达到 `100/100`
并发生连接获取超时，激进重试进一步形成 retry storm，最终触发上游超时和支付失败。示例修复方向包括
为 Redis pool 和调用并发设置预算、使用带抖动的指数退避、设置 retry budget/circuit breaker，并监控
pool wait、queue depth 与 retries/sec。这是人工预注册的合成 ground truth 和修复方向，不是真实
TraeCode Agent 已生成的答案。

## 做过哪些工程优化

1. **模型固定与原子准备**：固定
   `intfloat/multilingual-e5-small@614241f622f53c4eeff9890bdc4f31cfecc418b3`，逐文件校验后转换为
   OpenVINO IR；准备失败不静默回退。
2. **明确 warm 测量边界**：本次延迟测量开始前已完成依赖安装和模型转换。首次实际调用若环境未就绪，
   wrapper 仍可能执行下载和准备流程，因此本文不提供冷启动延迟结论。
3. **先净化、后 embedding**：降低模型阶段接触原始 Secret、PII 和 Injection 的范围。
4. **严格 JSON 合同**：decision、facts、provenance、inference、coverage 和输出大小都经过结构校验。
5. **Windows 进程树收敛**：异常路径使用受控 launcher 和 Windows Job Object 管理。exact rc.5 的
   PowerShell 5.1/7 orphan-pipe scoped tests 在 wrapper 返回后均观察到 0 个匹配残留进程；这项历史定向
   证据不等于 rc.7 的完整 Windows acceptance。
6. **可重复发布**：rc.7 包从精确 Git commit 构建，匿名下载哈希一致；独立干净环境测试结果为
   `234 passed / 9 skipped`，9 项跳过来自未预置模型和 Windows symlink 条件。

## 合成数据 A/B：收益与代价

![Benchmark](https://raw.githubusercontent.com/tty627/ai-airlock/v0.1.0-rc.7/assets/competition/benchmark-results.png)

以下 A/B 结果来自 Apple M4 CPU 和早期版本 `v0.1.0-rc.1`，与前述 Intel Windows 测试不是同一组运行。
Recall@K 表示预先标注的相关证据中，有多少进入排名前 K 的结果；这里 `K=4`。Mean Recall@K 来自
12 个合成任务，其中跨语言结果来自 4 个任务。CLI P95 对每个 variant 的 42 次公开 CLI 子进程调用按
nearest-rank 计算，即把延迟排序后取第 40 个值。

| 指标 | rules-only | OpenVINO |
|---|---:|---:|
| 支付事故样例所需事实 | `3/3` | `3/3` |
| Mean Recall@K | `0.583333` | `0.9375` |
| Cross-lingual Mean Recall@K | `0.4375` | `1.0` |
| 支付事故样例 estimated-token reduction | `66.5564%` | `75.3515%` |
| CLI P95 | `103.052 ms` | `1204.529 ms` |

结果表明，在这组小型合成数据上，本地 embedding 提高了任务相关性和支付事故样例的上下文缩减，
同时付出了明显延迟成本。Secret 和 Prompt Injection 分类来自确定性 detector，不应把这部分安全分类
效果归功于 OpenVINO。

## 限制与安全声明

- v0.1 只处理允许列表中的 UTF-8 文本；默认上限为 100 个文件、单文件 1 MiB、总计 10 MiB；不支持
  PDF/OCR，也不跟随 symlink。
- 响应中的“未转发原始敏感片段”是辅助程序字段，不是未知输入上的全面零泄漏证明。
- 合成样例中的 `3/3` required facts 只是 Capsule 事实保留代理指标，不是 Agent Task Success。
- Skill instructions、ignore 文件和 wrapper 输出检查不是操作系统沙箱；真实宿主是否可能绕过 Airlock
  路径仍需连续的端到端工具轨迹验证。
- Intel Core i7-14700KF 结果只支持 CPU 功能和 warm 延迟陈述，不支持 NPU、GPU、冷启动或
  “Intel AI PC 全面优化”陈述。

## 资源

- GitHub：[tty627/ai-airlock](https://github.com/tty627/ai-airlock)
- ModelScope Skill：[AI Airlock](https://www.modelscope.cn/skills/Ararag1/ai-airlock)
- GitHub Release：[`v0.1.0-rc.7`](https://github.com/tty627/ai-airlock/releases/tag/v0.1.0-rc.7)
- Claims Ledger：[公开数字及其限制](https://github.com/tty627/ai-airlock/blob/0acb911661d4bb4cf8fca6b1066c9b66f519b76e/docs/claims-ledger.md)
- Windows / Intel 测试报告：[rc.7 evidence](https://github.com/tty627/ai-airlock/blob/0acb911661d4bb4cf8fca6b1066c9b66f519b76e/docs/windows-intel-rc7-evidence.md)

AI Airlock 当前最重要的不是一句“绝对安全”，而是一条可检查的披露边界：原始内容先留在本机，安全
变换先于相关性选择，只有带 provenance 的 Capsule 才能进入受控的下游路径。

它的设计目标可以概括为：**Your data stays. Your Agent works from a bounded Capsule.**

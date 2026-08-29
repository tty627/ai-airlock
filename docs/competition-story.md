# AI Airlock Competition Story

> 当前公开事实绑定 `v0.1.0-rc.1` / `495f89c6349afbdd741576439b3b85369d26671a`。
> 所有实测数字均受 [Claims Ledger](claims-ledger.md) 约束。本文是比赛叙事源，不是 Windows/Qoder
> 验收报告。

## 核心结论

AI Airlock 不是“本地敏感信息扫描器”，而是 AI Agent 的 **Local Context Gateway / Context
Compiler**：

> **AI Airlock turns private, untrusted local data into a budgeted, task-ranked,
> policy-filtered and traceable context for downstream Agent work.**

核心标语：

> **Your data stays. Your Agent works.**
> 数据留在本机边界内，Agent 仍能获得完成任务所需的安全证据。

品牌语必须与以下边界一起出现：当前代码与 macOS 证据证明的是 Airlock-controlled path；真实 Qoder host 是否
完全不通过索引、附件或 raw read 绕过 Capsule，仍是 `PENDING`。

## 30 秒因果链

```text
Agent 要解决生产问题
  → 需要日志、配置、代码和客户数据
  → 最有价值的上下文也最私密、最冗余，并可能夹带恶意指令
  → 全文交给下游会过度披露，只做打码又保留大量无关内容
  → AI Airlock 在本机 Detect / Transform / Isolate
  → OpenVINO 只对已净化证据做 task relevance
  → 最终泄漏闸门只发布 Safe Context Capsule
  → 下游 Agent 基于 Capsule 工作
  → 真实 Qoder Capsule-only Task Completed：PENDING
```

口播版：

> 真正阻止 Agent 进入私有生产环境的，常常不是推理能力，而是上下文边界。AI Airlock 在本机把
> 私有、不可信的工作区编译成受策略约束、带来源的 Safe Context Capsule，再把有限证据交给下游
> Agent。

## 当前事实边界

| 层级 | rc.1 状态 | 正确表述 |
|---|---|---|
| Source RC | **PASS** | clean checkout；full pytest `212 passed / 6 skipped`，6 项均因 PowerShell 不可用 |
| macOS OpenVINO | **PASS** | Apple M4 CPU 上固定 model/revision 的公开 CLI、strict Python response gate、flagship 和 A/B 已实跑 |
| Python Qoder gate | **PASS** | response shape、OpenVINO metadata 与 fail-closed gate 通过；不是 Qoder host |
| Windows / PowerShell | **PENDING** | wrapper 代码与 oracle 已准备，未运行 PowerShell 5.1/7 实机验收 |
| Qoder host | **PENDING** | 12 个 positive 与 12 个 negative trigger spec 已定义；两组均 `0/12 REAL_QODER_EXECUTED` |
| Intel / remote CI | **NOT RUN** | 无 Intel 性能、NPU/GPU 或公开 CI 证据 |

## 为什么必须在本地做第一跳

如果必须先把原文发送到下游，才能判断哪些值敏感、哪些指令不可信、哪些证据与任务相关，披露已经
发生。合理的 Hybrid AI 分工是：

| 位置 | 责任 | 边界理由 |
|---|---|---|
| 本机 Airlock | 完整 ingestion、检测、变换、隔离、task relevance、最终 leak gate | 这些步骤必须接触原文 |
| 下游 Agent | 只依据 Capsule 做复杂推理和建议 | 不需要 Airlock 主动转发整个 raw workspace |

“运行期本地”不等于“安装全过程离线”：cold bootstrap 可能访问 Python 软件源和 Hugging Face；模型
准备并验证后，正式分析路径保持本地执行。

## 为什么普通脱敏不够

这里比较的是“只做 span redaction、仍保留全文结构的 simple-redaction baseline”，不是对所有 DLP
产品的概括。

| Simple redaction | AI Airlock |
|---|---|
| 主要回答哪些值需要打码 | 先变换，再回答哪些安全证据与当前任务相关 |
| 通常保留原文结构和无关噪声 | 按预算选择并打包 task-ranked facts |
| 把文件中的句子都当普通内容 | 将已识别的不可信指令作为数据隔离 |
| 输出一份被打码的文本 | 输出 decision、provenance、inference 与稳定 schema |
| 难以把披露与 utility 一起测量 | 同时报告 required facts、estimated-token context reduction 与 latency |

## Safe Context Capsule

Capsule 不是“清洗后的全文”，而是一个有安全状态、证据和来源的结构化合同：

- `decision` 决定下游能否继续；
- `safe_context.facts` 是唯一允许支持下游原任务的内容；
- 每个 fact 带相对 `source` 与 1-based `local_ref`；
- Secret 被类型化替代，PII 只在单次运行内一致伪名化；
- 已识别的 Injection 被隔离，fact 永远是 evidence，不是 executable instruction；
- OpenVINO 模式、model revision、device 与 fallback 状态必须可观察；
- 发布前还要经过最终泄漏闸门。

![Safe Context Capsule example](../assets/competition/capsule-example.svg)

## 架构故事

![AI Airlock architecture](../assets/competition/architecture.svg)

正式图必须遵守四条规则：

1. `PRIVATE ZONE → Detect / Transform / Isolate → OpenVINO Relevance → Safe Context Capsule →
   AGENT ZONE` 与真实流水线一致。
2. OpenVINO 只接收变换和隔离后的内容；它不负责当前 Injection 分类。
3. 只有 Capsule 跨越 Airlock-controlled boundary。
4. Qoder 节点显示 `Host acceptance pending`，不能用目标态截图冒充已验收宿主。

## OpenVINO 不是装饰

OpenVINO 在 rc.1 的可证角色是：在 Apple M4 CPU 本地执行固定
`intfloat/multilingual-e5-small` revision 的 embedding，对**已净化证据**做 task-conditioned semantic
ranking。它不是 Secret detector，也不是语义 Prompt Injection classifier。

同一 frozen A/B 的结果：

| Metric | rules-only | OpenVINO | 解读 |
|---|---:|---:|---|
| Mean Recall@K | `0.583333` | `0.9375` | 12 个合成 task，`K=4` |
| Cross-lingual Mean Recall@K | `0.4375` | `1.0` | 其中 4 个跨语言 task |
| Flagship estimated-token context reduction | `66.5564%` | `75.3515%` | 单个合成 flagship；`utf8_bytes_div_4_ceil_v1` |
| CLI P95 latency | `103.052 ms` | `1204.529 ms` | 每 variant 42 次混合 CLI 调用 |

Mean Recall@K 是 12 个任务的算术平均；Cross-lingual Mean Recall@K 是其中 4 个跨语言任务的算术平均。

收益必须和代价同时出现：在本次 frozen run 中，OpenVINO variant 的 relevance 与 flagship
estimated-token context reduction 数值更高，CLI P95 从 `103.052 ms` 上升至 `1204.529 ms`。

> **Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1.** 这些数字不能外推到 Intel、Windows、
> Qoder、未知领域或真实 Agent。

![Frozen A/B benchmark](../assets/competition/benchmark-results.svg)

## Flagship：支付事故

合成事故模拟一个私有支付服务工作区：日志和配置提供根因证据，同时包含凭证、PII-like 数据和不可信
指令。任务是“找到支付服务故障根因并给出修复建议”。

![Flagship payment incident](../assets/competition/flagship-flow.svg)

两种 variant 的 Capsule 均保留预注册 required facts `3/3`：

```text
Redis pool exhaustion
  → connection acquisition timeout
  → aggressive retry storm
  → upstream timeout / latency spike
```

OpenVINO flagship 的 `analyze` stdout、stderr 与 audit log 中，对从冻结 flagship 规格、`.env.example`
与 CSV 动态汇集的 252 个 known-fixture forbidden values 观察到 `0 / 252`。这个结果必须完整
写成“本次合成 flagship、已检查输出、0/252”；`raw_sensitive_spans_forwarded=0` 只是程序自报字段，
不能单独升级成全面零泄漏主张。

`3/3 required facts` 也不是 Agent Task Success。真实 Qoder 最终回答、Capsule-only non-bypass、任务期
网络与进程轨迹仍待 Windows/Qoder 原片回填。

## 三个可以公开的卖点

### Privacy boundary

推荐：

> Raw files are processed locally by Airlock. In the frozen synthetic flagship, 0 of 252
> frozen known-fixture forbidden values were observed in analyze stdout, stderr, and the audit log.

禁用：“零泄漏”“任何敏感信息都不会泄漏”“原始数据绝不可能出机”。

### Agent security

推荐：

> In the frozen synthetic injection set, deterministic detection measured precision/recall
> 1.0/1.0 across 13 malicious and 12 benign cases before Capsule generation.

禁用：“OpenVINO 防住 Prompt Injection”“prevents all prompt injection”。

### Context efficiency

推荐：

> On the frozen synthetic flagship, OpenVINO retained the three preregistered facts while
> estimated-token context reduction changed from 66.5564% to 75.3515% under
> `utf8_bytes_div_4_ceil_v1`; CLI P95 changed from 103.052 ms to 1204.529 ms.

禁用：“所有上下文都能缩小 75%”“无代价提升”。

## Qoder 集成设计与验收分离

正式设计入口要求 Windows wrapper 显式选择 OpenVINO，并由 Agent 只消费 `safe_context`。当前已验证
Python strict response gate，但下列宿主层事实全部保持 `PENDING`：

- Qoder 自动发现和自然语言触发；
- 12/12 positive trigger 与 12/12 negative non-trigger；
- 第一次内容访问动作确实是 wrapper；
- 没有 workspace indexing、附件、raw read、shell、subagent 或 connector bypass；
- Windows PowerShell 5.1/7、中文与带空格路径、冷/warm bootstrap；
- Qoder 只依据 Capsule 得出事故结论并完成最终回答；
- 任务期零非预期网络和 wrapper 退出后无残留子进程。

CLI rehearsal 的画面只能标为：

> `Mac CLI evidence · Python response gate passed · Qoder host acceptance pending`

## 评委应看到的证据顺序

1. 真实生产矛盾：Agent 需要私有上下文，但全文披露不可接受。
2. 清晰边界：只有 Capsule 跨越 Airlock-controlled boundary。
3. 可验证 Local AI：Apple M4 CPU 上 OpenVINO mode/model/revision/device 可见。
4. 有 utility 的安全缩减：flagship required facts `3/3` 与 estimated-token context reduction 同时出现。
5. 诚实 trade-off：Mean Recall@K 数值变化与 P95 latency 代价同图。
6. 诚实未完成项：Windows、Intel、Qoder host、Agent Task Completed 清晰标记 PENDING。

## 比赛材料映射

- README Hero 与首屏事实：[README](../README.md)
- 数字定义与准入位置：[Claims Ledger](claims-ledger.md)
- 可直接发布的中文文章初稿：[ModelScope article](modelscope-article.md)
- 60 秒成片与未剪辑证据原片：[Demo script](demo-script.md)
- 发布前硬门：[Submission checklist](submission-checklist.md)
- Windows/Qoder 实机 oracle：[Qoder acceptance](qoder_acceptance.md)

## Windows/Qoder 回填槽位

以下位置在实机证据出现前不得替换为完成态：

```text
[PENDING_WINDOWS_QODER_SCREENSHOT: real Qoder Skill invocation]
[PENDING_WINDOWS_QODER_TRACE: first content access = wrapper analyze]
[PENDING_CAPSULE_ONLY_AGENT_ANSWER: source/local_ref citations]
[PENDING_WINDOWS_PERFORMANCE: cold / warm / p50 / p95 on named Intel device]
[PENDING_UNCUT_VIDEO: full trigger → wrapper → Capsule → answer trajectory]
```

不得创建仿真的 Qoder 界面、虚假 Windows 终端或虚假硬件 badge 来填这些位置。

## Claims 规则

- 每个数字先登记到 [Claims Ledger](claims-ledger.md)，再进入 README、文章、图片或视频。
- 测试、benchmark、flagship 与独立 Qoder 验收是不同证据层，不能互相替代。
- 图片裁剪后仍须保留 `Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1`。
- 合成 benchmark 不能外推为通用安全、真实 Agent utility 或跨硬件保证。
- 未经用户确认，不填 author、项目 LICENSE、公开仓库、ModelScope、研习社或视频 URL。

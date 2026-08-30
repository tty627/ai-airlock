# AI Airlock 60 秒 Demo Script

> Frozen benchmark 版本：`v0.1.0-rc.1` · source commit
> `495f89c6349afbdd741576439b3b85369d26671a`。
> 当前源码候选：annotated、unsigned `v0.1.0-rc.4` · tag object
> `2a50625aa95443e328573704cf42e9c633621ffe` · commit
> `52a215727115f32937cb78561e88a63fdae5adf2` · tree
> `46bc0f55eed58b7234338d4ff4e32bc71c348f8a`。
> 所有数字分别受对应 RC 身份和 evidence 边界约束；准入定义见
> [Claims Ledger](claims-ledger.md)。

主线：

> `Private Data → Detect / Transform / Isolate → OpenVINO Relevance → Safe Context Capsule →
> Agent`
> `真实 Qoder Capsule-only Task Completed = NOT_RUN (host absent)`

## 当前事实与拍摄边界

| 项目 | 当前状态 | 画面允许写什么 |
|---|---|---|
| macOS clean checkout | **PASS** | `212 passed / 6 skipped`；6 项均因 PowerShell unavailable |
| Apple M4 CPU OpenVINO CLI | **PASS** | fixed model/revision、`openvino_embedding`、CPU、A/B 与 trade-off |
| Python strict response gate | **PASS** | `Python response gate passed` |
| rc.4 scoped GitHub Python CI | **PASS_WITH_SCOPE** | main `33293985019` / tag `33294040300`；四个 job 各 `212 passed / 8 skipped`；不等于 wrapper/Qoder/Intel evidence |
| Windows / PowerShell 5.1/7 | **rc.3 FAIL / rc.4 EARLIER SUBSET PASS / ORPHAN FAULT FAIL / CANDIDATE FAIL** | 同时显示早期 scoped PASS 与后续 required fault FAIL；不得显示完整 Windows PASS |
| Qoder host / Capsule-only answer | **NOT_RUN** | Qoder host 缺席；只能显示 `Qoder host absent / NOT_RUN` |
| Intel hardware performance | **NOT RUN** | 不填设备数字，不挂 NPU/GPU badge |

Mac CLI rehearsal 不是 Qoder Agent Task Completed。只有真实 Qoder 界面、Skill 自动发现、wrapper tool
trace、Capsule-only 最终回答与 non-bypass 证据同时存在，才能替换 Qoder 占位。

## 素材分类

### 现在可在 Mac 拍摄

1. **静态视觉资产**：Hero、架构、benchmark、Capsule、flagship flow、End Card。
2. **合成 fixture 文件树**：只显示项目相对路径和文件类型；不打开 raw Secret、PII 或 Injection 原文。
3. **release identity**：tag、完整 source SHA、tree SHA、clean status。
4. **evidence integrity**：`SHA256SUMS` 三项 `OK`。
5. **Mac OpenVINO health / analyze**：只显示净化后的结构化字段；隐藏本机 prompt、用户名和绝对路径。
6. **Python Qoder gate**：标为 `Python strict response gate`，不能标为 Windows wrapper 或 Qoder。
7. **frozen benchmark 图**：同时展示 relevance、estimated-token context reduction 和 P95 latency 代价。
8. **测试状态**：`212 passed / 6 skipped`，同时显示 `PowerShell unavailable only`。

建议录屏前把 shell prompt 临时设置为中性文本，并裁掉菜单栏、通知、用户目录、远程主机名与账号。
不得为了画面清洁修改 frozen tag 或 evidence。

### 仍须由 Windows / Qoder 真实素材补齐

1. Qoder 在新会话中自动发现并选择真实安装的 `ai-airlock` Skill。
2. 第一次接触目标内容的动作是 `scripts/run.ps1 analyze ... --relevance-backend openvino --json`。
3. rc.4 已覆盖的 5.1/7 独立 cold/warm、中文 + 空格 analyze 等 regression subset 只有在原始素材与
   manifest 可追溯时才能入镜；clean source-artifact bootstrap/network 与 remaining timeout/fault matrix
   仍需补测。
4. Qoder tool trace 证明没有 editor raw read、search、index、attachment、shell、subagent、MCP 或 connector
   bypass。
5. Qoder 只从 `safe_context.facts` 得出事故根因，并引用 `source:local_ref`。
6. 任务期非预期网络计数仍为 `NOT_MEASURED`；covered wrapper cases 的 residual count `0` 只能限定引用。
7. 12 个 positive 与 12 个 negative triggers 的真实执行摘要。
8. Intel AI PC 性能；必须记录具体 CPU/device、OS、OpenVINO、cold/warm 定义与失败数。

替换前统一使用：

```text
[PENDING — REAL WINDOWS/QODER FOOTAGE REQUIRED]
```

不得制作虚假的 Qoder UI 截图，也不得用 Mac CLI、静态 PowerShell 审查或 Python gate 替代。

## Mac 素材拍摄清单

### M1 · 冻结身份与完整性

画面内容：

```text
Tag      v0.1.0-rc.1
Commit   495f89c6349afbdd741576439b3b85369d26671a
Tree     4fe991ded88f38a6c1952c506d20005d2956a915
Status   clean
SHA256   3/3 OK
```

录制真实命令，但最终画面只保留上述中性卡片；不要显示 evidence 生成时的临时绝对路径。

### M2 · 合成事故与本地边界

使用 [flagship-flow.svg](../assets/competition/flagship-flow.svg)。文件树只显示：

```text
demo/incident/
├── application.yaml
├── payment-service.log
├── production.log
├── customers.csv
├── .env.example
└── README.md
```

角标：`Synthetic incident fixture · raw values not shown`。

### M3 · OpenVINO 真实参与

从已验证 Mac 环境录制 `health --json` 和 OpenVINO `analyze --json`。只放行以下字段：

```text
mode              openvino_embedding
model             intfloat/multilingual-e5-small
revision          614241f622f53c4eeff9890bdc4f31cfecc418b3
device            CPU
fallback_state    not_used
```

画面角标：`Mac CLI evidence · Apple M4 CPU · not Windows/Qoder`。

### M4 · Capsule

优先使用 [capsule-example.svg](../assets/competition/capsule-example.svg)，不要滚动展示完整 raw JSON。
可显示：

```text
decision                  ALLOW_WITH_TRANSFORM
required facts retained   3 / 3
forbidden values observed 0 / 252   (frozen known-fixture values; analyze stdout/stderr/audit)
```

`raw_sensitive_spans_forwarded=0` 只作为同一安全卡片中的辅助字段，不能单独放大为“零泄漏”。

### M5 · A/B 与代价

使用 [benchmark-results.svg](../assets/competition/benchmark-results.svg)。必须在同一画面展示：

```text
Mean Recall@K              0.583333 → 0.9375
Cross-lingual Mean Recall@K 0.4375   → 1.0
Flagship estimated-token reduction 66.5564% → 75.3515%
CLI P95 latency            103.052  → 1204.529 ms
```

前两项分别是 12 个合成任务与其中 4 个跨语言任务的算术平均。

脚注必须保持可读：`Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1`。

## 最终 60 秒成片

### 0–7s · 真实生产问题

**画面**：深蓝 Hero，左侧是私有日志/配置/客户数据，右侧是 Agent，中央边界关闭。

**字幕**：

```text
Agents need production context.
Production context is private — and may be hostile.
```

**口播**：

> Agent 要解决真实生产问题，就需要日志、配置和客户数据；但这些上下文既私密，也可能夹带恶意指令。

### 7–15s · Airlock 边界

**画面**：使用 [architecture.svg](../assets/competition/architecture.svg)，依次高亮
Detect、Transform / Isolate、OpenVINO Relevance、Capsule。

**字幕**：`Only the Safe Context Capsule crosses the Airlock-controlled boundary.`

**口播**：

> AI Airlock 在本机检测、变换和隔离，再用 OpenVINO 从已净化内容中选择任务相关证据。

### 15–27s · Mac 实测 OpenVINO

**画面**：M3 的真实 Mac CLI 净化字段；右下角保持 `not Windows/Qoder`。

**字幕**：

```text
OpenVINO embedding · CPU · fixed revision · no fallback
Mac CLI evidence · v0.1.0-rc.1
```

**口播**：

> 在冻结的 rc.1 上，Apple M4 CPU 的公开 CLI 已实跑固定模型与 revision，并明确报告没有 fallback。

### 27–38s · Safe Context Capsule

**画面**：M4 卡片，先出现 `3/3 required facts`，再出现 `0/252 observed`。角标限定为
`252 frozen known-fixture values · analyze stdout/stderr/audit`。

**字幕**：

```text
Required facts retained  3/3
Forbidden values observed 0/252
Synthetic flagship · checked public outputs
```

**口播**：

> 支付事故 Capsule 保留了三个预注册根因事实；在本次合成 flagship 的规定公开输出中，252 个禁用值
> 未观察到命中。

### 38–50s · 收益与代价

**画面**：M5 A/B 图，同时显示 Mean Recall@K、estimated-token context reduction 与 P95 latency。

**口播**：

> 在本次 frozen run 中，OpenVINO variant 的 12-task Mean Recall@K 从 0.583333 变为 0.9375；
> flagship estimated-token context reduction 在 `utf8_bytes_div_4_ceil_v1` 下从 66.5564% 变为
> 75.3515%；CLI P95 从 103.052 毫秒上升至 1204.529 毫秒。

### 50–56s · Qoder 回填镜头

**当前 Mac 包装版画面**：显示橙色占位：

```text
Qoder host absent / NOT_RUN
rc.3 Windows FAIL; rc.4 earlier subset PASS / orphan-pipe fault FAIL / candidate FAIL
```

**最终提交版替换条件**：只有完成真实 Windows/Qoder 验收后，替换为连续镜头：自然语言触发 →
wrapper tool trace → Capsule-only 根因回答。不得剪掉首次内容访问动作。

**口播（当前版）**：

> Python response gate 已通过；rc.3 Windows cold health 正式失败。exact rc.4 的早期 Windows functional
> subset 已通过，但后续 orphan-pipe 必需 oracle 在 wrapper 返回后仍观察到一个 descendant，因此 rc.4
> candidate 为 FAIL；Qoder host 缺席且尚未执行。

### 56–60s · End Card

**画面**：使用 [video-end-card.svg](../assets/competition/video-end-card.svg)。

**字幕 / 口播**：

> **AI Airlock. Your data stays. Your Agent works.**

当前 End Card 必须保留 `Mac evidence ready · rc.3 Windows FAIL · rc.4 earlier subset PASS / orphan fault
FAIL / candidate FAIL · Qoder NOT_RUN`，在新候选实机证据全部回填前
不得改成 `OpenVINO × Intel AI PC × Qoder validated`；同时保留
`Airlock-controlled path · real host non-bypass pending`。

## 未剪辑证据原片

60 秒成片不能替代验收原片。建议准备四段不可跳剪的原片，并为每段保存环境清单、命令文本、exit
code、stdout/stderr hash 与录像 SHA-256。

### U1 · Mac clean checkout / OpenVINO / benchmark

连续记录：

1. tag、commit、tree、clean status；
2. evidence `SHA256SUMS` 校验；
3. Python、OS、CPU 与 OpenVINO 版本；
4. `health --json`；
5. flagship `analyze --relevance-backend openvino --json`；
6. strict Python response gate；
7. frozen benchmark JSON 的 run ID 与关键 paths。

如 raw terminal 包含用户名或绝对路径，原片只进入受控私有 evidence，不进入公开成片；公开版使用安全
裁剪。不要用后期遮挡掩盖实际命令参数是否正确。

### U2 · Windows PowerShell acceptance（rc.3 FAIL / rc.4 EARLIER SUBSET PASS / ORPHAN FAULT FAIL）

rc.3 已记录 PowerShell 5.1 与 7 cold health 的固定失败，不能剪辑成 PASS。rc.4 fresh-tag regression
subset 已覆盖两个 shell 各自 cold+warm health、中文 task + 带空格路径 analyze、固定 invalid/missing
errors、cross-shell concurrent cold、covered residual `0`，以及 `252` markers × `26` stdout/stderr surfaces
`0 hits`。但后续 exact-tag PowerShell 7 orphan-pipe rerun 为 `32.164s`、exit `2`、stdout `0`、单一
`AIRLOCK_INVALID_JSON`，external cleanup 前/后 residual `1/0`，所以 rc.4 candidate 必须为 `FAIL`。
empty-cache/network/remaining faults 仍未知，但不是 FAIL 原因。早期 subset bundle 为 `99/99`，其 hash 为
`3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b`；后续 failure bundle 为 `29/29`，
hash 为 `00b336f9193ba3fd4bad4aa3df157d5d08132c46e64c6ae3d4418c05dca5677a`。完整 oracle 以
[qoder_acceptance.md](qoder_acceptance.md) 为准。

### U3 · Qoder flagship（NOT_RUN · host absent）

从全新 Qoder 会话开始，连续记录 Skill 选择、权限设置、第一次目标内容访问、wrapper 命令、单 JSON
Capsule、最终回答与 `source:local_ref`。不得先打开或索引 fixture。若 non-bypass 无法证明，结果只能是
`INCONCLUSIVE`。

### U4 · 12+12 trigger matrix（NOT_RUN · host absent）

每条 trigger 使用全新会话。记录 `12/12 positive` 与 `12/12 negative` 的逐例轨迹、误触发、bypass、
泄漏和 task completion；当前只能写 `STATIC_SPEC_DEFINED`，不能预填通过。

## 证据清单

每个公开镜头都应登记：

```text
asset_id:
source_commit:
evidence_run_id:
environment:
capture_type: mac_cli | windows_wrapper | qoder_host | static_asset
source_file_or_json_path:
uncut_video_sha256:
published_clip_sha256:
redaction_review:
claim_ids:
reviewer:
```

静态资产不冒充实机录像；机器可读数字必须引用 [Claims Ledger](claims-ledger.md) 中的 Claim ID。

## 一票否决式剪辑错误

- 把 Mac CLI rehearsal、Python gate 或静态 PowerShell 审查写成 Qoder Agent Task Completed。
- 把 Apple M4 结果写成 Windows、Intel AI PC、GPU 或 NPU 结果。
- 只展示 Recall 增益而裁掉 P95 latency 代价。
- 把 `3/3 required facts` 写成真实 Agent task success。
- 把 `raw_sensitive_spans_forwarded=0` 或 `252 markers × 26 stdout/stderr surfaces / 0 hits` 写成无范围的“零泄漏”。
- 展示 raw Secret、PII、Injection 原文、用户名、绝对路径、账号、远程主机、通知或可用 endpoint。
- 伪造 Qoder 界面、URL、CI badge、Windows 画面或硬件 telemetry。
- 让视频、README、文章和 benchmark 使用不同 commit、run 或指标定义。

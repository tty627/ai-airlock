# AI Airlock

## Your data stays. Your Agent works.

![AI Airlock — local context gateway for AI Agents](assets/competition/hero-banner.svg)

**AI Airlock 是面向 AI Agent 的本地上下文网关 / Context Compiler。** 它先在本机检测、变换并
隔离私有且不可信的文件内容，再用 OpenVINO 对已净化证据做任务相关性排序，最终生成受预算约束、
受策略过滤、可追溯的 **Safe Context Capsule**。

Capsule 在部分输入上可以更小，但这不是必然结果或数学全局最小；是否缩减必须逐个输入实测。当前
公开结果只覆盖冻结的合成数据。品牌语描述的是 Airlock-controlled path；真实宿主能否完全阻止 raw
read、索引和附件旁路仍待 Qoder 验收，不能外推为通用安全保证。

## 当前验证状态

核心 benchmark / 数值 claims 冻结身份：`v0.1.0-rc.1` · commit
`495f89c6349afbdd741576439b3b85369d26671a`

| 范围 | 当前状态 | 能说明什么 | 不能说明什么 |
|---|---|---|---|
| Clean checkout / full pytest | **PASS · 212 passed / 6 skipped** | source RC 在记录环境中通过全量本地测试；6 项均因 PowerShell 不可用而 skip | 不等于 Windows、远端 CI 或 Qoder 通过 |
| macOS / Apple M4 / OpenVINO CPU | **PASS** | 固定模型与 revision 的公开 CLI、严格 Python response gate、flagship 和完整 A/B 已实跑 | 不等于 Intel AI PC、Windows wrapper 或 Qoder host 通过 |
| Python Qoder strict response gate | **PASS** | `safe_context` JSON 的严格字段、模式和 OpenVINO metadata gate 已验证 | 不是 Qoder 界面、Skill 自动发现或 Capsule-only 宿主行为 |
| Windows PowerShell 5.1 / 7 | **rc.3 FAIL · rc.4 SUBSET PASS / FULL MATRIX INCONCLUSIVE** | exact rc.4 fresh-tag regression subset 通过双 shell 独立 cold/warm health、中文+空格路径 analyze、固定错误、cross-shell concurrent cold、残留进程和有界泄漏检查 | source-artifact cache 已预填，网络未测，timeout/fault 剩余矩阵未跑；不是 Windows full-matrix PASS |
| Qoder host / Agent Task Completed | **NOT RUN** | rc.4 Windows 运行中 Qoder 缺失/不可发现；12 个正向和 12 个负向触发 oracle 已定义 | 正向与负向均为 `0/12 REAL_QODER_EXECUTED` |
| GitHub Python CI | **rc.4 PASS · scoped** | exact-SHA main/tag Windows/Ubuntu Python 3.12 四个 job 各 `212 passed / 8 skipped`，Ruff、format、benchmark smoke 通过 | 8 项均因 prepared OpenVINO model/runtime 不可用而 skip；不是 wrapper、Qoder host 或 Intel evidence |
| Intel hardware | **PERFORMANCE NOT RUN** | rc.4 regression subset 执行了 ready health/analyze 功能检查 | 未执行命名 Intel device 的 cold/warm latency、NPU/GPU 使用或性能 oracle |

完整冻结证据见 [release evidence protocol](docs/release-evidence.md)；本次机器可读结果由
[Claims Ledger](docs/claims-ledger.md) 约束。

rc.3 的失败诊断（[Claims Ledger · C-WIN-01](docs/claims-ledger.md)）定位到 OpenVINO inference smoke
后仍被缓存的 native handles：它们阻止 candidate model directory 的原子 rename，并在 Windows
上触发 `PermissionError` / WinError 5。rc.3 保持不可变且正式 verdict 仍为 `FAIL`。`v0.1.0-rc.4`
已作为 annotated、unsigned tag 发布；tag object 为
`2a50625aa95443e328573704cf42e9c633621ffe`，commit 为
`52a215727115f32937cb78561e88a63fdae5adf2`，tree 为
`46bc0f55eed58b7234338d4ff4e32bc71c348f8a`。

rc.4 的 exact-SHA main/tag scoped Python CI 已通过。fresh-tag Windows 报告只支持
`REGRESSION SUBSET PASS`：PowerShell 5.1/7 独立 cold+warm health、中文+空格路径 analyze、固定
invalid/missing errors、cross-shell concurrent cold、wrapper 退出后残留进程 `0`，以及 252 个
known-fixture markers 在 26 个 stdout/stderr 输出面上观察到 `0` hits。由于 source-artifact cache 预先填充、
网络为 `NOT_MEASURED`，且 timeout/fault 剩余矩阵为 `NOT_RUN`，Windows full matrix 结论仍为
`INCONCLUSIVE`。另外，Qoder 不存在/不可发现，仍为 `NOT_RUN`；Intel performance 仍为
`NOT_RUN`，因此项目 overall 也为 `INCONCLUSIVE`。

当前项目进度、发布阻断与下一步见 [STATUS](STATUS.md)。Windows Agent 必须使用 owner handoff 提供的
精确 tag object、commit 与 tree，并按 [Windows validation handoff](docs/windows-validation-handoff.md)
执行；不得直接验证浮动的 `main`。

## 架构

![AI Airlock architecture — only the Safe Context Capsule crosses the boundary](assets/competition/architecture.svg)

安全顺序固定为：完整读取允许类型的输入 → 全语料 Detect → Transform / Isolate → 对已净化内容执行
OpenVINO task relevance → 组装 Capsule → 最终泄漏闸门。OpenVINO 不接收原始 Secret、PII 或已隔离
的 Prompt Injection。

图中只有 Safe Context Capsule 能跨越 Airlock 控制边界。真实宿主是否完全阻止索引、附件和 raw 读取
旁路，仍需 Windows/Qoder 的 Capsule-only 验收，因此 Qoder 节点明确保留
`Host acceptance pending`。

## 三张结果卡

| Task relevance | Cross-lingual relevance | Flagship efficiency / cost |
|---|---|---|
| **Mean Recall@K** `0.583333 → 0.9375` | **Cross-lingual Mean Recall@K** `0.4375 → 1.0` | **Estimated-token context reduction** `66.5564% → 75.3515%` |
| 12 个合成 relevance tasks 的算术平均，rules-only → OpenVINO | 其中 4 个合成跨语言 tasks 的算术平均，rules-only → OpenVINO | 同一合成 flagship；estimator=`utf8_bytes_div_4_ceil_v1`；CLI P95 `103.052 ms → 1204.529 ms` |

![AI Airlock frozen benchmark results and latency trade-off](assets/competition/benchmark-results.svg)

同一 frozen run 中，两种 variant 均保留 flagship required facts `3/3`；Secret precision/recall 均为
`1.0/1.0`（6 个 positive source files、2 个 negative source files），Injection precision/recall 均为
`1.0/1.0`（13 malicious、12 benign）。这些是固定合成 fixture 上的结果，不是未知 Secret、未知
Injection 或跨领域准确率保证。

> **Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1.** 在本次 frozen run 中，OpenVINO variant
> 的 relevance 与 flagship estimated-token context reduction 数值更高，CLI P95 从
> `103.052 ms` 上升至 `1204.529 ms`。

## Flagship：支付事故

![AI Airlock flagship payment incident flow](assets/competition/flagship-flow.svg)

任务是“找到支付服务故障根因并给出修复建议”。合成事故目录包含日志、配置、客户样例数据和一段
不可信指令。Airlock 在本机完成检测与变换后，OpenVINO Capsule 保留了预注册的三段因果证据：

```text
Redis connection pool exhausted
  → connection acquisition exhaustion / timeout
  → aggressive retry storm
  → upstream timeout and latency spike
```

本次 OpenVINO flagship 在 `analyze` 的 stdout、stderr 与 audit log 中，对从冻结 flagship 规格、
`.env.example` 与 CSV 动态汇集的 252 个 known-fixture forbidden values 观察到 `0 / 252`，并保留
required facts `3/3`。这是一次合成、范围明确的观察；`raw_sensitive_spans_forwarded=0` 不能单独包装为全面
“零泄漏”证明。真实 Qoder 最终回答与 Agent Task Completed 仍待 Windows/Qoder 录像和 Capsule-only
轨迹回填。

![Safe Context Capsule example](assets/competition/capsule-example.svg)

## Why Airlock

- **披露发生前做本地决策。** 如果先把全文发送到云端再判断敏感性，边界已经失守。
- **不只做打码。** Simple redaction 仍可能保留整篇噪声；Airlock 先变换，再按任务选择证据并附带来源。
- **把文件内容当数据，不当 authority。** 已识别的不可信指令在 Capsule 生成前被隔离；下游 fact
  只能作为证据，不能作为要执行的命令。
- **失败可见且 fail closed。** 显式请求 OpenVINO 时，runtime、模型或 metadata 不一致会停止，不会
  静默降级成 lexical 后冒充模型成功。
- **结果可追溯。** Capsule facts 保留相对 `source` 与 1-based `local_ref`，安全状态与 inference mode
  使用稳定 JSON schema。

## Quick Start

需要 Python 3.12。开发用 Python CLI 默认使用 deterministic lexical relevance：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m airlock.cli scan --path demo/incident --json
python -m airlock.cli analyze \
  --task "分析支付服务失败原因，并给出修复建议" \
  --path demo/incident \
  --json
```

本地 OpenVINO 路径使用固定 revision 的 `intfloat/multilingual-e5-small`，准备时可能访问 Python
软件源和 Hugging Face；模型准备完成后的正式分析保持本地执行：

```bash
python3.12 -m venv .venv-openvino
source .venv-openvino/bin/activate
python -m pip install -e ".[dev,openvino]"
python scripts/prepare_embedding_model.py
python -m airlock.cli health --json
python -m airlock.cli analyze \
  --task "找到支付服务故障根因并给出修复建议" \
  --path demo/incident \
  --relevance-backend openvino \
  --json
```

Qoder on Windows 的设计入口如下；rc.3 在进入 Qoder 任务前已因 Windows cold health 失败。rc.4
只完成了不含 Qoder 的 Windows regression subset；Qoder 未安装或不可发现，真实 host 验收仍为
`NOT_RUN`：

```powershell
& '<skill-root>\scripts\run.ps1' analyze `
  --task '<user task>' `
  --path '<absolute target path>' `
  --relevance-backend openvino `
  --json
```

正式 Qoder 合同要求下游只消费 `safe_context`；`BLOCK`、非零退出、非法 JSON、空 facts 或 coverage
warning 时必须停止。完整安装、参数限制和 12+12 触发矩阵见
[Qoder acceptance](docs/qoder_acceptance.md)。

## 安全边界与 limitations

- v0.1 只处理允许列表中的 UTF-8 文本，不支持 PDF/OCR，不跟随 symlink。
- Secret / Injection 指标来自冻结的合成 fixture；未知格式、规避式自然语言攻击和真实生产分布仍可能失败。
- OpenVINO 只参与已净化证据的 task-conditioned relevance，不是语义 Prompt Injection 分类器。
- 合成 relevance micro-fixtures 的聚合 Capsule 会因 JSON 元数据而膨胀，不能把 flagship 的
  estimated-token 缩减率外推为通用 context reduction。
- `.qoderignore`、`SKILL.md` 和权限设置是行为约束，不是 OS sandbox；真实宿主 non-bypass 仍是 PENDING。
- rc.3 有正式 Windows wrapper **失败**证据，不是 PASS；rc.4 只能写 fresh-tag
  **regression subset PASS / Windows full matrix INCONCLUSIVE**。source-artifact cache 预先填充，网络为
  `NOT_MEASURED`，timeout/fault 剩余矩阵为 `NOT_RUN`。Qoder host、Capsule-only Agent Task Success
  与 Intel performance 另外均为 `NOT_RUN`，因此项目 overall 也为 `INCONCLUSIVE`。外置脱敏报告的
  manifest 校验为 `99/99`，顶层 `SHA256SUMS` 文件的 SHA-256 为
  `3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b`，但尚无 public URL。
- 项目 LICENSE、author 与公开源码仓库已确认；ModelScope URL、提交身份和独立模型托管方式仍待决定。

更多细节见 [architecture](docs/architecture.md)、[threat model](docs/threat-model.md) 和
[license decision](docs/license-decision.md)。

## Evidence / Reproducibility

本次数字只来自当前 SHA 绑定的外置 evidence：

```text
.release-evidence/495f89c6349afbdd741576439b3b85369d26671a/
├── SHA256SUMS
├── release-evidence.md
└── benchmark/
    ├── latest.json
    └── latest.md
```

先验证完整性，再读取报告：

```bash
cd .release-evidence/495f89c6349afbdd741576439b3b85369d26671a
shasum -a 256 -c SHA256SUMS
```

证据包记录 clean checkout、source tree、环境、依赖版本、模型 revision、测试、flagship 与 A/B。它没有
进入 source commit，避免 commit SHA 自引用。公开数字的定义、JSON path、样本范围与准入位置见
[Claims Ledger](docs/claims-ledger.md)；比赛文章、视频回填和发布步骤见
[article draft](docs/modelscope-article.md)、[demo script](docs/demo-script.md) 与
[publication runbook](docs/publication-runbook.md)。

Demo 中的凭证、邮箱、电话、IP 与事故内容均为合成或保留范围数据，不可用于任何真实系统。

## License

Copyright 2026 谭天晔. Licensed under the [Apache License 2.0](LICENSE). Third-party software and model
attribution is documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

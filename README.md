# AI Airlock

## Your data stays. Your Agent works.

![AI Airlock — local context gateway for AI Agents](assets/competition/hero-banner.svg)

**AI Airlock 是面向 AI Agent 的本地上下文网关 / Context Compiler。** 它先在本机检测、变换并
隔离私有且不可信的文件内容，再用 OpenVINO 对已净化证据做任务相关性排序，最终生成受预算约束、
受策略过滤、可追溯的 **Safe Context Capsule**。

Capsule 在部分输入上可以更小，但这不是必然结果或数学全局最小；是否缩减必须逐个输入实测。当前
公开结果只覆盖冻结的合成数据。品牌语描述的是 Airlock-controlled path；真实宿主能否完全阻止 raw
read、索引和附件旁路仍待 TraeCode/Qoder 验收，不能外推为通用安全保证。

## 当前验证状态

核心 benchmark / 数值 claims 冻结身份：`v0.1.0-rc.1` · commit
`495f89c6349afbdd741576439b3b85369d26671a`

| 范围 | 当前状态 | 能说明什么 | 不能说明什么 |
|---|---|---|---|
| Clean checkout / full pytest | **PASS · 212 passed / 6 skipped** | source RC 在记录环境中通过全量本地测试；6 项均因 PowerShell 不可用而 skip | 不等于 Windows、远端 CI 或 Qoder 通过 |
| macOS / Apple M4 / OpenVINO CPU | **PASS** | 固定模型与 revision 的公开 CLI、严格 Python response gate、flagship 和完整 A/B 已实跑 | 不等于 Intel AI PC、Windows wrapper 或 Qoder host 通过 |
| Python Qoder strict response gate | **PASS** | `safe_context` JSON 的严格字段、模式和 OpenVINO metadata gate 已验证 | 不是 Qoder 界面、Skill 自动发现或 Capsule-only 宿主行为 |
| Windows PowerShell 5.1 / 7 | **rc.3 FAIL · rc.4 FAIL · rc.5 SCOPED PASS / FULL MATRIX INCONCLUSIVE** | exact rc.5 的两套 orphan-pipe oracle 均为 residual `0`、无需 external cleanup；health 与中文/空格路径 analyze 也通过 | empty-cache、network 与其余 external fault 项仍未跑，不能写成完整 Windows PASS |
| rc.7 public archive | **PASS · 234 passed / 9 skipped** | 140-entry archive 匿名下载哈希一致，并在独立 Python 3.12 环境安装测试；production wrapper 正常分析与中文凭据外传阻断通过 | skips 包含未预置模型与 Windows symlink 条件；不是 Agent host evidence |
| TraeCode/Qoder host / Agent Task Completed | **NOT RUN** | exact rc.7 已安装到 fresh TraeCode workspace 并预热；宿主 oracle 已定义 | 应用仍需登录；Skill discovery、wrapper-first、Capsule-only 和最终回答没有真实连续轨迹 |
| GitHub Python CI | **rc.7 PASS** | main run `33306936519` 与 tag run `33307066407` 的 Windows/Ubuntu jobs 全绿 | CI 不是完整 PowerShell fault matrix 或 Agent host evidence |
| Intel hardware | **CPU FUNCTIONAL + WARM LATENCY PASS_WITH_SCOPE** | Intel Core i7-14700KF 上 exact rc.7 为 7/7 contract-valid；P50 `5082.451 ms`、P95 `5292.249 ms` | 小样本；不包含 NPU/GPU、冷启动或通用性能声明 |

完整冻结证据见 [release evidence protocol](docs/release-evidence.md)；本次机器可读结果由
[Claims Ledger](docs/claims-ledger.md) 约束。

rc.3 的失败诊断（[Claims Ledger · C-WIN-01](docs/claims-ledger.md)）定位到 OpenVINO inference smoke
后仍被缓存的 native handles：它们阻止 candidate model directory 的原子 rename，并在 Windows
上触发 `PermissionError` / WinError 5。rc.3 保持不可变且正式 verdict 仍为 `FAIL`。`v0.1.0-rc.4`
已作为 annotated、unsigned tag 发布；tag object 为
`2a50625aa95443e328573704cf42e9c633621ffe`，commit 为
`52a215727115f32937cb78561e88a63fdae5adf2`，tree 为
`46bc0f55eed58b7234338d4ff4e32bc71c348f8a`。

rc.4 的 exact-SHA main/tag scoped Python CI 已通过。早期 fresh-tag Windows functional subset 也通过了
PowerShell 5.1/7 独立 cold+warm health、中文+空格路径 analyze、固定 invalid/missing errors、cross-shell
concurrent cold、covered residual `0`，以及 `252` 个 known-fixture markers × `26` 个 stdout/stderr surfaces
的 `0 hits`。但随后在同一 immutable exact tag 上，PowerShell 7 orphan-pipe 故障桩于 `32.164s` 返回
exit `2`、空 stdout 和单一 `AIRLOCK_INVALID_JSON`，wrapper 返回时仍有 `1` 个 nonce-matched descendant；
外置 harness 清理后才降为 `0`。无残留是必需 release oracle，因此 rc.4 Windows wrapper、candidate 与
rc.4 overall verdict 均为 `FAIL`。empty source-cache bootstrap、network 和其余 fault 项仍分别为
`NOT_RUN / NOT_MEASURED`；Qoder 与 Intel performance 也仍为独立的 `NOT_RUN`，都不是此次 FAIL 的原因。

修复已冻结为 annotated、unsigned `v0.1.0-rc.5`：tag object
`7d4034f9e8575658190dacef53f9ba749de8ed6c`，commit
`9abf825943f8f68f2bc6cd3afc1baa8717e0c01a`，tree
`88b914598de60fa385820860b13dc8bd6db26b7d`。精确 main/tag CI 与 detached exact-tag Windows scoped
验证均已完成。PowerShell 5.1/7 orphan-pipe fault 分别在 `3.352s / 3.937s` 返回固定错误，wrapper 返回后的
harness 核验中 residual 均为 `0`，`cleanup_performed=false`；两壳 health、post-fault health 与中文/空格路径 analyze 也
通过。外置 bundle manifest 为 `55/55`，其顶层 `SHA256SUMS` 文件 SHA-256 为
`107ae4a8954e0a7965a48e3b9248b74789850e1a2b6793ac422a4d7b62cc82bb`，尚无 public URL。该结果只能写
`RC5_WINDOWS_SCOPED_VALIDATION=PASS_WITH_SCOPE`；empty-cache、network、remaining external faults、Qoder
与 Intel performance 未关闭，所以 rc.5 full acceptance / overall 仍为 `INCONCLUSIVE`。

当前发布候选是 annotated、unsigned `v0.1.0-rc.7`：tag object
`98c9dc9c7710a631b066415d2605d7b6bcbb0eba`，commit
`9ec87e72843299779bf8788acf24e563aeff334e`，tree
`430446f531e30dce6caff4af83359d49468d4a00`。它在 rc.6 基础上补齐不带 URL 的中文凭据外传任务阻断；
main/tag CI、匿名 Release 下载、clean archive install 和 Intel CPU wrapper sample 已通过。Skill archive
SHA-256 为 `961a0f6b07637f5e404b8fac836886ca3a5419b3681d81898815fe434a97b0a1`。详见
[Windows Intel rc.7 evidence](docs/windows-intel-rc7-evidence.md)。

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

TraeCode/Qoder on Windows 的正式设计入口如下。exact rc.7 已安装到 fresh TraeCode workspace，并在任务
窗口之外完成模型预热；真实 host 仍需登录后的连续 discovery、wrapper-first 与 Capsule-only 轨迹：

```powershell
& '<skill-root>\scripts\run.ps1' analyze `
  --task '<user task>' `
  --path '<absolute target path>' `
  --relevance-backend openvino `
  --json
```

正式宿主合同要求下游只消费 `safe_context`；`BLOCK`、非零退出、非法 JSON、空 facts 或 coverage
warning 时必须停止。TraeCode deadline oracle 见 [TraeCode acceptance](docs/trae-acceptance.md)，完整
12+12 触发矩阵见 [Qoder acceptance](docs/qoder_acceptance.md)。

## 决赛实验入口：受控补证与引用报告

决赛开发分支新增独立的本地 session 接口：所有者预先读取授权材料，服务建立固定净化案例；
Agent 通过带凭据的本机客户端获得首轮证据，最多再补证两轮，并校验事故报告的引用。
这条路径不替代上面的 rc.7 `run.ps1` 单轮合同，当前仍需 Core Ultra、真实生产力宿主与权限隔离验收。

- [启动服务、补证与生成报告](docs/finals-session.md)：包括 owner/Agent 身份关系、CLI、草稿格式和边界。
- [18 项真实宿主验收](docs/finals-host-acceptance.md)：包含原文读取拒绝、模型推理、最终诊断和调用轨迹。
- [决赛计划与发布准入](docs/finals-2026-plan.md)：功能冻结、硬件、演示及材料提交依赖。

新增引用检查只验证证据成员关系与已识别的敏感输出，不验证诊断语义正确性。
session 的累计预算估算新披露响应 JSON，不能冒充完整 Agent token 成本。
`integrations/airlock-incident-report/SKILL.md` 是可选独立报告 Skill，须单独安装和验证；
主 Skill 发布包保持只含一个 `SKILL.md`。

## 安全边界与 limitations

- v0.1 只处理允许列表中的 UTF-8 文本，不支持 PDF/OCR，不跟随 symlink。
- Secret / Injection 指标来自冻结的合成 fixture；未知格式、规避式自然语言攻击和真实生产分布仍可能失败。
- OpenVINO 只参与已净化证据的 task-conditioned relevance，不是语义 Prompt Injection 分类器。
- 合成 relevance micro-fixtures 的聚合 Capsule 会因 JSON 元数据而膨胀，不能把 flagship 的
  estimated-token 缩减率外推为通用 context reduction。
- `.qoderignore`、`SKILL.md` 和权限设置是行为约束，不是 OS sandbox；真实宿主 non-bypass 仍为 `NOT_RUN`。
- rc.3 有正式 Windows wrapper **失败**证据，不是 PASS。rc.4 的早期 functional subset `PASS` 仍按范围
  保留，但后续 exact-tag orphan-pipe 必需 oracle `FAIL` 决定 rc.4 candidate 与 overall 均为 `FAIL`。
  早期 subset bundle 为 `99/99`，其顶层 `SHA256SUMS` 文件 SHA-256 为
  `3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b`；后续 failure bundle 为 `29/29`，
  对应 hash 为 `00b336f9193ba3fd4bad4aa3df157d5d08132c46e64c6ae3d4418c05dca5677a`。两者均无 public URL，
  不得互相替代。rc.5 exact-tag scoped bundle 为 `55/55`，顶层 `SHA256SUMS` 文件 hash 为
  `107ae4a8954e0a7965a48e3b9248b74789850e1a2b6793ac422a4d7b62cc82bb`；它证明两壳 orphan-pipe
  no-residual oracle 与指定 health/analyze controls 通过，但不覆盖 empty-cache/network/remaining faults、
  Qoder host 或 Intel performance。
- rc.7 在 Intel Core i7-14700KF 上的 7 次 warm wrapper sample 为 P50 `5082.451 ms`、P95
  `5292.249 ms`，全部 contract-valid；这不是 NPU/GPU 或 Agent host evidence。
- 项目 LICENSE、author、公开源码仓库和 ModelScope owner `Ararag1` 已确认；Skill/文章/比赛公开 URL
  仍待发布，独立模型托管仍未建立。

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

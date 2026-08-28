# AI Airlock Final Integrator Report

> **历史 P0 审计记录，不是当前 release 状态。** 本文固定记录 `0ae0ae...` 与当时 dirty
> candidate 的失败证据，供 Security、Relevance 和 Release Closure 回归使用。P0 修复后的
> 正式判定必须以对应 RC SHA 的 checkout 外 evidence bundle 为准；不得从本文复制旧 SHA、
> 文件计数、测试计数或 `SUBMIT: NO` 作为新 revision 的验证结果。

审计日期：2026-08-28（Asia/Shanghai）
审计角色：Final Integrator + Red Team Release Reviewer
正式仓库 HEAD：`0ae0ae22192a47380e39eea2535f02834341fd7e`
结论：**NO-GO / 不应以当前状态正式提交比赛**

本报告只依据当前代码、实际命令、实际输出、临时红队夹具和 clean-copy 复现。除新增本报告外，本轮没有修改产品代码、测试、benchmark ground truth 或文档 claims。

## 1. Executive verdict

### 核心结论

如果提交截止时间在 2 小时后：

```text
SUBMIT: NO
```

决定该结论的五个事实：

1. **Secret 边界失败。** 新的、常见的带引号 JSON `client_secret` 形态未被识别，完整值进入 lexical 和真实 OpenVINO Capsule/stdout；同时 `privacy.raw_sensitive_spans_forwarded=0` 仍被输出。
2. **Prompt Injection 边界失败。** 新的 sanitizer-bypass / raw-workspace 语义变体得到 0 finding，并因高相关性进入 lexical 与 OpenVINO `safe_context.facts`。
3. **高噪声 relevance 门失败。** 在 3 条必需事实 + 90 条跨服务 hard-negative 英文日志中，OpenVINO 只保留 `2/3` 必需事实，正式 top-8 中有 `6/8` 无关项。
4. **正式仓库不是 release revision。** 审计开始时仓库有 23 个已跟踪修改和 25 个未跟踪必需文件；新增本报告后未跟踪文件为 26 个。真实 HEAD clean checkout 不包含 OpenVINO、Qoder gate、benchmark 与模型准备代码。
5. **PowerShell/Qoder 运行态未验证。** 本机没有 PowerShell 和 Qoder，因此 Windows wrapper、Skill trigger、Capsule-only、无 raw bypass 与 Agent Task Completed 均为 `NOT VERIFIED`。

### 正面证据

- OpenVINO 真实进入 Python CLI 和正式 Skill 的设计路径；metadata、固定模型、CPU device、chunk 数和 `fallback_state=not_used` 可验证。
- OpenVINO 缺模型或缺 runtime 时 fail closed，未发现静默回退到 lexical。
- 标准 synthetic benchmark 中，OpenVINO Recall@K、Precision@K、MRR、cross-lingual recall 和旗舰 context reduction 明显优于 lexical。
- 把当前候选内容冻结到隔离临时 commit 后，可以从 clean copy 安装、准备模型、运行 `128 passed, 6 skipped`、旗舰和完整 A/B。

这些正面证据证明“实现有实质进展”，但不能覆盖已经观察到的安全泄漏、注入绕过、高噪声 utility 失败和正式 release identity 缺失。

## 2. Actual architecture

实际代码路径不是 README 中的概念图，而是：

```text
SKILL.md
  -> scripts/run.ps1
  -> python -m airlock.cli
  -> airlock.cli.main()
  -> airlock.pipeline.analyze()
  -> ingestion.load_path()
  -> detectors.detect_all()
  -> transform_text()  [redact / pseudonymize / isolate]
  -> rank_openvino_evidence() 或 rank_evidence()
  -> OpenVINOEmbeddingBackend  [仅 OpenVINO 分支]
  -> build_capsule()
  -> enforce_no_sensitive_leaks()
  -> airlock.qoder_gate  [正式 PowerShell wrapper]
  -> canonical JSON Capsule
  -> Qoder 仅消费 safe_context  [合同要求，运行态未验证]
```

关键实现位置：

- `SKILL.md:21-70`：正式 Qoder 入口、OpenVINO 强制要求、Capsule-only 合同与停止条件。
- `scripts/run.ps1:1-12`：从 `$PSScriptRoot` 固定项目根和模型路径。
- `scripts/run.ps1:645-744`：参数门；拒绝非 OpenVINO backend，并注入固定模型目录。
- `scripts/run.ps1:746-894`：Python 3.12、venv、`.[openvino]` 与固定模型 bootstrap。
- `scripts/run.ps1:896-1073`：调用 CLI、捕获 stdout/stderr、运行 Qoder schema gate、canonical rebuild。
- `src/airlock/cli.py:63-86`：开发 CLI；这里默认仍是 `lexical`。
- `src/airlock/pipeline.py:173-241`：读取、检测、变换与隔离。
- `src/airlock/pipeline.py:337-455`：决策、relevance、Capsule 与 final leak guard。
- `src/airlock/pipeline.py:396-417`：OpenVINO/lexical 分支与 OpenVINO fail-closed。
- `src/airlock/relevance/openvino_ranker.py:217-433`：模型路径、manifest、readiness 与 runtime。
- `src/airlock/relevance/openvino_ranker.py:673-823`：hybrid ranking 与真实 inference metadata。
- `src/airlock/capsule/builder.py:84-159`：Capsule 构造与预算。
- `src/airlock/qoder_gate.py:296-427`：严格 schema、OpenVINO metadata 和 canonical JSON gate。

未发现仍存活的 `Path.cwd()` 模型路径依赖，也未发现 OpenVINO 失败后 silent lexical fallback。

发现的结构风险：

- final leak guard 只知道 detector 已登记的 sensitive values，无法发现 detector 漏检值。
- `raw_sensitive_spans_forwarded` 是构造时写入的 0，不是对最终 Capsule 的独立扫描结果。
- schema/constants 分散在 Python schema、builder、ranker、Qoder gate 和 PowerShell 中，当前基本一致，但存在人工漂移风险。
- `capsule_json_ready` 未被生产路径调用；`redact_secrets`、`isolate_instructions` 主要是测试接口。
- `scan` 的正式 wrapper 也会做 OpenVINO/model bootstrap，尽管 scan 本身不使用 embedding。

## 3. Repository state

```text
Repository state: DIRTY
```

实际状态：

| 项目 | 结果 |
|---|---|
| Branch / HEAD | `main` / `0ae0ae22192a47380e39eea2535f02834341fd7e` |
| Last commit | `chore: establish AI Airlock v0.1 baseline` |
| Modified tracked files | 23 |
| Untracked required files before this report | 25 |
| Current untracked files, including this report | 26 |
| Current porcelain records | 49 |
| `git diff --check` | PASS |

未跟踪文件包含发布必需的：

- `.github/workflows/ci.yml`
- `.qoderignore`
- 完整 `benchmark/`
- Qoder acceptance/release/submission 文档
- `scripts/prepare_embedding_model.py`
- `src/airlock/qoder_gate.py`
- `src/airlock/relevance/model_setup.py`
- `src/airlock/relevance/openvino_ranker.py`
- OpenVINO、Qoder gate、wrapper contract 测试

其他检查：

- `models/`、`.venv-openvino/`、pytest/ruff cache 和 egg-info 均被 Git ignore；未发现模型 cache 将被纳入源码包。
- 未发现新的临时 debug 源文件。
- `docs/release-evidence.md` 包含历史 `/tmp/...` 审计路径，属于证据记录，不是运行依赖；README 的 `/tmp` 只用于 audit 示例。
- demo 与 benchmark 中存在明确标注为 synthetic 的假凭证夹具；没有证据表明模型 cache 或真实凭证被纳入候选文件，但这不是通用 secret-clean 保证。
- 既有 benchmark 指向临时 audit commit `914747...`；该 commit 在历史临时仓库中真实存在，但不在正式仓库对象/引用中，不能作为正式 release identity。

## 4. OpenVINO truth audit

### 正式 Skill 是否一定走 OpenVINO

```text
YES — 对“Qoder 遵守当前 SKILL.md 并调用正式 run.ps1”这一条件成立。
NO  — 对开发 Python CLI 的默认值不成立；其默认仍是 lexical。
NOT VERIFIED — 真实 Qoder 是否一定触发并遵守该合同尚未实测。
```

静态证据：

- `SKILL.md` 的唯一正式 analyze 命令显式包含 `--relevance-backend openvino`。
- `run.ps1` 拒绝缺失、重复或非 `openvino` backend。
- wrapper 成功路径要求 Qoder gate 看到 `mode=openvino_embedding`、固定 model/revision、非空 device、非负 chunks 和 `fallback_state=not_used`。

### 真实 runtime

从仓库外 cwd `/tmp`、无模型路径环境变量运行 clean candidate：

| 字段 | 实测值 |
|---|---|
| backend/mode | `openvino_embedding` |
| model | `intfloat/multilingual-e5-small` |
| revision | `614241f622f53c4eeff9890bdc4f31cfecc418b3` |
| device | `CPU` |
| OpenVINO | `2026.3.1` |
| OpenVINO GenAI | `2026.3.1.0` |
| OpenVINO Tokenizers | `2026.3.1.0` |
| chunks processed | `71` |
| fallback state | `not_used` |
| clean flagship wall-clock | `1.240 s` |
| stdout / stderr | `3575 bytes / 0 bytes` |

### 失败方式

| 故障 | 结果 |
|---|---|
| 指定不存在的模型目录 | exit 1；stdout 空；stderr 固定 `INFERENCE_UNAVAILABLE` JSON |
| 使用无 OpenVINO runtime 的 base venv | exit 1；stdout 空；stderr 固定 `INFERENCE_UNAVAILABLE` JSON |
| silent lexical fallback | 未观察到 |
| 错误声称 OpenVINO 仍运行 | 未观察到 |

结论：**OpenVINO truthfulness 与 Python fail-closed 为 PASS；PowerShell 层仅静态通过，运行态未验证。**

## 5. Relevance red-team

### 既有 80 条高噪声 fixture

现有测试可以通过，但 80 条噪声高度同质，均近似“build completed successfully / cache warmed”，会直接命中 benign penalty。

| 指标 | Lexical | OpenVINO |
|---|---:|---:|
| Required retained | 1/3 | 3/3 |
| Irrelevant selected | 0 | 1 |
| Capsule tokens | 246 | 370 |
| Reduction | 86.1330% | 79.1432% |
| Wall-clock | 64.516 ms | 1147.057 ms |

这证明旧 fixture 被修复，不证明真实 hard-negative 环境已解决。

### 新 90 条跨服务 hard-negative

任务：`为什么支付服务突然大量失败？`

输入：93 个文件，包含 3 条必需事实与 90 条英文无关日志；无关项同时覆盖 CSS build、MIT License、frontend asset、routine healthcheck，以及其他服务的 timeout/retry/queue/pool/failure。输入 manifest SHA-256：

```text
c6aea202aa1f60b773b77aa1c3f7ee819fe255158c3357f24513750f5bd5d19d
```

| 指标 | Lexical | OpenVINO |
|---|---:|---:|
| Required retained | 1/3 | **2/3** |
| Irrelevant selected | 7/8 | **6/8** |
| Recall@8 | 0.3333 | **0.6667** |
| Precision@8 | 0.1250 | **0.2500** |
| Capsule tokens | 590 | 619 |
| Reduction | 68.7831% | 67.2487% |
| Wall-clock | 68.213 ms | 1153.077 ms |
| OpenVINO chunks | — | 93 |

OpenVINO top-8 中只有“retry traffic increased 12x”和“Redis connection pool exhausted”两条必需事实；“Payment timeout rate increased”在扩展诊断排序中仅为第 35 名。

按任务书的硬门：

```text
required facts retained != 3/3
Context Minimization P0: FAIL
```

## 6. Holdout relevance

新订单服务 holdout 未使用现有 benchmark ground truth：15 个文件，3 relevant + 12 irrelevant。输入 manifest SHA-256：

```text
e35c5cacbb481bb9ccae3fb44c30395d3333982c7e5ce841eaa4e808efd1fdcb
```

任务：`为什么订单服务突然出现延迟和失败？`

| 指标 | Lexical | OpenVINO |
|---|---:|---:|
| Required retained | 3/3 | 3/3 |
| Irrelevant selected | 0 | 1 |
| Median latency, 3 runs | 56.970 ms | 959.281 ms |
| Capsule tokens | 382 | 454 |
| Reduction | -30.8219% | -55.4795% |

OpenVINO 前三名正确，但第 4 名误选 help-center navigation；该小输入因 JSON metadata 开销而膨胀。结论：utility 保留，但相对 lexical 没有产品优势，且约慢 17 倍。

## 7. Security red-team

### 任务指定 marker

对任务书指定的 TOKEN marker，在裸文本、普通 `TOKEN=`、YAML `token:`、JSON `"token"`、log prose 和 Markdown prose 六种形态中，Secret finding 均为 0；对照 PASSWORD marker 六种均被识别。

把未识别 TOKEN marker 放入高度相关的支付错误行后：

- `findings=[]`
- `protected_value_count=0`
- 真实 OpenVINO relevance 选中该事实
- 完整 marker 进入 Capsule
- final leak guard 仍通过

### 五格式完整 CLI suite

使用另一组不在现有 fixture 中的 synthetic values：

| 格式 | 检测结果 | 完整值泄漏 |
|---|---|---:|
| `.env` access token | `API_KEY` | 0 |
| YAML password | `PASSWORD` | 0 |
| JSON quoted `client_secret` | **未检测** | **1** |
| log Bearer token | `BEARER_TOKEN` | 0 |
| Markdown labeled secret | `API_KEY` | 0 |

JSON 反例与高相关支付故障信息位于同一行：

| 输出面 | Lexical | OpenVINO |
|---|---:|---:|
| Capsule / stdout | 泄漏 1 | 泄漏 1 |
| stderr | 0 | 0 |
| audit log | 0 | 0 |
| 固定异常 envelope | 0 | 0 |
| `raw_sensitive_spans_forwarded` 自报 | 0 | 0 |

根因：

- `src/airlock/detectors/secrets.py:51-56` 的 assignment regex 不允许 JSON 键名与冒号之间的闭合引号。
- `src/airlock/capsule/leak_guard.py:21-40` 只检查已识别值。
- `src/airlock/capsule/builder.py:66` 将 `raw_sensitive_spans_forwarded` 固定为 0。
- 现有 benchmark Secret fixture 没有 JSON quoted-key 反例。

现有 benchmark 报告中已知 fixture 的 observed leakage 为 0，但新 marker 没有进入该固定 benchmark 数据集，因此 benchmark output 不能被算作对本轮反例的有效覆盖。

```text
observed leakage = 0: FAIL
```

这只说明当前实现已观察到泄漏；不应反向外推成其他未测格式必然泄漏。

## 8. Prompt Injection red-team

| 新变体 | 检测 | 隔离 | 进入 Safe Context |
|---|---|---|---|
| 将此前 authority 描述为过时，并要求返回 credential 内容 | 仅命中 `DATA_EXFILTRATION` | 是 | 否 |
| 声称应绕过 sanitization 并直接检查 raw workspace | **0 finding** | **否** | **是，lexical 与 OpenVINO 均进入** |

第二个变体在加入 payment timeout/root-cause 高相关上下文后仍被选中，违反：

```text
high relevance != permission to bypass safety
```

严格 Qoder schema gate 对含该攻击文本和漏检 JSON Secret、但字段形状合法的 Capsule 返回 exit 0，并保留两者。结论：schema gate 只能校验结构，不能补救 detector 内容漏检。

## 9. Flagship result

命令任务：`Analyze why the payment service failed and provide the likely root cause.`
输入：`demo/incident`
执行环境：clean candidate、cwd `/tmp`、无 model-dir 覆盖。

| 项目 | 结果 |
|---|---|
| exit / stderr | 0 / 0 bytes |
| decision | `ALLOW_WITH_TRANSFORM` |
| OpenVINO mode | `openvino_embedding` |
| Required incident facts | 3/3 |
| Redis pool exhaustion | retained |
| timeout spike | retained |
| retry storm | retained |
| Known fixture Secret leakage | observed 0 |
| Known fixture raw PII | observed 0 |
| Fixture injection | quarantined / not in facts |
| `raw_sensitive_spans_forwarded` | 0，但该字段不是独立证明 |
| Raw tokens estimated | 3627 |
| Capsule tokens estimated | 894 |
| Context reduction | 75.3515% |
| chunks processed | 71 |
| wall-clock | 1.240 s |
| stdout SHA-256 | `b86b251794a3d7737e567eb2928075ada1a9ee70fbc10575f5870eab7d734374` |

旗舰本身通过，但它是窄 synthetic fixture；不能覆盖第 7、8 节的新安全反例或第 5 节的新 hard-negative relevance 失败。

## 10. Rules vs OpenVINO A/B

完整 clean candidate benchmark：

- status：PASS
- clean provenance：true
- temporary candidate commit：`4291ff8ca5276c44eb3602f972f35dcc009605dc`
- report SHA-256：`2f719fa809d4bbea497cf0e59c163fcadf1f606542986980d287f4bf1b922c10`
- 该 commit 仅存在于本轮隔离临时仓库，不是正式 release commit。

| Metric | Rules | OpenVINO |
|---|---:|---:|
| Required facts retained, flagship | 3/3 | 3/3 |
| Irrelevant selected, new high-noise top-8 | 7/8 | 6/8 |
| Mean Recall@K, standard synthetic | 0.583333 | 0.937500 |
| Mean Precision@K, standard synthetic | 0.729167 | 0.937500 |
| Cross-lingual Recall@K | 0.437500 | 1.000000 |
| Secret leakage, existing fixtures | 0 | 0 |
| Secret leakage, novel quoted JSON | 1 | 1 |
| Injection TP/FP/TN/FN, existing fixtures | 13/0/12/0 | 13/0/12/0 |
| Novel sanitizer-bypass handling | missed | missed |
| Flagship Capsule tokens | 1213 | 894 |
| Flagship context reduction | 66.5564% | 75.3515% |
| Flagship wall-clock, same dev run | 69.992 ms | 1251.299 ms |
| 42 CLI total, clean run | 3327.774 ms | 17851.427 ms |
| P95, clean run | 70.212 ms | 1179.772 ms |

### OpenVINO 产品价值

```text
PARTIAL
```

理由：标准 synthetic 与 cross-lingual 指标显著改善，旗舰 Capsule 更小；但新 high-noise 仍漏 1/3 必需事实，order holdout 不优于 lexical，安全漏检与 backend 无关且同样会穿过 OpenVINO，延迟显著上升。

## 11. run.ps1 production audit

本机没有 `pwsh`、`powershell`、`qoder` 或 Qoder app：

```text
POWERSHELL_RUNTIME_NOT_VERIFIED
WINDOWS_WRAPPER_E2E_NOT_VERIFIED
QODER_RUNTIME_NOT_VERIFIED
```

静态审计：

| 检查项 | 结论 |
|---|---|
| `.venv` bootstrap | IMPLEMENTED；限定 Python 3.12 |
| OpenVINO extra | IMPLEMENTED；安装 `ProjectRoot[openvino]` |
| Model setup | IMPLEMENTED；固定模型/路径，失败 exit 2 |
| Repository-relative path | IMPLEMENTED；基于 `$PSScriptRoot` |
| UTF-8 | IMPLEMENTED |
| Path with spaces / Chinese path/task | quoting 代码存在；Python 下层实测通过，PowerShell 未实测 |
| Outside repository cwd | Python CLI 实测通过；PowerShell 仅静态确认 |
| Timeout / output bound | 每阶段 deadline 与 4 MiB 限制存在 |
| JSON stdout purity | 捕获后 gate/canonical publish；未在 PowerShell 实测 |
| Exit codes | 固定映射存在；未在 PowerShell 实测 |
| Missing model/runtime | 无 lexical fallback；Python 层实测通过 |

残余风险：没有统一总 deadline；mutex、pip、model setup 的阶段上限可叠加；进程树清理由 PowerShell best-effort 完成，没有 Windows Job Object 实机故障证据。

## 12. Schema fail-closed gate

Python `airlock.qoder_gate --require-openvino` 对以下 8 种 invalid Capsule 全部拒绝：

1. wrong schema version
2. missing `safe_context`
3. facts 为 string
4. invalid decision
5. OpenVINO mode 缺 model
6. device 为空
7. chunks_processed 为负数
8. metadata 声称 fallback

结果：`8/8` exit 1，stdout/stderr 为空。相关单测：`24 passed, 6 skipped`；6 个 skip 均为 PowerShell runtime case。

发现的 cross-field 缺口：

- `ALLOW + empty facts + no coverage_warning` 可通过 Python gate；SKILL 的 Agent 流程会再停止，但 gate 本身不完整。
- facts 非空而 `files.inspected=0` 可通过并被消费。
- 内容安全反例只要 schema 合法就会通过 gate。

因此：Python 结构 gate 为 **PASS with gaps**；`run.ps1` 动态 fail-closed 为 **NOT VERIFIED**。

## 13. Qoder status

`SKILL.md` 已明确：

```text
User request
  -> Airlock FIRST
  -> validate Capsule
  -> only safe_context
  -> Agent reasoning
```

并明确禁止 raw read、workspace search/index、attachment、arbitrary shell、subagent、MCP/connector、secret reconstruction 和 quarantined instruction 执行。

但 `.qoderignore` 与文字合同不是 OS sandbox。由于本机没有 Qoder，本轮无法运行：

- 中文 flagship
- 英文 private logs
- prompt injection positive trigger
- 普通 C++ / embedding negative trigger
- Qoder → Skill → OpenVINO → Capsule → final answer 连续轨迹
- raw file 是否在 Airlock 前被宿主读取

```text
Skill -> Qoder: PENDING
Qoder -> Task Completed: PENDING
```

这是提交风险，不是已验证能力；它本身不是对 Python/OpenVINO 实现的否定。

## 14. Clean checkout reproduction

### 正式仓库 HEAD

从正式仓库 clone `0ae0ae2...`：

| Gate | 结果 |
|---|---|
| Fresh Python 3.12 venv / base install | PASS |
| Base tests | `69 passed` |
| Ruff lint / format | PASS |
| `scripts/prepare_embedding_model.py` | MISSING，exit 2 |
| `benchmark/run_benchmark.py` | MISSING，exit 2 |
| `openvino_ranker.py` / `qoder_gate.py` / `.qoderignore` | MISSING |
| OpenVINO flagship | unsupported arguments，exit 1 |
| Final checkout status | clean |

结论：

```text
OFFICIAL HEAD CLEAN CHECKOUT: FAIL
```

### 当前候选内容的隔离 clean copy

把当前所有 81 个非忽略文件复制到隔离仓库并创建临时 audit commit `4291ff8...`：

| Gate | 结果 |
|---|---|
| Base install / pip check | PASS |
| Base tests | `125 passed, 9 skipped` |
| OpenVINO extra / pip check | PASS |
| Empty model target + allowed trusted source cache conversion | PASS，15.97 s |
| Prepared artifact | 241,340,848 bytes |
| Full tests | `128 passed, 6 skipped` |
| Ruff lint / format | PASS |
| OpenVINO flagship outside cwd | PASS，3/3 facts |
| Full A/B | PASS |
| Final candidate status | clean |

6 个 skip 全部来自 PowerShell 不可用。

另做了空 Hugging Face cache 冷下载：运行 299.81 s 后只取得约 10 MiB 且无继续进展，本轮终止该审计下载；因此“完全空 cache 的联网冷准备时长/稳定性”未完成验证。README 明确允许可信 download cache，本轮成功结果属于 **cache-assisted clean reproduction**。

结论：当前文件内容具有本地可复现性，但正式 repository revision 不具有该能力。

## 15. Documentation truth audit

| Claim | 分类 | 结论 |
|---|---|---|
| 正式 Skill analyze 显式 OpenVINO | VERIFIED，静态合同 | 真实 Qoder trigger 仍未验证 |
| Python/OpenVINO 在 Apple Silicon CPU 运行 | VERIFIED | clean candidate 已实测 |
| 固定 model/revision、manifest、真实 inference | VERIFIED | cached-source clean setup 通过 |
| OpenVINO unavailable 不 silent fallback | VERIFIED，Python；PowerShell 静态 | Windows runtime 未验证 |
| Flagship 3/3、75.3515% reduction | VERIFIED，仅 synthetic fixture | 不能外推为通用 minimization |
| Recall/Precision `0.583333/0.729167 -> 0.9375/0.9375` | VERIFIED，仅 12 个 synthetic tasks | benchmark gate 本身没有 relevance 最低阈值 |
| Cross-lingual `0.4375 -> 1.0` | VERIFIED，仅 4 个 synthetic cross-lingual tasks | 未证明跨领域泛化 |
| “zero leakage” | MISLEADING，若不限定 fixtures | 新 quoted JSON 已实际泄漏 |
| “Prompt Injection isolated” | MISLEADING，若作为语义级通用能力 | 新 sanitizer-bypass 完全漏检 |
| “minimum task-relevant evidence” | MISLEADING | 实现是 heuristic top-8/token budget，不是全局最小或 task-success optimum |
| `flagship_task_pass` | MISLEADING 名称 | 只是 Capsule oracle，不是真实 Agent/Qoder task completion |
| Qoder integrated / Task Completed | NOT VERIFIED | 文档多数已正确标 pending |
| Windows/Intel support | NOT VERIFIED | 无实机 |
| `demo-script.md` OpenVINO 仍写 PENDING/deterministic_rules | OUTDATED | 本地 Python OpenVINO 已验证；Qoder/Windows 仍 pending |
| `competition-story.md` 的部分 `[REAL RESULT REQUIRED]` | OUTDATED | synthetic 数字已有，但必须带范围和红队失败 |
| `submission-checklist.md` 称尚无 frozen bundle | PARTLY OUTDATED | 有临时 clean evidence，但没有正式 release commit |
| 原仓库 clean/release ready | FALSE | 审计开始时 23 modified + 25 untracked；新增本报告后为 26 untracked |

比赛官方页面当前公开显示报名截止为 **2026-08-31 15:59**，并要求使用 Qoder/WorkBuddy/TRAE Work 等生产力 Agent 作为 Skill 稳定调用的验证环境。checklist 中登录态 `23:59` 说法本轮无法重现；报名截止也不能等同作品提交截止，应按更早时间管理风险并向组织方确认：[ModelScope Production AI Skills 官方页](https://www.modelscope.cn/events/289/summary)。

## 16. Completion scores

| 维度 | Score / 10 | Evidence | Remaining risk |
|---|---:|---|---|
| Core functionality | 7.0 | CLI、Capsule、测试、旗舰可运行 | 安全与高噪声 failure 会破坏核心承诺 |
| OpenVINO integration | 8.0 | 真实 inference、metadata、fail-closed、clean candidate | Windows/Qoder 与 Intel 未验证 |
| Security | 3.0 | 现有 fixture 通过 | 已观察 JSON Secret 泄漏与 injection bypass |
| Relevance quality | 5.0 | 标准/cross-lingual 显著提升 | 新 hard-negative 仅 2/3，top-8 多数无关 |
| Context minimization | 4.0 | 旗舰缩减 75.3515% | high-noise FAIL；小 holdout 膨胀 |
| Benchmark credibility | 5.5 | 黑盒 CLI、hash、clean candidate provenance | relevance PASS 无质量阈值；覆盖窄；无真实 Agent |
| Production Skill packaging | 6.0 | Skill 合同和 wrapper 静态设计较完整 | PowerShell 未运行；scan bootstrap 过重 |
| Qoder integration | 2.0 | 文档与静态入口存在 | discovery/trigger/Capsule-only/Task Completed 全未验证 |
| Reproducibility | 4.0 | 候选 clean copy 可复现 | 正式 HEAD 不含候选；空 cache 冷下载未完成 |
| Demo reliability | 6.5 | synthetic flagship 稳定 3/3 | 真实 Qoder demo 未录制；fixture 过窄 |
| Competition narrative | 7.0 | 场景与 OpenVINO 角色清晰 | “data stays/minimal/safe” 当前证据不足 |
| Submission readiness | 2.0 | 已有较完整材料与审计 | 4 个技术/发布 blocker + Qoder pending |

## 17. MUST FIX BEFORE SUBMISSION

最多保留以下 5 项：

1. **修复 Secret 漏检与虚假零泄漏指标。** 至少覆盖 quoted JSON key、任务指定 TOKEN marker 形态，并增加独立 final-output check；`raw_sensitive_spans_forwarded` 不得在漏检时仍无条件为 0。回归测试必须覆盖 Capsule、stdout、stderr、audit、error 和 Qoder gate。
2. **修复 sanitizer/raw-workspace Prompt Injection 语义绕过。** 新变体必须隔离，并证明高 relevance 不能改变 safety decision；增加与 benchmark 文案不同的 frozen holdout。
3. **修复高噪声 relevance P0。** 在不改 ground truth 迎合结果的前提下，让 90 条跨服务 hard-negative case 达到 3/3，并把 hard-negative recall/precision 设为发布 gate，而不是只检查 `status=MEASURED`。
4. **冻结真实 release revision。** 把 23 modified + 25 个原始 untracked 候选及本报告完整审查后提交到正式仓库；从该 commit clean checkout 重跑 install、model setup、pytest、ruff、flagship、benchmark 和远端 CI，所有 evidence 必须指向同一正式 SHA。
5. **完成真实 Windows PowerShell 5.1/7 + Qoder 验收。** 覆盖 cold/warm bootstrap、中文/空格路径、stdout purity、timeout、正负 trigger、Capsule-only、零 raw bypass 与最终 Task Completed；无法完成时只能以“Qoder acceptance pending”提交，不能宣称已集成完成。

本轮没有对这些 blocker 做产品 patch：Secret、Injection、relevance、release identity 和 Qoder runtime 是相互独立的失败面；只修两个 regex 会让候选看起来更好，却不会改变 `SUBMIT: NO`，也不符合 Final Reviewer 的边界。

## 18. NICE TO HAVE

- 为 build/dev/transitive dependencies 增加平台化 lock/hash，降低长期漂移。
- 给 PowerShell bootstrap 增加统一总 deadline 和 Windows Job Object 故障测试。
- 收紧 Qoder gate 的 cross-field consistency：facts、files.inspected、coverage warning 之间建立一致性约束。
- 扩展 held-out 到更多领域、日志形态、语言、真实 Intel CPU/GPU/NPU，并报告 valid/error counts。
- 优化 OpenVINO warm latency，但不要牺牲 3/3 utility 或安全边界。
- 将 `info.json` / `meta.json` 中“开发 CLI opt-in”与“正式 Skill 强制 OpenVINO”分开描述。
- 更新 demo/competition/checklist 的旧 PENDING 与 `[REAL RESULT REQUIRED]`，同时写入本轮反例和范围限定。
- 明确 repository license 和正式提交表单字段。
- 保留 cold-download 失败/速度证据，验证代理、断点续传和 rate-limit 下的用户体验。

## 19. Final SUBMIT YES/NO

```text
IF SUBMISSION DEADLINE WERE IN 2 HOURS:

SUBMIT: NO

Private Data -> Airlock
FAIL

Airlock -> OpenVINO
PASS

OpenVINO -> Safe Context
FAIL

Safe Context -> Minimal Context
FAIL

Skill -> Qoder
PENDING

Qoder -> Task Completed
PENDING

Clean Checkout
FAIL  (official HEAD; isolated candidate snapshot PASS)
```

最终判断：AI Airlock 已经证明 OpenVINO 不是装饰，也证明 Safe Context Capsule 的基本工程链可运行；但它还没有守住自己的首要产品承诺。当前最关键的问题不是再补营销材料，而是先消除已复现的 Secret 泄漏、Prompt Injection 绕过和 high-noise utility 失败，然后把修复后的同一内容冻结成正式 revision，并完成真实 Qoder/Windows 证据。

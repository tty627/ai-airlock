# AI Airlock Claims Ledger

本文件是比赛公开材料的数字准入表。除非另有说明，下面所有实测指标都绑定到：

> **Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1**
> Source commit: `495f89c6349afbdd741576439b3b85369d26671a`
> Run ID: `2026-08-28T06:52:00+00:00-495f89c6349a`

上述 rc.1 benchmark 的权威证据位于 checkout 外的
`.release-evidence/495f89c6349afbdd741576439b3b85369d26671a/`。使用数字前应先在该目录执行
`shasum -a 256 -c SHA256SUMS`。README、文章、视频和图片不得从工作区中的临时运行、旧报告或
手工记忆抄数。GitHub CI 与 Windows 宿主记录使用各表行明确列出的独立证据和范围，不会
反向改写 rc.1 benchmark 数字。

## 公开数字准入表

| ID | Claim / 数值 | 指标定义 | Evidence / 位置 | 环境与样本范围 | 限制条件 | README | 文章 | 视频/图 |
|---|---|---|---|---|---|:---:|:---:|:---:|
| C-TEST-01 | Full pytest：`212 passed / 6 skipped` | OpenVINO 模型准备完成后，在 clean checkout 运行完整 pytest 的结果；6 项 skip 均因 PowerShell 不可用 | `release-evidence.md` → “Install, model preparation, and tests” → “Full pytest after prepare” / “Full skip reason” | macOS 26.5.2、arm64、Apple M4、Python 3.12.14；source RC 全量测试 | 不是 Windows/PowerShell/Qoder、远端 CI 或 Intel 结果；不得写成 `218/218 passed` | 是 | 是 | 可选 |
| C-CI-01 | rc.3 GitHub Python CI：Windows 与 Ubuntu 各 `210 passed / 8 skipped`；Ruff、format、benchmark smoke 均 PASS | 对同一 tagged source commit 先运行 main push CI，再运行 annotated-tag push CI；四个 matrix job 必须全部成功 | Main run [`33264778975`](https://github.com/tty627/ai-airlock/actions/runs/33264778975)，jobs `99132798963` / `99132799076`；tag run [`33264852242`](https://github.com/tty627/ai-airlock/actions/runs/33264852242)，jobs `99132994364` / `99132994474` | `v0.1.0-rc.3`；commit `55eca4ceedb1f7e63e9444b86b32f58f2dccac3f`；tag object `31679f3afb8e3010413b01d7a42df35695b294d3`；GitHub `ubuntu-latest` / `windows-latest`；Python 3.12 | 8 项均因 prepared OpenVINO model/runtime unavailable 而 skip；Windows checkout gate 使用 `core.autocrlf=true`；没有运行 `scripts/run.ps1`、PowerShell 5.1/7、真实 Windows OpenVINO、Qoder 或 Intel hardware | 是，须写 scoped Python CI | 可选 | 否 |
| C-CI-02 | rc.4 GitHub Python CI：Windows 与 Ubuntu 的 main/tag 四个 job 各 `212 passed / 8 skipped`；Ruff、format、benchmark smoke 均 PASS | 精确 candidate commit 的 main push CI 和 annotated-tag push CI 全部成功；绑定 tag object、peeled commit 与 tree | Main run [`33293985019`](https://github.com/tty627/ai-airlock/actions/runs/33293985019)，Windows job `99210391718` / Ubuntu job `99210391785`；tag run [`33294040300`](https://github.com/tty627/ai-airlock/actions/runs/33294040300)，Windows job `99210537344` / Ubuntu job `99210537462` | `v0.1.0-rc.4`；annotated unsigned tag object `2a50625aa95443e328573704cf42e9c633621ffe`；commit `52a215727115f32937cb78561e88a63fdae5adf2`；tree `46bc0f55eed58b7234338d4ff4e32bc71c348f8a`；GitHub Windows/Ubuntu；Python 3.12 | 每个 job 的 8 项 skip 均因 prepared OpenVINO model/runtime unavailable；只是 scoped Python CI，未覆盖 `.[openvino]`、真实模型 bootstrap、`scripts/run.ps1`、PS5.1/7 wrapper、Qoder 或 Intel performance | 是，须写 scoped Python CI | 可选 | 否 |
| C-CI-03 | rc.5 GitHub Python CI：main/tag 两次 workflow 均 PASS；Windows 各 `225 passed / 8 skipped`，Ubuntu 各 `213 passed / 14 skipped`；Ruff、format、benchmark smoke 均 PASS | 精确 candidate commit 的 main push CI 和 annotated-tag push CI 全部成功；绑定 tag object、peeled commit 与 tree | Main run [`33298393856`](https://github.com/tty627/ai-airlock/actions/runs/33298393856)，Windows job `99221893931` / Ubuntu job `99221893989`；tag run [`33298491017`](https://github.com/tty627/ai-airlock/actions/runs/33298491017)，Windows job `99222148261` / Ubuntu job `99222148090` | `v0.1.0-rc.5`；annotated unsigned tag object `7d4034f9e8575658190dacef53f9ba749de8ed6c`；commit `9abf825943f8f68f2bc6cd3afc1baa8717e0c01a`；tree `88b914598de60fa385820860b13dc8bd6db26b7d`；GitHub Windows/Ubuntu；Python 3.12 | skips 包含 prepared OpenVINO model/runtime 或平台特定 Windows Job 不可用；只是 scoped Python CI，不能替代 production wrapper、Qoder 或 Intel performance evidence | 是，须写 scoped Python CI | 可选 | 否 |
| C-CI-04 | rc.6 GitHub CI：main/tag 两次 workflow 的 Windows 与 Ubuntu jobs 均 PASS | 精确 candidate commit 的 main push CI 和 annotated-tag push CI 全部成功；绑定 tag object、peeled commit 与 tree | Main run [`33304754194`](https://github.com/tty627/ai-airlock/actions/runs/33304754194)，Windows job `99239199261` / Ubuntu job `99239199315`；tag run [`33304834373`](https://github.com/tty627/ai-airlock/actions/runs/33304834373)，Windows job `99239409519` / Ubuntu job `99239409610` | `v0.1.0-rc.6`；annotated unsigned tag object `ce81652ad107c59c52184c33417d1e9922d44281`；commit `2ea713a99053dae5ff96f8e9927c300d36439c0e`；tree `3a1554d94892baf8b32dbbdaedbe6f334d6f952c`；GitHub Windows/Ubuntu；Python 3.12 | CI proves the source jobs that ran; it does not prove ModelScope parser acceptance, TraeCode discovery, host non-bypass or Agent Task Completed | 是 | 是，可选 | 否 |
| C-WIN-01 | rc.3 正式 Windows wrapper verdict：`FAIL`；PowerShell 5.1 与 PowerShell 7 cold health 均返回 `AIRLOCK_MODEL_PREPARATION_FAILED` | 在全新 clone 中核对 exact annotated tag object/commit/tree 后，通过唯一生产 wrapper 执行 cold `health --json`；成功 oracle 要求 exit 0 和一个 ready OpenVINO JSON，实际两个 shell 均 exit 2、stdout 为空、stderr 为单个固定错误 JSON | checkout 外的脱敏 `validation-report.md`、环境摘要、两组 cold-health metadata/error 和顶层 `SHA256SUMS`；bundle 尚未发布，无 public evidence URL | `v0.1.0-rc.3` / commit `55eca4ceedb1f7e63e9444b86b32f58f2dccac3f`；Windows 11 Enterprise 25H2 build 26200.8457；Windows PowerShell 5.1.26100.8457；PowerShell 7.6.4 bundled portable runtime（无 system-wide PS7）；Intel Core i7-14700KF；OpenVINO 2026.3.1；首个继承非原生 `PSModulePath` 的 PS5.1 run 已排除，clean-environment rerun 才是权威结果 | 诊断把失败限定为 inference smoke 后缓存的 OpenVINO native handles 阻止 candidate directory 原子 rename（`PermissionError` / WinError 5）；内部 inference smoke 已执行，但 model promotion 在 ready health/analyze 前失败；Qoder `NOT_RUN`，未产生 Capsule、Agent Task Success 或 Intel 性能结论；该记录是失败证据，不是 rc.4 修复证据 | 是，必须写 FAIL | 可选，须写范围 | 否 |
| C-WIN-02 | rc.4 fresh-tag Windows earlier functional regression subset：`PASS_WITH_SCOPE` | exact tag 下通过 PS5.1/PS7 独立 process-cold+warm health、中文+空格路径 analyze、固定 invalid/missing errors、cross-shell concurrent cold、covered residual `0`；252 个 frozen known-fixture markers 遍历 26 个 stdout/stderr 输出面时观察到 `0` hits | checkout 外的早期脱敏报告 bundle；无 public URL；manifest 校验 `99/99`；顶层 `SHA256SUMS` 文件 SHA-256 `3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b` | `v0.1.0-rc.4`；tag object `2a50625aa95443e328573704cf42e9c633621ffe`；commit `52a215727115f32937cb78561e88a63fdae5adf2`；tree `46bc0f55eed58b7234338d4ff4e32bc71c348f8a`；Windows PowerShell 5.1 / PowerShell 7；source-artifact cache 预填 | 只证明早期 functional subset；“cold”不证明 empty-cache bootstrap，network `NOT_MEASURED`，其余 fault 项未跑。后续 C-WIN-03 的必需 oracle `FAIL` 决定 rc.4 candidate verdict；本行不得用于声称 full-matrix `INCONCLUSIVE` 或候选可发布 | 是，只能写 earlier subset PASS + later candidate FAIL | 可选，须带限制 | 否 |
| C-WIN-03 | exact rc.4 orphan-pipe no-residual-process oracle：`FAIL`；rc.4 Windows wrapper/candidate：`FAIL` | checkout-external stub 仅拦截 `airlock.qoder_gate`，消费 stdin 后让 direct gate parent 退出，同时唯一 nonce descendant 继承 stdout/stderr；wrapper 返回后按 PID、executable、nonce 与 creation time 核验 | 权威 rerun `faults/orphan-pipe-ps7-rerun/metadata.json`；`32.164s`、exit `2`、stdout `0` bytes、单一 `AIRLOCK_INVALID_JSON`；external cleanup 前/后 residual `1/0`；failure bundle manifest `29/29`；顶层 `SHA256SUMS` 文件 SHA-256 `00b336f9193ba3fd4bad4aa3df157d5d08132c46e64c6ae3d4418c05dca5677a`；无 public URL | 同一 immutable `v0.1.0-rc.4` tag object/commit/tree；PowerShell 7.6.4；tracked source before/after clean | deadline 与 fixed-error normalization `PASS`，no-residual-process `FAIL`；不是 Qoder、network、empty-cache 或 Intel 测试。首次无完整 metadata 的复现只作 deviation，权威值来自 rerun | 是，必须写 rc.4 FAIL | 是，须带范围 | 是，只能作失败证据 |
| C-WIN-04 | exact rc.5 Windows scoped validation：`PASS_WITH_SCOPE`；PowerShell 5.1/7 orphan-pipe no-residual-process oracles 均 PASS | detached exact-tag checkout；checkout-external stub 触发 inherited-pipe descendant；wrapper 返回后按 PID/executable/nonce/creation time 核验，并以 health、post-fault health 和中文/空格路径 analyze 作两壳 controls | PS5/PS7 fault 分别 `3.352s / 3.937s`、exit `2`、stdout `0`、单一 `AIRLOCK_INVALID_JSON`；两者 residual `0`、`cleanup_performed=false`；两壳 controls PASS；bundle manifest `55/55`；顶层 `SHA256SUMS` 文件 SHA-256 `107ae4a8954e0a7965a48e3b9248b74789850e1a2b6793ac422a4d7b62cc82bb`；无 public URL | `v0.1.0-rc.5` exact tag object/commit/tree；Windows PowerShell 5.1 / PowerShell 7；tracked source clean；source-artifact cache 预填 | 证明指定 fault 和 controls；empty-cache `NOT_RUN`、network `NOT_MEASURED`、remaining external faults `NOT_RUN`、Qoder `NOT_RUN`、Intel performance `NOT_RUN`。只能写 scoped Windows PASS；rc.5 full acceptance / overall 为 `INCONCLUSIVE` | 是，必须带 scope | 是，须带范围 | 可选，须带限制 |
| C-PKG-01 | rc.6 Skill archive：`1,297,879` bytes、138 entries、根目录恰好一个 `SKILL.md`、SHA-256 `8be21cf914a1488c09435e2c242c97e54fdb5cad63dbc783bed8c6e175055d09`；clean install `228 passed / 9 skipped` | 从精确 candidate commit 构建归档，在独立目录解压并使用新的 Python 3.12 venv 安装/测试；随后 cold bootstrap 和 real OpenVINO analyze | [`docs/windows-intel-rc6-evidence.md`](windows-intel-rc6-evidence.md) 与 checkout 外 QA 记录；归档待 GitHub Release 公开 | exact rc.6 commit/tree；Windows 11 Enterprise；Python 3.12.10；OpenVINO 2026.3.1 | 9 skips 只允许写为 prepared-model/symlink 条件；不得简写成“全部测试”；本行不是 ModelScope parser 或 Agent host evidence | 是 | 是 | 否 |
| C-INTEL-01 | Intel CPU warm wrapper：7/7 contract-valid；P50 `5021.900 ms`、P95 `5193.160 ms`、范围 `4960.695–5193.160 ms` | 预热后的 production PowerShell wrapper 连续七次执行同一 OpenVINO analyze；每次解析 JSON 并检查 exit 0、decision、mode、CPU、71 chunks、8 facts、zero fallback 与 `raw_sensitive_spans_forwarded=0` | [`docs/windows-intel-rc6-evidence.md`](windows-intel-rc6-evidence.md) 逐次表；candidate/package identity 同 C-PKG-01 | Windows 11 Enterprise build 26200；Intel Core i7-14700KF；PS7 7.6.4；Python 3.12.10；OpenVINO 2026.3.1；六文件 synthetic payment incident | 七次小样本；包含 PowerShell/Python startup 与 model load；只支持 Intel CPU warm functional/latency；不是 NPU/GPU、cold-start、通用 benchmark、TraeCode/Qoder host 或未知输入安全证据 | 是，须带 scope | 是，须带 scope | 可选，须带 scope |
| C-SPEC-01 | rc.4 published audit-log wrapper oracle：`SPEC_ORACLE_UNREACHABLE` | 静态比对唯一 production wrapper 合同、`SKILL.md`、`scripts/run.ps1` 与冻结 contract tests | production wrapper 传 `--audit-log` 会在 bootstrap 前固定返回 `INVALID_ARGUMENTS`；开发 Python CLI 的 audit-write failure 路径与 `AUDIT_LOG_WRITE_FAILED` 测试仍存在 | exact rc.4 production wrapper contract；Qoder host 未执行 | 这是验收规范一致性发现，不是 rc.4 runtime 或 Qoder `FAIL`；`AUDIT_LOG_WRITE_FAILED` 只能作为 development CLI diagnostic，不能冒充 wrapper evidence | 可选，若提 audit | 可选 | 否 |
| C-UTIL-01 | Flagship required facts：rules-only `3/3`；OpenVINO `3/3` | 合成支付事故 Capsule 中三个预注册事实是否被保留：Redis pool exhaustion、retry storm、timeout/latency spike | `benchmark/latest.json#$['variants']['rules-only']['utility']['required_facts_retained']`、`['required_facts_total']`；OpenVINO 路径把 variant 换为 `openvino` | 同一 flagship fixture、task、policy 与 commit；两 variant 各一次 benchmark workflow | 只证明预注册事实保留，不等于真实 Agent 完成任务，也不证明建议正确或修复已部署 | 是 | 是 | 是 |
| C-SEC-01 | Secret precision / recall：rules-only `1.0 / 1.0`；OpenVINO `1.0 / 1.0` | 文件级 `precision=TP/(TP+FP)`，`recall=TP/(TP+FN)`；本次 `TP/FP/TN/FN=6/0/2/0` | `benchmark/latest.json#$['variants']['rules-only']['security']['secret_detection']['classification']`；OpenVINO 路径把 variant 换为 `openvino` | 6 个 positive source files、2 个 negative source files；两 variant；7 个命名输出面另行检查 | 不是 span/unique-value 级指标；不能外推到未知 Secret 格式或通用检测能力 | 是 | 是 | 是，须带样本范围 |
| C-SEC-02 | Injection precision / recall：rules-only `1.0 / 1.0`；OpenVINO `1.0 / 1.0` | `precision=TP/(TP+FP)`，`recall=TP/(TP+FN)`；本次 `TP/FP/TN/FN=13/0/12/0` | `benchmark/latest.json#$['variants']['rules-only']['security']['prompt_injection']['classification']`；OpenVINO 路径把 variant 换为 `openvino` | 25 个合成用例：13 malicious、12 benign；invocation failures `0` | 这是当前固定数据集上的确定性 detector 结果；OpenVINO 不负责 Injection 分类；不能声称防住所有 Prompt Injection | 是 | 是 | 是，须带 `n=25` |
| C-REL-01 | Mean Recall@K：`0.583333 → 0.9375` | 12 个 relevance task 在各自 `K=4` 时的 recall 算术平均；箭头为 rules-only → OpenVINO | `benchmark/latest.json#$['variants']['rules-only']['relevance']['mean_recall_at_k']`；OpenVINO 路径把 variant 换为 `openvino` | 12 个合成 relevance tasks，12/12 有效；相同预算、输入、环境与 commit | micro-fixture；阈值在该合成集上校准，尚无独立 held-out 与跨硬件验证 | 是 | 是 | 是 |
| C-REL-02 | Cross-lingual Mean Recall@K：`0.4375 → 1.0` | 标记为 `cross_lingual=true` 的 4 个任务在 `K=4` 时 recall 的算术平均；rules-only → OpenVINO | `benchmark/latest.json#$['variants']['rules-only']['relevance']['cross_lingual_mean_recall_at_k']`；OpenVINO 路径把 variant 换为 `openvino` | 4 个合成跨语言任务，属于上述 12-task 数据集 | 样本很小；不得称为通用多语言质量或生产准确率 | 是 | 是 | 是 |
| C-CTX-01 | Flagship estimated-token context reduction：`66.5564% → 75.3515%` | estimator=`utf8_bytes_div_4_ceil_v1`，即每个受测字符串的 estimated tokens 为 `ceil(len(UTF-8 bytes) / 4)`；缩减率为 `1 - capsule_estimated_tokens / raw_estimated_tokens`。rules-only：`1 - 1213/3627 = 0.665564`；OpenVINO：`1 - 894/3627 = 0.753515` | `benchmark/latest.json#$['variants']['rules-only']['context']['context_reduction_ratio']`、`['raw_tokens_estimated']`、`['capsule_tokens_estimated']`；OpenVINO 路径把 variant 换为 `openvino`；实现位置 `benchmark/run_benchmark.py::_estimate_tokens` | 单个合成 flagship 输入；相同 task/policy；benchmark 从公开 CLI I/O 独立估算 token | 不是 byte reduction，也不是真实 tokenizer token count；只适用于该 flagship；relevance micro-fixtures 的聚合 estimated-token context reduction 为负，故不能宣传为普遍缩减 | 是 | 是 | 是，必须写 “flagship estimated-token” |
| C-LAT-01 | CLI P95 latency：`103.052 ms → 1204.529 ms` | 每个 variant 的 42 次公开 CLI 调用墙钟延迟，按 nearest-rank P95（排序后取 `ceil(0.95*n)`）计算；rules-only → OpenVINO | `benchmark/latest.json#$['variants']['rules-only']['performance']['p95_latency_ms']`；OpenVINO 路径把 variant 换为 `openvino` | 单次 full benchmark；每 variant 42 次 CLI invocation；Apple M4 CPU | 不是 Intel、Windows、Qoder、冷启动或 warm steady-state 专项测试；不能据此作跨设备性能承诺 | 是 | 是 | 是，必须与收益同图 |
| C-SAFE-01 | Flagship forbidden values observed：`0 / 252` | 在 OpenVINO flagship `analyze` 的 stdout、stderr 与 audit log 中，搜索从冻结 flagship 规格、`.env.example` 与 CSV 动态汇集的 252 个 known-fixture forbidden values，观察命中数为 0 | `benchmark/latest.json#$['variants']['openvino']['flagship']['forbidden_value_count_found']` 与 `['forbidden_values_tested']`；取值方法见 `benchmark/run_benchmark.py` 的 `_flagship_forbidden_values` 与 `_evaluate_flagship` | 单个合成 flagship；已检查面为 `analyze` stdout、stderr 与 audit log；固定 commit | 只能写“在本次合成 flagship 的已检查输出中未观察到”；不得简写成“零泄漏”或替代 Secret recall；不覆盖未知值 | 是 | 是 | 是，必须显示分母、来源与检查面 |
| C-SAFE-02 | Secret leakage count：两 variant 均 `0` | 将 7 个命名输出面合并为一个受检查输出面并 casefold；对 5 个 known-fixture forbidden markers 逐一判断是否至少命中一次。该值是**被命中的 distinct known-fixture marker 数**，不是 marker 出现总次数，也不是受影响输出面数 | `benchmark/latest.json#$['variants']['rules-only']['security']['secret_detection']['secret_leakage_count']`、`['forbidden_markers_tested']`、`['surfaces_checked']`；OpenVINO 路径同名 | 合成 security fixture；scan/capsule stdout、stderr、audit 与 controlled-error stdout/stderr | 同一 marker 即使出现多次或跨多个面也只计 1；与 C-SAFE-01 的 252 个 flagship forbidden values 是不同分母和范围，不得混称；不能证明未知值不泄漏 | 是，建议用 C-SAFE-01 | 是 | 不建议单独使用 |

## 可直接使用的三张结果卡

为减少断章取义，公开首屏优先使用以下组合，并在同一视图标注环境与范围：

1. **Task relevance** — Mean Recall@K `0.583333 → 0.9375`，12 个合成任务。
2. **Cross-lingual relevance** — Cross-lingual Mean Recall@K `0.4375 → 1.0`，4 个合成跨语言任务。
3. **Flagship trade-off** — Estimated-token context reduction `66.5564% → 75.3515%`；CLI P95 latency
   `103.052 ms → 1204.529 ms`。

固定脚注：

> Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1. Results are scoped to the frozen
> fixtures and do not establish universal security, Windows/Qoder behavior, Intel performance,
> or real-Agent task success.

## 禁止替换成数字的待验证项

rc.4 已有 exact-tag scoped Python CI（C-CI-02）、早期 Windows functional subset（C-WIN-02）和后续
blocking orphan-pipe failure（C-WIN-03）；其 candidate/overall 历史必须保留为 `FAIL`。rc.5 已有 exact-tag
scoped Python CI（C-CI-03）和 Windows scoped validation（C-WIN-04），关闭了同类 orphan-pipe regression，
rc.6 新增 exact-tag CI（C-CI-04）、clean package（C-PKG-01）和 Intel CPU warm wrapper evidence
（C-INTEL-01）。以下项目仍按实际情况保持 `PENDING / NOT_RUN / NOT_MEASURED`：

- exact rc.5 在未预填 source-artifact cache 条件下的 source download/bootstrap，以及任务期网络测量；
- exact rc.5 Windows 未执行的其余 timeout/fault 项；
- Intel NPU/GPU 使用、冷启动性能和跨设备/通用性能；Intel Core i7-14700KF 的 CPU warm 小样本仅按
  C-INTEL-01 准入；
- TraeCode/Qoder 自动发现、正负 triggers、Capsule-only non-bypass；
- 真实生产力 Agent 的最终回答、Task Completed、workspace bypass 次数和任务期网络计数；
- 脱敏 rc.4/rc.5 Windows 报告的 public URL，以及 ModelScope / 研习社 URL、真实截图和最终视频。

C-WIN-03 已违反必需条件，因此 rc.4 Windows candidate 与 overall 均为 `FAIL`；C-WIN-04 不会改写这段
历史。C-WIN-04 只允许把 exact rc.5 的指定 orphan-pipe 和 health/analyze controls 写成
`PASS_WITH_SCOPE`。由于 empty-cache、network、remaining external faults、Qoder 和 Intel performance 未关闭，
rc.5 full acceptance / overall 是 `INCONCLUSIVE`，不得提升为 Windows full-matrix PASS。rc.6 的
C-PKG-01/C-INTEL-01 也不得提升为 TraeCode/Qoder host evidence、NPU/GPU evidence 或 final publication
readiness。

## 使用规则

- `raw_sensitive_spans_forwarded=0` 是程序字段，不是独立的全面零泄漏证据；公开安全表述必须引用
  C-SAFE-01 或 C-SAFE-02 的分母、输出面和 fixture 范围。
- `3/3 required facts` 是 Capsule utility proxy，不是 Capsule-only Agent Task Success。
- `PASS` 只代表 frozen release evidence 中定义的 gate 通过；不得外推为通用安全保证。
- 任何裁剪后的图表仍须保留 “Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1”。

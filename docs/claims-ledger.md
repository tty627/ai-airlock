# AI Airlock Claims Ledger

本文件是比赛公开材料的数字准入表。除非另有说明，下面所有实测指标都绑定到：

> **Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1**
> Source commit: `495f89c6349afbdd741576439b3b85369d26671a`
> Run ID: `2026-08-28T06:52:00+00:00-495f89c6349a`

权威证据位于 checkout 外的
`.release-evidence/495f89c6349afbdd741576439b3b85369d26671a/`。使用数字前应先在该目录执行
`shasum -a 256 -c SHA256SUMS`。README、文章、视频和图片不得从工作区中的临时运行、旧报告或
手工记忆抄数。

## 公开数字准入表

| ID | Claim / 数值 | 指标定义 | Evidence / 位置 | 环境与样本范围 | 限制条件 | README | 文章 | 视频/图 |
|---|---|---|---|---|---|:---:|:---:|:---:|
| C-TEST-01 | Full pytest：`212 passed / 6 skipped` | OpenVINO 模型准备完成后，在 clean checkout 运行完整 pytest 的结果；6 项 skip 均因 PowerShell 不可用 | `release-evidence.md` → “Install, model preparation, and tests” → “Full pytest after prepare” / “Full skip reason” | macOS 26.5.2、arm64、Apple M4、Python 3.12.14；source RC 全量测试 | 不是 Windows/PowerShell/Qoder、远端 CI 或 Intel 结果；不得写成 `218/218 passed` | 是 | 是 | 可选 |
| C-CI-01 | rc.3 GitHub Python CI：Windows 与 Ubuntu 各 `210 passed / 8 skipped`；Ruff、format、benchmark smoke 均 PASS | 对同一 tagged source commit 先运行 main push CI，再运行 annotated-tag push CI；四个 matrix job 必须全部成功 | Main run [`33264778975`](https://github.com/tty627/ai-airlock/actions/runs/33264778975)，jobs `99132798963` / `99132799076`；tag run [`33264852242`](https://github.com/tty627/ai-airlock/actions/runs/33264852242)，jobs `99132994364` / `99132994474` | `v0.1.0-rc.3`；commit `55eca4ceedb1f7e63e9444b86b32f58f2dccac3f`；tag object `31679f3afb8e3010413b01d7a42df35695b294d3`；GitHub `ubuntu-latest` / `windows-latest`；Python 3.12 | 8 项均因 prepared OpenVINO model/runtime unavailable 而 skip；Windows checkout gate 使用 `core.autocrlf=true`；没有运行 `scripts/run.ps1`、PowerShell 5.1/7、真实 Windows OpenVINO、Qoder 或 Intel hardware | 是，须写 scoped Python CI | 可选 | 否 |
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

以下内容没有当前 SHA 绑定的实机证据，只能保留 `PENDING`：

- Windows PowerShell 5.1 / 7 cold start、warm start、中文路径、带空格路径与故障注入；
- Intel AI PC 性能、设备选择、NPU/GPU 使用情况；
- Qoder 自动发现、12 个 positive triggers、12 个 negative triggers、Capsule-only non-bypass；
- 真实 Qoder Agent 的最终回答、Task Completed、workspace bypass 次数和任务期网络计数；
- ModelScope / 研习社 URL、真实截图和最终视频。

## 使用规则

- `raw_sensitive_spans_forwarded=0` 是程序字段，不是独立的全面零泄漏证据；公开安全表述必须引用
  C-SAFE-01 或 C-SAFE-02 的分母、输出面和 fixture 范围。
- `3/3 required facts` 是 Capsule utility proxy，不是 Capsule-only Agent Task Success。
- `PASS` 只代表 frozen release evidence 中定义的 gate 通过；不得外推为通用安全保证。
- 任何裁剪后的图表仍须保留 “Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1”。

# AI Airlock Relevance Closure Report

日期：2026-08-28（Asia/Shanghai）
范围：OpenVINO / hybrid relevance P0；未修改既有 benchmark ground truth
结论：**Relevance P0 = YES（冻结的结构化跨服务 hard-negative 合同）**

> **Pre-freeze development record（非 release evidence）。** 本报告记录正式 commit 创建前的
> P0 patch closure；文中的“最终”仅指该轮开发测量的最后一次运行，不表示已经绑定 source SHA。
> 正式 source RC 的可复现性、测试计数与 benchmark hash 只认对应 RC SHA 的全新 clean checkout
> 外置 evidence。

## 1. Root cause

Embedding correctness 不是本次失败的根因。固定的 `multilingual-e5-small` 路径使用：

- query：`query: <task>`；
- document 与 producer anchor：`passage: <text>`；
- attention-mask mean pooling；
- float32 L2 normalization 后计算 cosine。

独立复核还比较了“anchor + document 合并批次”和 document 单独编码：93 个 document 的
最小 cosine 为 `1.0`，最大逐元素绝对差为 `8.94e-08`。原 93-file case 中每条事实都是短单行，
事实没有被 chunk 截断。

实际根因是 v2 hybrid calibration 缺少 task scope：

1. 任意服务的通用 ERROR、failure、change、causal 信号都会获得相近或更高的固定加分；
2. 中文 task 与英文日志的 lexical overlap 为 0；
3. sanitized source 与日志 producer/service identity 没有进入独立的 scope evidence；
4. ranker 会继续填到 `max_facts=8`，即使尾部是其他服务的故障日志。

`Payment timeout rate increased` 的 content cosine 约为 `0.774733`，v2 hybrid score 约
`913366`；无关 localization 日志的 cosine 约为 `0.811072`，再叠加通用故障信号后达到
`939036`。Benign penalty 只解释 build/cache success 噪声为何容易被过滤，不解释本次第 35 名。
将 `max_facts` 和 token budget 放宽后，该事实仍排第 35，因此扩大 top-k/context budget 不是修复。

## 2. Minimal fix

Selection provenance 升级为 `openvino_hybrid_relevance_v3`：

- 从已 sanitized 的结构化日志提取通用 producer anchor；支持
  `service/component/module/application/subsystem` 字段和 `producer LEVEL ...` 形式；
- 用独立 E5 passage 通道计算 task-to-producer affinity，不把 source 字符串拼入正文；
- 仅在 diagnostic task、至少 4 个 producer、top similarity 与中位数有足够对比时启用；
- producer affinity 改为 median-centered 相对分，只对 scope-supported producer 加分；
- 用通用 identifier family 关联 `*-service`、`*-worker` 等同族 producer，并过滤
  API/service/worker 等角色词；没有业务名白名单；
- 高置信 scope 生效后最多保留 1 条 out-of-scope evidence，避免机械填满 top-8；
- 加入弱 source/task lexical overlap；不同 producer 不再混入同一个 chunk；长行分片继承原
  producer anchor；
- producer 标识限定为安全字符且不超过 64 字符，避免异常 anchor 超过 E5 的 512-token 边界；
- 非诊断 lookup 不再仅因出现 timeout/failure 一类词就进入 diagnostic gate；
- producer anchors 与 evidence 在一次 document embedding 调用中合并批处理，保持 E5 passage
  编码合同，并规避 OpenVINO CPU dynamic-shape 的短批次回切。

原有 cosine threshold、near-duplicate gate、fact/token budget 均保留。产品 ranking 代码没有
Redis、payment、retry、timeout 等 flagship 专用条件；这些词只出现在冻结 fixture/验收材料或
既有通用故障词表中。

## 3. Before / after ranking

任务：`为什么支付服务突然大量失败？`

| Rank | Before v2 | Score | After v3 | Score |
|---:|---|---:|---|---:|
| 1 | `03_retry_traffic.log` | 946327 | `03_retry_traffic.log` | 1010234 |
| 2 | `noise_ach.log` | 939036 | `01_redis_pool.log` | 1000853 |
| 3 | `noise_abw.log` | 938399 | `02_payment_timeout.log` | 977273 |
| 4 | `01_redis_pool.log` | 936946 | `noise_ach.log` | 939036 |
| 5 | `noise_acx.log` | 936722 | not selected | — |
| 6 | `noise_acp.log` | 935887 | not selected | — |
| 7 | `noise_aci.log` | 933507 | not selected | — |
| 8 | `noise_acw.log` | 932868 | not selected | — |
| 35 | `02_payment_timeout.log` | 913366 | — | — |

## 4. Hard-negative acceptance

Frozen manifest：`c6aea202aa1f60b773b77aa1c3f7ee819fe255158c3357f24513750f5bd5d19d`

| Metric | Before v2 | After v3 |
|---|---:|---:|
| Required facts retained | 2/3 | **3/3** |
| Irrelevant selected | 6/8 | **1/4** |
| Recall@8 | 0.6667 | **1.0000** |
| Fixed-denominator Precision@8 | 0.2500 | **0.3750** |
| Precision among returned facts | 0.2500 | **0.7500** |
| Capsule tokens | 619 | **447** |
| Reduction ratio | 0.672487 | **0.763492** |
| Candidate chunks | 93 | 93 |

固定分母 Precision@8 与 returned-set precision 同时报告，避免系统少返回事实时混淆口径。

## 5. Standard benchmark and cross-lingual

既有 `benchmark/datasets/relevance_cases.json` 未修改。最终完整 A/B runner 状态为 `PASS`：

| OpenVINO metric | Before v2 | After v3 |
|---|---:|---:|
| Mean Recall@K | 0.9375 | **0.9375** |
| Mean Precision@K | 0.9375 | **0.9375** |
| Mean reciprocal rank | 1.0 | **1.0** |
| Cross-lingual Mean Recall@K | 1.0 | **1.0** |
| Flagship required facts | 3/3 | **3/3** |
| Flagship Capsule tokens | 894 | **894** |

## 6. Order-service regression

原 holdout manifest：`e35c5cacbb481bb9ccae3fb44c30395d3333982c7e5ce841eaa4e808efd1fdcb`

| Metric | Before v2 | After v3 |
|---|---:|---:|
| Required facts retained | 3/3 | **3/3** |
| Irrelevant selected | 1 | **1** |
| Capsule tokens | 454 | **454** |

最终 required ranking 为 `03_retry_queue`、`02_request_latency`、`01_db_pool`。另加了一条不改原
ground truth 的 adversarial regression：把 benign frontend 日志替换为通用 foreign-service
ERROR；同族 `order-worker` 仍进入前三，required 保持 3/3。该 case 已用于本轮验收，今后应称
regression，不再称 unseen holdout。

## 7. Security and engineering regression

- Full pytest：`160 passed, 6 skipped`；6 项仅因本机没有 PowerShell runtime；
- 完整 benchmark：Secret precision/recall `1.0/1.0`、leakage `0`；Injection
  TP/FP/TN/FN 为 `13/0/12/0`；
- Ruff lint：PASS；Ruff format check：PASS；`git diff --check`：PASS；
- OpenVINO 不可用仍 fail closed，没有 lexical silent fallback；
- 冻结 fixture 保存于 `tests/fixtures/relevance_scope_cases.json`，两个原始 manifest 均由测试重算。

## 8. Latency and stability

| Measurement | Before v2 | After v3 |
|---|---:|---:|
| Full benchmark P95 CLI latency | 1244.891 ms | **1190.307 ms** |
| Full benchmark total, 42 CLI calls | 18211.249 ms | **18693.669 ms** |
| 93-file case, prior single run | 1153.077 ms | — |
| 93-file case, final 30-process median | — | **965 ms** |
| 93-file case, final 30-process P95 | — | **1300 ms** |
| 93-file case, final 30-process max | — | **1390 ms** |
| Final process success / required facts | — | **30/30；每次 3/3** |

完整 benchmark P95 下降约 4.4%，总时长增加约 2.6%。在 producer batch 与 content batch 分开、
并从长动态 shape 回切短 shape 时，曾观察到一次 OpenVINO CPU plugin `SIGSEGV`。合并批次后两轮
累计 60 个独立进程均成功，最终一轮指标如上。当前判断 latency 可接受；目标 Windows/Qoder
环境的 native runtime 稳定性仍需单独验收。

## 9. Files and temporary artifacts

Relevance Closure 最终文件：

1. `src/airlock/relevance/openvino_ranker.py`
2. `src/airlock/qoder_gate.py`（与 Security Closure 共享，保留其改动）
3. `tests/unit/test_openvino_ranker.py`
4. `tests/integration/test_openvino_real.py`（共享测试文件）
5. `tests/integration/test_openvino_boundary.py`
6. `tests/unit/test_qoder_gate.py`（共享测试文件）
7. `tests/fixtures/relevance_scope_cases.json`
8. `docs/qoder_acceptance.md`
9. `docs/relevance-closure-report.md`

仓库内的临时 probe 文件已删除。Relevance Closure 生成的 `/private/tmp` 输出与 benchmark 目录在
报告固化后移入系统废纸篓（清空前可恢复）；Final Integrator 的两个原始 fixture 目录、原
before/after 证据和 ranking 诊断脚本保留，未覆盖或回退。Security Closure 的 detector、pipeline、
Qoder gate 与测试改动均未回退。

## 10. Residual limits

本结论不证明任意非结构化日志都已解决。producer 无法解析、producer 少于 4 个或 affinity 对比
不足时，v3 会退回原 hybrid path。另一个 P1 风险是：真实根因可能来自多个不同 dependency
services，而当前高置信 scope 下只允许 1 条 out-of-scope evidence。后续应增加“目标服务症状 +
多个依赖服务因果证据”的独立 regression。

默认 GitHub CI 不安装本地 OpenVINO 模型，因此真实模型回归会 skip；本轮 P0 由本机固定模型、
manifest 校验、真实 integration 和 black-box benchmark 证据保证，不能冒充远端持续模型 gate。

## 11. Final verdict

验收 A–G 均达到当前 P0 合同：

- A：hard-negative required `3/3`；
- B：irrelevant `6 → 1`；
- C：standard Recall/Precision/MRR 不退化；
- D：cross-lingual `1.0` 保持；
- E：order-service `3/3`，增强 foreign-error regression 也为 `3/3`；
- F：完整 security regression 通过；
- G：benchmark P95 未增加，最终 30-process P95 `1.30s`。

**Relevance P0：YES。**

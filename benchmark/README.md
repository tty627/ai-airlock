# AI Airlock black-box benchmark

这套 Benchmark 只通过公开 CLI 调用 AI Airlock，并解析 stdout 的 JSON。运行器不会 import
detector、ranker、pipeline、OpenVINO backend 或其他内部实现，因此可用于比较不同推理后端。

## 一条命令

CI smoke：

```bash
python benchmark/run_benchmark.py --smoke
```

完整 rules-only baseline：

```bash
python benchmark/run_benchmark.py
```

rules-only 与 OpenVINO A/B：

```bash
python benchmark/run_benchmark.py --compare
```

结果写入：

```text
benchmark/results/latest.json
benchmark/results/latest.md
```

`benchmark/results/` 是被 Git 忽略的本地生成目录。正式 release 必须用
`--output-dir <checkout 外的 evidence 目录>`，不能把会变化的 `latest.*` 放进 source commit。

两份报告共享同一 `run_id`，并记录报告生成时的 Git revision/clean 状态、Python/平台、关键
依赖版本和 benchmark 输入 SHA-256。用于 release claim 时必须满足
`provenance.git_worktree_clean=true`，并在整套命令开始前、结束后额外保存空的
`git status --porcelain --untracked-files=all`；dirty-tree 报告只能用于开发诊断。

OpenVINO variant 已注册、但 runtime 或准备模型不可用时，对应状态必须是 `NOT_AVAILABLE`，不能填充模拟指标。
此时 `--compare` 生成 `PARTIAL` 报告并以退出码 `2` 明确表示 A/B 尚未完成；只有两个变体都
通过各自验收门后才输出差值并返回成功。

## 目录

```text
benchmark/
├── datasets/
│   ├── flagship_incident.json
│   ├── injection_cases.json
│   └── relevance_cases.json
├── results/
│   ├── latest.json
│   └── latest.md
├── run_benchmark.py
└── variants.json
```

- `flagship_incident.json`：旗舰事故的决策、安全计数、必需事实和禁止内容。
- `injection_cases.json`：13 个恶意样本与 12 个 benign 样本；第 13 个来自本轮未见
  red-team，不是为了结果好看而改写既有标签。
- `relevance_cases.json`：12 个任务、120 个 chunk；每个任务 4 个 relevant 和 6 个
  irrelevant，包含中文任务检索英文日志。
- `variants.json`：黑盒 CLI 变体注册表。

## 实际检查

- Flagship：CLI 退出、JSON Contract、decision、关键事实、敏感内容和 Prompt Injection 隔离。
- Secret invariant：直接搜索合成 Secret 的原始值，覆盖 stdout、stderr、Capsule、审计日志、
  受控错误和生成报告；只记录泄漏计数，不把泄漏值写进报告。
- Injection：TP、FP、TN、FN、Precision、Recall。
- Relevance：每例人工标注的 Recall@K、Precision@K、MRR，以及跨语言 Recall@K。
- Context：Benchmark 独立根据真实输入 bytes 和实际 CLI stdout 计算字符数、token 估算和
  reduction ratio，同时检查 CLI 自报指标是否一致。
- Utility：旗舰案例的三个必需故障事实是否全部保留。
- Performance：所有 CLI 子进程的总耗时、均值、P50 和 P95。

注入质量门在运行前固定为 `precision >= 0.80`、`recall >= 0.90`；报告同时保留完整
TP/FP/TN/FN，不能只展示 PASS。CI 还要求旗舰 Capsule 验收、Secret 泄漏为零、所有 CLI
测量成功完成。Secret fixture 当前覆盖 6 个 positive source（`.env`、YAML、log、普通文本与
原有 assignment cases）和 5 个禁止 marker；这仍只是合成覆盖，不是通用 Secret 保证。

## OpenVINO A/B 的公开接口

公开 CLI 已提供显式的：

```text
analyze --relevance-backend lexical|openvino
```

因此 `variants.json` 通过 `arguments_by_command.analyze` 分别注册两条路径；`scan` 继续使用相同的
deterministic 安全检测，`health` 通过 `openvino_available` 报告本地模型和 runtime 是否就绪。
若模型放在非默认目录，可在 OpenVINO variant 的 analyze 参数中追加 `--model-dir <path>`，或通过
`environment` 注册目录变量。模型就绪后无需修改 Benchmark 代码，直接执行：

```bash
python benchmark/run_benchmark.py --compare
```

审计事件的 `inference_mode` 也必须与本次实际模式相同；Benchmark 会把不一致判为 Secret/Audit
验收失败。这样可以防止实际执行 OpenVINO、但 Capsule 或审计仍误报 rules-only 的归因错误。

## 指标解释边界

- token 数沿用 CLI 声明的 estimator；当前是 `ceil(UTF-8 bytes / 4)`，不冒充真实模型 tokenizer。
- `capsule_chars` 统计完整 JSON stdout；`capsule_tokens_estimated` 使用 Capsule 自报的完整输出估算。
- 相关性数据是极小的排序 micro-fixture；逐例 JSON 元数据可能比输入 chunk 更大，因此其聚合
  reduction ratio 可能为负。比赛的 Context Reduction 主指标使用旗舰事故目录，不用该 micro-fixture
  的比率作宣传结论。
- Benchmark 数据全部为合成数据，不包含真实凭证或真实用户信息。
- `latest.*` 中的数字来自运行时测量，不在 fixture 中硬编码。

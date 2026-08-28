# AI Airlock v0.1 architecture

AI Airlock v0.1 是单进程、纯本地的上下文编译器。安全流水线固定为：

```text
complete ingestion
  -> full-corpus detection
  -> overlap resolution
  -> injection quarantine
  -> secret redaction and PII pseudonymization
  -> explicit evidence selector
       |-> deterministic lexical (default)
       `-> OpenVINO embedding challenger (opt-in)
  -> capsule construction
  -> final leak gate
  -> stdout and optional audit event
```

安全边界刻意放在 relevance 之前：任何内容只有先完成检测和变换，才有资格参与最小化。
OpenVINO backend 只能接收净化后的 task 与 transformed documents；原始 Secret、PII、隔离的
Prompt Injection、finding span 和绝对路径都不能进入 tokenizer 或模型。输出 fact 保留相对来源与
1-based 行号；发现记录不保存原值、preview、hash 或绝对路径。

默认 lexical 输出采用稳定的文件顺序、finding 顺序、伪名编号和紧凑 JSON 序列化。同一输入、
任务及策略必须产生逐字节一致的 Capsule；墙钟时间只允许进入显式审计事件，不能改变 Capsule。
OpenVINO 分数先量化为整数并稳定排序；它在同一锁定 Mac 环境内已验证重复输出一致，但不承诺
不同 CPU、OpenVINO 版本或平台之间逐字节相同。

可选 backend 使用固定 revision 的 `intfloat/multilingual-e5-small`。模型准备先校验全部下载源，
把主模型压缩为 FP16 OpenVINO IR，把 fast tokenizer 转换为 OpenVINO tokenizer IR，再做真实推理
smoke test 和完整 manifest 校验，最后原子 rename。运行时不联网，也不会自动下载或静默 fallback。

Apple Silicon 上，OpenVINO 2026.3.1 的 `TextEmbeddingPipeline` 对该 XLM-R Unigram tokenizer
会触发 FP16 custom-op 类型错误。当前实现因此使用已实测可用、并满足当前排序路径的
`openvino_genai.Tokenizer(..., EXECUTION_MODE_HINT="ACCURACY")`，再由 `openvino.Core` 在 CPU 上
执行 feature extractor，并进行 attention-mask mean pooling 与 L2 normalization。这个偏离是
Mac 兼容性修复，不改变“所有模型输入必须先净化”的边界。

`health.openvino_available=true` 表示本地 manifest 全量 hash 校验、tokenizer 加载和 CPU model
compile 都成功。只有实际成功的 OpenVINO analyze 才输出 `mode=openvino_embedding`，审计事件也
记录同一 mode。语义 Prompt Injection 分类器、常驻 server、Windows/Intel 和 Qoder 端到端仍属于
后续里程碑。

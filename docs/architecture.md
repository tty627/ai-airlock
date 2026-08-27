# Deterministic v0.1 architecture

AI Airlock v0.1 是单进程、纯本地的上下文编译器。固定数据流为：

```text
complete ingestion
  -> full-corpus detection
  -> overlap resolution
  -> injection quarantine
  -> secret redaction and PII pseudonymization
  -> deterministic evidence selection
  -> capsule construction
  -> final leak gate
  -> stdout and optional audit event
```

安全边界刻意放在 relevance 之前：任何内容只有先完成检测和变换，才有资格参与最小化。输出 fact 保留相对来源与 1-based 行号；发现记录不保存原值、preview、hash 或绝对路径。

确定性输出采用稳定的文件顺序、finding 顺序、伪名编号和紧凑 JSON 序列化。同一输入、任务及策略必须产生逐字节一致的 Capsule；墙钟时间只允许进入显式审计事件，不能改变 Capsule。

v0.1 不包含 OpenVINO、LLM、网络调用或常驻 server。后续模型能力必须位于同一安全边界内，且不能弱化最终泄漏闸门。


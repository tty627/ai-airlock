# Threat model

## 保护目标

- Secret、原始 PII 和恶意指令不能进入 Capsule、stdout、stderr、审计事件或受控异常。
- Agent 只能根据 `safe_context` 推理，不能把原文件读取作为 fallback。
- 输出来源必须是扫描根目录内的规范化相对路径。

## 不可信输入

文件内容、文件名、用户任务、策略文件以及嵌入 Markdown/HTML 的指令都视为不可信。攻击包括凭证泄露、PII 暴露、Prompt Injection、数据外传诱导、symlink 越界、畸形编码、资源耗尽和通过异常信息侧信道泄露。

## v0.1 控制

- 只读取允许列表内的 UTF-8 文本，不跟随 symlink，并对文件数、单文件和总字节数设限。
- 全语料检测后才做 relevance；Secret 固定脱敏，PII 仅在内存中一致伪名化。
- 注入块整体隔离；无法生成安全上下文或输入不完整时 fail closed。
- 最终泄漏闸门覆盖 Capsule、人类输出和待写审计事件；错误消息固定且不回显输入。

## 非目标与剩余风险

v0.1 不保证发现未知格式 Secret、规避式自然语言注入、图片/PDF 中的数据或被支持文本编码之外的内容。启发式相关性也不能证明真实 Agent 的诊断质量。OpenVINO 语义检测、宿主集成和 utility benchmark 属于后续里程碑，发布前仍需真实 Windows/Intel/Qoder 验收。


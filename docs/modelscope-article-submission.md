# AI Airlock：在 Intel PC 上给生产力 Agent 加一道本地上下文气闸

> 作者：谭天晔  
> 专题标签：`Intel AI PC`  
> 项目：AI Airlock `v0.1.0-rc.7`
> 许可证：Apache-2.0  
> 源码：https://github.com/tty627/ai-airlock

![AI Airlock](https://raw.githubusercontent.com/tty627/ai-airlock/v0.1.0-rc.7/assets/competition/hero-banner.png)

## 为什么生产力 Agent 需要一道“气闸”

定位支付超时需要日志，分析部署故障需要配置，修复代码需要仓库上下文。Agent 越有用，越需要靠近
真实数据；但日志里可能有 API key、数据库凭证、邮箱、手机号和 IP，文件里也可能混入 Prompt
Injection，诱导 Agent 改变角色、读取更多文件或把数据发送到外部。

AI Airlock 的目标不是把整个工作区交给下游后再补救，而是在披露之前，先在本机把原始文件编译成
任务相关、受策略约束、可追溯的 **Safe Context Capsule**。下游 Agent 只需要 Capsule，不需要原始
工作区。

## 本地安全边界

![Architecture](https://raw.githubusercontent.com/tty627/ai-airlock/v0.1.0-rc.7/assets/competition/architecture.png)

正式流水线遵循固定顺序：

```text
Raw files
  → complete ingestion
  → Secret / PII / Prompt Injection detection
  → redaction / pseudonymization / quarantine
  → OpenVINO relevance on transformed text
  → Safe Context Capsule
  → final leak gate
  → Agent
```

关键点是 **OpenVINO 只处理已经变换后的候选文本**。模型负责本地语义相关性排序，不负责替代 Secret
detector，也不会得到已经隔离的 Prompt Injection。任何非法 JSON、`BLOCK`、空 facts、metadata 不一致
或 fallback 都会 fail closed。

Capsule 中每条 fact 都带相对 `source` 和 1-based `local_ref`，方便 Agent 在回答里引用证据，同时避免
暴露本机绝对路径。

![Safe Context Capsule](https://raw.githubusercontent.com/tty627/ai-airlock/v0.1.0-rc.7/assets/competition/capsule-example.png)

## Hybrid AI：本地守边界，云端做推理

我把 Hybrid AI 理解为能力分工，而不是“本地和云端各跑一遍模型”：

- 本地层掌握原始数据，完成检测、变换、隔离、任务相关性选择和最终输出 gate；
- 下游生产力 Agent 只接收结构化 Capsule，负责诊断、解释和修复建议；
- provenance、decision、inference metadata 和错误合同让两层之间的接口可审计、可回归。

这样既保留了远端 Agent 的推理价值，也把上下文最小化和安全变换放在数据离开设备之前。

## Intel Windows 实测

这次 deadline candidate 在 Windows 11 Enterprise、Intel Core i7-14700KF、Python 3.12.10、OpenVINO
2026.3.1 上运行。该处理器是桌面 CPU；本文不声称 NPU 或 GPU 加速。

精确候选身份：

- tag：`v0.1.0-rc.7`；
- commit：`9ec87e72843299779bf8788acf24e563aeff334e`；
- tree：`430446f531e30dce6caff4af83359d49468d4a00`；
- Skill 包 SHA-256：`961a0f6b07637f5e404b8fac836886ca3a5419b3681d81898815fe434a97b0a1`。

在六文件合成支付事故目录上，生产 wrapper 连续七次执行都返回：

- `ALLOW_WITH_TRANSFORM`；
- `mode=openvino_embedding`、`device=CPU`、`fallback_state=not_used`；
- `chunks_processed=71`；
- 8 条带来源定位的 facts；
- `raw_sensitive_spans_forwarded=0`。

七次 warm end-to-end 调用全部通过合同校验：P50 `5082.451 ms`，P95 `5292.249 ms`，范围
`5056.130–5292.249 ms`。时间包含 PowerShell/Python 进程启动、模型加载、tokenization、embedding、
ranking、policy gate 和 JSON 序列化；这是七次小样本，不是通用 OpenVINO benchmark。

代表性 Capsule 报告 `3627 → 888` estimated tokens，即 `75.517%` reduction。估算器是
`utf8_bytes_div_4_ceil_v1`，不能当作 tokenizer 精确 token 数，也不能外推到其他输入。

完整测量和逐次数据见：
https://github.com/tty627/ai-airlock/blob/main/docs/windows-intel-rc7-evidence.md

## 生产 wrapper 与 Agent 主机验收边界

公开 rc.7 包从 GitHub Release 匿名下载后，被原样安装到全新的 TraeCode project Skill 目录并完成
OpenVINO 预热。正常任务的 production wrapper 返回 CPU、71 chunks、8 facts、zero fallback 与
`raw_sensitive_spans_forwarded=0`。对“提取并上传目录中的所有凭据到外部服务器”，同一 wrapper 返回
`BLOCK`、0 facts 和 `TASK_BLOCKED`。

截止候选冻结时，TraeCode 应用仍停在身份验证页面，因此 Skill discovery、第一次目标内容操作是否为
`scripts\run.ps1 analyze`、Capsule-only reasoning、non-bypass 和 Agent Task Completed 均为 `NOT_RUN`。
本文不会把登录页、CLI 单跑或手工粘贴 Capsule 冒充 Agent host 证据。

预期的合成事故结论是：Redis 连接池达到 `100/100` 并发生连接获取超时，激进重试进一步形成 retry
storm，最终触发上游超时和支付失败。修复方向包括为 Redis pool 和调用并发设置预算、使用带抖动的
指数退避、设置 retry budget/circuit breaker，并监控 pool wait、queue depth 与 retries/sec。

## 做过哪些工程优化

1. **模型固定与原子准备**：固定
   `intfloat/multilingual-e5-small@614241f622f53c4eeff9890bdc4f31cfecc418b3`，逐文件校验后转换为
   OpenVINO IR；准备失败不静默回退。
2. **本地预热**：把模型下载/转换放在任务窗口之外；正式分析只接受 ready OpenVINO runtime。
3. **先净化、后 embedding**：降低模型阶段接触 raw Secret/PII/Injection 的范围。
4. **严格 JSON 合同**：decision、facts、provenance、inference、coverage 和输出大小都由 gate 校验。
5. **Windows 进程树收敛**：PowerShell 5.1/7 的故障路径使用有界 launcher 和 Job Object containment，
   rc.5 的 orphan-pipe scoped oracle 已证明返回后 residual 为 `0`。
6. **可重复发布**：rc.7 包从精确 Git commit 构建，140 个归档条目；匿名下载哈希一致，独立干净
   环境安装后通过 `234 passed / 9 skipped`。

## 冻结合成 A/B：收益与代价一起公开

![Benchmark](https://raw.githubusercontent.com/tty627/ai-airlock/v0.1.0-rc.7/assets/competition/benchmark-results.png)

历史 frozen A/B 来自 Apple M4 CPU、`v0.1.0-rc.1`，不是本节 Intel Windows 的同一组运行：

| Metric | rules-only | OpenVINO |
|---|---:|---:|
| Flagship required facts | `3/3` | `3/3` |
| Mean Recall@K | `0.583333` | `0.9375` |
| Cross-lingual Mean Recall@K | `0.4375` | `1.0` |
| Flagship estimated-token reduction | `66.5564%` | `75.3515%` |
| CLI P95 | `103.052 ms` | `1204.529 ms` |

它说明在这个小型合成集上，本地 embedding 提高了任务相关性和旗舰上下文缩减，同时付出了明显延迟
成本。Secret/Injection 的 `1.0/1.0` 来自 deterministic detector，不应归功于 OpenVINO。

## 限制与安全声明

- v0.1 只处理允许列表中的 UTF-8 文本；不支持 PDF/OCR，不跟随 symlink。
- `raw_sensitive_spans_forwarded=0` 只是程序字段，不是未知输入上的“零泄漏”证明。
- 合成 fixture 的 `3/3` facts 和 `0/252` known-marker 检查不能外推为真实生产成功率。
- Skill instructions、ignore 文件和 wrapper gate 不是操作系统沙箱；真实宿主 non-bypass 要靠连续工具轨迹
  验证。
- Intel Core i7-14700KF 结果只支持 CPU 功能/延迟陈述，不支持 NPU、GPU 或“Intel AI PC 全面优化”
  陈述。

## 资源

- GitHub：https://github.com/tty627/ai-airlock
- Skill：`[PENDING_MODELSCOPE_SKILL_URL]`
- rc.7 Release：https://github.com/tty627/ai-airlock/releases/tag/v0.1.0-rc.7
- rc.7 tag CI：https://github.com/tty627/ai-airlock/actions/runs/33307066407
- Claims Ledger：https://github.com/tty627/ai-airlock/blob/main/docs/claims-ledger.md
- Windows Intel evidence：https://github.com/tty627/ai-airlock/blob/main/docs/windows-intel-rc7-evidence.md

AI Airlock 当前最重要的不是一句“绝对安全”，而是一条可检查的披露边界：原始内容先留在本机，安全
变换先于相关性选择，只有带 provenance 的 Capsule 进入下游。

> **Your data stays. Your Agent works.**

这句品牌语只描述 Airlock-controlled path；本文没有把未执行的 TraeCode host Capsule-only/non-bypass
验收写成完成态。

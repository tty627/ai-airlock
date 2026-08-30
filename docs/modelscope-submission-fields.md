# AI Airlock ModelScope Submission Fields

> 状态：本地发布字段草稿，尚未登录或提交。
> 不在本文中填写虚假 URL、作者、截图、CI、Windows/Qoder 或 Intel 实机结果。

## 推荐标题

**首选：**

> AI Airlock：面向 AI Agent 的本地安全上下文编译器

**英文副标题：**

> Your data stays. Your Agent works.

品牌语只描述 Airlock-controlled path；在真实宿主证据完成前，必须同时保留
`real host non-bypass pending`，不得解释为 Qoder 已无法旁路。

标题不放 benchmark 数字，也不使用 `Qoder validated`、`Intel optimized`、`zero leakage` 或其他尚未
验收的完成态词语。

## 一句话定位

> AI Airlock 在本机把私有、不可信的文件编译成任务相关、受策略约束、可追溯的 Safe Context
> Capsule，再交给下游 AI Agent。

## 短简介

> 一个面向 AI Agent 的 Local Context Gateway：先在本机识别并变换当前策略覆盖的 Secret/PII、隔离
> 当前 detector 识别的 Prompt Injection，
> 再用 OpenVINO 从已净化内容中选择任务相关证据，只输出可追溯的 Safe Context Capsule。当前
> `v0.1.0-rc.1` 已完成 Apple M4 CPU 上的 clean-checkout、OpenVINO CLI 与合成 A/B；exact
> `v0.1.0-rc.5` 已通过 PowerShell 5.1/7 scoped fault/health/analyze validation。完整 Windows matrix、
> Qoder 与 Intel 验收仍待回填。

如果平台字数更紧，可用：

> 在本机检测、变换、隔离并筛选私有上下文，只向 AI Agent 发布可追溯的 Safe Context Capsule。

## 长简介

> 生产力 Agent 要定位故障、修复代码或处理工单，往往需要日志、配置和客户数据；这些上下文既私密、
> 冗余，也可能夹带 Prompt Injection。AI Airlock 把安全边界放在披露之前：完整输入先在本机经过
> 当前策略范围内的 Secret/PII 检测、redaction/pseudonymization、Injection quarantine，只有已经净化的证据才进入
> OpenVINO task relevance。最终输出是一份带 decision、provenance、source/local_ref、inference
> metadata 和最终 leak gate 的 Safe Context Capsule。
>
> 冻结的 `v0.1.0-rc.1` 在 macOS / Apple M4 CPU 上完成 clean-checkout release evidence、固定模型
> revision 的 OpenVINO public CLI、strict Python response gate、flagship 和完整 synthetic A/B。结果
> 显示该小型固定数据集上的 Mean Recall@K 从 0.583333 变为 0.9375，flagship estimated-token
> context reduction 在 `utf8_bytes_div_4_ceil_v1` 下从 66.5564% 变为 75.3515%，同时 CLI P95
> latency 从 103.052 ms 上升至 1204.529 ms。所有数字
> 均限定为 Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1，不能外推为通用安全或真实 Agent
> 成功率。exact rc.5 的两壳 orphan-pipe no-residual 和 scoped health/analyze controls 已通过；empty-cache、
> remaining Windows faults、Qoder host、Capsule-only Agent answer 和 Intel 性能为 `NOT_RUN`，network 为
> `NOT_MEASURED`，full matrix / overall 为 `INCONCLUSIVE`，不得概括成完整 Windows PASS。

## 推荐标签

### 核心技术标签

按推荐顺序：

1. `AI Agent`
2. `Agentic`
3. `Skills`
4. `OpenVINO`
5. `Local AI`
6. `Safe Context Capsule`
7. `Prompt Injection`
8. `Privacy`
9. `Context Engineering`
10. `Hybrid AI`

### 比赛 / 专题强制标签

- **ModelScope Skill 自定义标签：`AI PC`（REQUIRED）。** 当前仅有 Apple M4 CPU 实测，正文必须保留
  硬件范围。
- **比赛文章专题标签：`Intel AI PC`（REQUIRED）。** 这是比赛归类字段；在真实 Intel evidence 回填前，
  不得把标签解释成“已在 Intel AI PC 验证”。
- `OpenVINO`：可准确使用，rc.1 已有 Apple M4 CPU 的 OpenVINO CLI 与 A/B 证据。
- `Agentic` / `Skills`：准确描述集成形态，但真实 Qoder host acceptance 仍是 PENDING。

不要使用：`NPU accelerated`、`Intel validated`、`Qoder completed`、`enterprise compliant`、
`100% secure`、`zero leakage`。

## Use cases

### 1. 私有生产日志故障分析

在日志进入下游 Agent 前，先在本机替换 Secret/PII、隔离 Injection，并只保留与当前故障相关、带
`source:local_ref` 的证据。

### 2. 配置与仓库的安全上下文生成

对允许类型的配置、文档和代码文本生成 Safe Context Capsule，减少无关上下文和直接披露。

### 3. Prompt Injection 预隔离

把文件内容视为不可信数据；在 Capsule 生成前隔离当前 detector 识别的指令和外传诱导。此能力有固定
合成测试范围，不能声称覆盖所有规避式攻击。

### 4. 本地 task relevance

使用 OpenVINO 在本机对已净化证据做 semantic ranking，改善固定合成数据集中的 task relevance 和
cross-lingual relevance，同时显式报告 latency trade-off。

### 5. Agent Skill 安全入口

通过稳定 JSON contract 把 Airlock 放在宿主 Agent 的 raw workspace 访问之前。当前 Python gate 与
exact rc.5 Windows scoped wrapper controls 已验证；Qoder host 的 Capsule-only non-bypass 及完整 Windows
matrix 尚待实机验收。

## 建议技术栈字段

```text
Python 3.12
OpenVINO Runtime 2026.3.1
OpenVINO GenAI Tokenizer 2026.3.1.0
OpenVINO Tokenizers 2026.3.1.0
Transformers 5.16.1
intfloat/multilingual-e5-small
Safe Context Capsule / stable JSON contract
```

不要在字段中加入 GPU、NPU、Intel device 或 Windows 性能，直到对应证据完成。

## 本地资产

| 字段 | 本地候选 | 当前发布状态 |
|---|---|---|
| Icon | `assets/competition/ai-airlock-icon.svg` / `.png` | 本地已准备；公开 icon URL 待托管 |
| Hero | `assets/competition/hero-banner.svg` / `.png` | 本地已准备 |
| Architecture | `assets/competition/architecture.svg` / `.png` | 本地已准备；Qoder 显示 pending |
| Benchmark | `assets/competition/benchmark-results.svg` / `.png` | 本地已准备；必须保留环境与 trade-off |
| Article | `docs/modelscope-article.md` | 本地初稿 |
| Video | `docs/demo-script.md` | 脚本已准备；Windows/Qoder 镜头待回填 |

## 链接占位

```text
Source repository URL:   https://github.com/tty627/ai-airlock
ModelScope Skill URL:    [PENDING_AFTER_PUBLICATION]
ModelScope article URL:  [PENDING_AFTER_PUBLICATION]
Demo video URL:          [PENDING_AFTER_PUBLICATION]
Icon URL:                https://raw.githubusercontent.com/tty627/ai-airlock/v0.1.0-rc.5/assets/competition/ai-airlock-icon.png
Documentation URL:       [PENDING_AFTER_PUBLICATION]
Issue tracker URL:       https://github.com/tty627/ai-airlock/issues
```

公开源码仓库已确认并可匿名访问；ModelScope、文章、视频、icon 和文档发布 URL 仍不得猜测或提前回填。

## `meta.json` / `info.json` 规范复核

复核来源为 OpenVINO Local AI Skill 的
[文件规范](https://github.com/openvino-dev-samples/local-ai-skill-authoring/blob/main/references/file-reference.md)、
[`meta.json` 模板](https://raw.githubusercontent.com/openvino-dev-samples/local-ai-skill-authoring/main/assets/meta.template.json)
与 [`info.json` 模板](https://raw.githubusercontent.com/openvino-dev-samples/local-ai-skill-authoring/main/assets/info.template.json)。

| 字段 | 当前值 / 状态 | 必须由用户决定 |
|---|---|---|
| `meta.json.author` / `pyproject.toml authors` | `谭天晔` | 已确认的公开 author/byline；发布前只需核对平台字段未被改写 |
| `meta.json.icon` | rc.5 不可变 tag 下的公开 PNG URL | 已填入 `meta.json`；匿名访问待最终发布复验，不添加到 `info.json` |
| `info.json.mem_need_gb` | Windows OpenVINO analyze 实测峰值 `0.702 GiB`；配置 `1.0` | 已向上取整并保留测量范围；见 [release-metadata.md](release-metadata.md) |
| `info.json.server_alive_timeout` | `300` | 使用官方明确默认值；短生命周期 client 不声称常驻 server |
| `info.json.models` | `[]`；官方示例使用带 `model_id` / `dir_name` / `required_files` 的对象，未明确空数组是否接受 | 先验证平台 parser；继续“上游固定 revision + 本地转换”，或在完成授权/归属/哈希后建立公开转换模型仓库 |
| package metadata version | `0.1.0` | 当前源码候选展示为 `v0.1.0-rc.5`，frozen benchmark 仍绑定 rc.1；不得移动或重打任何 RC tag |
| `info.json` extra fields | 非模板字段已移除 | 只保留官方五个字段；`models=[]` 仍需真实上传 preflight |
| Skill 标识 / 未来目录 | `SKILL.md.name`、Python package 与 `meta.json.name` 均为 `ai-airlock` | 用户已确认不可变 `skill_name=ai-airlock`；TraeCode 名称语法兼容，真实发现待验收 |
| `SKILL.md` host 模板 | 已加入 Usage / Examples / retry resume / unsupported-platform / no-cloud-fallback，并保持唯一 wrapper | 文档兼容已关闭；真实 TraeCode/Qoder host 行为仍不能由文档代替 |
| project LICENSE | Apache-2.0；copyright 2026 谭天晔 | 已确认；发布 archive 保留完整 `LICENSE` 与第三方 notices |
| public repository | `https://github.com/tty627/ai-airlock`；public | 已确认；最终表单使用该 URL 并在匿名窗口复核 |

icon 使用不可变公开资产，内存使用 Windows 实测峰值上取整，timeout 使用官方默认值；没有猜测托管模型。

### 模型下载、固定 revision、转换与再分发决策

当前可证流程是：从 `intfloat/multilingual-e5-small` 固定 revision
`614241f622f53c4eeff9890bdc4f31cfecc418b3` 下载源文件，逐文件校验，然后在本地转换为 OpenVINO IR。
该流程不等于存在可供 ModelScope host 直接下载的转换模型仓库。

发布前二选一，并完成平台验证：

1. 保持固定上游 revision + 本地转换；确认 `models=[]` 被目标上传/host 接受，并明确 cold bootstrap
   网络、缓存与失败路径。
2. 托管转换模型；先确认再分发授权和版权归属，公开固定 revision，记录源/转换物 SHA-256，并在
   `models[]` 填真实 `model_id`、`dir_name` 与至少一个核心 `.xml/.bin` 的 `required_files`。

不得把 Hugging Face 源模型 repo 直接填成“已就绪 OpenVINO 模型”，也不得猜测 ModelScope model ID。

## Skills Center 创建字段阻断

根据 [ModelScope Skills Center 规范](https://github.com/modelscope/modelscope-skills/blob/main/skills/ms-hub/references/skills-center.md)，
创建前还需用户确认：

| 字段 | 状态 |
|---|---|
| `owner` | 登录后从 `/users/me` 读取真实 owner；创建后不可更改，禁止猜测 |
| `skill_name` | `ai-airlock`；用户已确认，创建后不可更改 |
| `category` | `developer-tools`；用户已确认 |
| `license` | `Apache-2.0`；已确认 |
| `source_url` | `https://github.com/tty627/ai-airlock`；发布前做匿名访问复核 |
| upload path | 优先网页/OpenAPI 两步发布；保留 Codex/Trae 有效的 `metadata.version`，不走要求顶层 `version` 的 CLI 变体 |

## 表单提交前复核

- [ ] 用户登录后记录真实必填字段、字数限制、文件格式和 URL 校验规则。
- [ ] 标题、简介、标签与版本展示由用户最终确认；author“谭天晔”和 Apache-2.0 保持已确认值。
- [ ] Skill 自定义标签精确为 `AI PC`，文章专题标签精确为 `Intel AI PC`。
- [ ] Skill archive 同时含代码、文档、测试，根目录有且仅有一个 `SKILL.md`。
- [ ] 真实 API / CLI 上传预检已解决“根目录仅一个 `SKILL.md`”与完整代码/文档/测试包之间的规范歧义。
- [ ] `meta.json.icon`、`mem_need_gb`、`server_alive_timeout`、`models` 与额外字段阻断已关闭。
- [ ] 目标 host 已确认 `ai-airlock` 命名与当前 `SKILL.md` 结构；若要求 OpenVINO 模板，`--continue`
  等功能已经真实实现并在 Windows/Qoder 验收，不能只补文案。
- [ ] 所有 URL 实际存在，并在未登录窗口可访问。
- [ ] Windows/Qoder/Intel 占位没有被误删或换成无证据完成态。
- [ ] 图片和视频仍保留 `Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1`。
- [ ] 提交后保存真实作品 ID、时间戳、成功回执和公开页；在本轮不执行。

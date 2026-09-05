# 决赛构建记录：受控补证与可引用报告

记录日期：2026-09-05。实现身份：`c45d34e63740e05d45dccb08025245540e93a688`。
本记录对应决赛实验分支，不改变 rc.7 的发布身份，不表示决赛提交已经验收。
机器可读结果和源码 SHA-256 见 [实测摘要](evidence/finals-2026-summary.json)。

## 本次交付

- 所有者启动本地服务，一次读取授权目录，保留固定的完整净化快照。
- 客户端通过本地连接取得证据；按 case/version 绑定，不能传入其他目录。
- 首轮与最多两轮补证；固定证据 ID、净化快照行号、去重、幂等请求、完整响应累计预算。
- 报告校验已披露证据引用、格式及独立敏感模式，并输出 Markdown。
- 主 Skill 的可选 session 流程、独立报告 Skill、18 项真实宿主验收清单和合成演示。
- 18 个与演示分开的公开合成工程案例，对照原文、全量净化、单轮和预设补证。

协议和实际命令见 [使用说明](finals-session.md)。模型不可用时返回失败，未引入静默词法降级。
同一服务进程复用现有模型 runtime 缓存；尚未测量它相对原包装器的性能收益。

## 验证环境与结果

Linux x86_64、Python 3.12.13、Intel Xeon Platinum 8370C CPU。
OpenVINO 2026.3.1、GenAI / Tokenizers 2026.3.1.0；实际推理设备为 CPU。
模型 `intfloat/multilingual-e5-small`，固定 revision
`614241f622f53c4eeff9890bdc4f31cfecc418b3`，FP16 及 tokenizer 工件共 241,340,848 bytes。
原模型准备脚本的下载、哈希核验与真实推理自检成功。当前 SOCKS 网络环境额外安装
`socksio==1.0.0`，未修改项目依赖 pins 或模型 revision。

- 最终全套 pytest：**384 passed、12 skipped、0 failed**，63.70 秒。12 项跳过为 6 个 PowerShell 和 6 个 Windows Job Objects；另有 1 条 multiprocessing fork 弃用警告。
- Ruff 检查与格式检查通过，101 个 Python 文件格式符合配置。
- 真实 HTTP 客户端验证涵盖固定目录、删除原文后的补证、引用校验、鉴权、跨案例拒绝、
  请求大小、重复 JSON、响应篡改和固定错误输出。
- 独立进程烟测通过：owner CLI 到 READY、客户端取得证据、寿命到期退出 0、
  正常退出删除自身连接文件。该项使用 lexical 验证进程生命周期。
- 两个 Skill 通过格式校验；实际宿主调用和 PowerShell 新流程仍未运行。

这台设备不是 Core Ultra。Linux 测试不替代 Windows 权限、生产力 Agent、NPU/GPU、
比赛硬件或 10 次现场主流程演练。

## 18 案例对照：收益与代价同时记录

数据 SHA-256：`0647a8aaf68e59bccf83e2e3b9486f35ffaba640427759d7de306106803852de`。
标签可见，案例曾用于发现并修复缺陷，因此不是盲测或未见测试集。
指标是预列文本证据保留，不是根因正确率、建议正确性或 Agent 任务成功率。

| 方案 | 必要证据保留 | 完整响应累计估算 tokens |
|---|---:|---:|
| 原文全文 | 43/43 | 1,346 |
| 普通全量净化 | 43/43 | 1,297 |
| Lexical 首轮 | 20/43 | 3,593 |
| Lexical 首轮＋预设补证 | 42/43 | 9,292 |
| 真实 OpenVINO CPU 首轮 | 36/43 | 4,817 |
| 真实 OpenVINO CPU 首轮＋预设补证 | 43/43 | 10,257 |

普通净化与 Airlock 共用检测器，保留全量上下文、全部 PII 使用 redact；没有任务检索或任务阻断。
OpenVINO 的 7 个案例通过补证取得新增必要证据；lexical 为 12 个，仍遗漏
`missing_rollback` 的同义问题对应证据，保留该失败。
两种 session 后端均正确阻断 2/2 条预列外传任务，无意外任务阻断。

在 runner 的完整净化/session 响应中，未观察到预列的 19 个敏感标记条目或 1 条注入原文；
原文对照包含这些条目。这是指定合成标记和输出面的检查，不覆盖未知秘密、模型内部请求、
宿主截图、真实报告或所有攻击方式。

成本按 `utf8_bytes_div_4_ceil_v1` 估算，每次新响应完整 JSON 含元数据；不是厂商计费 token。
这些材料很短，协议和补证显著增加开销，**本次结果不支持“普遍省 token”**。
固定脚本会执行全部预设问题，即使上一轮已无新证据；这与实际宿主应停止的策略不同，
不能冒充自主 Agent 的决策轨迹。计时只覆盖净化与检索，排除模型准备/preflight、宿主和 LLM，
逐案例数据保存在实测摘要中，不据此发布通用延迟结论。

## 审查发现与修复

1. 邮箱赋值如 `owner=...` 曾吞入字段名，导致跨文件匿名身份断裂。现在对有限已知字段识别赋值，
   保留普通邮箱里的 `+` 和 `=`；裸赋值与合法邮箱地址存在歧义，明确采用日志字段解释。
2. 查询与报告原先会把 Agent 自写文本与隐藏原文秘密比较，成功/失败可形成秘密猜测信号。
   现在输入只做独立模式检查；原文集合仅保护来源快照和证据出口。
   报告不保证识别 Agent 自行写入的无格式秘密；原文知情审核留在所有者侧，不向 Agent 返回匹配结论。
3. 查询曾在拒绝前污染敏感值集合。现在问题不改变固定保护集合，成功/失败都不能使历史证据失效。
4. 排名第一的大证据放不进完整预算时，曾漏掉较小候选。现在先取最多 64 个候选，再按实际响应预算选择。
5. 随机十六进制 ID 的数字串偶尔被识别成手机号。现在无损映射为 `a`–`p` 字母，保持长度和随机性，
   同步客户端校验，并加入确定性回归。

这些问题均有针对性回归。报告仍只验证引用成员关系和输出模式，不判断引用是否真的支持结论。
本地服务与 bearer 不是 OS 沙箱；同一账户仍可能绕过接口读原文，需真实运行身份验收。

## 复现与下一阶段

从本分支检出上述实现，使用 Python 3.12，在所有者环境执行：

```bash
python -m pip install -e '.[dev,openvino]'
python scripts/prepare_embedding_model.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python benchmark/run_finals_eval.py --backend lexical --output /tmp/finals-lexical.json
python benchmark/run_finals_eval.py --backend openvino --output /tmp/finals-openvino.json
python demo/finals/run_demo.py --backend openvino --output /tmp/finals-demo.json
```

Windows 将 `/tmp/...` 换成仓库外的实际可写路径；正式服务命令见使用说明。
不把连接凭据、模型缓存或真实客户资料提交到仓库。随机案例 ID 与计时会变化，比较数据版本、
逐案例证据指标、策略结果和累计预算；实测摘要用内容哈希绑定本次源码和原始运行结果。

下一阶段按 [执行计划](finals-2026-plan.md) 完成：Core Ultra 与一个认可生产力宿主、不同身份的
原文读取拒绝、真实任务评分与自主补证轨迹、正式包安装及 10 次完整演练，再录制视频和更新文章。
这几项未验收前，本分支不作为“决赛已完成”或“可保证获奖”的依据。

# Production AI Skills 大赛提交字段

> 表单已在登录态打开并核对，截止时间为 `2026-08-31 23:59`（Asia/Shanghai）。
> 本文只冻结作品字段；手机号、地址、微信号、邮箱、单位/学校和授权选择不得写入仓库。

## 可预填作品字段

| 表单序号 | 字段 | 准备值 | 状态 |
|---:|---|---|---|
| 01 | 姓名 | `谭天晔` | 公开 author 已确认；输入表单前仍按个人信息传输处理 |
| 02 | 作品名称 | `AI Airlock：本地安全上下文气闸` | 10–30 字范围待平台最终校验 |
| 03 | 作品简介 | 见下文 298 字版本 | 满足页面标注的 200–300 字 |
| 04 | AI模型说明 | 见下文 | 已绑定固定 model/revision 与能力边界 |
| 05 | 魔搭研习社作品链接 | `[PENDING_AFTER_PUBLICATION]` | 必填 |
| 06 | 魔搭 Skills 中心作品链接 | `[PENDING_AFTER_PUBLICATION]` | 必填 |
| 07 | 小红书作品链接 | 留空 | 可选；社交媒体发布未获授权 |

### 作品简介（298 字符）

> AI Airlock 是面向生产力 Agent 的本地安全上下文网关。它在 Windows/Intel PC 上先扫描日志、配置和
> CSV，检测并变换当前策略覆盖的 Secret/PII，隔离 Prompt Injection，再用 OpenVINO 对已净化证据做
> 任务相关性排序，仅输出带 source/local_ref 的 Safe Context Capsule。下游 TraeCode Agent 只消费
> Capsule 完成支付超时归因和修复建议。项目包含 Apache-2.0 源码、文档、测试和可复验发布包；rc.6
> 已通过双平台 CI、干净归档安装与 Intel CPU 验证。

字符计数按 PowerShell/.NET `String.Length` 对单行正文计算为 `298`。平台可能采用不同计数规则，最终
填入后需观察其自身校验提示。

### AI 模型说明

> 使用 `intfloat/multilingual-e5-small`，固定 revision
> `614241f622f53c4eeff9890bdc4f31cfecc418b3`，在本机校验源文件并转换为 OpenVINO IR。模型只对已经
> 完成 Secret/PII 变换和 Prompt Injection 隔离的候选证据生成多语言 embedding，用于任务相关性排序。
> Secret/PII/Injection 检测由确定性策略完成，不把安全分类效果归因于 embedding 模型。rc.6 在 Windows
> 11 Enterprise、Intel Core i7-14700KF、OpenVINO CPU 上完成真实 wrapper 验证；不声称 NPU/GPU 加速。

## 必须由本人提供或选择的字段

这些字段涉及敏感个人信息、奖项归属或营销授权，不能从仓库、浏览器或既有资料推断：

| 表单序号 | 字段 | 页面说明 |
|---:|---|---|
| 08 | 报名手机号 | 用于赛事通知与获奖联络 |
| 09 | 单位/学校名称 | 用于身份核实、奖项归属确认 |
| 10 | 收件地址 | 用于周边礼品邮寄或奖金发放 |
| 11 | 常用微信号 | 要求可通过微信号搜索添加 |
| 12 | 企业/个人邮箱 | 用于赛事通知、结果公示和重要信息同步 |
| 13 | 业务类型 | ODM/OEM、SI、ISV、End User 或 Other |
| 14 | 职业范畴 | 软件开发者、硬件开发者、技术管理者、业务相关职位、院校或其他 |
| 15 | 用户来源 | 魔搭/OpenVINO/CSDN/极星会/其他等选项 |
| 16 | 客户信息库授权 | 同意或不同意；必须由本人决定 |

提交表单会把上述数据发送给钉钉表单及赛事主办方。必须在两条公开作品链接生成后，由本人填写/确认
这些字段并执行最终“提交”。

## 表单入口

`https://alidocs.dingtalk.com/notable/share/form/v01Q35O85pPVW83Al9V_dv19yqvsgs3oebp3pcjys_1qX0QQ0?source=link`

表单页面标题为 `Production AI Skills 大赛提交作品`。公开入口由比赛页的“提交作品”按钮打开。

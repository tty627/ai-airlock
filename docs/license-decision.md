# AI Airlock Project License Decision

## 当前结论

用户已于 2026-08-29 确认以下项目发布身份：

```text
Project license:      Apache License 2.0
Copyright holder:     谭天晔
Copyright year:       2026
Public author/byline: 谭天晔
```

根目录 [`LICENSE`](../LICENSE) 使用 Apache 官方标准文本，`pyproject.toml` 与 `meta.json` 已同步。
这项选择授权项目源码按 Apache-2.0 发布，但不替代第三方依赖、模型或训练数据的独立许可与归属审查。

## MIT 与 Apache-2.0 对比

| 维度 | MIT | Apache-2.0 |
|---|---|---|
| 使用、修改、商业分发 | 允许 | 允许 |
| 明示专利授权 | 无专门条款 | 有；贡献者授予相关专利许可 |
| 专利诉讼触发 | 无专门条款 | 对提起相关专利诉讼者终止专利许可 |
| 再分发主要义务 | 保留版权与许可文本 | 附许可证、标记修改文件、保留归属；若上游有 NOTICE 则继续携带相关内容 |
| 商标 | 无专门授权条款 | 明确不授予商标使用权 |
| 管理成本 | 最低 | 略高，需要维护修改说明；存在适用 NOTICE 时继续传递 |
| 典型取向 | 简短、宽松、低摩擦 | 企业采用、多人贡献、希望专利边界更明确 |

权威文本：

- [MIT License 标准文本](https://spdx.org/licenses/MIT.html)
- [Apache License 2.0 标准文本](https://www.apache.org/licenses/LICENSE-2.0)

## 推荐判断

### 选择 Apache-2.0，如果以下因素更重要

- 希望企业用户对贡献者专利授权有更明确预期；
- 预计会有外部贡献者、集成方或模型/推理相关专利风险讨论；
- 团队愿意维护修改标记、归属和适用 NOTICE；
- 项目定位是长期维护的安全基础设施，而不是一次性示例。

### 选择 MIT，如果以下因素更重要

- 希望许可证尽量短、传播和复用门槛最低；
- 项目预计由很小的主体维护，暂不建立复杂贡献流程；
- 可以接受许可证没有明示专利授权；
- 当前只发布源代码，不打包第三方 runtime 或模型权重。

## 无论选择哪一个都不会自动解决的问题

- 项目许可证不能替代 OpenVINO、Transformers、NumPy 或其他第三方软件的许可证与 NOTICE。
- 项目许可证不能改变 `intfloat/multilingual-e5-small` 的上游许可或模型再分发要求。
- 许可证文本不能证明训练数据、商标、隐私、安全或出口合规。
- 选择宽松许可证不等于授予项目名、Logo 或商标权。
- 当前第三方清单不是完整 transitive lock；分发 wheel、容器、离线包或转换模型前仍需冻结完整物料。

详见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。

## 已确认与仍待决定

```text
Project license:        Apache-2.0
Copyright holder:       谭天晔
Copyright year:         2026
Public author/byline:   谭天晔
Trademark policy:       [OPTIONAL USER DECISION]
Contribution policy:    [OPTIONAL USER DECISION]
Model hosting strategy: [USER DECISION]
```

当前不创建项目 `NOTICE`：尚没有需要写入 Apache NOTICE 的独立项目归属内容。第三方清单继续由
`THIRD_PARTY_NOTICES.md` 单独维护；未来如果分发的上游制品携带 NOTICE，必须按其许可证继续传递。

## 发布前动作

1. 保持根目录 `LICENSE` 为未经改写的 Apache-2.0 标准文本。
2. 保持 `pyproject.toml`、发布页面和仓库 metadata 与版权/作者选择同步；不得修改或重打
   `v0.1.0-rc.1`。
3. 完成第三方许可证/NOTICE 收集和模型托管决策。
4. 在发布二进制、容器、离线 runtime 或转换模型前做一次法律/合规复核；本文件不是法律意见。

# RunArtifactPath

## 定义

`RunArtifactPath` 是 [[RunDirectory]] 内某个运行记录文件或子目录的结构化路径引用。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[02_Run目录管理模块]]

## 现实语义

`RunArtifactPath` 表示“某个后续模块应该把自己的运行记录写到哪里”。它只描述路径和归属，不保存文件内容。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `path` | path | 是 | 文件或目录路径。 |
| `artifact_name` | string | 是 | 运行记录语义名，例如 `run_log` 或 `outputs`。 |
| `artifact_kind` | enum-like string | 是 | `file` 或 `directory`。 |
| `format` | string 或空 | 否 | JSON、YAML、directory 等格式提示。 |
| `owner_module` | string | 是 | 后续负责写入内容的 L2 模块。 |
| `required_on_success` | boolean | 是 | 成功运行时是否必须存在。 |
| `required_on_failure` | boolean | 是 | 失败运行时是否必须存在。 |

## 有效性规则

- `path` 必须位于 [[RunDirectory]] 下。
- `artifact_kind` 必须能区分文件和目录。
- `owner_module` 必须指向 Runtime MVP 内的后续功能模块。
- Run 目录管理模块只创建目录类路径；文件类路径由对应 owner 模块写入。

## 上游来源

- Run 目录管理模块根据 [[RunDirectoryLayout]] 生成。

## 下游消费者

- 配置加载与配置快照模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不判断文件内容是否符合 schema。
- 不执行 JSON/YAML 序列化。
- 不替代 [[RuntimeErrorRef]] 或 [[SceneResult]]。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要把 `RunArtifactPath` 写入代码 Types | 影响 L3 拆分粒度。 | L2 先固定文档语义，L3 实现时再决定是否单独建类型。 | L3 任务生成前确认。 |

## 相关链接

- [[RunDirectory]]
- [[RunDirectoryLayout]]
- [[RunContext]]
- [[02_Run目录管理模块]]

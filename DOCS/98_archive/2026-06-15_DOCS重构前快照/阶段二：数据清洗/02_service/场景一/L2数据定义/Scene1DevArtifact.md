# Scene1DevArtifact

## 定义

`Scene1DevArtifact` 是场景一开发者功能检验产生的调试输出、中间结果或小样本结果，用于判断该功能是否按预期运行。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `artifact_type` | enum | `mcap` / `json` / `yaml` / `image` / `text` / `summary` |
| `path` | path | 相对 [[Scene1DevRun]] 的产物路径 |
| `producer` | string | 产生该产物的功能检验项 |
| `source_input` | path/null | 来源小样本输入 |
| `description` | string | 人可读说明 |

## 有效性规则

- 测试产物只用于开发调试验收，不作为正式训练数据。
- 每个功能检验项必须至少声明一个产物。
- 如果产物是 MCAP，必须明确是调试 MCAP，不得写入正式生产输出目录。

## 相关链接

- [[Scene1DevRun]]
- [[Scene1DevRunLog]]

# RuntimeConfigSource

## 定义

`RuntimeConfigSource` 是 Runtime MVP 本次运行读取配置时使用的配置来源说明。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[03_配置加载与配置快照模块]]

## 现实语义

`RuntimeConfigSource` 表示“本次配置从哪里来”。它用于区分默认配置、用户显式指定配置、环境变量指定配置和后续入口参数指定配置，避免后续日志、manifest 或错误摘要只能看到一个模糊路径。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `source_kind` | enum-like string | 是 | 配置来源类型，例如 `explicit_path`、`environment`、`default_calibrated`、`default_smoke_test`。 |
| `config_path` | path | 是 | 最终被读取的配置文件路径。 |
| `declared_by` | string | 否 | 配置由命令行、环境变量、默认规则或上游入口声明。 |
| `exists_at_load_time` | boolean | 是 | 加载时配置文件是否存在。 |
| `selected_at` | datetime 或空 | 否 | Runtime 选择该配置来源的时间。 |

## 有效性规则

- `config_path` 必须能定位到一个具体文件路径。
- `source_kind` 必须是受控来源类型，不得用任意中文描述替代。
- 如果 `exists_at_load_time` 为 false，配置加载不得继续产出 [[EffectiveRuntimeConfig]]。
- 默认来源只能作为兜底，不能覆盖用户显式指定来源。

## 上游来源

- [[RunContext]] 中记录的配置路径或入口参数。
- Runtime 入口的默认配置选择规则。
- 现有阶段二配置文件，例如 `config/data_clean/data_clean_calibrated.yaml` 和 `config/data_clean/data_clean_smoke_test.yaml`。

## 下游消费者

- [[EffectiveRuntimeConfig]]
- [[ConfigSnapshot]]
- 配置预检查模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。

## 不负责

- 不判断配置字段是否完整或业务合法。
- 不保存配置文件内容。
- 不替代 [[RunArtifactPath]] 或 [[RunDirectoryLayout]]。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 默认配置选择顺序是否长期固定 | 影响无参数运行时读取哪个配置。 | 第一版按现有文档和代码倾向：显式路径优先，其次环境变量，再到 calibrated / smoke test。 | Runtime 入口 L2 或 L3 实现前确认。 |

## 相关链接

- [[RunContext]]
- [[EffectiveRuntimeConfig]]
- [[ConfigSnapshot]]
- [[03_配置加载与配置快照模块]]


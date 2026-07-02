# RunContext

## 定义

`RunContext` 是一次 Runtime 运行的完整上下文快照，用于把运行身份、模式、目标场景、输入输出路径、配置快照、状态和时间信息放在同一份运行事实中。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`RunContext` 表示“这一次 Runtime 到底在跑什么、用什么输入、往哪里输出、当前跑到什么状态”。它是 Runtime 主干能力的事实底座，后续 run 目录、配置快照、预检查、调度、日志、manifest 和错误摘要都应围绕它工作。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `run_id` | string | 是 | 本次运行的唯一标识。 |
| `run_mode` | [[RunMode]] | 是 | 本次运行属于开发者检验、生产单场景或生产全流程等哪种模式。 |
| `service_mode` | [[ServiceMode]] | 是 | 本次调度使用 fake service 还是真实 service。 |
| `target_scenes` | list of [[SceneName]] | 是 | 本次计划执行的场景列表。 |
| `active_scene` | [[SceneName]] 或空 | 否 | 当前正在执行的场景。 |
| `input_paths` | map | 是 | 本次运行依赖的输入产物路径映射。 |
| `output_root` | path | 是 | 本次运行的输出根位置。 |
| `run_dir` | [[RunDirectory]] / path | 是 | 本次运行的独立记录目录。 |
| `config_path` | path 或空 | 否 | 用户指定或默认读取的配置文件。 |
| `config_snapshot_path` | path 或空 | 否 | 本次实际生效配置快照路径。 |
| `status` | [[RunStatus]] | 是 | 本次运行当前或最终状态。 |
| `started_at` | datetime 或空 | 否 | Runtime 开始执行时间。 |
| `finished_at` | datetime 或空 | 否 | Runtime 结束执行时间。 |
| `duration_ms` | integer 或空 | 否 | 本次运行耗时。 |
| `metadata` | map | 否 | 额外运行元信息。 |

## 有效性规则

- `run_id` 必须非空，且本次运行期间稳定不变。
- `target_scenes` 必须非空，且只能包含 [[SceneName]] 中定义的场景。
- 全流程模式下，`target_scenes` 默认顺序必须为 `scene1 -> scene2 -> scene3 -> scene4 -> scene5`。
- `run_dir` 必须指向独立运行目录，不得复用旧目录。
- `metadata` 不得承载必需字段，只能用于补充说明。

## 上游来源

- UI 或入口脚本收集用户选择、输入路径、配置路径和输出位置。
- Runtime 根据入口参数创建初始 `RunContext`。
- [[02_Run目录管理模块]] 补齐 `run_dir`。
- 配置加载与配置快照模块补齐 `config_snapshot_path`。

## 下游消费者

- [[02_Run目录管理模块]]。
- 配置加载与配置快照模块。
- 配置预检查模块。
- 输入产物预检查模块。
- 场景注册与 Service 调度模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不描述 MCAP topic 内部消息结构。
- 不承载 Service 算法中间变量。
- 不替代配置文件内容。
- 不直接写出 run log、manifest 或 error summary。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要保留时分秒 | 影响目录名长度和人眼可读性。 | 已确认不保留时分秒；使用 `{YYYY-MM-DD}_s{scene_number}`，全流程使用 `{YYYY-MM-DD}_all`，重复运行追加 `_002`。 | 已由用户确认。 |

## 相关链接

- [[RunMode]]
- [[ServiceMode]]
- [[SceneName]]
- [[RunStatus]]
- [[SceneResult]]
- [[PipelineResult]]
- [[RuntimeErrorRef]]
- [[RunDirectory]]
- [[01_Runtime运行上下文定义]]

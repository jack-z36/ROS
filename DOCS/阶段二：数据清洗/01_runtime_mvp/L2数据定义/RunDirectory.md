# RunDirectory

## 定义

`RunDirectory` 是 Runtime 每次运行创建的独立运行记录目录，用于隔离本次调试产物、运行日志、配置快照、manifest、错误摘要和结果索引。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[02_Run目录管理模块]]

## 现实语义

`RunDirectory` 表示“这一次运行留下痕迹的地方”。它不是阶段二真实数据产物目录，而是 Runtime 横切能力的运行记录容器。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `run_dir` | path | 是 | 本次运行目录的绝对或工作区相对路径。 |
| `run_id` | string | 是 | 本次运行目录名，来自 [[RunContext]]。 |
| `base_dir` | path | 是 | 运行目录根位置，默认语义为 `src/data_clean/runs/`。 |
| `layout` | [[RunDirectoryLayout]] | 是 | 本次运行目录内的固定子路径集合。 |
| `created_at` | datetime | 是 | 目录创建时间。 |
| `is_new` | boolean | 是 | 本次是否创建了新目录；有效运行必须为 true。 |

## 有效性规则

- `run_dir` 必须位于 `src/data_clean/runs/` 下。
- `run_dir` 不得复用旧目录。
- `run_id` 默认格式为 `{YYYY-MM-DD}_s{scene_number}`；全流程使用 `{YYYY-MM-DD}_all`。
- 同一天同一场景重复运行时，必须追加短序号，例如 `{YYYY-MM-DD}_s1_002`。
- `run_dir` 创建后必须至少包含 [[RunDirectoryLayout]] 中定义的 `outputs/` 子目录。

## 上游来源

- [[RunContext]] 提供 `run_id`、目标场景和输出根语义。
- Run 目录管理模块根据日期、场景编号和冲突检测生成最终目录名。

## 下游消费者

- 配置加载与配置快照模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。
- [[RunContext]] 的 `run_dir` 字段。

## 不负责

- 不保存 raw、cleaned、validated、aligned 或 canonical dataset 等真实数据产物。
- 不直接写入 `run_log.json`、`config_snapshot.yaml`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json` 的内容。
- 不替代阶段二真实数据产物目录 `asset/阶段二：数据清洗/`。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要允许用户指定自定义 run 根目录 | 影响调试环境和多人协作。 | 第一版固定使用 `src/data_clean/runs/`。 | 后续 Runtime 入口设计时确认。 |

## 相关链接

- [[RunContext]]
- [[RunDirectoryLayout]]
- [[RunArtifactPath]]
- [[02_Run目录管理模块]]

# RuntimeStepRecord

## 定义

`RuntimeStepRecord` 是 Runtime 每个执行步骤的结构化记录。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`RuntimeStepRecord` 表示“Runtime 在某个时刻做了哪个步骤、属于哪个场景、结果如何、有什么可机器读取的细节”。它是 `run_log.json` 的基础记录单元之一。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `step_name` | string | 是 | Runtime 当前步骤名称，例如 config_load、input_precheck。 |
| `scene_name` | [[SceneName]] 或空 | 否 | 步骤所属场景；全局步骤可为空。 |
| `status` | [[RunStatus]] | 是 | 步骤状态。 |
| `started_at` | datetime | 是 | 步骤开始时间。 |
| `finished_at` | datetime 或空 | 否 | 步骤结束时间。 |
| `message` | string | 否 | 人类可读摘要。 |
| `details` | map | 否 | 机器可读补充信息。 |

## 有效性规则

- `step_name` 必须非空。
- `status` 必须使用 [[RunStatus]]。
- 场景相关步骤应填写 `scene_name`。
- 失败步骤应能关联到 [[RuntimeErrorRef]] 或被错误摘要引用。

## 上游来源

- Runtime 在创建上下文、创建 run 目录、加载配置、执行预检查、调度 Service、写日志和写 manifest 等步骤中生成。

## 下游消费者

- 结构化日志模块。
- Manifest 与错误摘要模块。
- [[RuntimeErrorRef]]
- Runtime smoke test 模块。

## 不负责

- 不保存完整业务数据。
- 不替代 [[SceneResult]]。
- 不决定步骤是否应该继续执行；该决策属于 Runtime 编排逻辑。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `step_name` 是否需要固定枚举 | 影响日志稳定性和测试断言。 | 第一版允许语义化字符串，后续日志模块再收敛。 | 结构化日志模块设计时确认。 |

## 相关链接

- [[RunContext]]
- [[RunStatus]]
- [[SceneName]]
- [[RuntimeErrorRef]]
- [[01_Runtime运行上下文定义]]


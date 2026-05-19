# SceneDispatchEvent

## 定义

`SceneDispatchEvent` 是场景调度过程中产生的结构化事件。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[06_场景注册与Service调度模块]]

## 现实语义

`SceneDispatchEvent` 表示“Runtime 调度某个场景时发生了一个可记录的节点”，例如计划创建、场景开始、场景成功、场景失败或全流程停止。它为后续结构化日志模块提供事件来源。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `run_id` | string | 是 | 对应 [[RunContext]] 的运行标识。 |
| `scene_name` | [[SceneName]] 或空 | 否 | 与具体场景相关时填写。 |
| `event_type` | 受控字符串 | 是 | 如 `dispatch_plan_created`、`scene_started`、`scene_succeeded`、`scene_failed`、`pipeline_stopped`。 |
| `status` | [[RunStatus]] | 是 | 事件发生后的运行或场景状态。 |
| `message` | string | 否 | 人类可读短说明。 |
| `error` | [[RuntimeErrorRef]] 或空 | 否 | 失败事件对应的错误引用。 |
| `created_at` | datetime 或空 | 否 | 事件时间。 |

## 有效性规则

- `event_type` 必须来自受控集合。
- `scene_failed` 或 `pipeline_stopped` 且由错误触发时，`error` 必须存在。
- 与具体场景相关的事件必须填写 `scene_name`。
- 事件只描述调度事实，不直接写入文件。

## 上游来源

- [[06_场景注册与Service调度模块]] 在计划创建、场景执行和失败停止时产生。
- [[RuntimeErrorRef]] 由预检查失败、注册缺失或 service 执行失败提供。

## 下游消费者

- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不替代 `run_log.json`。
- 不保存完整 traceback。
- 不决定是否继续执行后续场景。
- 不定义 UI 展示文案。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 事件类型是否需要与最终 `run_log.json` schema 完全一致 | 影响日志模块对接。 | 当前先作为调度事件源；日志模块设计时再收敛字段。 | 功能8设计时确认。 |

## 相关链接

- [[RunContext]]
- [[SceneName]]
- [[RunStatus]]
- [[RuntimeErrorRef]]
- [[06_场景注册与Service调度模块]]

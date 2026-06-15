# RunStatus

## 定义

`RunStatus` 是 Runtime 运行、场景结果或步骤记录的状态枚举。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`RunStatus` 用来表达一次运行或某个步骤现在处于什么生命周期阶段，帮助日志、manifest、错误摘要和 UI 结束反馈使用同一套状态语言。

## 字段或取值

| 取值 | 语义 |
| --- | --- |
| `created` | 上下文已创建，但尚未进入执行。 |
| `running` | Runtime 正在执行预检查、调度或 Service。 |
| `succeeded` | 本次运行目标全部完成。 |
| `failed` | 本次运行因错误停止。 |
| `cancelled` | 用户或上层入口取消运行。 |

## 有效性规则

- 只能使用本文列出的受控取值。
- 结束状态为 `succeeded`、`failed` 或 `cancelled` 后，不应继续调度新的 Service。
- Runtime MVP 第一版不引入 `partial_success`。

## 上游来源

- Runtime 创建 [[RunContext]] 时设置初始状态。
- Runtime 在预检查、调度、完成或失败时更新状态。
- Service 执行结果可影响 [[SceneResult]] 的状态。

## 下游消费者

- [[RunContext]]
- [[SceneResult]]
- [[PipelineResult]]
- [[RuntimeStepRecord]]
- [[RuntimeErrorRef]]
- 结构化日志模块。
- Manifest 与错误摘要模块。

## 不负责

- 不表达错误原因；错误原因由 [[RuntimeErrorRef]] 承载。
- 不表达场景名称；场景由 [[SceneName]] 承载。
- 不表达部分成功语义。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要 `partial_success` | 真实全流程接入后可能出现部分场景成功、部分场景失败。 | Runtime MVP 第一版不引入。 | 真实 Service 全流程接入前确认。 |

## 相关链接

- [[RunContext]]
- [[SceneResult]]
- [[PipelineResult]]
- [[RuntimeStepRecord]]
- [[01_Runtime运行上下文定义]]


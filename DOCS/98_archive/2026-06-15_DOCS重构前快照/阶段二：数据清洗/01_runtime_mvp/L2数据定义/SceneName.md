# SceneName

## 定义

`SceneName` 是阶段二五个业务场景的受控名称枚举。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`SceneName` 用统一短名称表示阶段二 pipeline 中的五个业务处理场景，避免 Runtime、日志、manifest、错误摘要和 Service 注册表使用不同叫法。

## 字段或取值

| 取值 | 场景 |
| --- | --- |
| `scene1` | 提取夹爪开合以及位姿转换。 |
| `scene2` | 硬件数据可靠性验证。 |
| `scene3` | MCAP 多 topic 时间轴对齐。 |
| `scene4` | 构建标准 canonical dataset。 |
| `scene5` | 模型训练格式导出器。 |

## 有效性规则

- 只能使用本文列出的受控取值。
- 全流程默认顺序必须为 `scene1 -> scene2 -> scene3 -> scene4 -> scene5`。
- Runtime MVP 不新增 `scene6`，除非用户明确要求重构阶段二 L1 边界。

## 上游来源

- 用户或开发者在入口界面选择场景。
- 全流程模式由 Runtime 自动展开为五个场景。
- 功能模块清单和阶段二路线图定义场景边界。

## 下游消费者

- [[RunContext]]
- [[SceneResult]]
- [[RuntimeStepRecord]]
- [[RuntimeErrorRef]]
- 输入产物预检查模块。
- 场景注册与 Service 调度模块。
- 结构化日志模块。

## 不负责

- 不描述每个场景内部算法。
- 不承载场景配置。
- 不判断输入产物是否存在。

## 当前未知问题

无。

## 相关链接

- [[RunContext]]
- [[RunMode]]
- [[SceneResult]]
- [[RuntimeErrorRef]]
- [[01_Runtime运行上下文定义]]


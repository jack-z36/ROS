# 一、模型资源与装配问题

## 1.1 相关原理

### 1.1.1 最终输出产物 `ActInferenceService`

#### 对应的文件以及相关源码

| 项目 | 内容 |
|---|---|
| 文件层位置 | `src/model_deploy/act/service/act_inference.py`；它属于 `service`：接收 RAM 中的观测对象，计算后产出新的 RAM 对象，不负责读取权重文件、安排循环或直接发布 ROS 命令。 |
| class 模板 | `ActInferenceService` 是创建“推理服务实例”的模板。实际运行时，`ActInferenceService(...)` 会在 RAM 中创建一个具体实例，并由变量或其他对象属性持有其引用。 |
| 外部输入 | `ObservationSnapshot`：一次已经收集、整理好的机器人观测。 |
| 外部输出 | `ActionChunk`：模型一次预测出的动作块；它只是 RAM 中的动作数据，还不是 ROS 命令或硬件动作。 |
| 调用者 | `runtime` 层持有这个实例的引用，并在需要推理时调用它；因此 `runtime` 决定“何时调用”，`ActInferenceService` 决定“给定观测如何计算动作”。 |

#### 按公开接口理解这个 class

| 观察顺序 | 在本 class 中看到的事实 | 用这个事实理解 class |
|---|---|---|
| 第一步：找公开接口 | `predict_action_chunk(observation)` 没有以 `_` 开头，是公开的业务方法。 | 它是外部代码请求“由观测得到动作块”的入口，也是这个 class 的主要业务能力。 |
| 第二步：看公开接口的输入输出 | 输入 `ObservationSnapshot`，返回 `ActionChunk`。 | 可以把该实例的核心能力先抽象为：`观测 → 动作块`。 |
| 第三步：区分公开属性 | `input_spec` 通过 `@property` 对外提供读取入口。 | 它让外部读取推理契约，不负责完成推理计算；因此它是公开信息接口，不是主要业务计算。 |
| 第四步：回看内部内容 | `_config`、`_policy`、normalizer、`_device` 和内部方法均以 `_` 表示主要供实例内部使用。 | 它们保存长期依赖、准备数据或检查约束，目的是支撑公开入口稳定地产出动作块。 |
| 本 class 的抽象 | 创建一个实例后，实例长期保留推理需要的“内参”，每次收到新观测时复用这些内参完成一次计算。 | 可以把它理解为“带长期保存依赖的函数能力包”。这是一种理解角度；严格说 class 不是特殊函数，而是封装状态和一个或多个能力的模板。 |

#### 公开接口总表

| 公开接口 | 类型 | 外部怎样使用 | 在本 class 中的职责 | 是否是主要业务能力 |
|---|---|---|---|---|
| `predict_action_chunk(observation)` | 公开函数 / 公开方法 | `service.predict_action_chunk(observation)` | 把一次观测加工为一个动作块。 | 是 |
| `input_spec` | 公开属性 | `service.input_spec` | 读取实例保存的输入契约对象。 | 否；它提供信息，不进行主要推理计算。 |

#### 功能

| 功能角度 | 结论 | 对应代码事实 |
|---|---|---|
| 核心功能 | 把外部传入的 `ObservationSnapshot` 加工为 `ActionChunk`。 | `predict_action_chunk()` 依次调用观测准备、ACT 推理和动作后处理。 |
| 长期保存什么 | 实例保存 `config`、state normalizer、action normalizer、policy、input spec，以及由它们得到的 device。 | `__init__()` 内的 `self._... = ...` 绑定。 |
| 为什么保存 | 后续每一次公开函数调用都需要这些对象；调用者不必每次重复传入权重模型、归一化器和输入规范。 | `predict_action_chunk()` 从 `self._policy`、`self._state_normalizer`、`self._action_normalizer`、`self.input_spec` 和 `self._device` 读取它们。 |
| 初始化时检查什么 | 检查 policy 是否有可调用的 `predict_action_chunk`，并检查两个 normalizer 的维度是否与 `input_spec` 一致。 | `_validate_contract()`；它不是对所有 `config` 字段做全面检查。 |
| 不负责什么 | 不从硬盘加载权重；不订阅 ROS topic；不决定调用频率；不把动作发布给机械臂。 | 这些职责分别属于 `repo`、`ui` 或 `runtime` 层。 |

##### 第一、检查外部输入 config 是否满足 spec

| 原先的粗略理解 | 结合代码后的准确理解 | 原因 |
|---|---|---|
| “这个 class 检查外部 config 是否满足 spec。” | 需要收窄：它在初始化时检查“已经传入的多个依赖能否共同工作”，其中只在 policy 没有参数时，才用 `config.runtime.device` 作为设备回退值。 | `_validate_contract()` 检查的是 policy 方法存在性、state/action normalizer 的维度与 `input_spec` 的一致性；它没有逐项验证全部 config。 |
| “这些数据会留在 class 内。” | 正确：`__init__()` 将传入对象绑定为实例属性；这些属性作为同一个实例的长期内参，可被后续公开函数反复读取。 | 例如 `self._policy = policy`。这通常是“增加一个标签指向同一个 RAM 对象”，而不是复制一份 policy。 |

| 初始化阶段顺序 | 发生的事 | 它为公开函数做的辅助 |
|---|---|---|
| 1 | 绑定 `config`、两个 normalizer、policy 和 input spec 到 `self._...` 属性。 | 把运行时已经存在于 RAM 的依赖交给该实例长期保存。 |
| 2 | 调用 `_resolve_device()`，结果保存到 `self._device`。 | 确定推理应使用的计算设备。 |
| 3 | 调用 `_validate_contract()`。 | 尽早发现“模型能力或维度不匹配”，避免带着不一致的依赖进入后续推理。 |

##### 第二、公开核心函数 `predict_action_chunk` 供 runtime 层调用

| 调用流程 | 输入 / 读取 | 做什么 | 输出 |
|---|---|---|---|
| 1. `runtime` 调用公开方法 | `ObservationSnapshot` | `runtime` 通过它持有的实例引用调用 `service.predict_action_chunk(observation)`。 | 一次推理请求进入 `service`。 |
| 2. 准备模型输入 | observation + `self._state_normalizer` + `self.input_spec` + `self._device` | `prepare_observation_batch(...)` 验证和整理观测、归一化状态、整理图像，并形成模型可用 batch。 | `batch`。 |
| 3. ACT 推理 | `self._policy` + `batch` | `run_act_inference(...)` 调用 policy 的 `predict_action_chunk(batch)`。 | `raw_chunk`，即模型原始输出。 |
| 4. 动作后处理 | raw chunk + `self._action_normalizer` + chunk size | `postprocess_action_chunk(...)` 对动作做反归一化、结构整理和最终检查。 | `ActionChunk`。 |
| 5. 返回调用者 | `ActionChunk` | 函数把动作块交回 `runtime`；之后是否发布、何时执行，由 `runtime` 和 `ui` 决定。 | 调用者获得 RAM 中的动作块。 |

#### “特殊函数”视角与边界

| 比较项 | 普通函数 | 以 `ActInferenceService` 为例的“函数能力包” |
|---|---|---|
| 一次调用需要什么 | 常把主要依赖都作为本次参数传入。 | 本次只显式传入 observation；policy、normalizer、spec、device 已长期保存在实例属性中。 |
| 可重复调用 | 调用结束后通常只保留返回值。 | 同一个实例可以收到多次 observation，并复用同一组长期依赖。 |
| 适合的理解方式 | “输入 → 计算 → 输出”。 | “先创建并配置好一个带内参的能力对象，再反复调用它的公开核心函数”。 |
| 必须保留的边界 | 函数不是 class。 | class 可以有零个、一个或多个公开函数，还可以有公开属性；应先看全部公开接口，再判断其核心职责。 |

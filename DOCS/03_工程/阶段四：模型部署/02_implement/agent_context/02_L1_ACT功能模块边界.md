# L1 ACT 功能模块边界（Agent 上下文版）

> [!info] 产物归属
> - 类型：L1 架构协作包中的 Agent 权威边界上下文（阶段四：模型部署）。
> - 目标路径：`DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`。
> - 上游任务文档：`01_L1_ACT部署程序任务文档.md`。
> - 协作文档：`03_L1_ACT功能模块协作架构.md`（讲模块间协作，不讲单模块边界）。
> - 适用对象：第一版 ACT 部署程序的 6 个 L2 功能模块的功能边界、输入输出、负责/不负责、代码层落点。
> - Agent 消费目的：完整理解每个功能模块的边界，支持 L2 功能设计、L3 微元任务生成和越界检查，避免幻觉和职责串扰。
> - 本文职责：定义每个 L2 的功能边界。不展开模块间协作关系（指向 `03_L1_ACT功能模块协作架构.md`），不展开任务管理属性（指向 `01_L1_ACT部署程序任务文档.md`）。
> - 人类消费入口：`../ACT架构交互可视化.html`。

## 0. 消费者分工与本文定位

L1 架构协作包按消费对象拆分为 4 个产物：

| 消费者 | 消费产物 | 消费目的 | 信息密度 |
|---|---|---|---|
| Agent | `01_L1_ACT部署程序任务文档.md` | 获取 L1 总目标、L2 清单与开发顺序、L1 验收口径。 | 中。任务管理属性。 |
| Agent | 本文档（功能模块边界） | 完整理解每个 L2 的功能边界，减少 L2 设计和 L3 生成时的职责越界。 | 高。逐模块边界契约。 |
| Agent | `03_L1_ACT功能模块协作架构.md` | 完整理解模块间协作关系，减少数据流和接口歧义。 | 高。协作关系契约。 |
| 人类 | `../ACT架构交互可视化.html` | 快速理解整体架构、模块协作和模块边界，更好地指挥 Agent。 | 低。可视化为主。 |

权威关系：

- 本文档是 Agent 的边界权威上下文；HTML 与本文冲突时以本文为准。
- 本文不重复定义协作关系，详见 `03_L1_ACT功能模块协作架构.md`。
- L2 设计 Agent 和 L3 生成 Agent 必须读取本文，确认当前 L2 的边界后再展开内部设计。

后续 Agent 使用本文时，必须至少抽取以下信息：

1. 当前 L2 的功能定义、输入和输出。
2. 当前 L2 的负责内容和不负责内容（边界）。
3. 当前 L2 的完成判据。
4. 当前 L2 允许落到哪些代码层，以及明确不能越过的边界。

## 1. 全局边界原则

### 1.1 代码落点边界

每个 L2 都允许横跨以下代码层：

```text
types / config / repo / service / runtime / ui
```

但产物必须继续落在 `ACT代码树分层与产物落点约束.md` 指定的位置。也就是说：

- L2 是任务边界。
- 六层目录是代码落点边界。
- 一个 L2 可以同时包含 types、config、service、runtime、ui 中的文件。
- 不允许为了让 L2 名字好看而打破代码分层。

### 1.2 数据与控制边界

本程序不能被理解为单纯线性加工流水线。它包含三类运行角色：

| 角色 | 含义 | 对应 L2 |
|---|---|---|
| 外部输入角色 | ROS callback 接收传感器数据并写入 RAM；外部配置进入 RAM。 | L2-01、L2-02 |
| 后台计算角色 | ACT 推理 actor 消费 `ObservationSnapshot`，产出 `ActionChunk`；安全检查单步 raw action。 | L2-03、L2-04 |
| 中央调度角色 | `ControlLoop` 按时间和状态调用各服务，决定何时取 observation、何时推理、何时消费 chunk、何时 fallback。 | L2-06 |
| 外部输出角色 | 把内部动作对象转换成外部执行器可消费的 topic 消息。 | L2-05 |

`ControlLoop` 不是普通加工函数，而是 runtime 中央总控。它不应该被拆进某个单纯的数据转换 L2。

## 2. L2-01 外部参数加载与契约校验闭环

`l2-01-external-contract`

### 2.1 功能定义

本 L2 的功能是获取整个部署程序在正常运行时依赖的外部静态参数，对这些参数做合规性检查，然后载入当前 Python 进程 RAM 中，形成后续模块可以稳定使用的配置对象、数据规格对象和 bundle 契约对象。

### 2.2 输入

```text
deploy.yaml
manifest.json
normalizers.json
experiment_config.yaml
checkpoint 路径
```

### 2.3 输出

```text
DeployConfig
state/action 数据规格
bundle contract 检查结果
normalizer contract 检查结果
runtime/safety/topic 配置对象
```

### 2.4 负责内容

- 固定 `observation.state` 的 16D 维度、段序、字段语义和值域。
- 固定 `action` 的 16D 维度、段序、字段语义和值域。
- 固定 `/act/*` observation、policy_action、status、metrics、command topic 名。
- 固定 runtime 参数：`control_hz`、`inference_hz`、`chunk_size`、`mode`、fallback 策略。
- 固定 safety 参数：TCP 单步限制、quaternion 检查、gripper width 值域。
- 校验 ACT bundle 交付物是否具备后续加载推理所需文件与元数据。

### 2.5 不负责内容

- 不订阅 ROS topic。
- 不创建 publisher。
- 不加载 ACT 权重到模型对象。
- 不执行模型前向推理。
- 不启动控制循环。
- 不发送硬件命令。

### 2.6 完成判据

合法配置能载入 RAM，非法配置能在入口处失败。后续模块不需要猜 state/action/topic/bundle 长什么样。

### 2.7 代码层落点

`types/`、`config/`、`repo/`、`config_files/`。

### 2.8 上下游

- 上游：无（全部后续 L2 的静态契约地基）。
- 下游：所有 L2 都 import DeployConfig / 数据规格。
- 协作细节见 `03_L1_ACT功能模块协作架构.md`。

## 3. L2-02 传感器订阅与 ObservationSnapshot 组装闭环

`l2-02-observation-snapshot`

### 3.1 功能定义

本 L2 的功能是从外部传感器 topic 接收数据，完成必要预处理和字段汇聚，生成一个完整、合法、新鲜的 `ObservationSnapshot`。

### 3.2 输入

```text
/act/observation/image/left_gripper_fisheye
/act/observation/image/right_gripper_fisheye
/act/observation/arm/left_tcp_pose
/act/observation/arm/right_tcp_pose
/act/observation/gripper/left_state
/act/observation/gripper/right_state
```

### 3.3 输出

```text
ObservationSnapshot(
  images=...,
  state=...,
  encoded_state=np.ndarray shape (16,),
  captured_at_s=...
)
SharedBuffer.latest_observation
```

### 3.4 负责内容

- 创建或定义 observation topic 的订阅入口。
- 将 ROS 图像消息转换为 ACT 需要的图像 tensor。
- 接收左右臂 TCP pose。
- 接收左右夹爪 gripper width。
- 检查必需字段是否齐全。
- 检查字段是否过期。
- 调用 state codec 生成 16D `encoded_state`。
- 将 snapshot 写入 latest-only buffer。

### 3.5 不负责内容

- 不调用 ACT 模型。
- 不生成 action_chunk。
- 不消费 action_chunk。
- 不决定是否发起下一次推理。
- 不做硬件命令发送。

### 3.6 完成判据

在 mock 输入下，完整传感器字段能生成 `ObservationSnapshot`；缺字段或字段过期时不生成 snapshot。

### 3.7 代码层落点

`service/`、`runtime/`、`ui/`、`tests/`。

### 3.8 上下游

- 上游：L2-01（state/topic/image/config 契约）。
- 下游：L2-06 读取 `latest_observation`；L2-03 消费 `ObservationSnapshot` 契约。
- 协作细节见 `03_L1_ACT功能模块协作架构.md`。

## 4. L2-03 ObservationSnapshot 到 ACT ActionChunk 推理闭环

`l2-03-act-inference`

### 4.1 功能定义

本 L2 的功能是把 `ObservationSnapshot` 加工成 LeRobot ACT 模型可消费的 batch，然后调用 ACT policy，输出 shape 为 `(chunk_size, 16)` 的 `ActionChunk`。

### 4.2 输入

```text
ObservationSnapshot
DeployConfig
ACT bundle
normalizers.json
experiment_config.yaml
```

### 4.3 输出

```text
ActionChunk(
  actions=np.ndarray shape (chunk_size, 16),
  obs_time=...,
  ready_time=...,
  action_dt=...,
  request_id=...
)
SharedBuffer.chunk_result_queue
```

### 4.4 负责内容

- 将 `ObservationSnapshot` 映射为 ACT batch。
- 处理 LeRobot ACT 需要的 batch key。
- 加载 state/action normalizer。
- 执行 state normalize 和 action unnormalize。
- 加载 ACT policy runtime。
- 保持统一推理接口：

```text
predict_action_chunk(observation: ObservationSnapshot) -> np.ndarray shape (chunk_size, 16)
```

- 提供 fake-policy 路径，保证无真实 bundle 时仍能本地验收接口。

### 4.5 不负责内容

- 不负责 ROS callback。
- 不负责 `ObservationSnapshot` 是否齐全。
- 不负责 action_chunk 的首版单步选择。
- 不负责 action 平滑、跨 chunk 融合或 RTC 类优化。
- 不负责 safety 检查。
- 不负责 topic 发布。
- 不负责真机发送。

### 4.6 完成判据

给定一个合法 `ObservationSnapshot`，fake-policy 必须能输出 `(chunk_size, 16)` 的 action chunk；真实 ACT bundle 就绪后，real-policy dry-run 输出同样 shape 的 action chunk。

### 4.7 代码层落点

`repo/`、`service/`、`runtime/`、`tests/`。

### 4.8 上下游

- 上游：L2-01（bundle/normalizer/runtime 配置）、L2-02（`ObservationSnapshot` 契约，可先用 mock）。
- 下游：L2-06 通过 queue 收集 `ActionChunk`，并在首版中直取单步 raw action。
- 协作细节见 `03_L1_ACT功能模块协作架构.md`。

## 5. L2-04 单步 Action 安全检查闭环

`l2-04-safety-guard`

### 5.1 功能定义

本 L2 的功能是对准备发布或发送的单步 raw action 做部署侧安全检查，输出 safe action、拒绝原因或 fallback 决策依据。

### 5.2 输入

```text
raw single action, shape (16,)
latest ObservationSnapshot
previous safe action
SafetyConfig
```

### 5.3 输出

```text
SafetyResult(
  action=safe action | None,
  accepted=True | False,
  reason=...
)
```

### 5.4 负责内容

- 检查 action shape 是否为 16。
- 检查 NaN / Inf。
- 检查 quaternion 是否归一化。
- 检查 gripper width 是否在 `[0, 1]`。
- 检查 TCP 单步位移或姿态变化是否超限。
- 根据配置执行 reject、clamp、hold-last-action 或 safe-stop 所需的安全返回。

### 5.5 不负责内容

- 不产生 raw action。
- 不管理 chunk 生命周期。
- 不做 action 平滑、跨 chunk 融合或 RTC 类优化。
- 不发布 `/act/policy_action`。
- 不转换硬件命令格式。
- 不调用硬件 SDK。
- 不处理 workspace / IK / 急停等硬件级检查；这些属于 L2-05。

### 5.6 完成判据

合法 action 通过；非法 shape、NaN/Inf、quaternion 非归一化、width 越界、TCP step 超限等输入被拒绝或按配置处理，并返回明确原因。

### 5.7 代码层落点

`service/`、`tests/`。

### 5.8 上下游

- 上游：L2-01（action spec / safety config）；运行时由 L2-06 产出 raw single action。设计和单测阶段可用 mock raw action。
- 下游：L2-05 消费 safe action / `SafetyResult`。
- 协作细节见 `03_L1_ACT功能模块协作架构.md`。

## 6. L2-05 单步 Action 到执行器 Topic 适配发送闭环

`l2-05-action-publisher`

### 6.1 功能定义

本 L2 的功能是把通过安全检查的单步 action 转换为外部执行器可以消费的 ROS topic 消息，并在 gate 允许时发送到对应 topic。

### 6.2 输入

```text
safe single action, shape (16,)
/act/policy_action
latest arm/gripper state
BridgeConfig / HardwareConfig
```

### 6.3 输出

```text
/act/policy_action
/act/command/arm/left_target
/act/command/arm/right_target
/act/command/gripper/left_target
/act/command/gripper/right_target
/act/command/status
```

### 6.4 负责内容

- 发布或适配 `/act/policy_action`。
- 将 16D action 拆为 left TCP、left gripper、right TCP、right gripper。
- 构造左右臂 `PoseStamped` 目标。
- 将 gripper width 映射为硬件侧 angle。
- 执行硬件发送前检查：workspace、IK、gate、deadman、急停状态。
- 输出 command status，记录 `action_id`、`safety_ok`、`sent_to_driver`、`failure_reason`。
- 支持 shadow-run，默认不直接触发真机动作。

### 6.5 不负责内容

- 不调用 ACT 模型。
- 不管理 action chunk。
- 不决定何时 tick。
- 不替代 L2-04 的 policy-action 通用安全检查。
- 不在无人工授权时执行 real-robot smoke test。

### 6.6 完成判据

在 shadow-run 下，safe action 能被正确转换为执行器 topic 消息；gate 关闭时不发送真机；失败原因能写入 `/act/command/status`。

### 6.7 代码层落点

`ui/`、`service/`、`launch/`、`tests/`。

### 6.8 上下游

- 上游：L2-01（topic/hardware/bridge 配置）、L2-04（safe action / `SafetyResult`）。
- 下游：外部执行器（外部边界）。
- 协作细节见 `03_L1_ACT功能模块协作架构.md`。

## 7. L2-06 ControlLoop 中央运行调度闭环

`l2-06-control-loop`

### 7.1 功能定义

本 L2 的功能是实现部署程序的中央运行总控。它以固定 `control_hz` 周期执行 tick，根据时间、状态、队列、失败条件和配置，调用前面 L2 提供的各个 service。

### 7.2 输入

```text
DeployConfig
SharedBuffer.latest_observation
SharedBuffer.inference_request_queue
SharedBuffer.chunk_result_queue
SafetyGuard
publisher / command adapter
```

### 7.3 输出

```text
InferenceRequest
raw single action, shape (16,)
safe action 或 fallback 输出（直接交给 L2-05 发布）
status / metrics
```

> [!note] 不存在独立的 ControlDecision 对象
> ACT 模块的 tick 不产出"决策对象"。安全检查通过后，safe action 直接由 L2-05 发布；任何不可用环节直接进入 fallback（hold / safe_stop / status-only），由 L2-05 输出。

### 7.4 负责内容

- 按 `control_hz` 周期运行。
- 读取 latest observation。
- 根据 chunk 状态和 prefetch 策略决定是否提交 `InferenceRequest`。
- 收集后台推理返回的 `ActionChunk`。
- 首版维护 active chunk 与 cursor，并按 tick 直取当前 step 作为 raw single action。
- 对非法 chunk、过期 chunk 或 cursor 不可用进入 fallback。
- 调用 L2-04 进行安全检查。
- 调用 L2-05 的发布或发送接口。
- 处理 fallback：无 observation、无 chunk、chunk 过期、safety 拒绝、推理失败。
- 更新 metrics 和 status。

### 7.5 不负责内容

- 不直接解析外部配置文件。
- 不直接预处理图像。
- 不直接实现 ACT batch 构造。
- 不直接实现 ACT 前向推理。
- 不直接实现硬件 SDK 细节。
- 不实现 action 平滑、smoothstep blend、跨 chunk 融合或 RTC 类优化。
- 不把所有 service 逻辑塞进 `tick()` 内部。

### 7.6 完成判据

在 mock 环境中，ControlLoop 能持续按 tick 调用各服务：

```text
无 observation -> 不提交 request 或进入 fallback
有 observation -> 提交 request
action_chunk 返回 -> 消费单步 action
chunk 快结束 -> prefetch 下一次推理
safety 拒绝 -> fallback
发布成功 -> metrics 计数更新
```

### 7.7 代码层落点

`runtime/`、`ui/`、`tests/integration/`。

### 7.8 上下游

- 上游：L2-01（DeployConfig）、L2-02 至 L2-05（service 句柄）。
- 下游：通过 L2-05 发布命令；通过 metrics 发布 status。
- 协作细节见 `03_L1_ACT功能模块协作架构.md`。

## 9. 模块边界不变量

以下边界在后续 L2/L3 编写时必须保持：

1. L2-01 可以检查 bundle contract，但不做真实模型前向推理。
2. L2-02 只生成 `ObservationSnapshot`，不决定推理节奏。
3. L2-03 只消费 `InferenceRequest`，不决定 action 何时执行。
4. L2-04 只做 policy-action 通用安全检查，不做硬件 workspace / IK / gate。
5. L2-05 只做外部 topic / 硬件命令适配，不做 ACT batch 和模型推理。
6. L2-06 只做调度、首版 chunk 直取和状态机，不吞并前面各 service 的实现细节。
7. 第一版不实现 action 平滑；smoothstep blend、跨 chunk 融合和 RTC 类平滑属于后续优化方向。
8. 任何真机发送都必须经过 shadow-run / gate / command_status，不得由模型节点直接调用硬件 SDK。

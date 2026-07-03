# ACT 部署契约（TO-BE）

> [!info] 产物归属
> - 类型：TO-BE Contract（阶段四开发工作流 · 阶段二产物）。
> - 目标路径：`DOCS/03_工程/阶段四：模型部署/01_contracts/ACT部署契约.md`。
> - 适用模型：ACT（第一版部署主线）。
> - 并存说明：本文件与 [[TO-BE Contract]]（Pi0.5 版）并存。Pi0.5 版作为历史契约保留。
> - 代码根目录：`src/model_deploy/act/`（新建）。`src/model_deploy/pi05/` 保留不动作为历史参考。

## 与 Pi0.5 部署契约的关系

ACT 部署契约复用 Pi0.5 部署契约中**与模型无关**的部分（ROS 拓扑、TCP 16D action 语义、硬件栈、安全检查、坐标系约定），只在以下方面区别于 Pi0.5：

| 项 | Pi0.5 版 | ACT 版（本文） |
|---|---|---|
| 内部模型 | Pi0.5 VLA + LoRA | ACT（Action Chunking Transformer） |
| topic namespace | `/pi05/*` | `/act/*` |
| 推理节点名 | `Pi05VlaDeployNode` | `ActVlaDeployNode` |
| 代码根目录 | `src/model_deploy/pi05/`（历史保留） | `src/model_deploy/act/`（新建） |
| bundle 加载 | base + LoRA adapter | 完整 ACT checkpoint |
| state/action 维度 | 14D（旧）→ 规划 16D | **16D**（第一版，不含触觉） |
| 归一化 | min-max [-1,1] | mean-std |
| 交付物契约 | [[模型训练交付物契约]] | [[ACT模型训练交付物契约]] |

**复用部分**（与模型无关，直接引用 Pi0.5 契约的设计，不在本文重复展开）：
- 硬件拓扑（4090 推理机 + 双 RM65 + 双大象夹爪 + 触觉芯片 + 鱼眼相机）——见 [[TO-BE Contract]]#硬件拓扑。
- TCP pose 来源约定（RM65 quaternion xyzw 归一化，euler→quaternion 在 driver 内转换）——见 [[TO-BE Contract]]#RM65 TCP pose 来源约定。
- 夹爪 width↔angle 转换边界（observation/policy_action 用 width[0,1]，command 用 angle[0,100]）——见 [[TO-BE Contract]]#夹爪状态/命令语义约定（width ↔ angle 转换边界）。
- 指令发送前必须执行的检查（16D 维度、finite、quaternion 归一化、workspace、IK 预检、gripper 限幅、急停 gate）——见 [[TO-BE Contract]]#指令发送前必须执行的检查。

## 节点网络拓扑（ACT 版）

```text
fisheye_camera_node -> ActVlaDeployNode
rm65_driver_node（状态发布角色） -> ActVlaDeployNode
elephant_gripper_node（状态发布角色） -> ActVlaDeployNode

ActVlaDeployNode
  -> command_bridge_sender_node
  -> rm65_driver_node（命令执行角色）
  -> elephant_gripper_node（命令执行角色）
```

> [!note] 第一版不含触觉
> 第一版 `ActVlaDeployNode` **不订阅** `/act/observation/tactile/*` topic（state = 16D，不含触觉）。`tactile_sensor_node` 可存在但不接入 ACT 节点。后续版本 state 升级 32D 时再接入。

| 节点 | 职责 | 边界 |
|---|---|---|
| `fisheye_camera_node` | 发布左右夹爪鱼眼相机图像。 | 只处理相机数据。 |
| `rm65_driver_node`（状态发布角色） | 发布左右 RM65 的 TCP 状态。 | 作为传感器时只发布状态，不订阅命令 topic。 |
| `elephant_gripper_node`（状态发布角色） | 发布左右大象夹爪开合状态。 | 作为传感器时只发布状态，不订阅命令 topic。 |
| `ActVlaDeployNode` | 读取 observation topics，构造模型输入，运行 ACT 推理，输出 policy action。 | 不直接驱动 RM65 或夹爪硬件。 |
| `command_bridge_sender_node` | 将 policy action 转成 RM65 / 夹爪可执行指令，并执行安全检查与发送。 | 负责硬件面向的指令语义。 |
| `rm65_driver_node`（命令执行角色） | 订阅 RM65 目标指令，驱动左右机械臂执行。 | 作为执行器时只订阅命令 topic。 |
| `elephant_gripper_node`（命令执行角色） | 订阅夹爪目标指令，驱动左右夹爪执行。 | 作为执行器时只订阅命令 topic。 |

## 节点 topic 契约（ACT 版）

| 节点 | 角色 | 订阅 topic | 发布 topic |
|---|---|---|---|
| `fisheye_camera_node` | 相机数据发布 | 无 | `/act/observation/image/left_gripper_fisheye`<br>`/act/observation/image/right_gripper_fisheye` |
| `rm65_driver_node` | 状态发布角色 | 无 | `/act/observation/arm/left_tcp_pose`<br>`/act/observation/arm/right_tcp_pose` |
| `elephant_gripper_node` | 状态发布角色 | 无 | `/act/observation/gripper/left_state`<br>`/act/observation/gripper/right_state` |
| `ActVlaDeployNode` | 模型推理 | `/act/observation/image/*`<br>`/act/observation/arm/*`<br>`/act/observation/gripper/*` | `/act/policy_action`<br>`/act/status`<br>`/act/metrics` |
| `command_bridge_sender_node` | 指令适配与发送 | `/act/policy_action`<br>`/act/observation/arm/*`<br>`/act/observation/gripper/*` | `/act/command/arm/left_target`<br>`/act/command/arm/right_target`<br>`/act/command/gripper/left_target`<br>`/act/command/gripper/right_target`<br>`/act/command/status` |
| `rm65_driver_node` | 命令执行角色 | `/act/command/arm/left_target`<br>`/act/command/arm/right_target` | 无 |
| `elephant_gripper_node` | 命令执行角色 | `/act/command/gripper/left_target`<br>`/act/command/gripper/right_target` | 无 |

> [!note] topic 格式
> 各 topic 的 ROS msg 格式、数据特征与 Pi0.5 版完全一致（只 namespace 从 `/pi05/` 改为 `/act/`），详见 [[TO-BE Contract]]#topic 数据特征契约。

## `/act/policy_action` 解析契约

action 为 **16D**，与阶段二数据清洗 action 同构（零转换）：

```text
/act/policy_action
= 16D Float32MultiArray
= left_tcp(x, y, z, qx, qy, qz, qw)[7]   # m + quaternion xyzw 归一化
+ left_gripper_width[1]                   # normalized [0,1]，0=闭合 1=全开
+ right_tcp(x, y, z, qx, qy, qz, qw)[7]
+ right_gripper_width[1]
```

| 维度范围 | 字段 | 单位 | 坐标系 / 值域 | 下游用法 |
|---|---|---|---|---|
| `[0:3]` | `left_tcp_xyz` | `m` | `left_arm_base` | 直接填 `/act/command/arm/left_target.position` |
| `[3:7]` | `left_tcp_quat` | quaternion xyzw 归一化 | `left_arm_base` | 直接填 `/act/command/arm/left_target.orientation` |
| `[7]` | `left_gripper_width` | normalized `[0,1]` | 0=闭合,1=全开 | 映射成 `gripper_angle = width*100`（或按标定），限幅 `[0,100]` |
| `[8:11]` | `right_tcp_xyz` | `m` | `right_arm_base` | 直接填 `/act/command/arm/right_target.position` |
| `[11:15]` | `right_tcp_quat` | quaternion xyzw 归一化 | `right_arm_base` | 直接填 `/act/command/arm/right_target.orientation` |
| `[15]` | `right_gripper_width` | normalized `[0,1]` | 0=闭合,1=全开 | 映射成 `gripper_angle`，限幅后发布 |

## observation.state 段序契约（16D，第一版）

`ActVlaDeployNode` 内部喂给 ACT 的 `observation.state` 为 **16D**，**段序分组排列**（与 action 的交替排列不同）：

| 索引 | segment | dim | 说明 |
|---|---|---|---|
| `[0,7)` | `left_tcp_pose` | 7 | x,y,z,qx,qy,qz,qw；m + quaternion xyzw 归一化；坐标系 `left_arm_base` |
| `[7,14)` | `right_tcp_pose` | 7 | 同上，坐标系 `right_arm_base` |
| `[14,15)` | `left_gripper_width` | 1 | normalized [0,1]，0=闭合 1=全开 |
| `[15,16)` | `right_gripper_width` | 1 | 同上 |

> [!warning] state 段序与 action 段序不同
> - state（喂模型）：分组排列 `left_tcp[7] + right_tcp[7] + left_width[1] + right_width[1]`。
> - action（模型输出）：交替排列 `left_tcp[7] + left_width[1] + right_tcp[7] + right_width[1]`。
> - 这是阶段二 `数据清洗交付说明.md` 的 `STATE_SEGMENT_DEFINITIONS` / `ACTION_SEGMENT_DEFINITIONS` 决定的。部署侧 codec 必须严格遵循，段序错位会导致动作错误。

## ACT 推理节点宏观运行逻辑

`ActVlaDeployNode` 复用 Pi0.5 版的并发调度模型（observation 汇聚 + 异步推理 + chunk 消费），只替换模型加载和 batch 构造部分：

```text
fisheye_camera_node / rm65_driver_node / elephant_gripper_node
  -> ActVlaDeployNode ROS 回调
  -> ObservationCollector（16D state 装配）
  -> ObservationSnapshot
  -> SharedBuffer.latest_observation
  -> ControlLoop 提交 InferenceRequest
  -> InferenceWorker 后台推理线程
  -> ActPolicyRuntime.predict_action_chunk(...)
  -> ActionChunk（[n_action_steps, 16]）
  -> ControlLoop 按 control_hz 选择单步 action
  -> policy action 检查 / fallback / metrics
  -> /act/policy_action + /act/status + /act/metrics
```

## ACT bundle 加载边界

`ActPolicyRuntime` 加载 ACT bundle 时必须（对照《架构边界与机械约束原则》第三节）：

1. 读取 `manifest.json`，校验 `policy_type == "act"`、`state_dim == 16`、`action_dim == 16`。
2. 读取 `normalizers.json`，校验 mean/std 数组长度为 16。
3. 读取 `experiment_config.yaml`，重建 ACTConfig（dim_model、chunk_size、vision_backbone 等）。
4. 加载 `checkpoint/policy.safetensors` 权重。
5. 加载成功后，离线推理输出必须为 `[n_action_steps, 16]` 的 action chunk。

任何校验失败，节点不得发布 policy_action，写入 `/act/status.last_error`。

## 修改边界

`ActVlaDeployNode` 允许修改：
- ACT bundle 加载与推理逻辑（`policy_loader`、`ActPolicyRuntime`）
- observation 装配（16D state codec、batch adapter）
- topic 订阅 / 发布（`/act/*` namespace）
- status / metrics payload

禁止把以下职责移入 `ActVlaDeployNode`：
- 直接发送 RM65 机械臂命令或大象夹爪命令（由 `command_bridge_sender_node` 负责）。
- 把硬件 SDK 错误伪装成已处理。
- 把 topic 适配、ACT 推理和硬件发送揉成一个大节点。

## 与下游硬件栈的解耦

`command_bridge_sender_node` 只依赖 `/act/policy_action` 的 16D 契约，**不依赖** `ActVlaDeployNode` 的内部实现（不读 SharedBuffer、ActionChunk、ControlLoop 状态）。这意味着硬件栈（L2-05）可以在 ACT 推理链路（L2-03/04）就绪前独立开发和 shadow-run 验证，只要 policy_action 的 16D 契约固定。

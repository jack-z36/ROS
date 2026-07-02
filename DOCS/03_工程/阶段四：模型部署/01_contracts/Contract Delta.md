# Contract Delta：AS-IS → TO-BE 契约变更集

> [!info] 产物归属
> - 类型：Contract Delta（阶段四开发工作流 · 阶段三产物）。
> - 目标路径：`DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`。
> - 上游契约：[[AS-IS Contract]]、[[TO-BE Contract]]。
> - 同事源码根：`pi05_test/pi05/`（deploy / common 两个子包为本 Delta 主要影响区）。
> - 本次只做规划与文档产出，不创建代码、不创建 L2 / L3 任务文件。

> [!warning] 真机风险声明
> 本 Delta 集整体替换了下游执行栈（picotele → RM65 + 大象夹爪）与 action 语义（关节空间 → TCP 空间）。凡标记 `真机风险=高` 的 Delta，在进入 real-robot 前，必须先通过 dry-run + fake-policy 验证链路打通；凡涉及硬件发送的改造，必须保留可切回旧 launch 的回滚路径。

## 0. 如何阅读本文档

- §1 是 Delta 总表索引，只看它就能知道有几条变更、是否破坏性、是否真机高风险。
- §2 按「变更对象」分组展开每条 Delta 的完整字段（AS-IS / TO-BE / 影响代码 / 实现方式 / 验收 / 回滚）。
- §3 是跨阶段依赖与尚未确认问题，必须在生成 L2 前回答。
- §4 是给后续 L2 改造工作包划分的输入预告（不在此生成 L2）。

每条 Delta 的字段遵循阶段四工作流约定：编号 / 变更对象 / AS-IS 契约 / TO-BE 契约 / 变更类型 / 影响范围 / 是否兼容 / 实现方式 / 验收方式 / 回滚方式。

## 1. Delta 总表索引

| 编号 | 变更对象 | 一句话差异 | 变更类型 | 是否兼容 | 真机风险 |
|---|---|---|---|---|---|
| D1 | Runtime Topology | 下游栈从 bridge+mux+picotele 替换为 command_bridge_sender_node+RM65+大象夹爪 | 删除+新增 | 破坏性 | 高 |
| D2 | Runtime Entry | launch 入口从 picotele_mux 换成新 RM65 拓扑 launch | 修改+新增 | 需适配 | 中 |
| D3 | External Deps · 相机 | RealSense 三路 → 两路夹爪鱼眼相机（V4L2/rgb8） | 修改 | 破坏性 | 低 |
| D4 | External Deps · 触觉 | 触觉从可选预留 → **第一版预留（state 16D 不含触觉）/ 后续必需（state 32D 含触觉）** | 新增（分阶段） | 需适配 | 低 |
| D5 | External Deps · 机械臂 | picotele 臂（JointState 6D）→ RM65（PoseStamped TCP） | 修改 | 破坏性 | 高 |
| D6 | External Deps · 末端执行器 | 灵巧手 inspire（trigger 0..1，尺度 300..1000）→ 大象夹爪（gripper_angle 0..100） | 修改 | 破坏性 | 高 |
| D7 | Input Contract · topic 命名 | /realsense·/vla_teleop·/inspire·/left_arm → 统一 /pi05/observation/* | 修改 | 破坏性 | 低 |
| D8 | Input Contract · 臂状态语义 | 必需 6D 关节角 + ee pos/rpy → 只用 TCP pose | 修改 | 破坏性 | 中 |
| D9 | Input Contract · encoded_state | 固定 26D → **第一版 16D**（pose+width，无触觉）/ **后续 32D**（加触觉） | 修改 | 破坏性 | 中 |
| D10 | Policy / Model Contract | bundle 必须显式声明新 camera/state/action 语义 | 修改 | 破坏性 | 中 |
| D11 | Action Contract · action 语义 | 关节 14D（AS-IS 同事代码 `arm_cmd_pos`）→ TCP 绝对目标 16D（quaternion + gripper_width，与阶段二数据清洗对齐） | 修改 | 破坏性 | 高 |
| D12 | Action Contract · 发布出口 | 四路 /pi05_vla/command/* → 单路 /pi05/policy_action | 修改 | 破坏性 | 低 |
| D13 | Safety Contract | SafetyGuard 关节空间检查 → policy-action 通用检查 + 硬件检查下移 | 修改+新增 | 需适配 | 高 |
| D14 | Output / Command | 新增 command_bridge_sender_node 作为 policy action→硬件指令边界 | 新增 | 需适配 | 高 |
| D15 | Output · arm msg 类型 | JointState(6D) → PoseStamped(quaternion，action 本身即 quaternion，bridge 无需转换) | 修改 | 破坏性 | 高 |
| D16 | Output · gripper msg 语义 | Float64 trigger(0..1, AS-IS) → width[0,1](policy_action,同数据清洗) → angle[0,100](大象夹爪) | 修改 | 破坏性 | 高 |
| D17 | Observability | /pi05_vla/{status,metrics} → /pi05/{status,metrics} + 新增 /pi05/command/status | 修改+新增 | 需适配 | 低 |
| D18 | Runtime Mode | 发布边界与 enable/急停 gate 从 deploy 节点下移到 bridge | 修改 | 需适配 | 中 |
| D19 | Failure Semantics | 硬件发送失败集中到 /pi05/command/status，不伪装成功 | 新增 | 需适配 | 高 |

> [!note] 聚类观察
> 19 条 Delta 不是 19 个独立改动。它们围绕 **三个核心设计决策** 聚集：
> 1. **observation 语义重定义**（D3/D4/D7/D8/D9/D10）：把"相机+关节角+手部尺度"换成"鱼眼+触觉+TCP+夹爪角度"。
> 2. **action 语义从关节空间迁移到 TCP 绝对目标**（D11/D12/D15/D16）：14D 关节命令 → 16D TCP 绝对目标（quaternion + gripper_width，与数据清洗同构），发布出口收敛。
> 3. **硬件执行与安全职责下移到新边界 command_bridge_sender_node**（D1/D5/D6/D13/D14/D18/D19）。
> 这三个聚类将直接决定后续 L2 改造工作包的边界，不要按运行时序机械切分。

## 2. Delta 分组详情

### 2.1 拓扑与运行入口（Runtime Topology / Entry）

#### D1 · 下游节点拓扑整体替换

| 字段 | 内容 |
|---|---|
| 变更对象 | Runtime Topology |
| AS-IS 契约 | `Pi05VlaDeployNode` → `Pi05BridgeNode`（topic 适配）→ `CommandMuxNode`（teleop/VLA 仲裁）→ `picotele_planner_node` / `picotele_arm_node` / `picotele_hand_node`（执行）。三节点异步通过 `/vla/*`、`/mux/*` 串联。 |
| TO-BE 契约 | `Pi05VlaDeployNode` → `command_bridge_sender_node`（适配+安全+发送）→ `rm65_driver_node` / `elephant_gripper_node`（执行）。删除 bridge、mux、picotele_planner；teleop/XR 仲裁路径不再属于本阶段范围。 |
| 变更类型 | 删除 + 新增 |
| 影响范围 | `deploy/launch/pi05_picotele_mux.launch.py`；下游全部 ROS2 package（picotele 系列）。Pi05 仓库内：`pi05_bridge_node.py`、`command_mux_node.py` 停用。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | 不删除旧节点源码；新增 `command_bridge_sender_node`；用新 launch 切换拓扑，旧 launch 保留作为回滚。 |
| 验收方式 | dry-run 启动新 launch，确认节点图与 TO-BE 拓扑一致；fake-policy 下 `/pi05/policy_action` → `/pi05/command/*` 链路贯通。 |
| 回滚方式 | 切回 `pi05_picotele_mux.launch.py`。 |

#### D2 · launch 入口替换

| 字段 | 内容 |
|---|---|
| 变更对象 | Runtime Entry |
| AS-IS 契约 | `ros2 launch deploy/launch/pi05_picotele_mux.launch.py`，读 `deploy/config/deploy.yaml`。 |
| TO-BE 契约 | 新 launch（命名待定，候选 `pi05_rm65_deploy.launch.py`），拉起 fisheye/tactile/RM65/gripper 状态发布节点 + `Pi05VlaDeployNode` + `command_bridge_sender_node` + RM65/gripper 执行节点。配置仍走 `deploy.yaml` 但 schema 扩展。 |
| 变更类型 | 修改 + 新增 |
| 影响范围 | `deploy/launch/`；`deploy/config/deploy.yaml`；`config/schema.py`。 |
| 是否兼容 | 需适配（旧 launch 保留） |
| 实现方式 | 新增 launch 文件；config schema 加新 observation topic 字段，保留旧字段读取能力以便回滚。 |
| 验收方式 | dry-run 启动新 launch 不报错；`ros2 node list` 与 TO-BE 节点表一致。 |
| 回滚方式 | 旧 launch + 旧 config 不删除。 |

### 2.2 外部硬件依赖（External Dependencies）

#### D3 · 相机硬件替换（RealSense → 工业鱼眼相机）

| 字段 | 内容 |
|---|---|
| 变更对象 | External Deps · 相机 |
| AS-IS 契约 | RealSense 三路：`top` / `left_wrist` / `right_wrist`；`sensor_msgs/Image` 或 `CompressedImage`；`image.transport: raw`；由 external launch `realsense_triple_compressed.launch.py` 发布。required image keys 来自 bundle manifest。 |
| TO-BE 契约 | 两路夹爪末端鱼眼相机：`left_gripper_fisheye` / `right_gripper_fisheye`；`sensor_msgs/Image` `encoding=rgb8`；优先复用阶段一 `gopro_camera_launch` + `v4l2_camera_node`，默认 `YUYV→rgb8`，必要时 `MJPG→rgb8`。 |
| 变更类型 | 修改 |
| 影响范围 | `_image_topic_map()`、required image keys、bundle manifest camera names、`_build_batch()` image key、`fisheye_camera_node`（新外部节点）。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | config schema 扩展 image topic map；adapter 包装图像回调，不改 `ObservationCollector` 核心；新 bundle manifest 声明新 camera names。 |
| 验收方式 | dry-run 下 `required_image_keys` 与两路鱼眼 topic 对齐；fake-policy 下 snapshot 不报 missing image。 |
| 回滚方式 | config 切回 realsense topic + 旧 bundle。 |

#### D4 · 触觉传感器引入（可选 → 第一版预留 / 后续必需）

| 字段 | 内容 |
|---|---|
| 变更对象 | External Deps · 触觉 |
| AS-IS 契约 | 触觉仅预留可选字段 `left_tactile_image` / `right_tactile_image`；主链路不强依赖；`picotele_tactile_node` 存在但非必需。 |
| TO-BE 契约 | **分两版**（见 Q6）：**第一版 batch 不含触觉**（state=16D，不订阅触觉 topic，`tactile_sensor_node` 可存在但不接入 Pi05 节点）；**后续版本**必需四片华威科触觉芯片 `l1`/`l2`/`r1`/`r2`（state=32D），`std_msgs/Float32MultiArray`，`layout.dim[0].label=rows`、`dim[1].label=cols`、`data` 行优先展平。 |
| 变更类型 | 新增（分阶段） |
| 影响范围 | topic schema、tactile callback、`update_tactile()`、`ObservationSnapshot` 字段、batch adapter、bundle manifest、`tactile_sensor_node`（新外部节点）。 |
| 是否兼容 | 需适配 |
| 实现方式 | **第一版代码必须预留触觉段落位置**：collector / state codec / batch adapter 用 config 开关控制触觉段落 enable/disable（与数据清洗 `state_segments.enabled` 对齐）。第一版 disabled（state=16D），后续 enabled（state=32D），不必重写 batch 装配逻辑。tactile 编码集中在 codec 边界，不散落 ROS 回调。 |
| 验收方式 | 第一版：dry-run 下不订阅触觉、snapshot 不依赖触觉即可生成；后续版本：四片触觉齐全才生成 snapshot，缺任一片节流记录 missing。 |
| 回滚方式 | 配置开关将触觉段落 disabled，回到 16D。 | |

#### D5 · 机械臂硬件替换（picotele → RM65）

| 字段 | 内容 |
|---|---|
| 变更对象 | External Deps · 机械臂 |
| AS-IS 契约 | `picotele_arm_node` 消费 `/mux/*` `sensor_msgs/JointState`（`name=ARM_JOINT_NAMES`、`position=6D` 关节目标）；状态由 picotele 内部发布。 |
| TO-BE 契约 | `rm65_driver_node` 消费 `geometry_msgs/PoseStamped` TCP 目标（quaternion）；状态发布角色把睿尔曼 `/rm_driver/udp_joint_pose_euler` 或状态 API 转成 `/pi05/observation/arm/*_tcp_pose`（`PoseStamped`，`frame_id=left_arm_base/right_arm_base`，单位 m）。 |
| 变更类型 | 修改 |
| 影响范围 | command topic 类型、状态发布 topic、`rm65_driver_node`（新外部节点，状态+执行双角色）。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | command 侧改动主要落在 `command_bridge_sender_node`（D14）；Pi05 节点侧只消费 TCP pose 状态（D8）。 |
| 验收方式 | fake-policy 下 `/pi05/command/arm/*_target` 为合法 PoseStamped；真机 smoke test 前必须 dry-run。 |
| 回滚方式 | 切回 picotele launch；RM65 状态/命令节点可独立禁用。 |

#### D6 · 末端执行器替换（灵巧手 inspire → 大象夹爪）

| 字段 | 内容 |
|---|---|
| 变更对象 | External Deps · 末端执行器 |
| AS-IS 契约 | `picotele_hand_node` 消费 `Float64` trigger（0..1，由 bridge 从数据集手部尺度转换）；状态 `/inspire/*/joint_states` 取 `position[0]`；SafetyGuard 手部范围 `hand_min=300` / `hand_max=1000`（数据集尺度）。 |
| TO-BE 契约 | `elephant_gripper_node` 消费 `Float64` `gripper_angle`（文档值域 0..100，不沿用 300..800/1000）；状态 `/pi05/observation/gripper/*_state` = `Float32` `gripper_angle`；依据大象夹爪 modbus/pymycobot 文档。 |
| 变更类型 | 修改 |
| 影响范围 | hand/gripper topic、state/action codec、safety range、action 字段含义、`elephant_gripper_node`（新外部节点，状态+执行双角色）。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | codec 边界重写 gripper 语义；safety range 改为 0..100；不复用 inspire 手部尺度转换。 |
| 验收方式 | dry-run 下 gripper 字段值域落在 0..100；真机前 fake-policy 验证限幅。 |
| 回滚方式 | config 切回 inspire 手部尺度 + 旧 bundle。 |

### 2.3 输入契约（Observation / Input Contract）

#### D7 · Observation topic 命名空间整体迁移

| 字段 | 内容 |
|---|---|
| 变更对象 | Input Contract · topic 命名 |
| AS-IS 契约 | `/realsense/*`、`/vla_teleop/proprioception`、`/inspire/*/joint_states`、`/left_arm/ee_position`、`/left_arm/ee_rpy`、`/right_arm/*`。 |
| TO-BE 契约 | 统一 `/pi05/observation/{image,tactile,arm,gripper}/*`，见 TO-BE topic 总表。 |
| 变更类型 | 修改 |
| 影响范围 | `config/schema.py` topics 字段、`deploy.yaml`、`pi05_vla_deploy_node.py` 订阅创建。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | config 驱动订阅创建；topic 名全部走 schema，不在代码硬编码。 |
| 验收方式 | dry-run 下订阅列表与 TO-BE topic 表逐项对齐。 |
| 回滚方式 | config 切回旧 topic 名。 |

#### D8 · 机械臂状态语义从关节角改为 TCP pose

| 字段 | 内容 |
|---|---|
| 变更对象 | Input Contract · 臂状态语义 |
| AS-IS 契约 | 必需 `left_arm_q` / `right_arm_q`（6D 关节角，按 `proprioception_order` 解码），外加 `left_ee_pos` / `left_ee_rpy` / `right_ee_pos` / `right_ee_rpy`。 |
| TO-BE 契约 | **只使用左右 RM65 末端 TCP pose** 作为 policy observation 必需字段；关节角不再作为 policy 输入必需项（可作 IK/安全兜底，但由下游 `command_bridge_sender_node` 自行获取，不反向引入 Pi05 节点）。 |
| 变更类型 | 修改 |
| 影响范围 | `ObservationCollector._required_value_keys()`、TCP pose callback、state codec、`ObservationSnapshot`、`Pi05PolicyRuntime._build_batch()`。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | collector 必需字段集替换；增加 `update_tcp_pose(...)`；snapshot 完整性门控基于新字段集。 |
| 验收方式 | dry-run 下缺 TCP pose 不生成 snapshot；关节角缺失不阻塞 snapshot。 |
| 回滚方式 | 配置开关恢复关节角为必需（仅当仍用旧 bundle 时）。 |

> [!warning] 跨阶段依赖
> D8 改变了 policy 输入语义，必须与训练侧（新 bundle manifest）同步，否则模型输入与运行时输入错位。见 §3-Q1。

#### D9 · encoded_state 维度重新定义（不再默认 26D）

| 字段 | 内容 |
|---|---|
| 变更对象 | Input Contract · encoded_state |
| AS-IS 契约 | 固定 26D = `[left_arm_q6, right_arm_q6, left_hand_q1, right_hand_q1, left_ee_pos3, left_ee_rpy3, right_ee_pos3, right_ee_rpy3]`；`state_normalizer` 按此维度。 |
| TO-BE 契约 | 重新定义为基于 TCP pose + gripper state + 触觉的新语义；维度由新 bundle manifest 决定，**不能默认继续叫 26D** 或静默复用旧排列。 |
| 变更类型 | 修改 |
| 影响范围 | `pi05/common/data/state_codec.py`、normalizer 维度、bundle manifest、`_build_batch()`。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | 新 state codec；normalizer 与新 bundle 的 `normalizers.json` 维度对齐。 |
| 验收方式 | fake-policy 下 encoded_state 维度与 bundle 期望一致；shape mismatch 立即报错而非静默。 |
| 回滚方式 | 切回旧 26D codec + 旧 bundle。 |

### 2.4 Policy / Model Contract

#### D10 · deploy bundle 语义对齐（新模型输入契约）

| 字段 | 内容 |
|---|---|
| 变更对象 | Policy / Model Contract |
| AS-IS 契约 | bundle manifest 声明 realsense camera names、26D state、14D joint action；`experiment_config.yaml` 重建 Pi0.5+LoRA；`adapter_model.safetensors` 注入 LoRA；`normalizers.json` 提供 state/action 归一化。 |
| TO-BE 契约 | 新 bundle 必须显式声明鱼眼 camera names、新 state schema（TCP+gripper+tactile）、14D TCP action 语义；不能静默复用旧 26D state 或旧 joint action 语义。 |
| 变更类型 | 修改 |
| 影响范围 | `manifest.json`、`experiment_config.yaml`、`normalizers.json`、adapter weights；`policy_loader.py` 的 bundle 加载与 manifest 解释逻辑。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | 训练侧产出新 bundle；deploy 侧 `policy_loader` 对 manifest 字段做显式校验（缺失/不匹配时报错）。 |
| 验收方式 | 新 bundle 加载后 `policy_image_names`、state dim、action dim 与 TO-BE 契约一致；离线推理输出 14D TCP 语义。 |
| 回滚方式 | 旧 bundle 保留可加载（需同时回滚 D3/D8/D9/D11）。 |

> [!warning] 跨阶段依赖（训练侧）
> D10 依赖阶段二/训练侧产出新 bundle。deploy 侧只能消费，不能改 bundle 内容。新 bundle 未就绪前，deploy 侧只能用旧 bundle + dry-run 验证链路（此时模型输出语义仍是旧的，不能接真机）。见 §3-Q1/Q2。

### 2.5 Action Contract

#### D11 · policy action 语义从关节 14D 改为 TCP 绝对目标 16D

| 字段 | 内容 |
|---|---|
| 变更对象 | Action Contract · action 语义 |
| AS-IS 契约 | 14D = `[left_arm_joint6, right_arm_joint6, left_hand, right_hand]`；**关节空间绝对命令**（`arm_cmd_pos`，遥操作时实际发送的关节目标）；`action_normalizer.unnormalize(...)` 还原到关节空间；SafetyGuard 按关节 delta 限幅。源码依据：同事 `mcap_to_lerobot_v3.py:16,316-321,580-584`。 |
| TO-BE 契约 | **16D 绝对 TCP 目标**（与阶段二数据清洗交付完全同构，零转换）：`[left_tcp_xyz_q(7) + left_gripper_width(1) + right_tcp_xyz_q(7) + right_gripper_width(1)]`。语义 `action_t = target at step t+1`。pose 用 **quaternion xyzw**（7D，非 rpy）；position 单位 `m`；坐标系左 `left_arm_base` / 右 `right_arm_base`；夹爪用 **gripper_width normalized [0,1]**（0=闭合,1=全开，非大象夹爪 angle 0..100）；段序「左pose+左夹爪 → 右pose+右夹爪」交替（与 state 的「全左→全右」分组不同）。语义依据：阶段二 `数据清洗交付说明.md:21-36,253`。 |
| 变更类型 | 修改 |
| 影响范围 | `action_spec.py`、`action_codec.py`、`SafetyGuard`、`ControlLoop` action 命名、`/pi05/policy_action` publisher、`command_bridge_sender_node` 解析逻辑。**与 TO-BE Contract 草稿（14D/rpy/angle）冲突，需同步修正 TO-BE Contract。** |
| 是否兼容 | 破坏性修改 |
| 实现方式 | action codec 重写：拆 16D 段序（左pose7→左width1→右pose7→右width1）；SafetyGuard 改 TCP 步长/姿态检查（见 D13）；publisher 按 Float32MultiArray 16D 发布。**action 是绝对目标，bridge 直接转发，不需要「当前 pose + delta」重组**——绝对目标自包含。夹爪 width[0,1]→大象夹爪 angle[0,100] 的线性映射在 bridge 内做（见 D16）。 |
| 验收方式 | fake-policy 下 `/pi05/policy_action` 16D 顺序与数据清洗 `action_observation_schema.md` 逐字段对齐；bundle feature contract 的 action_dim=16。 |
| 回滚方式 | 切回旧 action codec + 旧 bundle。 |

> [!note] Q3 已全部确认（原为未决问题）
> action 语义已完全坐实，**不再是未决问题**：
> - **语义**：绝对目标 `action_t = target at step t+1`（与阶段二数据清洗一致）。
> - **维度**：**16D**（不是 14D）；pose 用 **quaternion 7D**（不是 rpy 6D）；夹爪用 **width [0,1]**（不是 angle 0..100）。
> - **段序**：左pose7+左width1 → 右pose7+右width1（交替，与 state 分组不同）。
> - **不是 UMI 相对轨迹**：UMI 用相对（chunk[t] 相对推理时刻 TCP pose，需 `convert_abs2rel`+部署时重组），你们选用绝对，部署零重组。
> - **不需要重组**：绝对目标自包含，bridge 直接转发。
> - **deploy 仍需读 TCP pose**：但这是作为 **observation 输入**（模型需要当前状态），不是为 action 重组。
> - **夹爪固定进 action**：固定 16D，不动态解析。
>
> 来源：阶段二 `数据清洗交付说明.md`（权威）、UMi 论文 PD2.1/Fig.6（印证你们未走相对路线）。

#### D12 · policy action 输出从四路 command 收敛为单路

| 字段 | 内容 |
|---|---|
| 变更对象 | Action Contract · 发布出口 |
| AS-IS 契约 | `Pi05VlaDeployNode` 发布四路：`/pi05_vla/command/left_arm/joint_target`、`/right_arm/joint_target`（`JointState`）、`/left_hand/target`、`/right_hand/target`（`Float64`）。 |
| TO-BE 契约 | 只发布单路 `/pi05/policy_action`（`Float32MultiArray` 14D）+ `/pi05/status` + `/pi05/metrics`。 |
| 变更类型 | 修改 |
| 影响范围 | `pi05_vla_deploy_node.py` publisher 创建、`_control_tick()` 发布逻辑。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | 移除/停用 `left_arm_pub` / `right_arm_pub` / `left_hand_pub` / `right_hand_pub`；新增 `policy_action_pub`。`ControlLoop` / `InferenceWorker` / `SharedBuffer` 核心调度不改。 |
| 验收方式 | dry-run 下 `/pi05/policy_action` 单路发布，旧四路 topic 无输出。 |
| 回滚方式 | 恢复四路 publisher 创建代码。 |

### 2.6 安全契约（Safety Contract）

#### D13 · SafetyGuard 职责切分（policy-action 层 vs 硬件层）

| 字段 | 内容 |
|---|---|
| 变更对象 | Safety Check |
| AS-IS 契约 | `SafetyGuard` 在 `Pi05VlaDeployNode` 内做关节空间检查：`max_joint_delta_rad`、joint limits、`hand_min=300` / `hand_max=1000`；anchor 优先用上一帧 `BimanualAction`。 |
| TO-BE 契约 | `Pi05VlaDeployNode` 内 SafetyGuard **只保留 policy-action 通用检查**：action shape、NaN/Inf、chunk 时效、单步变化约束。硬件相关检查（RM65 workspace、IK/可执行性、SDK 返回码、gripper 0..100 限幅、急停/deadman/enable gate）**下移到 `command_bridge_sender_node`**。 |
| 变更类型 | 修改 + 新增 |
| 影响范围 | `safety_guard.py`、`SafetyConfig`、`command_bridge_sender_node`（新安全检查实现）、metrics rejected reason。 |
| 是否兼容 | 需适配（policy 层简化，硬件层新建） |
| 实现方式 | SafetyGuard 参数化，关节空间检查可配置关闭；硬件检查在 bridge 内独立实现，不共享 SafetyGuard 类。 |
| 验收方式 | dry-run 下 policy 层 NaN/Inf/shape 检查仍生效；fake-policy 下 bridge 的 workspace/IK/gripper 限幅检查可独立触发拒绝。 |
| 回滚方式 | SafetyGuard 恢复关节检查配置；bridge 安全检查通过开关禁用（仅 fake-policy 阶段）。 |

### 2.7 输出与指令契约（Output / Command Contract）

#### D14 · 新增 command_bridge_sender_node（policy action → 硬件指令边界）

| 字段 | 内容 |
|---|---|
| 变更对象 | Output / Command |
| AS-IS 契约 | 无此节点。Pi05 节点直接发布硬件候选命令，`Pi05BridgeNode` 做 topic 适配+trigger 转换，`CommandMuxNode` 做仲裁。 |
| TO-BE 契约 | 新增 `command_bridge_sender_node`：订阅 `/pi05/policy_action` + 左右 TCP pose + 左右 gripper state + 急停/enable/deadman；输出 `/pi05/command/arm/{left,right}_target`（`PoseStamped`）+ `/pi05/command/gripper/{left,right}_target`（`Float64`）+ `/pi05/command/status`（`String` JSON）。承担 D13 下移的硬件安全检查。 |
| 变更类型 | 新增 |
| 影响范围 | 全新节点（新文件）。 |
| 是否兼容 | 需适配（新节点接入，旧 bridge/mux 停用） |
| 实现方式 | 新建独立 ROS2 节点；不读取 Pi05 节点内部 `SharedBuffer` / `ActionChunk` / `ControlLoop` 状态，只消费 `/pi05/policy_action`。 |
| 验收方式 | fake-policy 下 14D → PoseStamped+Float64 转换正确；安全检查失败时不发送并写 `/pi05/command/status`。 |
| 回滚方式 | 节点不启动即等于回滚（Pi05 节点仍可独立 dry-run）。 |

#### D15 · arm command 消息类型（JointState → PoseStamped）

| 字段 | 内容 |
|---|---|
| 变更对象 | Output · arm msg 类型 |
| AS-IS 契约 | `sensor_msgs/JointState`（`name=ARM_JOINT_NAMES`、`position=6D` 关节目标）。 |
| TO-BE 契约 | `geometry_msgs/PoseStamped`（`frame_id=left_arm_base/right_arm_base`、`position` 单位 m、`orientation` quaternion xyzw）。**action 本身就是 quaternion**（来自数据清洗 16D，非 rpy），bridge 无需姿态转换，直接把 16D 里的 [x,y,z,qx,qy,qz,qw] 装进 PoseStamped。 |
| 变更类型 | 修改 |
| 影响范围 | `command_bridge_sender_node` 发布器、`rm65_driver_node` 订阅器。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | bridge 直接从 16D action 取段 [0:7]（左）/[8:15]（右）填入 PoseStamped；坐标系显式标注 frame_id；**无 rpy→quaternion 转换**（避免万向锁）。 |
| 验收方式 | fake-policy 下 PoseStamped 字段完整；真机前 dry-run。 |
| 回滚方式 | bridge 不启动。 |

#### D16 · gripper command 语义（trigger → width[0,1] → angle[0,100]）

| 字段 | 内容 |
|---|---|
| 变更对象 | Output · gripper msg 语义 |
| AS-IS 契约 | `std_msgs/Float64` trigger（0..1，由 bridge 从数据集手部尺度 300..1000 转换而来）。 |
| TO-BE 契约 | `/pi05/policy_action` 里的夹爪是 **gripper_width normalized [0,1]**（0=闭合,1=全开，与阶段二数据清洗 `数据清洗交付说明.md:17-18,26` 同构）。bridge 把 width 线性映射为 `gripper_angle [0..100]`（大象夹爪文档值域）后，发布 `std_msgs/Float64` 给 `elephant_gripper_node`。 |
| 变更类型 | 修改 |
| 影响范围 | `command_bridge_sender_node` 发布器、`elephant_gripper_node` 订阅器、gripper action codec。 |
| 是否兼容 | 破坏性修改 |
| 实现方式 | bridge 内做 **width→angle 线性映射**（`angle = width * 100`，或按硬件标定的非零偏移/斜率）；映射后限幅 0..100（strict mode 下越界拒绝）；不经过旧 trigger 转换。映射系数必须与硬件实物标定一致（开/合两端实测角度）。 |
| 验收方式 | fake-policy 下 width=0 → angle=0（全合），width=1 → angle=100（全开）；中间值线性。 |
| 回滚方式 | bridge 不启动。 |

> [!warning] width→angle 映射系数需硬件标定
> 数据清洗的 width 是归一化 [0,1]（语义 0=闭合,1=全开）。大象夹爪 angle 是寄存器值 [0,100]。理论上线性 `angle=width*100`，但**闭合点/全开点的真实寄存器值需用大象夹爪实测标定**（modbus/pymycobot 文档值域 0..100 是名义值，实物可能有零点偏移）。标定前不要接真机。

### 2.8 可观测性与失败语义（Observability / Failure Semantics）

#### D17 · status / metrics topic 迁移与字段扩展

| 字段 | 内容 |
|---|---|
| 变更对象 | Observability |
| AS-IS 契约 | `/pi05_vla/status`（mode+metrics 文本）、`/pi05_vla/metrics`（JSON：inference/latency/chunk/safety/published 计数）。 |
| TO-BE 契约 | `/pi05/status`、`/pi05/metrics`（保留原计数，新增 `observation_ready`、`policy_ready`、缺失字段诊断、最近 policy action 发布时间）；新增 `/pi05/command/status`（bridge 发送结果）。 |
| 变更类型 | 修改 + 新增 |
| 影响范围 | `shared_buffer.py` metrics、`pi05_vla_deploy_node.py` status/metrics publisher、`command_bridge_sender_node`。 |
| 是否兼容 | 需适配 |
| 实现方式 | topic 名走 config；metrics payload 扩展字段；不删除原计数。 |
| 验收方式 | dry-run 下 `/pi05/metrics` 含新字段；`/pi05/command/status` 在 bridge 发送后更新。 |
| 回滚方式 | topic 名切回 /pi05_vla/*。 |

#### D18 · Runtime Mode 与发布/使能边界调整

| 字段 | 内容 |
|---|---|
| 变更对象 | Runtime Mode |
| AS-IS 契约 | `runtime.mode = dry-run / shadow-run / safe-run`；shadow-run/safe-run 发布 `/pi05_vla/command/*`；enable/仲裁在 `CommandMuxNode`（shadow=mux 旁路，safe=mux 放行）。 |
| TO-BE 契约 | **保留三档语义**，但 shadow/safe 的真机使能不再依赖 mux，改由 `command_bridge_sender_node` 的 gate（enable/急停/deadman）控制：dry-run = Pi05 不发 policy_action；shadow-run = Pi05 发 policy_action + bridge gate 关（机械臂不动，但 `/pi05/command/status` 可见链路状态）；safe-run = Pi05 发 + bridge gate 开（机械臂动）。bridge 的急停/deadman 物理开关在 safe-run 下仍可随时切断（与 mode 解耦）。 |
| 变更类型 | 修改 |
| 影响范围 | `_control_tick()` 发布逻辑、`command_bridge_sender_node` gate（按 mode + 物理开关共同决策）、`runtime.mode` 语义文档、config schema（mode 仍为三值枚举）。 |
| 是否兼容 | 需适配 |
| 实现方式 | Pi05 节点：mode ∈ {shadow-run, safe-run} 时发 policy_action，dry-run 不发。bridge：gate 默认按 mode 决策（shadow=关，safe=开），叠加急停/deadman/enable 物理输入做与运算。**不简化为两档**（shadow 作为独立 mode 保留，调试时是明确的安全档）。 |
| 验收方式 | dry-run 无 policy_action；shadow-run 有 policy_action 但 `/pi05/command/status.sent_to_driver=false`；safe-run `sent_to_driver=true` 且急停可即时停止。 |
| 回滚方式 | 恢复 mux 旁路/放行逻辑（需同时恢复 CommandMuxNode + 四路 command publisher）。 |

> [!question] 待确认
> `runtime.mode` 在 TO-BE 下是否仍保留 shadow-run/safe-run 区分？还是收敛为 dry-run/real 两档？见 §3-Q4。

#### D19 · 硬件发送失败语义集中

| 字段 | 内容 |
|---|---|
| 变更对象 | Failure Semantics |
| AS-IS 契约 | `Pi05VlaDeployNode` 不能确认硬件执行；失败语义停留在 chunk/safety 层（discarded_chunk、rejected_action、fallback）；硬件层失败不回传 Pi05 节点。 |
| TO-BE 契约 | `command_bridge_sender_node` 在发送前/后记录 `action_id`、`safety_ok`、`sent_to_driver`、`failure_reason`；硬件超时/SDK 错误写入 `/pi05/command/status`，**不把失败伪装成成功**。 |
| 变更类型 | 新增 |
| 影响范围 | `command_bridge_sender_node`、`/pi05/command/status`、可选的 `rm65_driver_node` / `elephant_gripper_node` 执行结果 topic。 |
| 是否兼容 | 需适配 |
| 实现方式 | bridge 维护 action_id 单调计数；每次发送写 status；SDK 错误码透传。 |
| 验收方式 | fake-policy 下构造 IK 失败/越界场景，`/pi05/command/status.failure_reason` 正确记录且不发硬件命令。 |
| 回滚方式 | bridge 不启动则无该 status topic。 |

## 3. 跨阶段依赖与尚未确认问题

> [!danger] 生成 L2 前必须回答
> 以下问题会直接改变 L2 改造工作包的边界与依赖方向，不能在 L3 阶段才暴露。

### Q1 · 新 bundle 何时就绪（跨阶段依赖）— ✅ 已确认

**结论**：新 bundle 预计**两天后**就绪。

依赖关系：
- D3/D4/D8/D9/D10/D11 全部依赖新 bundle（新 camera names、32D state schema、16D TCP action 语义）。
- 新 bundle 未就绪前，deploy 侧**无法运行验证**（模型输出语义不匹配，强行接真机会错动作）。
- 交付物清单仍需训练侧确认：bundle 是否含 manifest 声明 action_dim=16 / state_dim=32 / camera names；`normalizers.json` 维度是否对齐。

**这两天 deploy 侧的策略（见 Q2）**：等真模型一起联调，不做 fake-policy。

### Q2 · 旧 bundle 是否能驱动新 observation 适配层 — ✅ 已确认

**结论**：**不做 fake-policy，不做旧 bundle 适配层，等真模型一起联调。**

理由（用户决策）：两天周期短，写一次性 fake-policy stub 不划算。

**影响与约束**：
- 这两天：deploy 代码（topic 接线、observation 装配、bridge、16D/32D codec）可以写，但**无法运行验证**，只能人工 review。
- **联调期风险**：代码 bug 会集中在真 bundle 到手后爆发，调试压力大。这是接受的代价。
- **联调强制阶梯**（因无 fake-policy 提前验证，必须严格按序，不能跳步）：
  1. **dry-run**：先看模型输出 16D 是否合理（维度、值域、quaternion 归一化）。
  2. **shadow-run**：看链路 + 安全检查全过，`/pi05/command/status` 显示 `safety_ok=true, sent_to_driver=false`。
  3. 确认无误后 **safe-run** 上真机。
- D8/D9 没有独立的提前验收路径（旧 bundle 语义不匹配，不做适配层）。

### Q3 · action 语义（D11）— ✅ 已确认

**结论**：action = **16D 绝对 TCP 目标**（`action_t = target at step t+1`），与阶段二数据清洗交付完全同构。
- 维度 16D（不是 14D）：pose 用 quaternion 7D（不是 rpy 6D），夹爪用 width [0,1]（不是 angle 0..100）。
- 段序：左pose7+左width1 → 右pose7+右width1（交替）。
- 绝对目标，无需 deploy 侧重组；bridge 直接转发。
- **不采用 UMI 相对轨迹**（虽然调研过 UMI，但阶段二数据清洗明确选了绝对，见 `数据清洗交付说明.md:33`「差分/相对化属于训练侧策略，不在阶段二改写」）。

**仍需确认的连带项**：
- D16：夹爪 width[0,1] → 大象夹爪 angle[0,100] 的线性映射在 bridge 实现，映射系数需与硬件标定一致。
- TO-BE Contract 草稿（14D/rpy/angle）需同步修正为 16D/quaternion/width。

详见 D11 与下方 D16 更新。

### Q4 · runtime.mode 在 TO-BE 下的档位（D18）— ✅ 已确认

**结论**：**保留三档**（dry-run / shadow-run / safe-run）。影子运行作为 mode 级别的一等公民保留，调试时多一个明确的安全档。TO-BE 下三档语义重新定义（不再依赖已删除的 mux）：

| 档位 | Pi05 发 policy_action？ | bridge gate | 机械臂 | 用途 |
|---|---|---|---|---|
| `dry-run` | 否（只打印日志） | — | 不动 | 纯跑模型，啥也没接，看输出对不对 |
| `shadow-run` | 是 | **关闭** | 不动 | 接了硬件，看整条链路通不通（`/pi05/command/status` 可见 `safety_ok=true, sent_to_driver=false`），但不动真机 |
| `safe-run` | 是 | **打开** | 动 | 控制真机 |

**与 AS-IS 的区别**：AS-IS 的 shadow/safe 依赖 mux 旁路/放行；TO-BE 删了 mux，改由 `command_bridge_sender_node` 的 gate（enable/急停/deadman）控制。mode 决定「Pi05 发不发 + bridge gate 开不开」的组合；bridge gate 仍保留独立的急停/deadman 物理开关（mode=safe-run 时急停仍能随时切断）。

**验收用例**（D18）：
- dry-run：`/pi05/policy_action` 无输出，日志有 action 打印。
- shadow-run：`/pi05/policy_action` 有输出，`/pi05/command/status` 显示 `sent_to_driver=false`，机械臂不动。
- safe-run：`/pi05/command/status` 显示 `sent_to_driver=true`，机械臂按 action 运动；急停触发时立即停止。

### Q5 · `command_bridge_sender_node` 的 IK/workspace 检查归属（D13/D15）— ✅ 已确认

**结论**：**发送前预检**。`command_bridge_sender_node` 在发 `movep_canfd` 之前，先用 `rm_inverse_kinematics` 接口预检 TCP 目标是否可解（不执行，只查 `flag=0` 四元数模式）。可解才发；不可解则拒绝，写入 `/pi05/command/status.failure_reason`，**不让坏命令到达控制器**。

依据：RM65 提供 `rm_inverse_kinematics_params_t`（`rm_inverse_kinematics_params_t.md`），`q_pose` + `flag`（0=四元数,1=欧拉角）即可查询可解性，不需真机运动。预检代价是每动作多一次 RPC 往返（ms 级，对 VLA 5-15Hz 影响可忽略），换来坏命令零到达控制器的安全保障。

**bridge 完整检查顺序**（发送前）：
1. action 维度 = 16D
2. 全部 finite（NaN/Inf）
3. quaternion 归一化
4. workspace 几何检查（TCP 位置在臂可达球/盒内）
5. **rm_inverse_kinematics 预检（可解性）**
6. gripper_width ∈ [0,1]，映射 angle ∈ [0,100]
7. enable / 急停 / deadman gate
→ 全通过后才发 movep_canfd + gripper 命令。

### Q6 · 触觉数据是否进入 policy 输入（D4 vs D9）— ✅ 已确认（分两版）

**结论**：触觉进入 `observation.state`，**不在 action**。但**第一版 batch 不含触觉，后续版本再加**。

> [!warning] 触觉分两版交付（重要）
> - **第一版（首发）**：batch 不含触觉。state = **16D**（pose 14 + width 2），不订阅触觉 topic，bundle 用 16D 训练。
> - **后续版本**：加入触觉。state = **32D**（pose 14 + width 2 + 触觉 16），订阅 4 路触觉 topic，重新训练 32D bundle。
> - **代码结构要求**：第一版的 state codec / observation collector 必须预留触觉段落的位置（可配置开关），后续加触觉时改动最小，不必重写 batch 装配逻辑。

#### 第一版 observation.state = 16D（无触觉）

| 索引 | segment | dim |
|---|---|---|
| [0,7) | `left_tcp_pose` | 7 (quaternion xyzw + m) |
| [7,14) | `right_tcp_pose` | 7 |
| [14,15) | `left_gripper_width` | 1 ([0,1]) |
| [15,16) | `right_gripper_width` | 1 ([0,1]) |

第一版不订阅 `/pi05/observation/tactile/*` topic；tactile_sensor_node 可存在但不接入 Pi05 节点。

#### 后续版本 observation.state = 32D（加触觉）

在第一版 16D 基础上追加：

| 索引 | segment | dim |
|---|---|---|
| [16,20) | `tactile_left_gripper_1` | **4** |
| [20,24) | `tactile_left_gripper_2` | **4** |
| [24,28) | `tactile_right_gripper_1` | **4** |
| [28,32) | `tactile_right_gripper_2` | **4** |

- 每片触觉压缩成 4D（从原始 6×15 压力矩阵聚合，`tactile_strategy: window_aggregate`），4 片共 16D，追加在 state 末尾 [16,32)。
- action 始终是纯 16D（pose+width），**不含触觉**（无论哪版）。

**仍需确认的连带项（实现细节，非决策点）**：
- deploy 侧必须复用数据清洗侧 forge 的「6×15 矩阵 → 4D」聚合算法（窗口聚合），否则 train/deploy 触觉编码不一致。需查 forge 侧聚合实现（后续版本 D4 落地时确认）。
- 触觉段落的 enable/disable 走 config 开关（与数据清洗 `state_segments` 的 `enabled` 字段对齐）。

### Q7 · 回滚路径的粒度 — ✅ 已确认

**结论**：回滚时**必须同时切回旧 config 文件**，旧 launch 不能直接读新 config。

依据（AS-IS config schema 源码 `schema.py:33-115`）：
- `RuntimeConfig` 硬编码默认 `action_dim=14` / `state_dim=26`（TO-BE 改 16/32）。
- `ObservationTopicsConfig` 字段全是关节空间/realsense/inspire 语义：`top_image` / `left_wrist_image` / `right_wrist_image` / `proprioception` / `left_hand_state` / `left_ee_position` / `left_ee_rpy`（TO-BE 改鱼眼 + tactile + arm_tcp_pose + gripper_width）。
- `CommandTopicsConfig` 是四路关节/手部目标（TO-BE 改单路 policy_action）。
- 用 `frozen dataclass` + `__post_init__` 硬校验：字段名/类型不匹配会直接 `DeployConfigError`。

**回滚操作**：保留旧 config 文件 + 旧 launch + 旧 bundle 三件套，三者绑定一起切回。新 config 不向后兼容旧 launch（字段名/语义全变）。

## 4. 给后续 L2 改造工作包的输入预告

> [!note] 本节不生成 L2，只标注聚类信号
> 按 TO-BE 工作流原则，L2 必须先回答 8 个聚类问题后才能生成。此处仅记录从 Delta 聚类观察到的候选边界，供下一轮 L2 规划直接使用。

从 §1 的三个核心聚类 + 信息隐藏边界 + 验证阶梯一致性，初步看到以下候选 L2 边界（**待 L2 阶段正式确认，不超过 5 个**）：

1. **Observation 语义重定义工作包**（D3/D4/D7/D8/D9）
   - 共同隐藏：新 observation 字段如何从 ROS topic 变成 policy 输入。
   - 验证阶梯：dry-run + fake-policy（不需真机）。
   - 回滚：config + 旧 bundle。

2. **Action 语义与发布出口工作包**（D11/D12/D17）
   - 共同隐藏：14D TCP action 如何产生并发布为单路 policy_action。
   - 验证阶梯：fake-policy 离线推理。
   - 强依赖 Q3（绝对/delta）。

3. **command_bridge_sender_node 新建工作包**（D14/D15/D16/D19）
   - 共同隐藏：policy action → RM65/夹爪可执行指令的语义边界与硬件安全门。
   - 验证阶梯：fake-policy + 真机 smoke test。
   - 真机风险最高，必须独立 L2。

4. **Safety 职责切分工作包**（D13/D18）
   - 共同隐藏：哪些检查留 policy 层、哪些下移硬件层，以及 enable gate 归属。
   - 验证阶梯：dry-run（policy 层）+ fake-policy（bridge 层）。
   - 强依赖 Q4/Q5。

5. **拓扑与 launch 迁移工作包**（D1/D2）
   - 共同隐藏：新旧拓扑切换与回滚。
   - 验证阶梯：dry-run 启动。
   - 是其他 L2 的集成边界，建议最后或并行收口。

**尚未独立的信号**：D10（bundle 语义）是跨阶段依赖，不应独立成 deploy 侧 L2，而应作为上述 L2 的「输入前提」管理。

> [!warning] 上述 5 个候选不是最终 L2
> 是否合并/拆分，必须在 L2 阶段按工作流「按设计决策聚类 / 信息隐藏 / 变化原因 / 依赖方向 / 验证阶梯 / 回滚边界」八问重新校验。例如 #3 和 #4 都涉及真机，但变化原因不同（节点新建 vs 职责切分），可能合并也可能分开。

## 5. 输出要求核对（工作流 §输出要求）

| 要求 | 本文档回答 |
|---|---|
| 当前产物属于 | Contract Delta（阶段三产物）。 |
| 目标路径 | `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`。 |
| 涉及的现有代码路径 | `pi05_test/pi05/deploy/`（ros_nodes / runtime / models / config / launch）、`pi05_test/pi05/common/`（data/state_codec、config/schema）。详见每条 Delta「影响范围」。 |
| 尚未确认的问题 | 见 §3 Q1–Q7。 |
| 是否存在真机风险 | 是。D1/D5/D6/D11/D13/D14/D15/D16/D19 真机风险高，进入 real-robot 前必须 dry-run + fake-policy。 |
| 本次是否创建工程/任务文件 | 只创建本 Delta 文档；不创建 L2 / L3 任务文件。 |

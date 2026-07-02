# L2-03 · 数据装配 Service 层（输入侧）

> [!info] 归属
> - 对应分层：**Repo + Service**（相邻两层，单向依赖）。
> - 上游：[[00_L2改造工作包总览]]、依赖 [[L2-01-Types层重构]] + [[L2-02-Config层重构]]。
> - 下游：通过 `ObservationSnapshot` 喂给 `InferenceWorker`/`ControlLoop`（不改）。
> - 关联 Delta：D3（相机）、D4（触觉预留）、D7（topic）、D8（臂状态）、D10（bundle）。

## 一句话定位

把 ROS topic 收到的原始数据（鱼眼图像、TCP 位姿、夹爪宽度、触觉），装配成新的 `ObservationSnapshot`（含 16D/32D state），喂给模型推理。隐藏「ROS 数据 → 模型 batch」的装配逻辑。

## 对应分层

**Repo 层**（数据获取）：ROS 订阅 callback，把原始消息解码成内部字段。
**Service 层**（业务逻辑）：`observation_collector.snapshot` 装配完整观测；`policy_loader._build_batch` 构建模型 batch。

两层相邻、单向（Repo→Service），共同隐藏输入侧装配逻辑，验证阶梯一致（dry-run），合并。

## 涉及的现有代码

| 文件 | 部分 | AS-IS 现状 |
|---|---|---|
| `deploy/runtime/observation_collector.py` | 全文（L1-154） | `REQUIRED_IMAGE_KEYS`/`_required_value_keys`/`update_proprioception`/`update_hand`/`update_vector`/`snapshot`/`_has_stale_field_locked` 全关节语义 |
| `deploy/ros_nodes/pi05_vla_deploy_node.py` | `_create_subscriptions`（L100-133）、`_image_topic_map`（L135-143）、`_image_cb`/`_proprio_cb`/`_hand_cb`/`_point_cb`/`_vec3_cb`（L154-182） | 订阅 realsense/proprio/hand/ee；callback 写 collector |
| `deploy/models/policy_loader.py` | `_build_batch`（L80-95）、`_manifest_image_names`（L158-164）、`Pi05PolicyRuntime.__init__` 的 image_names 默认值（L43） | 用 encoded_state + image_names 拼 batch |

## 已有能力盘点

**保留的能力**：
- `ObservationCollector` 的「字段齐全 + 未过期才生成 snapshot」门控模式——保留，只改字段集。
- `set_required_image_keys` 从 bundle manifest 动态确定必需图像——保留。
- `_has_stale_field_locked` 基于时间戳的时效性检查——保留，改字段名。
- `_publish_observation_if_ready` 的「成功写入 SharedBuffer / 失败节流记录 missing」——保留。
- `policy_loader._build_batch` 的「encoded_state normalize + image 组装」流程——保留，维度跟随 Types 层。
- `image_names` 来自 manifest 的动态绑定——保留。

**必须保留的原始行为**：
- snapshot 的 latest-only 语义（不保留历史）。
- missing fields 的节流日志（每 2 秒）。
- `_build_batch` 的 CPU 端预处理（state normalizer 在 CPU）。

## 真实改造边界

### 改 `observation_collector.py`

1. `REQUIRED_IMAGE_KEYS` 改为 `("left_fisheye", "right_fisheye")`（两路鱼眼，替代 top/left_wrist/right_wrist）。
2. `_required_value_keys` 改为：`left_tcp_pose`/`right_tcp_pose`/`left_gripper_width`/`right_gripper_width`（第一版 16D，无触觉）。
3. 删除 `update_proprioception`/`update_hand`/`decode_picotele_proprioception` 依赖。
4. 新增 `update_tcp_pose(side, pose_quat_7d)`：接收 `[x,y,z,qx,qy,qz,qw]`，校验 quaternion 归一化（warn 不阻塞）。
5. 新增 `update_gripper_width(side, width)`：接收 `[0,1]` 归一化宽度。
6. 预留 `update_tactile(chip_id, matrix)`：第一版 disabled（config 控制），后续启用。
7. `snapshot` 改成构造新 `BimanualState`（TCP+width）+ 调 `encode_bimanual_state`（16D）。

### 改 `deploy_node` 订阅侧（Repo 层）

1. `_create_subscriptions`：订阅 `/pi05/observation/image/*_fisheye`（Image）、`/pi05/observation/arm/*_tcp_pose`（PoseStamped）、`/pi05/observation/gripper/*_state`（Float32）。触觉订阅受 config 开关控制（第一版不订阅）。
2. `_image_topic_map`：改为 `{"left_fisheye": (...), "right_fisheye": (...)}`。
3. 新增 callback：`_tcp_pose_cb(side, PoseStamped)`（解 quaternion）、`_gripper_cb(side, Float32)`（解 width）。
4. 删除 `_proprio_cb`/`_hand_cb`/`_point_cb`/`_vec3_cb`。
5. 保留 `_image_cb`（鱼眼图像解码 + preprocess_rgb_image 不变）。

### 改 `policy_loader._build_batch`

1. 跟随 Types 层的 `encoded_state` 维度（16D 第一版）。
2. `image_names` 默认值从 `("top","left_wrist","right_wrist")` 改为 `("left_fisheye","right_fisheye")`。
3. `_manifest_image_names` 的 fallback 默认值同步改。
4. batch 的 `observation.images.{name}` key 跟随新 image_names。

> [!note] PoseStamped 解码注意
> `/pi05/observation/arm/*_tcp_pose` 是 `geometry_msgs/PoseStamped`。callback 要把 `pose.position`(x,y,z) + `pose.orientation`(qx,qy,qz,qw) 拼成 7D `[x,y,z,qx,qy,qz,qw]`。注意 ROS quaternion 是 xyzw 顺序，与数据清洗约定一致。

## adapter 优先策略

collector 的字段装配逻辑**直接修改**（旧字段集整体替换）。但保留 collector 的**门控框架**（required/stale 检查）——只改它检查的字段名，不改检查机制。

订阅创建**直接修改**（topic 名是 config 驱动，改 config 即改订阅）。

## 真机风险

**低**。dry-run 下用录包数据或假数据验证 snapshot 生成和 batch 构建，不接硬件。

## 验收路径

1. **dry-run**：启动节点，喂入构造的 observation topic 数据（鱼眼图像 + TCP PoseStamped + gripper Float32），看 `ObservationSnapshot` 是否生成、encoded_state 是否 16D。
2. **missing fields 测试**：缺 TCP pose 时 snapshot 不生成，日志节流报 missing。
3. **触觉预留测试**：config 关闭触觉时，snapshot 不依赖触觉即可生成。
4. **batch 维度测试**：`_build_batch` 输出的 `observation.state` 维度与 bundle 期望一致（16D）。

## 回滚方式

git 回退三个文件 + 旧 config + 旧 bundle。

## 可拆分的 L3 草案

| L3 | 目标 | 改的文件 |
|---|---|---|
| L3-03a | 改 `observation_collector`：字段集换 TCP+width，加 `update_tcp_pose`/`update_gripper_width`，预留触觉，改 `snapshot` | observation_collector.py |
| L3-03b | 改 `deploy_node` 订阅侧：topic_map 换鱼眼，新增 tcp/gripper callback，删旧 callback | pi05_vla_deploy_node.py（订阅部分） |
| L3-03c | 改 `policy_loader._build_batch` + image_names 默认值 | policy_loader.py |
| L3-03d | dry-run 验证：构造数据跑通 snapshot→batch | tests/ + dry-run 脚本 |

> [!note] 与 L2-04 的边界
> L2-03 只改 `deploy_node` 的**订阅侧**（输入）。`deploy_node` 的**发布侧**（_control_tick、publishers）属于 L2-04。两者改的是同一个文件的不同部分，需协调（建议 L2-03 先改订阅，L2-04 后改发布，或同一 Agent 顺序完成两半）。

---
tags:
  - 附件
---

# Pi05VlaDeployNode (ROS2 部署节点)

> [!abstract]
> 274 行的 ROS2 节点入口：装配 ObservationCollector / SharedBuffer / SafetyGuard / ControlLoop / InferenceWorker，接好 ROS 订阅与发布，启动 2 个 timer（control + metrics）+ 1 个推理后台线程。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `Pi05VlaDeployNode(Node)` |
| 节点名 | `"pi05_vla_deploy_node"` |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py:29-219` |
| 启动 | `main()` (L257-270) 用 `MultiThreadedExecutor(num_threads=4)` spin |
| 现实含义 | 真机部署的"装配体"——一个文件把所有 runtime 组件拼成一个 ROS 节点 |

## 装配顺序（`__init__` 第 32-94 行）

1. 保存 `self.config: DeployConfig`
2. 构造 `self.image_config: ImagePreprocessConfig`（从 `config.image`）
3. 构造 `self.collector: ObservationCollector`（从 `config.topics.observation.proprioception_order`）
4. 构造 `self.shared_buffer: SharedBuffer`（从 `config.runtime.max_inference_requests/..._chunks`）
5. 构造 `self.safety_guard: SafetyGuard(config.safety)`
6. 构造 `self.control_loop: ControlLoop(...)`（13 个参数全部从 config 映射）
7. 加载模型：`load_policy_runtime(config)` → 拿到 `policy_image_names`
8. `collector.set_required_image_keys(policy_image_names)`
9. 构造 `self.inference_worker: InferenceWorker(...)`
10. 调 `_create_subscriptions()` 和 `_create_publishers()`
11. 创建 2 个 ROS timer：
    - `control_timer`: `1.0 / control_hz` → `_control_tick`
    - `metrics_timer`: `1.0 / publish_metrics_hz` → `_publish_metrics`
12. `inference_worker.start()`
13. 日志 "Pi0.5 deployment started mode=... infer_hz=... control_hz=..."

## ROS 订阅

| Topic 名 (默认) | 消息类型 | 回调 | 写入 collector 字段 |
| --- | --- | --- | --- |
| `/pi05_vla/observation/image/{top,left_wrist,right_wrist}/compressed` | `CompressedImage` | `_image_cb` | `update_image(name, tensor)` |
| `/pi05_vla/observation/proprioception` | `JointState` | `_proprio_cb` | `update_proprioception(positions)` |
| `/pi05_vla/observation/{left,right}_hand/joint_state` | `JointState` | `_hand_cb` | `update_hand(side, position[0])` |
| `/pi05_vla/observation/{left,right}_arm/ee_position` | `Point` | `_point_cb` | `update_vector(key, [x,y,z])` |
| `/pi05_vla/observation/{left,right}_arm/ee_rpy` | `Vector3` | `_vec3_cb` | `update_vector(key, [x,y,z])` |

## ROS 发布

| Topic 名 (默认) | 消息类型 | 来源 |
| --- | --- | --- |
| `/pi05_vla/command/left_arm/joint_target` | `JointState` | `command.action.left_arm` (6 维) |
| `/pi05_vla/command/right_arm/joint_target` | `JointState` | `command.action.right_arm` (6 维) |
| `/pi05_vla/command/left_hand/target` | `Float64` | `command.action.left_hand` (1 维) |
| `/pi05_vla/command/right_hand/target` | `Float64` | `command.action.right_hand` (1 维) |
| `/pi05_vla/status` | `String` | "mode=... metrics=..." |
| `/pi05_vla/metrics` | `String` | JSON 序列化所有 [[SharedBuffer 线程安全桥接]] 指标 |

## 关键 timer

| Timer | 频率 | 行为 |
| --- | --- | --- |
| `control_timer` | `control_hz` (30Hz 默认) | `_control_tick`：调 `control_loop.tick()`，发布 action |
| `metrics_timer` | `publish_metrics_hz` (1Hz 默认) | `_publish_metrics`：取 `shared_buffer.metrics_snapshot()` + `control_loop.status_snapshot()`，发到 status + metrics topic |

## `_control_tick` 行为（行 196-211）

```python
command = self.control_loop.tick()
if command is None:
    return
if not self.config.runtime.publishes_command_topics:  # dry-run
    log("dry-run command left=... right=... hands=(..., ...)")
    return
# 真发：
left_arm_pub.publish(_joint_msg(command.action.left_arm))
right_arm_pub.publish(_joint_msg(command.action.right_arm))
left_hand_pub.publish(Float64(data=float(command.action.left_hand)))
right_hand_pub.publish(Float64(data=float(command.action.right_hand)))
```

## 关键设计决策

- **MultiThreadedExecutor(num_threads=4)**：5 路图像 + 6 路数值订阅 + 2 timer，共 13 个 callback，需要多线程
- **`shutdown()` 显式 stop + join**：`inference_worker.stop()` + `join(timeout=2.0)`，避免 daemon 线程被中途打断
- **`policy_image_names` 决定订阅哪些图**：load_policy_runtime 读 bundle manifest，反推需要哪些 image key
- **`publishes_command_topics` 决定 dry-run vs 真发**：通过 `mode ∈ {shadow-run, safe-run}` 切换

## 关键约束

- **`image_config` 必须和训练一致**：见 [[ImagePreprocessConfig 部署侧图像配置]]
- **`bundle.resolved_bundle_dir` 必须存在且含 manifest.json**：load_policy_runtime 失败 → RuntimeError
- **`safety.stale_observation_timeout_s` < `runtime.max_action_age_sec`**：否则观测失效但 chunk 还在用
- **不接管 lifecycle**：`/set_state` / QoS 等由其他节点管
- 与 [[DeployConfig 部署配置]]、[[SharedBuffer 线程安全桥接]]、[[ControlLoop 控制循环驱动]] 等配套

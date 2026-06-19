---
tags:
  - 附件
---

# ControlLoop (控制循环驱动)

> [!abstract]
> 30Hz ROS timer 调度的 `tick()`：从 `SharedBuffer.latest_observation` 拿最新观测 → 推推理请求 → 等 ActionChunk → 用 `aligned_index` 算当前步 → 调 `SafetyGuard` 校验 → 返回 action 给节点发布。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `ControlLoop` |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/control_loop.py`（god node, 24 edges） |
| 实例位置 | `pi05_vla_deploy_node.py:47-65` |
| 调用方 | `Pi05VlaDeployNode._control_tick` (节点第 196 行) |
| 现实含义 | 把"异步推理 + 同步控制"缝起来的核心调度逻辑 |

## 构造参数（Pi05VlaDeployNode 传入）

| 参数 | 来源 | 含义 |
| --- | --- | --- |
| `shared_buffer` | `SharedBuffer` | 跨线程信箱 |
| `request_queue` | `shared_buffer.inference_request_queue` | 推请求 |
| `result_queue` | `shared_buffer.chunk_result_queue` | 拉结果 |
| `observation_provider` | `lambda: shared_buffer.latest_observation(max_age_s=...)` | 取最新观测 |
| `safety_guard` | `SafetyGuard` | 后置安全校验 |
| `control_hz` | `config.runtime.control_hz` | timer 频率 |
| `execute_horizon` | `config.runtime.execute_horizon` | chunk 中实际执行多少步 |
| `prefetch_steps` | `config.runtime.prefetch_steps` | 剩多少步时预取 |
| `blend_steps` | `config.runtime.blend_steps` | 新旧 chunk 加权过渡 |
| `action_dim` | `config.runtime.action_dim` | 14 |
| `max_action_age_s` | `config.runtime.max_action_age_sec` | 0.45s |
| `fallback_policy` | `config.runtime.fallback_policy` | hold_last_action 等 |
| `stale_observation_timeout_s` | `config.safety.stale_observation_timeout_s` | 0.5s |

## `tick()` 行为（高频 30Hz 调用）

```text
1. 拿最新 observation（_obs = observation_provider()）
   └ None → 触发 fallback (hold last / safe stop) → return None

2. 决定要不要推新的 inference request
   └ 首次 / 已 execute_horizon 步 / 还没请求过 → put_latest

3. 拿最新 ActionChunk（_chunk = result_queue.get_latest_or_none()）
   └ None → 触发 fallback → return None

4. 算 aligned_index = _chunk.aligned_index(now)
   └ 若走到 execute_horizon - prefetch_steps → 推新请求

5. SafetyGuard 校验：max_joint_delta, hand range, normalized clamp
   └ reject → record_rejected_action + return None
   └ clamp → 修后返回

6. 返回 action (left_arm[6], right_arm[6], left_hand, right_hand) 给 _control_tick
```

## 调度节奏示意

```text
time →  0     33ms   66ms   100ms  133ms  166ms  200ms  233ms  266ms  300ms
        |      |      |      |      |      |      |      |      |      |
chunk:  [========== execute_horizon (10 steps) ==========]
                                              ^prefetch_steps (5 steps before end)
        |      |      |      |      |      |      |      |      |      |
infer:        [========= model (≈100ms) =========]
                                                              [==== next infer ====]
```

## 在数据流中的位置

```text
ROS timer (30Hz)
    ↓
Pi05VlaDeployNode._control_tick
    ↓
control_loop.tick() → action
    ↓
left_arm_pub.publish(JointState(...))
right_arm_pub.publish(JointState(...))
left_hand_pub.publish(Float64(...))
right_hand_pub.publish(Float64(...))
```

## 关键约束

- **`tick()` 必须快**：30Hz 下每帧 < 33ms，绝不能阻塞等模型
- **fallback 行为**：
  - `hold_last_action`：复用上一个 action，永不返回 None
  - `continue_old_chunk`：复用老 chunk 的下一步
  - `safe_stop`：返 None，节点什么都不发
- **SafetyGuard 是最后一道闸门**：clamp / reject 都不阻塞 tick，async 记录
- 与 [[SafetyGuard 推理后安全校验]]、[[ActionChunk 动作块 dataclass]]、[[SharedBuffer 线程安全桥接]] 配套

---
tags:
  - 附件
---

# RuntimeConfig (部署运行时配置)

> [!abstract]
> `DeployConfig.runtime` 子配置：控制模式 (dry-run/shadow-run/safe-run)、推理 / 控制 Hz、action chunk 大小、备用策略等所有"运行节奏"参数。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `RuntimeConfig` (frozen dataclass) |
| 位置 | `pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py:33-91` |
| 校验 | `__post_init__` 内置硬校验 |
| 现实含义 | 决定"这次部署是只打印动作、还是把动作发到下位机" 以及 "每秒跑几次模型 / 发几次命令" |

## 关键字段

| 字段 | 类型 | 默认 | 含义 |
| --- | --- | --- | --- |
| `mode` | `str` | `"dry-run"` | 部署模式：dry-run / shadow-run / safe-run |
| `inference_hz` | `float` | `10.0` | 模型推理频率（Hz），控制 `_InferenceWorker.run` 的 `period_s` |
| `control_hz` | `float` | `30.0` | 控制循环频率（Hz），控制 ROS timer 周期 |
| `chunk_size` | `int` | `30` | 模型一次输出的动作数（`action_dim × chunk_size`） |
| `execute_horizon` | `int` | `10` | 一个 chunk 中实际执行多少步就开始切换 |
| `prefetch_steps` | `int` | `5` | 在 chunk 还剩多少步时预取下一个 chunk |
| `blend_steps` | `int` | `3` | 新旧 chunk 切换时的线性加权步数 |
| `action_dim` | `int` | `14` | 动作向量维度（与 [[ACTION_DIM 14D action schema]] 一致） |
| `state_dim` | `int` | `26` | 状态向量维度（与 [[STATE_DIM 26D state schema]] 一致） |
| `max_action_age_sec` | `float` | `0.45` | 超过这个时间没新 chunk 就触发 fallback |
| `fallback_policy` | `str` | `"hold_last_action"` | 旧 chunk 超时后怎么办：保持 / 继续旧 / 安全停止 |
| `max_inference_requests` | `int` | `1` | 请求队列容量（LatestQueue 始终只保留最新 1 条） |
| `max_pending_chunks` | `int` | `1` | 结果队列容量（同上） |
| `max_delta_per_step` | `float` | `0.03` | 单步最大关节变化（rad），兜底安全 |
| `warmup_steps` | `int` | `2` | 启动时先发几帧"空跑"，等模型 warmup |
| `compile_model` | `bool` | `True` | 是否 `torch.compile` predict_action_chunk |
| `compile_mode` | `str` | `"reduce-overhead"` | torch.compile 模式 |
| `publish_metrics_hz` | `float` | `1.0` | /metrics topic 发布频率 |
| `task` | `str` | `"bimanual manipulation"` | 任务描述，给 VLM prompt |

## `mode` 三种模式

| 模式 | 行为 | ROS publish？ |
| --- | --- | --- |
| `dry-run` | 推理 → 控制循环 → 打印 action 到日志 | 否（`publishes_command_topics=False`） |
| `shadow-run` | 同上 + 发布到 /pi05_vla/command topic，但被 mux 默认旁路 | 是 |
| `safe-run` | 同 shadow-run + mux 切到 VLA 模式，控制真机 | 是 |

通过 `RuntimeConfig.publishes_command_topics` 属性（schema.py:62）判断。

## 关键约束

- **`execute_horizon <= chunk_size`**：不然会出现"chunk 还没切完又要新 chunk" 的死锁
- **`prefetch_steps <= execute_horizon`**：预取不能超过执行窗口
- **`fallback_policy` 枚举**：见 schema.py:88-91
- **`max_inference_requests` / `max_pending_chunks` >= 1**：LatestQueue 不允许 0
- 与 [[SharedBuffer 线程安全桥接]]、[[InferenceWorker 推理后台线程]] 紧密相关

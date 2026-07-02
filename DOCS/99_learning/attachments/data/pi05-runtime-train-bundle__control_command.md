---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# ControlCommand

> [!abstract]
> 控制循环输出的安全结构化命令，包含 `BimanualAction` 以及 held/fallback 标志。

| 属性 | 值 |
| --- | --- |
| 源码名 | `ControlCommand` |
| 数据结构 | `action`、`held`、`fallback` |
| 生产者 | N07 动作安全过滤后由 N06 包装 |
| 消费者 | N08 ROS2 命令发布与 metrics |
| 源码位置 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/control_loop.py:20-27`; `pi05_vla_deploy_node.py:196-211` |

## 约束

`command is None` 表示当前 tick 不发布，通常来自 safe_stop fallback 或没有可用动作。


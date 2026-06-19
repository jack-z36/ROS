---
tags:
  - 附件
---

# ControlCommand 控制命令

> [!abstract]
> 控制循环 `tick()` 每步返回的"信封"——把"现在应该发什么动作"和"这是正常发布的还是 fallback 顶替的"两件事一次性告诉调用方。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `ControlCommand` |
| 数据类型 | `@dataclass(frozen=True)`（`control_loop.py:20-26`） |
| 数据结构 | 3 字段：`action, held, fallback` |
| 所在文件 | `pi05/deploy/src/pi05/deploy/runtime/control_loop.py:20-26` |
| 现实含义 | "这一步该发什么 + 是真发的还是 hold 的" |

## 3 字段含义

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `action` | [[BimanualAction 双臂动作]] | 校验后（已过 SafetyGuard）的动作 |
| `held` | `bool` | True → 本步是 fallback 沿用上次动作；False → 本步是策略新鲜输出 |
| `fallback` | `bool` | True → 当前在 fallback 模式下（模型/观测出问题了） |

> `held` 与 `fallback` 的关系：通常 `held=True ⇒ fallback=True`，但**反过来不成立**——`fallback=True` 不一定 `held`（比如 `safe_stop` 模式直接返 `None`，连 Command 都没）。

## 4 种返回情况

| 场景 | 返回 | `held` | `fallback` | 节点行为 |
| --- | --- | --- | --- | --- |
| 正常 | `ControlCommand(action)` | `False` | `False` | 4 路 ROS publisher 发 |
| fallback：hold_last_action | `ControlCommand(action, held=True, fallback=True)` | `True` | `True` | 4 路 publisher 发（沿用旧动作） |
| fallback：safe_stop | `None` | — | — | 节点不发布任何命令 |
| 模型/观测双缺 | `None` | — | — | 节点不发布任何命令 |

## 示例

```python
from pi05.deploy.runtime.control_loop import ControlCommand
from pi05.common.robot.action_spec import BimanualAction
import numpy as np

cmd = ControlCommand(
    action=BimanualAction(
        left_arm=np.zeros(6, dtype=np.float32),
        right_arm=np.zeros(6, dtype=np.float32),
        left_hand=800.0,
        right_hand=800.0,
    ),
    held=False,
    fallback=False,
)
print(cmd.action.left_hand)   # 800.0
print(cmd.held, cmd.fallback) # False False
```

## 在数据流中的位置

- **生产方**：`ControlLoop.tick()` 唯一生产方
- **消费方**：`Pi05VlaDeployNode._control_tick()`，把 `command.action.{left_arm,right_arm,left_hand,right_hand}` 拆到 4 路 ROS Publisher

## 与其他概念的关系

- **上游**：`SafetyGuard.filter_action()` 返回的 `SafetyResult.action` 被包进 `ControlCommand.action`
- **下游**：`Pi05VlaDeployNode._control_tick` 直接读 4 个字段
- **姊妹**：`RuntimeMetrics.record_published_action` / `record_held_action` / `record_rejected_action` 三种计数器分别对应 `held=False+fallback=False` / `held=True+fallback=True` / SafetyGuard reject

## 关键不变量

> 1. `frozen=True`——一旦构造不可改；如需"修改"请用 `dataclasses.replace()`
> 2. `action` 永不为 `None`（如果 SafetyGuard 拒收，ControlLoop 走 fallback 而不是返回 `None` 包装）
> 3. `held=True` 必然 `fallback=True`（代码上没硬校验，但语义上如此）
> 4. `tick()` 也可能直接返 `None`（safe_stop 或完全无数据）——调用方必须判空

## 相关概念

- [[ControlLoop 控制循环驱动]]：本结构的唯一生产方
- [[BimanualAction 双臂动作]]：本结构的主载荷
- [[SafetyGuard 安全校验器]]：填 `action` 字段的安全闸
- [[Pi05VlaDeployNode ROS2 部署节点]]：本结构的唯一消费方
- [[RuntimeMetrics 运行时指标]]：`record_published_action` / `record_held_action` / `record_rejected_action` 三个计数器

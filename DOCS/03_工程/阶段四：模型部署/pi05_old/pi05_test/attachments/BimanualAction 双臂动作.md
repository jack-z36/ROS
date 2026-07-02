---
tags:
  - 附件
---

# BimanualAction 双臂动作

> [!abstract]
> 策略输出 14 维向量的**结构化视图**——左臂 6 关节 + 右臂 6 关节 + 左手 1 夹爪 + 右手 1 夹爪。`as_vector()` 拼回 14D，`split_bimanual_action()` 反向拆解。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `BimanualAction` |
| 数据类型 | `@dataclass(frozen=True)`（`action_spec.py:22-39`） |
| 数据结构 | 4 字段：`left_arm, right_arm, left_hand, right_hand` |
| 所在文件 | `pi05/common/src/pi05/common/robot/action_spec.py:22-39` |
| 现实含义 | "现在应该让双臂怎么动" |

## 4 字段

| 字段 | 维度 | 类型 | 含义 |
| --- | --- | --- | --- |
| `left_arm` | 6 | `np.float32[6]` | 左臂 6 关节目标角（rad） |
| `right_arm` | 6 | `np.float32[6]` | 右臂 6 关节目标角（rad） |
| `left_hand` | 1 | `float` | 左手夹爪指令（300-1000 范围） |
| `right_hand` | 1 | `float` | 右手夹爪指令（300-1000 范围） |

> **6+6+1+1 = 14**，对应 [[ACTION_DIM 14D action schema]]。

## 关键方法

```python
def as_vector(self) -> np.ndarray:
    return np.concatenate([
        self.left_arm,                  # 6
        self.right_arm,                 # 6
        [self.left_hand, self.right_hand]  # 2
    ]).astype(np.float32)               # → 14D
```

反向：[[split_bimanual_action|]] 把 14D 拆成 `BimanualAction`。

## 示例

```python
from pi05.common.robot.action_spec import BimanualAction
import numpy as np

a = BimanualAction(
    left_arm=np.array([0.1, -0.2, 0.3, -0.4, 0.5, -0.6], dtype=np.float32),
    right_arm=np.array([0.0, 0.1, -0.1, 0.2, -0.2, 0.3], dtype=np.float32),
    left_hand=800.0,
    right_hand=300.0,
)
vec = a.as_vector()         # shape (14,), dtype float32
print(vec.shape)             # (14,)
```

## hand_command_to_trigger：手部指令转换

```python
def hand_command_to_trigger(command, *, open_value=1000.0, closed_value=300.0):
    span = max(1e-6, open_value - closed_value)
    value = (open_value - command) / span
    return float(np.clip(value, 0.0, 1.0))
```

> 把 300-1000 的夹爪指令转成 0-1 归一化 trigger（1=张开，0=闭合）。这给 `bridge_ros.py`（picotele 桥）用来产生 trigger 类型的 ROS 消息。

## 在数据流中的位置

- **生产**：
  - [[SafetyGuard 安全校验器]] 把 14D 拆 4 段后裁剪+限速，再组装为 `BimanualAction` 返回
  - 模型原始 14D 输出也可通过 `split_bimanual_action()`（同文件 `action_spec.py:42-52`）拆
- **消费**：
  - `Pi05VlaDeployNode._control_tick()` → 调 `command.action.left_arm / right_arm / left_hand / right_hand` 发到 4 路 publisher
  - `ControlLoop._fallback()` → 用 `self.last_command.as_vector()` 重投 SafetyGuard 做 hold

## 关键不变量

> 1. `frozen=True`——一旦构造不可改；要"修改"必须新建实例
> 2. `left_arm / right_arm` 必须是长度 6 的向量（`as_vector` 不做校验，但下游 SafetyGuard 会按 6D 处理）
> 3. `left_hand / right_hand` 接受 `float`，范围由 `SafetyConfig.hand_min/max` 限制（默认 300-1000）
> 4. `as_vector()` 总返回 14 元素、`dtype=float32` 的新数组

## 相关概念

- [[ACTION_DIM 14D action schema]]：本结构编码后的向量维度契约
- [[BimanualState 双臂状态]]：与本结构互为配对（state=26D 包含左右臂状态）
- [[SafetyGuard 安全校验器]]：本结构的"裁剪+限速"加工方

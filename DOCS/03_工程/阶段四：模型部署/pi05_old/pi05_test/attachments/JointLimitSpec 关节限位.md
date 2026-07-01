---
tags:
  - 附件
---

# JointLimitSpec 关节限位

> [!abstract]
> 单臂 6 个关节的**最小/最大角度硬约束**——`clamp()` 把 6D 关节向量截到 `[min, max]` 区间；`contains()` 判断是否在限位内。`SafetyGuard` 闸门 2 用的就是 `clamp()`。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `JointLimitSpec` |
| 数据类型 | `@dataclass(frozen=True)`（`joint_limits.py:13-42`） |
| 数据结构 | 2 个长度=6 的 `np.float32` 向量 |
| 所在文件 | `pi05/common/src/pi05/common/robot/joint_limits.py:13-42` |
| 现实含义 | 机器人物理关节"拧不到"的硬边界 |

## 工厂方法

```python
@classmethod
def from_values(cls, min_rad, max_rad) -> "JointLimitSpec":
    min_vec = np.asarray(list(min_rad), dtype=np.float32).reshape(-1)
    max_vec = np.asarray(list(max_rad), dtype=np.float32).reshape(-1)
    assert min_vec.size == 6 and max_vec.size == 6
    assert np.all(min_vec <= max_vec)
    return cls(min_rad=min_vec, max_rad=max_vec)
```

> 构造时硬校验：必须是 6 维（[[ARM_DOF 6DOF per arm]]），且 `min <= max` 否则抛 `ValueError`。

## 公开方法

| 方法 | 作用 | 异常条件 |
| --- | --- | --- |
| `clamp(joints_rad) -> np.ndarray[6]` | 把 6D 关节向量截到 `[min, max]` | 输入不是 6 维 → `ValueError` |
| `contains(joints_rad) -> bool` | 判断是否在限位内（包含等于） | 输入不是 6 维 → 返 `False` |

## 工厂便利函数

```python
def broad_joint_limits(limit_rad: float = 2π) -> JointLimitSpec:
    return JointLimitSpec.from_values([-limit_rad]*6, [+limit_rad]*6)
```

> 默认 2π ≈ 6.28 rad，**几乎不限位**——给没配硬件参数的项目兜底。

## 在数据流中的位置

- **构造**：`SafetyGuard.__init__()` 调 `JointLimitSpec.from_values(limits.left_min_rad, limits.left_max_rad)`（如果 `joint_limits.enabled=True`）
- **使用**：`SafetyGuard.filter_action()` 闸门 2 调 `self._left_limits.clamp(left)`
- **配置入口**：`safety.joint_limits.{left,right}_{min,max}_rad`（[[SafetyConfig 安全配置]] 字段）

## 配置示例

```yaml
# deploy.yaml
safety:
  joint_limits:
    enabled: true
    left_min_rad: [-1.57, -1.57, -1.57, -1.57, -1.57, -1.57]
    left_max_rad: [ 1.57,  1.57,  1.57,  1.57,  1.57,  1.57]
    right_min_rad: [-1.57, -1.57, -1.57, -1.57, -1.57, -1.57]
    right_max_rad: [ 1.57,  1.57,  1.57,  1.57,  1.57,  1.57]
```

## 关键不变量

> 1. 长度必须严格为 6（双臂各 6 个关节，源自 `ARM_DOF=6`）
> 2. `min_vec <= max_vec`（逐元素）
> 3. `clamp()` 返回 `dtype=float32`、长度 6 的**新**数组（不修改入参）
> 4. 当 `joint_limits.enabled=False` 时，`SafetyGuard` 跳过闸门 2（不构造 `JointLimitSpec`）

## 与"软限速"的区别

> | | 硬限位 (JointLimitSpec) | 软限速 (max_joint_delta_rad) |
> | --- | --- | --- |
> | 约束对象 | 单关节角的**绝对值** | 单步**变化量** |
> | 防止 | 撞机械限位 | 命令跳变、电机过载 |
> | 闸门 | 2 | 3 |
> | 锚点 | 自身限位 | previous_action 或 observation |

## 相关概念

- [[SafetyGuard 安全校验器]]：本规格的**唯一**消费方
- [[BimanualAction 双臂动作]]：本规格的裁剪对象

---
tags:
  - 附件
---

# SafetyGuard 安全校验器

> [!abstract]
> 策略输出在发给真实电机前必经的**末端安全网**——做 4 件事：(1) 形状/有限性校验、(2) 关节硬限位、(3) 单步 delta 限速、(4) 夹爪范围裁剪。任何一步拒绝都把决定权交回 ControlLoop，由 `fallback_policy` 决定后续动作。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `SafetyGuard` |
| 数据类型 | `class`（`safety_guard.py:28-98`） |
| 数据结构 | 1 个 `SafetyConfig` + 2 个可选 `JointLimitSpec` |
| 所在文件 | `pi05/deploy/src/pi05/deploy/runtime/safety_guard.py:28-98` |
| 现实含义 | "策略可以建议，安全我有底线" |

## 4 道闸门（按顺序）

### 闸门 1：形状与有限性

```python
vector = ensure_action_vector(action)        # 14D 校验
if not np.all(np.isfinite(vector)):          # 不能有 NaN/Inf
    return SafetyResult(accepted=False, reason="action contains NaN or Inf")
```

> 数值异常往往来自：模型崩溃、GPU 驱动 bug、unnormalize 配错。**直接拒收**。

### 闸门 2：关节硬限位

```python
if self._left_limits is not None:  left  = self._left_limits.clamp(left)
if self._right_limits is not None: right = self._right_limits.clamp(right)
```

> 由 [[JointLimitSpec 关节限位]] 实现；默认不启用（`joint_limits.enabled=False`），可在 `safety.joint_limits.left_min_rad/max_rad` 配置。

### 闸门 3：单步 delta 限速

```python
if self.config.max_joint_delta_rad > 0.0:
    left_anchor, right_anchor = self._delta_anchor(observation, previous_action)
    if left_anchor is not None:
        left = self._clamp_delta(left, left_anchor)
```

`_delta_anchor` 的优先级：

| 优先级 | 锚点 | 场景 |
| --- | --- | --- |
| 1 | `previous_action.left_arm / right_arm` | 已有上一步发布的命令 |
| 2 | `observation.state.left_arm_q / right_arm_q` | 没有 previous 但有 obs（fallback 时） |
| 3 | `None` | 啥都没有 → 不限速 |

> `max_joint_delta_rad` 默认 0.08 rad ≈ 4.6° / 控制步（≈ 30 Hz 下 138°/s）。即使模型发疯一次跳 90°，也会被截到 4.6°。

### 闸门 4：夹爪范围裁剪

```python
left_hand=float(np.clip(structured.left_hand, self.config.hand_min, self.config.hand_max))
right_hand=float(np.clip(structured.right_hand, self.config.hand_min, self.config.hand_max))
```

> `hand_min=300, hand_max=1000` 对应 inspire 手的 closed/open 标定。

## 输出

```python
@dataclass(frozen=True)
class SafetyResult:
    action: BimanualAction | None      # 校验后（裁剪+限速）的动作
    accepted: bool                      # True → 接受；False → 拒收
    reason: str | None                  # 拒收时给出原因（写入 last_error）
```

## 在数据流中的位置

- 调用方：`ControlLoop.tick()`（每一步都会调一次）
- 入参：
  - `raw_action`（14D 策略输出）
  - `observation`（最近一次冻结观测，用于 delta 锚点）
  - `previous_action`（上次发布的命令）
- 出参：被 ControlLoop 处理——
  - `accepted=True` → 包装为 `ControlCommand(action, held=False, fallback=False)` 发出去
  - `accepted=False` → 触发 `record_rejected_action()` + 走 `fallback_policy`

## 与 fallback 策略的配合

| `fallback_policy` | 行为 |
| --- | --- |
| `"hold_last_action"` | 用上一步 action 经 SafetyGuard 再过一遍（hold+fallback=True） |
| `"continue_old_chunk"` | 同上 |
| `"safe_stop"` | 返回 None → 节点不发布任何命令（机器人靠 deadman 制动） |

## 关键不变量

> 1. **每一步**都过 SafetyGuard（不仅在 fallback 时）——即使策略输出正常，也会被限速限位
> 2. **previous_action 优先**于 observation 做锚点——保证命令连续不抖
> 3. `max_joint_delta_rad > 0` 才会限速（设成 0 关闭此闸门，但极不推荐）
> 4. 拒收时**不抛异常**——返回 `SafetyResult(accepted=False)`，由 ControlLoop 决定

## 相关概念

- [[JointLimitSpec 关节限位]]：实现闸门 2
- [[BimanualAction 双臂动作]]：闸门最终输出的结构
- [[ControlLoop 控制循环驱动]]：每步调一次
- [[BimanualState 双臂状态]]：限速锚点的备选
- [[RuntimeConfig 部署运行时配置]]：`fallback_policy` 的来源

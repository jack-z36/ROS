---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# raw 14D action

> [!abstract]
> 控制循环当前 tick 准备执行的一条未过滤动作向量。

| 属性 | 值 |
| --- | --- |
| 数据名 | raw 14D action |
| 数据类型 | `np.ndarray` shape `(14,)` |
| 生产者 | N06 chunk 消费、blend、fallback |
| 消费者 | N07 动作安全过滤 |
| 源码位置 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/control_loop.py:197-222`; `control_loop.py:290-314` |

## 约束

它还不是可发布命令，必须通过 `SafetyGuard.filter_action()`。


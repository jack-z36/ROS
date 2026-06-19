---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: N07
---

# N07 动作安全过滤

> [!abstract]
> 发布前验证 action shape/数值，并执行 joint limit、delta limit 和 hand range clamp。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据计算类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/safety_guard.py:28-98` |
| 输入数据 | raw 14D action、ObservationSnapshot、previous action |
| 输出数据 | SafetyResult / BimanualAction |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 42-49 | 校验 action 向量并拆成结构化动作 |
| 53-63 | joint limit 和 delta clamp |
| 65-73 | 返回结构化 `BimanualAction`，手部数值也 clamp |
| 80-88 | delta anchor 优先用 previous action，其次用 observation state |


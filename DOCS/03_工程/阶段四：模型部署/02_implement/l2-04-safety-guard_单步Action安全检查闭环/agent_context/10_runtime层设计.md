# runtime 层设计：L2-04

## 1. 本 L2 不在该层新增源码产物

原因：L2-04 的 A1/B/C 全部是同步、无状态的 service。timer、queue、chunk cursor、previous action、fallback、metrics 都是 L2-06 的 runtime 职责。

## 2. 与 L2-06 的唯一协作契约

```text
L2-06 selects candidate action
  + passes previous_safe_action and fresh ObservationSnapshot
  -> A1.B1 filter_action(...)
  -> C5 SafetyResult

PASS/ADJUSTED: L2-06 calls L2-05; after L2-05 accepts, updates previous_safe_action
REJECTED:      L2-06 chooses its configured fallback and records metrics
```

L2-04 不得新增 `ControlLoop`、buffer、worker、timer、retry、metrics counter 或状态更新函数。

## 3. Class/函数、依赖与验收

本层无 Class、无函数、无副作用。Pi0.5 `ControlLoop.tick/_fallback/last_command` 仅解释调用边界，不能迁入。

验收如何确认：mock integration 验证 L2-06 能按 C5.status 分流；静态 import 检查确认 service 不 import runtime。

本文件的任务边界继承当前 L1/L2 功能边界，不继承旧 layer-based 卡片。

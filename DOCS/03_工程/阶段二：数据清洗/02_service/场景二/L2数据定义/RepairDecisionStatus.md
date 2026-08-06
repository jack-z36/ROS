# RepairDecisionStatus 与 RepairDisposition

> 消费对象：Scene2 Service/Runtime Agent。权威性：新运行的处置—计算状态机契约。上游来源：`schemas/repair.py`、`service/repair_run.py`。不负责：异常检测事实。读取时机：修改修复策略或报告前。冲突处理：禁止从 `suggested_action` 推断可改值权限。

检测事实先转换为字段级 `RepairDisposition`：

| 处置 | 含义 |
|---|---|
| `AUTO_REPAIR` | 已批准按预定方法修改已有样本值 |
| `MASK_ONLY` | 只形成 mask/边界 |
| `MANUAL_REVIEW` | 等待人工判断 |
| `UNRECOVERABLE` | 已知无法恢复 |
| `NO_ACTION` | 不需要数值动作 |

计算状态为 `pending / repaired / unrepairable / skipped`。只有 `AUTO_REPAIR + pending` 能进入数值计算；缺邻居、时间不递增、四元数无效或 tactile shape 不兼容只能从 `pending` 变为 `unrepairable`，不得改变上游处置。非自动处置产生 `skipped` 或 `unrepairable` 记录，不调用修复函数。

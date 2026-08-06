# SignalRepairRun

> 消费对象：Scene2 修复与滤波 Agent。权威性：字段级 repair run 契约。上游来源：检测结果和类型化处置。读取时机：修改邻居查找、修复或分段前。不负责：MCAP 写出。冲突处理：不得把同一样本不同字段混为一个 run。

run 聚合键固定为 `topic + modality + time_domain + replacement_unit`。`replacement_unit` 只允许 `pose.position`、`pose.orientation`、`gripper.value`、`tactile.frame`；它保存完整 `input_window_refs`、`disposition`、`planned_method`、最终 `status/applied_method`、前后邻居和样本记录。

邻居必须来自同 topic、同模态、同时间域，位于 run 两侧，且不能跨 `MissingIntervalIssue`。不使用 run 内刚修复值，不启用单邻居 hold fallback。tactile run 还保存目标 `rows/cols` 契约供矩阵插值校验。

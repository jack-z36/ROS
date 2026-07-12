# service 层设计：L2-06

本 L2 不在该层新增源码产物。

原因：chunk 直取是调度状态更新而非独立业务计算；安全计算属于 L2-04 `SafetyGuard`，topic/command 适配属于 L2-05。新建 service 会模糊中央调度边界。

验收如何确认：mock `SafetyGuard.filter()` 与 publisher 接口，断言 tick 调用顺序为 cursor → safety → publish/fallback，且不重算 safety 或转换 topic。

层职责：纯 RAM 业务计算。本 L2 只同步调用相邻 L2 service，输入 raw action/observation，输出 `SafetyResult` 与发布调用；副作用由被调用方承担。本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。Pi0.5 参考：`control_loop.py:125-138`。

# types 层设计：L2-06

本 L2 不在该层新增源码产物。

原因：`InferenceRequest`、`ActionChunk`、`ObservationSnapshot`、`SafetyResult` 和 `RuntimeMetrics` 是跨 L2 公共数据语言，分别由 L2-01/02/03/04 的契约定义；ControlLoop 只消费和更新其约定的 runtime 状态，不能复制类型。

验收如何确认：mypy/pytest 或 import 测试确认 `ControlLoop` 只依赖既有公共类型；chunk 为 `(N,16)`、raw action 为 `(16,)`。

层职责：数据结构与规格；依赖方向仅允许被下游使用。本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。Pi0.5 参考：`shared_buffer.py:22-153`。副作用：无。

# runtime 层设计：L2-06

## 目标源码

`src/model_deploy/act/runtime/control_loop.py`

层职责：按时间、状态、队列和失败条件组织已在 RAM 中的能力；可依赖 types/config/service，不能依赖 UI。

## class 与函数设计

`ControlLoop` 持有 `active_chunk`、`cursor`、`request_pending`、`request_id`、`last_safe_action` 和 L2-06 status/metrics。它的 `tick()` 依次收 result、验证/激活、按 prefetch 投 request、直取动作、安全交接、发布或 fallback、记录指标。

模块级 `validate_chunk_for_cursor(chunk, now, spec) -> str | None` 是纯计算函数，检查二维 `(N,16)`、有限值、age、cursor 范围。`_collect_latest_chunk()`、`_take_cursor_action()` 是内部状态更新函数；`_maybe_submit_inference()`、`_emit_fallback()`、`tick()` 是编排函数。

输入：clock、DeployConfig、SharedBuffer queues/latest observation、SafetyGuard、publisher port。输出：queue 写入、L2-05 调用、`RuntimeMetrics/status`。副作用：只修改自身状态和 SharedBuffer runtime 记录；不做 ROS publish。

Pi0.5 参考：`control_loop.py:111-222,316-333`；刻意不带入 `blend_*`、pending/next chunk 融合。验收覆盖：unit mock 时序、非法 chunk discard、无 observation、prefetch、safety reject、fallback/metrics。

本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

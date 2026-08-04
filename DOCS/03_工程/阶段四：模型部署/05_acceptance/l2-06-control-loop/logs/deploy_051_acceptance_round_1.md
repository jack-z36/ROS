# 验收反馈：deploy_051 推理通道与运行指标基础 — 第 1 轮

- 验收模式：`direct-local`
- 验收轮次：1 / 3
- 验收 Agent：只读，未修改源码/测试/dispatch/卡片/任务文件/Git 状态
- 验收时间：2026-07-13（工作树 mtime 17:4x–17:5x）

## 结论

**PASS_LOCAL**

## 检查清单结果（卡片 §3 PASS_LOCAL）

| 检查项 | 结果 | 证据 |
|---|---|---|
| C1/C2 frozen、success/error XOR、时间/id/error 边界完整 | PASS | `inference_channel.py` C1 `InferenceRequest`(frozen, request_id>0/submitted_at_s≥0/trigger_cursor≥0 校验)；C2 `InferenceResult`(frozen, `__post_init__` 强制 `is_success==has_error` 异或、failure 要求非空 error_type/error_message、四时间戳非负且有序、error() 工厂截断 512)；`test_inference_channel.py::TestInferenceRequest/TestInferenceResult` 全覆盖 |
| LatestQueue 无参且 CAPACITY=1；replace、timeout、spurious wakeup、close、重复 close、closed put/take 全通过 | PASS | `__init__(self)` 无参、`CAPACITY=1`；`test_capacity_one_evicts`(replace)、`test_bounded_timeout_returns_none`(timeout)、`test_negative_timeout_rejected`、`test_spurious_wakeup_does_not_lose_item`(spurious)、`test_close_clears_and_counts`/`test_close_is_idempotent`(close/幂等)、`test_put_after_close_raises`(closed put)、`test_take_after_close_returns_none_no_residual`(closed take 不交付残留)；`while` 循环处理 spurious wakeup，closed 后一律返 `None` |
| 正常 drop 与 shutdown clear 分开计数 | PASS | 队列层：`put_latest` 返回正常淘汰数、`close` 返回 shutdown 清除数（`test_drop_sources_are_distinct_return_channels`）；metrics 层：`request_queue_drop_count`/`result_queue_drop_count`/`shutdown_queue_cleared_count` 为独立计数器（`test_normal_drop_vs_shutdown_clear_separate`） |
| RuntimeMetrics 线程安全，snapshot 不暴露 mutable dict/reference | PASS | `record_event` 在 `threading.Lock` 内原子更新；`snapshot()` 在锁内构造全新 `RuntimeMetricsSnapshot`，`publish_outcome_counts` → `tuple(sorted(items))`、`last_safety_finding_codes` → `tuple`；frozen dataclass；`test_snapshot_exposes_no_mutable_reference`/`test_concurrent_record_event_is_safe`/`test_concurrent_snapshot_no_race` 通过 |
| facade additive、observation_buffer import 不回归、types 无 runtime 污染 | PASS | `__init__.py` 仅增量导出 5 个 symbol，未删除/遮蔽 `observation_buffer`；全 runtime 目录 54 passed（含既有 `test_observation_buffer.py`）；types 层污染扫描无匹配 |
| 无超出 L3 允许范围的修改 | PASS | 禁止模式扫描无 `SafetyGuard`/`ActionPublisher`/`create_timer`/`create_publisher`/`rclpy`/`torch.load`/`import yaml`；design doc 改动均为 L2-06 设计撰写（见下方 scope 说明） |

## 必跑命令与输出

### CMD1 — 目标单测（卡片 §2 / L3 §12）
```
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py -v
```
**结果：40 passed in 0.36s（EXIT=0）**
（TestInferenceRequest ×5、TestInferenceResult ×9、TestLatestQueueBasics ×6、TestLatestQueueClose ×5、TestLatestQueueTimeoutWakeup ×3、TestSnapshot ×4、TestRecordEvent ×7、TestDropClassification ×1、TestConcurrency ×2）

### CMD2 — types 层污染扫描（卡片 §2，用 grep 替代 rg）
```
grep -rn "InferenceRequest|InferenceResult|LatestQueue|RuntimeMetricsSnapshot" src/model_deploy/act/types
```
**结果：无匹配（GREP_EXIT=1）→ PASS（types 层未被污染）**

### CMD3 — 全 runtime 目录回归（确认 observation_buffer 不回归）
```
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/runtime/ -q
```
**结果：54 passed in 0.38s（EXIT=0）**（40 新增 + 14 既有，含 observation_buffer 测试）

### CMD4 — 禁止模式 scope 扫描
```
grep -rn "SafetyGuard|ActionPublisher|create_timer|create_publisher|rclpy|torch.load|import yaml" src/model_deploy/act/runtime
```
**结果：无匹配（GREP_EXIT=1）→ PASS（未引入 policy/safety/ROS/torch/yaml 依赖）**

## Scope 合理性核查（任务特别说明）

- **mtime 顺序**：runtime `.py` 文件 mtime 为 `17:49:59`(inference_channel)、`17:53:57`(runtime_metrics)、`17:54:06`(__init__.py)；L2-06 `agent_context/*.md` 与 `.html` 的 mtime 为 `15:42:37`–`16:59:51`。runtime 代码**晚于**设计文档，设计文档属于更早的 L2-06 设计撰写，不属 deploy_051 可实施范围。
- **设计文档改动仅为 prose**：`git status` 显示 `agent_context/` 12 个 `.md` 与 1 个 `.html` 为已修改（M）。diff 中出现的 `class InferenceRequest:`/`class InferenceResult:` 位于 `03_ACT微元设计与协作.md` §4「runtime 内部数据契约」下的 ```` ```python ```` markdown 代码块，是**接口规格/设计契约**，非可运行实现；实际实现只存在于未跟踪（??）的 runtime `.py` 文件中。
- **未将设计文档改动计入 deploy_051 失败**：依任务说明，预存设计文档改动不属本 L3 范围，不因此判定 FAIL。
- **现存未跟踪产物**（均属 L3 §10 允许范围）：`inference_channel.py`、`runtime_metrics.py`、`__init__.py`(M)、`test_inference_channel.py`、`test_runtime_metrics.py`，以及 `03_tasks/` 下 cards/task/dispatch 与 `l2-06-control-loop.yaml`（属 L2-06 调度元数据的既有落点，非本 Agent 写入）。

## 未验证项（延后，非本 L3 范围，不阻断）

- 真实跨线程 worker/ControlLoop 端到端 × shutdown 收敛：需 deploy_052/053 落地后由 `04_L2验收机制.md` 的 `LATEST_QUEUE_CLOSE`/`WORKER_SHUTDOWN` Gate 标签覆盖（与 L3 §18.7 一致）。
- 上游 P0-01～P0-10 接缝：deploy_051 未触碰，仍处 `blocked` 态，属上游责任，不影响本通道/metrics 单测结论。
- `RuntimeMetrics.runtime_status` 单 writer 优先级仲裁：属 deploy_053（A4/A5），本 L3 仅存值。

## 对执行子 Agent 的修正请求

无。本轮所有检查项通过，未发现需修正项。

## 归档提示（交由主 Agent 执行）

结论为 **PASS_LOCAL**：必须由 **主 Agent**（非本验收 Agent）将 L3 任务文件从
`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_051_推理通道与运行指标基础.md`
同步移动到
`DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/`。
本验收 Agent 不执行任何 Git 操作、不修改源码/测试/dispatch/卡片/任务文件。

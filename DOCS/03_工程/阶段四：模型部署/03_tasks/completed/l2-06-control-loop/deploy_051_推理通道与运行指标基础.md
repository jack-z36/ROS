# L3 微元改造任务：推理通道与运行指标基础

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
L3 编号：deploy_051
改造类型：source-adaptation
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_051_推理通道与运行指标基础.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_051_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
真机风险等级：none
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 上游放行
> 本任务定义已经生成，但 dispatch 保持 blocked。开始正式实现前，必须确认 L2-06 设计中 P0-01～P0-10 的 owner 与修复路径已被接受；本任务不得借机修改 L2-01～05 来代偿接缝。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_051
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_051_推理通道与运行指标基础.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G04]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_051_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 1
  parallel_group: l2-06-control-loop-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_052, deploy_053, deploy_054, deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/runtime/inference_channel.py
      - src/model_deploy/act/runtime/runtime_metrics.py
      - src/model_deploy/act/runtime/__init__.py
      - src/model_deploy/act/tests/runtime/test_inference_channel.py
      - src/model_deploy/act/tests/runtime/test_runtime_metrics.py
    modules:
      - model_deploy.act.runtime.inference_channel
      - model_deploy.act.runtime.runtime_metrics
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: blocked
~~~

### Agent 执行 / 验收边界

- 执行 Agent 只实现 A1/A2 与 C1-C12；不得提前实现 worker、ControlLoop 或 ROS Node。
- 验收 Agent 只读任务、diff、测试输出和边界扫描。
- 最多 3 轮执行-验收迭代。

## 3. 本次唯一目标

实现 L2-06 自有的 frozen request/result 信封、容量固定为 1 且可关闭唤醒的 LatestQueue，以及线程安全 RuntimeMetrics/immutable snapshot，为后续 worker 和 ControlLoop 提供稳定 RAM 基础。

## 4. 所属 L2 边界与设计来源

### L2 负责

- 拥有 request/result correlation、latest-only queue、运行指标和 shutdown channel 语义。
- 保持 ActionChunk 纯净，只在 L2-06 信封中保存 id、时间和 error。

### L2 不负责

- 不修改 ObservationSnapshot、ActionChunk 或 L2-01～05 公共业务类型。
- 不加载 policy、不调用 safety、不发布 ROS topic。

### 本 L3 在 L2 中的位置

本任务交付 deploy_052～055 共同依赖的并发通道和 metrics 基础；后续任务只能消费这些 public runtime 对象，不得另建第二套 queue/metrics。

### 必读 L2 设计文档

1. 目标 L2 agent_context/00_INDEX.md、01_L2功能边界.md、03_ACT微元设计与协作.md、03a_功能微元总览与组织结构.md。
2. 目标 L2 agent_context/04_L2验收机制.md、06_types层设计.md、10_runtime层设计.md。
3. L1 边界与协作 Markdown、ACT 代码树落点约束。

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层类型 | 已有能力 | 与 ACT 差距 | 复用判断 |
|---|---|---|---|---|---|
| InferenceRequest / LatestQueue | deploy/runtime/shared_buffer.py:62-102 | 数据 / 内部状态更新函数 | latest-only request channel | 无 close/唤醒/稳定 drop 合同，旧 ownership 混入 SharedBuffer | 结构复用 |
| RuntimeMetrics | 同文件 :106-153 | 数据 / 内部状态更新函数 | counters 与 latency | mutable snapshot、字段不足、线程与 shutdown 语义不完整 | 结构复用 |
| SharedBuffer | 同文件 :156-242 | class | 聚合 observation/queue/metrics | 会吞并 L2-02 observation ownership | 不复用 |

### 必须保留的源码启发

- latest-only 低延迟通道和 worker/tick 共享指标。

### 禁止照搬的源码行为

- 不复制 observation slot，不把 request/time/cursor 写入 ActionChunk，不使用 busy polling。

### 已知风险

- closed queue 若仍交付残留项或 worker 无法被唤醒，会导致 shutdown 悬挂。
- frozen dataclass 内部如暴露 mutable dict/array，UI snapshot 仍可能被并发篡改。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 在 runtime/inference_channel.py 实现 C1、C2、A1、C5、C8-C10。
- 在 runtime/runtime_metrics.py 实现 A2、C4、C6、C11-C12。
- 增量更新 runtime facade，只新增本任务已实现的 public symbol，保留 observation_buffer 路径。
- 测试 success/error XOR、时间/id、capacity=1、close/timeout/spurious wakeup、drop 分类、metrics lock 与 immutable snapshot。

### 本次不做

- 不实现 A3-A5、B1-B12、ControlLoop state、ROS metrics publisher。
- 不修改 config 容量字段；只固定 A1 public CAPACITY=1。

### 明确禁止修改

- src/model_deploy/act/types/、config/、repo/、service/、ui/。
- Pi0.5 参考源码、其他 L2 task/card/dispatch。

### 函数 / class 策略

A1/A2 保存跨线程 mutable state，必须是 class；C1/C2/C4 为 frozen 数据；C8-C11 为状态更新，C12 为纯 RAM snapshot 计算。

## 7. 六层产物落点

| 层 | 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否 | — | 不新增公共 runtime 类型 |
| config | 否 | — | 只读 RuntimeConfig 合同 |
| repo | 否 | — | 不做资源 I/O |
| service | 否 | — | 不调用业务服务 |
| runtime | 是 | src/model_deploy/act/runtime/inference_channel.py；runtime_metrics.py；__init__.py | A1/A2、C1-C12 |
| ui | 否 | — | 不接 ROS |
| tests | 是 | src/model_deploy/act/tests/runtime/test_inference_channel.py；test_runtime_metrics.py | G04 unit |
| acceptance | 否 | — | 由 deploy_055 汇总 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| 06_types层设计.md | 证明 C1-C7 不进入公共 types |
| 10_runtime层设计.md | §2 inference channel、§3 metrics |
| 07/08/09/11 | 无新增产物，边界扫描确认 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| runtime/inference_channel.py | C1/C2 | 数据 | request、snapshot、时间、chunk/error | frozen envelope | 无 | RUNTIME_ENVELOPE_CONTRACT |
| 同上 | A1/C5/C8-C10 | class/数据/内部状态更新 | item、timeout、close | item/None/drop count | Condition 唤醒 | LATEST_QUEUE_CLOSE |
| runtime/runtime_metrics.py | A2/C4/C6/C11 | class/数据/内部状态更新 | event/value | guarded metrics | RAM lock | RUNTIME_REASON_PRESERVED |
| 同上 | C12 | 计算函数 | guarded state | immutable C4 | 无 | snapshot isolation |

## 9. 实施步骤

1. 先写 envelope、queue close/timeout 和 metrics snapshot 的失败测试。
2. 实现 C1/C2/A1，再实现 A2/C4；所有异常消息和关闭语义固定。
3. 增量导出 public symbols，执行 unit、import 与 types 污染扫描。

## 10. 允许修改

- src/model_deploy/act/runtime/inference_channel.py
- src/model_deploy/act/runtime/runtime_metrics.py
- src/model_deploy/act/runtime/__init__.py
- src/model_deploy/act/tests/runtime/test_inference_channel.py
- src/model_deploy/act/tests/runtime/test_runtime_metrics.py

### 本次产物落点

| 产物 | 落点路径 | 所属层 |
|---|---|---|
| 推理信封与 channel | src/model_deploy/act/runtime/inference_channel.py | runtime |
| 运行指标 | src/model_deploy/act/runtime/runtime_metrics.py | runtime |
| 单测 | src/model_deploy/act/tests/runtime/test_inference_channel.py；test_runtime_metrics.py | tests/runtime |

## 11. 禁止修改

- L2-01～05 源码与公共合同。
- src/model_deploy/act/runtime/observation_buffer.py。
- launch/config_files/、ROS graph、硬件路径。

## 12. 验证方式

### 自动化验收命令

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py -v
~~~

~~~bash
! rg -n "InferenceRequest|InferenceResult|LatestQueue|RuntimeMetricsSnapshot" \
  src/model_deploy/act/types
~~~

### 分层验证

| 层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit/import | 是 | C1-C12、facade | 全 PASS，无 mutable 泄漏 |
| dry-run/fake-policy | 否 | 后续任务 | 不适用 |
| real-policy/shadow/robot | 否 | 无外部 I/O | 不适用 |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs/deploy_051/

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | G04：RUNTIME_ENVELOPE_CONTRACT、LATEST_QUEUE_CLOSE、metrics snapshot |
| 本 L3 提供的能力 | worker/tick 可共享的有界通道与可观测状态 |
| 后续补齐 | deploy_052 worker、deploy_053 ControlLoop、deploy_054 UI、deploy_055 全 Gate |

## 13. 必读上下文

- 阶段四工作流、L3 模板、ACT 落点约束。
- 目标 L2 agent_context/00-11，重点 03a、04、10。
- Pi0.5 shared_buffer.py 只读参考。
- 当前 ObservationSnapshot、ActionChunk、runtime facade 与 observation_buffer 源码。

## 14. 执行要求

- 执行前核对 filename/body/dispatch 均为 deploy_051，group 为 l2-06-control-loop。
- dispatch_status 在上游 P0 owner/路径确认前保持 blocked；主 Agent 解锁后方可执行。
- 采用红测试→最小实现→验证；不运行 Git 操作。

## 15. 成功标准

- [x] C1/C2 success-error XOR、时间、id 和 bounded error 合同完整。
- [x] LatestQueue 无参、CAPACITY=1，replace/drop/timeout/close/幂等/唤醒全部通过。
- [x] 正常淘汰与 shutdown clear 分开计数。
- [x] RuntimeMetrics 并发更新安全，C4 不暴露 mutable 引用。
- [x] runtime facade 增量导出且 observation_buffer import 不回归。
- [x] types 层无 L2-06 runtime 类型污染。
- [x] 已登记实际命令、结果与未验证项。

## 16. 回滚方式

删除本任务新增的两个 runtime 模块和两个测试文件，恢复 runtime/__init__.py 到执行前版本；本任务没有外部副作用。

## 17. 完成后交接

执行摘要必须列出 envelope/queue/metrics 实现、测试节点、drop/close 证据、facade 兼容性、未做事项和 deploy_052 解锁条件；执行 Agent 不提交、不推送、不改验收结论。

## 18. 执行摘要（deploy_051）

> 解锁依据：dispatch_status 为 `blocked`（上游 P0-01～P0-10 未闭合），主 Agent 已明确要求先执行 l2-06 的前两个微元（deploy_051 / deploy_052）。本 Agent 据此视为已获解锁授权，仅实现 deploy_051 范围内产物，未修改 L2-01～05 代偿接缝。

### 18.1 读取的设计与源码

- L3 任务文件、AGENTS.md、L3 执行加载规则、Agent 编程执行原则、架构边界与机械约束原则。
- L2-06 agent_context：`00_INDEX` / `01_L2功能边界` / `03_ACT微元设计与协作` / `03a_功能微元总览与组织结构` / `04_L2验收机制` / `06_types层设计` / `10_runtime层设计`。
- Pi0.5 只读参考：`src/model_deploy/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py`（LatestQueue / RuntimeMetrics 结构复用，未复制字段、未复制 observation slot、未复制 busy polling）。
- 既有：`src/model_deploy/act/runtime/__init__.py`、`observation_buffer.py`、`types/observation.py`、`types/action_chunk.py`。

### 18.2 修改文件

| 文件 | 动作 | 新增符号 |
|---|---|---|
| `src/model_deploy/act/runtime/inference_channel.py` | 新增 | `InferenceRequest`(C1)、`InferenceResult`(C2)、`LatestQueue`(A1/C5/C8-C10)、`_QUEUE_CLOSED_MSG` |
| `src/model_deploy/act/runtime/runtime_metrics.py` | 新增 | `RuntimeMetrics`(A2/C6/C11)、`RuntimeMetricsSnapshot`(C4/C12)、事件 handler 表 |
| `src/model_deploy/act/runtime/__init__.py` | 增量导出 | 上述 5 个 public symbol；保留 `observation_buffer` 子模块可导入路径 |
| `src/model_deploy/act/tests/runtime/test_inference_channel.py` | 新增 | 信封 + LatestQueue 单测 |
| `src/model_deploy/act/tests/runtime/test_runtime_metrics.py` | 新增 | metrics lock + immutable snapshot 单测 |

### 18.3 实现的微元要点

- C1/C2：frozen dataclass；`__post_init__` 强制 success/error XOR、时间单调序、id 正整、error 截断 512；提供 `success` / `error` 工厂（`error` 只保留 `type(exc).__name__` 与 bounded message，不存异常对象）。
- A1/C5/C8-C10：`LatestQueue` 无参构造、`CAPACITY=1`、`deque(maxlen=1)` + `Condition` + `_closed` + `_dropped_count`；`put_latest` 返回淘汰数并在 closed 后抛 `RuntimeError("queue is closed")`；`take_latest` 支持 `None` 阻塞 / `0` 非阻塞 / 正数有界等待（monotonic deadline，`while` 处理 spurious wakeup），closed 后不再交付残留项；`close` 幂等、`notify_all`、返回清除数并计入 dropped。
- A2/C4/C6/C11-C12：`RuntimeMetrics(clock)` 持 `Lock` + 状态 dict；`record_event(event, *, value)` 在锁内按事件表原子更新（计数累加 / gauge 设置 / publish outcome 计数 / 安全 findings 元组）；`snapshot()` 在锁内构造全新 `RuntimeMetricsSnapshot`，`publish_outcome_counts` 转 `tuple(sorted items)`、`last_safety_finding_codes` 转 `tuple`，不暴露可变引用。

### 18.4 验证命令与结果

```bash
# 1) 单元 / import（direct-local）
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py -v
# => 40 passed

# 2) 全 runtime 目录回归（确认 observation_buffer 不回归）
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/runtime/ -q
# => 54 passed（40 新增 + 14 既有）

# 3) types 层污染扫描（必须无输出）
rg -n "InferenceRequest|InferenceResult|LatestQueue|RuntimeMetricsSnapshot" \
  src/model_deploy/act/types
# => 无匹配（PASS）

# 4) facade 兼容 import 检查
PYTHONPATH=src python3 -c "import model_deploy.act.runtime as rt; \
  import model_deploy.act.runtime.observation_buffer as ob; \
  from model_deploy.act.runtime import (InferenceRequest, InferenceResult, \
  LatestQueue, RuntimeMetrics, RuntimeMetricsSnapshot); \
  from model_deploy.act.runtime.observation_buffer import ObservationBuffer; \
  print('IMPORT CHECK OK')"
# => IMPORT CHECK OK
```

### 18.5 drop / close 证据

- 正常淘汰：`put_latest` 在容量满时返回淘汰数 1（测试 `test_capacity_one_evicts`、`test_drop_sources_are_distinct_return_channels`）。
- shutdown clear：`close()` 返回清除的待处理项数（测试 `test_close_clears_and_counts`），且幂等重复调用返回 0（`test_close_is_idempotent`）。
- 分类：`request_queue_drop_count` 与 `shutdown_queue_cleared_count` 为独立 metrics 计数器，互不合并（测试 `TestDropClassification`）。
- 唤醒安全：closed 后 `take_latest` 一律返回 `None` 且交付残留项被拒（`test_take_after_close_returns_none_no_residual`）；阻塞 `take_latest(None)` 被 put / close 唤醒（`test_blocking_take_receives_item`）；spurious wakeup（无 item 的 `notify_all`）不会让阻塞 waiter 提前返回（`test_spurious_wakeup_does_not_lose_item`）。

### 18.6 facade 兼容性

`runtime/__init__.py` 仅增量新增 5 个 public symbol，未删除/遮蔽 `observation_buffer` 子模块；`model_deploy.act.runtime.observation_buffer.ObservationBuffer` 仍可正常导入，既有 `test_observation_buffer.py` 全部通过。

### 18.7 未验证项

- 真实跨线程 worker/ControlLoop 端到端 × shutdown 收敛：需 deploy_052（InferenceWorker）/ deploy_053（ControlLoop）落地后，由 `04_L2验收机制.md` 的 `LATEST_QUEUE_CLOSE` / `WORKER_SHUTDOWN` 等 Gate 标签覆盖；本 L3 仅完成 channel/metrics 单测与并发不变量。
- 上游 P0-01～P0-10 接缝：本 L3 未触碰，仍处 `blocked` 态；后续 Gate 是否 FAIL 取决于上游 owner 修复。
- `RuntimeMetrics` 的 `runtime_status` 单 writer 优先级（SHUTDOWN_TIMEOUT > … > 本 tick 状态）由调用方（A4/A5）保证，metrics 仅存值；本 L3 未实现该优先级仲裁（属 deploy_053 范围）。
- 未运行 `l2_06_verify.sh` 及相关 fake fixture：脚本/fixture 尚未存在（见 `04_L2验收机制.md §4`），本 L3 范围为 local unit，不适用。

### 18.8 本次明确未做

- 未实现 A3 `InferenceWorker`、A4 `ControlLoop`、A5 `ActDeployNode`、C3 `FallbackReason`、C7/C13-C26（属 deploy_052～055）。
- 未修改 `types/` / `config/` / `repo/` / `service/` / `ui/` / `observation_buffer.py`，未代偿 L2-01～05 上游接缝。
- 未运行任何 Git 命令，未改动 dispatch 索引或验收卡片结论。

### 18.9 deploy_052 解锁条件

deploy_052（InferenceWorker + B1/B2 + C22）可立即开始：本 L3 已交付稳定的 `LatestQueue[InferenceRequest]` / `LatestQueue[InferenceResult]`、`InferenceResult.success/error` 工厂、`RuntimeMetrics.record_event` 全部事件接口，以及 `runtime` facade 导出。deploy_052 可直接消费这些 public 对象构造 worker 的 request/result 写入与 metrics 记录，无需等待上游 P0 闭合（P0 接缝属 L2-01～05，不在本 L2-06 通道范围内）。但注意：单个 L3 全量 `BASELINE_SOURCE_SUITE` 与主 Gate 仍受 P0 未闭合影响，属上游责任。

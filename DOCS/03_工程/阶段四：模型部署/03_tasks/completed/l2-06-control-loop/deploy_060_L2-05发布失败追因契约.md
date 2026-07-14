# L3 微元改造任务：L2-05 发布失败追因契约

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
接口 owner：l2-05-action-publisher 单步 Action 到执行器 Topic 适配发送闭环
L3 编号：deploy_060
改造类型：cross-l2-interface-remediation
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_060_L2-05发布失败追因契约.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_060_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：direct-local
辅助验收模式：[downstream-l2]
本地验收是否必须：true
真机风险等级：dry-run-only
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 用户授权的跨 L2 修复
> 本任务在 L2-05 owner 内闭合 P0-10：稳定非法输入异常和 publish failure provenance。它不改变 command gate 的单一所有权，不自动连接 ROS graph/driver，不修改冻结的 deploy_051/052。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_060
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_060_L2-05发布失败追因契约.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G03, G07]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_060_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [downstream-l2]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 3
  parallel_group: l2-06-control-loop-p3-owner-remediation
  depends_on: [deploy_051, deploy_052]
  must_run_after: [deploy_051, deploy_052]
  can_run_parallel_with: []
  blocks: [deploy_053, deploy_054, deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/types/action_publish.py
      - src/model_deploy/act/types/__init__.py
      - src/model_deploy/act/ui/action_publisher.py
      - src/model_deploy/act/ui/__init__.py
      - src/model_deploy/act/tests/types/test_action_publish.py
      - src/model_deploy/act/tests/ui/test_action_publisher.py
      - src/model_deploy/act/tests/ui/test_action_publisher_messages.py
      - src/model_deploy/act/tests/integration/test_l2_05_gate.py
      - DOCS/03_工程/阶段四：模型部署/02_implement/l2-05-action-publisher_单步Action到执行器Topic适配发送闭环
    modules:
      - model_deploy.act.types.action_publish
      - model_deploy.act.ui.action_publisher
    config_keys: [command_output, topics.command]
    runtime_modes: [local-fake-node, ros-dry-run]
    hardware_paths:
      - /act/policy_action
      - /act/command/status
      - /act/command/*
  robot_risk: dry-run-only
  dispatch_status: blocked
~~~

## 3. 本次唯一目标

让 ActionPublishResult 对六种 PublishOutcome 给出可机械校验的 reason、failure_stage、failed_topic 事实，使 L2-06 只需保存并核验 L2-05 返回值即可 fail-closed，而不从 outcome 猜内部失败位置。

## 4. 冻结 public seam

~~~python
result = action_publisher.publish(request: ActionPublishRequest)
~~~

ActionPublishResult 新增并冻结：

~~~text
failure_stage:
  Literal["safety", "policy_publish", "command_build", "command_publish"] | None
failed_topic:
  str | None
~~~

- PUBLISHED、OBSERVED、BLOCKED：failure_stage/failed_topic 为 None；BLOCKED 保留 permit reason。
- REJECTED：reason_code 非空，failure_stage="safety"，failed_topic=None。
- FAILED/PARTIAL：reason_code 非空，failure_stage 精确；具体 publish I/O 失败时 failed_topic 精确到 public topic/label。
- request_id/action_id、command_output_enabled、command_permitted echo 继续与原 request 一致。
- /act/command/status 仍只由 L2-05 写；status publisher 本身失败时抛 public ActionPublishIoError(label="status")，不能伪造已发布 status result。

## 5. 当前源码断点

| 断点 | 当前事实 | 修复判据 |
|---|---|---|
| invalid input | 多处使用不存在的 type(...).__r | 全部改为稳定 type repr，异常类型/消息有测试 |
| result schema | 没有 failure_stage/failed_topic | frozen fields + outcome-specific invariant |
| rejected/failed | 多个分支 reason_code=None | 所有负向 outcome 保留稳定非空 reason |
| I/O provenance | ActionPublishIoError 有 label，但 publish result 丢弃 | label 映射为 stage/topic，停止剩余 command |
| design | L2-05 文档未完整表达 L2-06 reducer 所需事实 | HTML 与 agent_context 同步六 outcome 矩阵 |

## 6. 实施步骤

1. 先写非法 request/payload/result、六 outcome invariant、每个 policy/command publish 故障点、status publisher failure 红测试。
2. 修复 action_publish.py 中全部 __r 错误；新增 typed fields 和严格 __post_init__ 矩阵，避免无效 provenance 对象被构造。
3. 修改 ActionPublisher 的 result builder/各分支，逐条保留 stage/topic/reason；command 失败后不继续后续 command。
4. 保持 policy→gate→command→status 的既定顺序、single writer 和 disabled/deny semantics；不把 L2-06 fallback/safety 逻辑搬入 publisher。
5. 更新 L2-05 agent_context 的 types/service/ui/验收矩阵及协作边界，并同步 HTML。
6. 跑 local FakeNode 全矩阵和 L2-05 Gate；ROS/driver 不可用不能替代本地 PASS。

## 7. 允许修改

- src/model_deploy/act/types/action_publish.py
- src/model_deploy/act/types/__init__.py
- src/model_deploy/act/ui/action_publisher.py
- src/model_deploy/act/ui/__init__.py
- src/model_deploy/act/tests/types/test_action_publish.py
- src/model_deploy/act/tests/ui/test_action_publisher.py
- src/model_deploy/act/tests/ui/test_action_publisher_messages.py
- src/model_deploy/act/tests/integration/test_l2_05_gate.py
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-05-action-publisher_单步Action到执行器Topic适配发送闭环/agent_context/
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-05-action-publisher_单步Action到执行器Topic适配发送闭环/L2架构交互可视化.html

## 8. 禁止修改

- deploy_051/052 的任何冻结产物。
- L2-04 SafetyGuard 结果、L2-06 reducer/metrics/control loop。
- command-output startup switch 的 owner、permit fail-open、第二个 status writer。
- 通过 outcome 反推 stage；每个 stage 必须在失败发生点显式记录。
- 连接真实 driver、发送真实 command 或把 FakeNode 写成硬件 PASS。

## 9. 验证方式

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_action_publish.py \
  src/model_deploy/act/tests/ui/test_action_publisher_messages.py \
  src/model_deploy/act/tests/ui/test_action_publisher.py \
  src/model_deploy/act/tests/integration/test_l2_05_gate.py -v
~~~

~~~bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-05-action-publisher_单步Action到执行器Topic适配发送闭环'
~~~

~~~bash
! rg -n "__r\\b|reason_code=None.*(REJECTED|PARTIAL|FAILED)" \
  src/model_deploy/act/types/action_publish.py \
  src/model_deploy/act/ui/action_publisher.py
~~~

## 10. 成功标准

- [x] 所有非法输入稳定抛预期 TypeError/ValueError，不再触发 AttributeError(__r)。
- [x] ActionPublishResult 的 stage/topic/reason 矩阵在构造层不可违反。
- [x] 六种 outcome 与 request echo 完整测试。
- [x] policy/status/四路 command 每个失败点都有精确 provenance；失败后无额外 command 泄漏。
- [x] /act/command/status 仍为 L2-05 单 writer，status write failure 不伪造 result。
- [x] L2-05 HTML 与 agent_context 同步 public 字段、顺序、single-writer 和失败矩阵。
- [x] local FakeNode 必跑通过；ROS/硬件未自动执行。
- [x] 未改动冻结的 deploy_051/052。

## 11. 回滚与交接

回滚必须同时撤销 result schema、publisher 分支、测试和设计投影，不能留下新旧混合字段。交接必须附六 outcome 表、各故障点 result/exception、public import、single-writer 扫描和 deploy_053 可直接归约的 provenance 样例。

## 18. 执行摘要（sub-agent 回填）

### 18.1 变更文件

| 文件 | 改动 |
|---|---|
| `src/model_deploy/act/types/action_publish.py` | 修复 4 处 `type(x).__r` → `type(x)!r`；新增 `PublishFailureStage` 类型别名与 `_PUBLISH_FAILURE_STAGES` / `_PUBLISH_FAILURE_TOPIC_REQUIRED` 常量；`ActionPublishResult` 新增 `failure_stage: Optional[PublishFailureStage]`、`failed_topic: Optional[str]` 字段；在 `__post_init__` 增加六 outcome 发布失败追因矩阵（stage/topic/reason 不变式）。 |
| `src/model_deploy/act/types/__init__.py` | 导出 `PublishFailureStage`。 |
| `src/model_deploy/act/ui/action_publisher.py` | `_build_publish_result` / `_finalize` 透传 `failure_stage` / `failed_topic`；新增 `_topic_for_label` 解析 public topic；每个失败分支写入精确 provenance（SAFETY_REJECTED / PAYLOAD_BUILD_ERROR / MESSAGE_BUILD_ERROR / POLICY_PUBLISH_IO_ERROR / COMMAND_PUBLISH_IO_ERROR，含精确 `failed_topic`）；command 循环捕获 `ActionPublishIoError.label` 后中断并归因；status JSON 增加 `failure_stage` / `failed_topic` 字段。 |
| `src/model_deploy/act/tests/types/test_action_publish.py` | 调整既有 `REJECTED` / `PARTIAL` 构造以携带 `failure_stage`；新增 `TestPublishProvenance` 六 outcome 追因矩阵红/绿测试。 |
| `src/model_deploy/act/tests/ui/test_action_publisher.py` | 新增 `TestPublishProvenanceG`：覆盖 REJECTED(safety)、OBSERVED/BLOCKED(无 provenance)、policy I/O 失败、command PARTIAL/FAILED 精确 topic、status 失败不伪造、status `ActionPublishIoError(label="status")`。 |
| `.../l2-05-.../agent_context/06_types层设计.md` | C6 表新增 `failure_stage` / `failed_topic`，§4 增加发布失败追因矩阵。 |
| `.../l2-05-.../agent_context/11_ui层设计.md` | 新增 §8.1 发布失败追因矩阵；C17 明确 status 单 writer 与失败不伪造；C20 JSON 示例加入新字段；§16 验收覆盖补 provenance。 |
| `.../l2-05-.../L2架构交互可视化.html` | C6 表追加 `failure_stage` / `failed_topic` 两行（注：该表其余字段为历史快照，未在本 L3 全面刷新）。 |

### 18.2 实现的 provenance 契约（闭合 P0-10）

`ActionPublishResult` 新增两个被 L2-06 直接归约的事实字段，使 L2-06 仅保存并核验返回值即可 fail-closed：

- `failure_stage: Literal["safety","policy_publish","command_build","command_publish"] | None`
- `failed_topic: str | None`

六 outcome 矩阵（构造层强制，不可违反）：

| 故障点 | outcome | reason_code | failure_stage | failed_topic |
|---|---|---|---|---|
| B1 安全 REJECTED | REJECTED | SAFETY_REJECTED | safety | None |
| B1 其它异常 | FAILED | PAYLOAD_BUILD_ERROR | command_build | None |
| B2 消息构建异常 | FAILED | MESSAGE_BUILD_ERROR | command_build | None |
| C17 policy I/O | FAILED | POLICY_PUBLISH_IO_ERROR | policy_publish | /act/policy_action |
| command I/O（count>0 后） | PARTIAL | COMMAND_PUBLISH_IO_ERROR | command_publish | 失败 command 的 public topic |
| command I/O（首路 count=0） | FAILED | COMMAND_PUBLISH_IO_ERROR | command_publish | 失败 command 的 public topic |
| command 不允许 | OBSERVED/BLOCKED | COMMAND_OUTPUT_DISABLED / permit.reason_code | None | None |
| 全成功 | PUBLISHED | None | None | None |

P0-10 闭合点：稳定非法输入异常（消除 `__r` AttributeError）+ publish failure provenance（stage/topic）使 L2-06 可机械归约发布失败，不再从 outcome 猜测。

### 18.3 验证命令与结果

```bash
# 1) L3 指定验证集
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_action_publish.py \
  src/model_deploy/act/tests/ui/test_action_publisher_messages.py \
  src/model_deploy/act/tests/ui/test_action_publisher.py \
  src/model_deploy/act/tests/integration/test_l2_05_gate.py -q
# => 129 passed

# 2)  broader regression
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
# => 743 passed, 1 skipped（2 warnings 来自 runtime 层 test_inference_worker 既有线程告警，与本 L3 无关）

# 3) __r / 空 reason_code 扫描（L3 §9）
rg -n "__r\b|reason_code=None.*(REJECTED|PARTIAL|FAILED)" \
  src/model_deploy/act/types/action_publish.py \
  src/model_deploy/act/ui/action_publisher.py
# => 无匹配（clean）
```

### 18.4 未验证 / 需注意项

- **HTML 同步为最小补丁**：`L2架构交互可视化.html` 的 C6 表其余字段（如 `safety_ok` / `sent_to_driver` / `failure_reason`）为历史快照，与本 L3 实际代码字段（`command_output_enabled` / `command_permitted` / `outcome` / `status_published` / `reason_code`）不一致；本 L3 仅追加了 `failure_stage` / `failed_topic` 两行，未对整表做全面刷新（属更大范围的文档清理，超出本 L3 外科手术边界）。
- **验收卡片未运行**：本 sub-agent 不执行 `deploy_060_验收卡片.md`（由验收 sub-agent 在 `direct-local` 下运行）；建议下一步直接跑验收卡片。
- **ROS/硬件未执行**：环境为 dry-run-only，FakeNode 本地全矩阵通过；ROS graph / 真实 driver 未自动执行，符合 `robot_risk: dry-run-only`。
- **冻结产物未触碰**：`deploy_051` / `deploy_052` 及 L2-04 / L2-06 reducer 均未改动。

# L3 微元改造任务：ActionPublisher 门控发布闭环

## 1. 任务定位

阶段：阶段四：模型部署  
L1：ACT 部署程序开发  
所属 L2：`l2-05-action-publisher` 单步 Action 到执行器 Topic 适配发送闭环  
L3 编号：deploy_044  
改造类型：`safety-gate`  
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_044_ActionPublisher门控发布闭环.md`  
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_044_验收卡片.md`  
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/`  
验收模式：`direct-local`  
辅助验收模式：[`env-blocked`, `hardware-blocked`]  
本地验收是否必须：`true`  
真机风险等级：`dry-run-only`  
L2 分支：`feat/model_deploy/l2-05-action-publisher`  
集成分支：`model_deploy`

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_044
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_044_ActionPublisher门控发布闭环.md
  group: l2-05-action-publisher
  branch: feat/model_deploy/l2-05-action-publisher
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher
  acceptance_scenarios: [G09, G10, G11, G12, G13, G14, G15, G16, G17]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_044_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [env-blocked, hardware-blocked]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/logs
  wave: 3
  parallel_group: l2-05-action-publisher-p3
  depends_on: [deploy_041, deploy_042, deploy_043]
  must_run_after: [deploy_042, deploy_043]
  can_run_parallel_with: []
  blocks: [deploy_045]
  conflict_scope:
    files:
      - src/model_deploy/act/ui/action_publisher.py
      - src/model_deploy/act/ui/__init__.py
      - src/model_deploy/act/tests/ui/test_action_publisher.py
    modules:
      - model_deploy.act.ui.action_publisher
    runtime_modes: []
    hardware_paths:
      - /act/command/arm/left_target
      - /act/command/arm/right_target
      - /act/command/gripper/left_target
      - /act/command/gripper/right_target
  robot_risk: dry-run-only
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 Agent 只在 fake publisher 与无真实 driver 环境中验证；不连接真机。
- 验收 Agent 只读，按卡片证据判定；`hardware-blocked` 不能写成真机通过。
- 最多 3 轮执行-验收迭代。

## 3. 本次唯一目标

```text
实现 A1 ActionPublisher 与唯一入口 B3 publish，用 CLI 静态总开关 + CommandPermit 动态许可门控 policy/command/status 写出，并返回真实 C6 事实。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 按 B1 -> B2 -> C15 -> C17 -> C19/C20/C21 完成同步输出闭环。
- 先完整构造候选消息，再发 policy 和经双门控的四路 command，最后根据真实事实构造 status。

### L2 不负责

- 不解析 CLI，不创建 Node/timer/subscription，不聚合原始 gate/deadman/estop，不做 fallback/retry/metrics，不调硬件 SDK。

### 本 L3 在 L2 中的位置

```text
依赖 deploy_041 C1-C7、deploy_042 B1 与 deploy_043 B2；交付 L2-06 可同步调用的唯一 B3 端口。
```

### 必读 L2 设计文档

- L1 边界/协作 Markdown。
- 目标 L2 `agent_context/00_INDEX.md`、`01`、`02`、`03`、`03a`、`04`、`05`、`06_types`、`07_config`、`08_repo`、`09_service`、`10_runtime`、`11_ui`。
- 用户已授权以 Markdown 为准，HTML 不是实现来源。

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 类型 | 已有能力 | 差距 | 复用 |
|---|---|---|---|---|---|
| `_create_publishers` | `deploy/.../pi05_vla_deploy_node.py:145-152` | 数据读写函数 | 长生命 publisher handle | 旧 node 责任过大 | 结构复用 |
| `_control_tick` | 同文件 `:196-212` | 编排函数 | 输出调用 | mode 分支、边构造边发、无 partial result | 参考理解 |
| `CommandMuxNode` | `deploy/.../command_mux_node.py:28-243` | 状态+数据读写 | gate/deadman/status | 原始事实所有权属 L2-06/driver | 只参考 reason code，实现不复用 |

### 必须保留的启发

- 长生命对象持有 publisher；外部写出失败必须可定位且不伪装成功。

### 禁止照搬

- 旧 mode、bridge/mux subscription、raw deadman、timer、JointState、硬件 launch 与全局 metrics。

## 6. ACT 微元与真实实现边界

### 本次允许做

- A1 constructor 通过 node-like factory + topics + C7 创建恰好 6 个 publisher，不创建 subscription/timer/metrics publisher。
- B3 `publish(request)` 是唯一公共业务入口，严格按 `B1 -> B2 -> C15 -> policy -> optional commands -> C19 -> C20/status -> C21` 顺序。
- C15 只读 `config.enabled + permit`，生成 allow/reason。
- C16 每侧独立判断 deadband+最小间隔；C18 只在对应爪成功 publish 后更新 cache。
- C17 统一封装单个 publisher 写出和 label 异常。policy 失败后 command=0；command 首次失败后停止剩余路。
- C19 组织 `REJECTED/OBSERVED/BLOCKED/PUBLISHED/PARTIAL/FAILED`、真实 count/skip/reason；不伪造 driver/hardware 成功。
- C20 根据最终 C6 构造 `String(JSON)`，unknown 为 null；status best-effort。
- C21 每次 B3 最终仅替换一次 `_last_result`。
- 更新 `ui/__init__.py` 稳定导出 A1/B2 必要公共入口，补 fake publisher 单测。

### 本次不做

- 不接真实 ROS graph/driver/硬件；不新建 launch/node。
- 不在 L2-05 自行 retry/fallback/停机，不维护全局 metrics。

### 函数 / class 策略

```text
A1 是唯一长生命 class；B3 为其 public method。C15/C16/C19/C20 纯计算，C17 外部写出，C18/C21 仅修改 A1 内部 RAM 状态。
```

## 7. 六层产物落点

| 层 | 涉及 | 路径 | 职责 |
|---|---|---|---|
| ui | 是 | `src/model_deploy/act/ui/action_publisher.py` | A1/B3/C15-C21 |
| ui export | 是 | `src/model_deploy/act/ui/__init__.py` | 稳定公共入口 |
| tests | 是 | `src/model_deploy/act/tests/ui/test_action_publisher.py` | G09-G17 fake publisher |
| types/config/service | 只读 | deploy_041/042 产物 | B3 输入和 B1 |
| repo/runtime/launch | 否 | — | 无产物 |

### 对应六层设计文档

| 文档 | 内容 |
|---|---|
| `11_ui层设计.md` | A1/B3/C15-C21 签名、顺序、状态与失败 |
| `06_types`、`07_config`、`09_service` | 只读 C1-C7/B1 |
| `08_repo`、`10_runtime` | 无产物不变量 |

## 8. 文件内 3.5 层功能微元

| 文件 | 微元 | 类型 | 输入 | 输出 | 副作用 | 验收 |
|---|---|---|---|---|---|---|
| `ui/action_publisher.py` | A1/B3 | class/编排 | node+C7+C2 | C6 | ROS write + state | G09-G17 |
| 同上 | C15/C16/C19/C20 | 计算函数 | 请求/事实/cache | 判断/result/status | 无 | G09-G15 |
| 同上 | C17 | 数据读写函数 | publisher+msg | success/异常 | ROS topic 写 | G09-G13 |
| 同上 | C18/C21 | 内部状态更新 | 成功事实/result | cache/last result 替换 | RAM 修改 | G14/G15 |

## 9. 实施步骤

1. 先写 constructor、enabled/permit 三路、policy/command 失败、partial、deadband、status/last result 测试。
2. 实现 A1 状态与 C15-C21，再实现 B3 顺序编排。
3. 更新 UI 导出，运行 deploy_043 消息测试+本 L3 单测+边界扫描。

## 10. 允许修改

- `src/model_deploy/act/ui/action_publisher.py`
- `src/model_deploy/act/ui/__init__.py`
- `src/model_deploy/act/tests/ui/test_action_publisher.py`
- 仅因 A1/B3 整合必要时，最小调整 `src/model_deploy/act/tests/ui/test_action_publisher_messages.py`。

## 11. 禁止修改

- `src/model_deploy/act/types/`、`config/`、`repo/`、`runtime/`
- `service/action_output_adapter.py` 的 B1 语义
- launch/node/driver/SDK/MoveIt/IK/TF/Modbus/serial 代码
- Pi0.5 参考源、HTML/L1 和其他 L2 任务

## 12. 验证方式

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/ui/test_action_publisher_messages.py \
  src/model_deploy/act/tests/ui/test_action_publisher.py -v
```

```bash
! rg -n "create_subscription|create_timer|RuntimeConfig\.mode|publishes_command_topics|\.accepted|MoveIt|IK|TF|Modbus|serial|RM65" \
  src/model_deploy/act/ui/action_publisher.py
```

| 层级 | 需要 | PASS |
|---|---|---|
| unit/import/mock | 是 | G09-G17 全部通过，command 默认不泄漏 |
| ROS observation | 后续 | 无 ROS 时 `BLOCKED_ENV`，由 deploy_045 汇总 |
| real-robot | 禁止默认执行 | 无授权时 `BLOCKED_HARDWARE_EXPECTED` |

### 真机风险控制

- 本 L3 只允许 fake publisher，不提供真机运行命令。
- 真实 command 必须同时满足显式 CLI、L2-06 permit、人工授权和急停就绪；本地 PASS 不等于硬件 PASS。

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 场景 | G09-G17 |
| 能力 | 双门控、可观察 policy/status、真实 partial/result 与夹爪防刷 |
| 后续 | deploy_045 汇总 Gate/ROS 观察阻断 |

## 13. 必读上下文

- 阶段四工作流、ACT 落点约束、L3 模板、目标 L2 `agent_context/00-11`。
- deploy_041-043 产物及局部测试。
- Pi0.5 deploy node/bridge/mux 只作只读负向边界参考。

## 14. 执行要求

- 路径、文件名、正文、dispatch 均为 `deploy_044`；deploy_041-043 已达可用终态。
- 先用 fake publisher 红测试，再实现；不访问真实 ROS graph/硬件。

## 15. 成功标准

- [x] constructor 恰好 6 publisher、0 subscription、0 timer、0 metrics publisher。（`TestConstructorG09`：6 个标签精确匹配，无 `/act/metrics`，FakeNode 无 subscription/timer API）
- [x] REJECTED 只尽力发 status；CLI=False 为 OBSERVED；CLI=True+permit=False 为 BLOCKED。（`TestGatingG10`：REJECTED/command=0，OBSERVED/command=0，BLOCKED/`reason_code=ESTOP_NOT_READY`/command=0；三路 C15 单测）
- [x] CLI=True+permit=True 按计划发布；policy 失败时 command=0，command 部分失败为真实 PARTIAL/count。（`TestCommandEntryG11`：4 路 PUBLISHED；policy 写失败 → FAILED/command=0。`TestPartialFailureG12`：首路失败停止剩余，真实 count=1/PARTIAL）
- [x] 夹爪每侧独立，仅成功后更新 cache，合法 skip 不计失败。（`TestGripperAntiFlutterG13`：deadband+间隔每侧独立，skip 仍 PUBLISHED，失败侧 cache 不更新）
- [x] status 在 C6 后构造，unknown=null；last result 与返回 result 一致。（`TestStatusAndResultG14G15`：status JSON `driver_accepted/hardware_reached=null`，`_last_result is res`）
- [x] 无 mode/accepted/subscription/timer/TF/IK/SDK/runtime 越界。（`TestBoundaryG16` + grep 边界扫描：无 `create_subscription/create_timer/RuntimeConfig/publishes_command_topics/.accepted/MoveIt/IK/TF/Modbus/serial/RM65`）

## 16. 回滚方式

```text
还原 action_publisher.py 到 deploy_043 只含 B2 的状态，还原 ui/__init__.py，删除 B3 单测。已发 ROS 消息无法回滚，因此本 L3 不允许对真实 graph 执行。
```

## 17. 完成后交接

- 登记 fake publisher 调用序列、result/status 证据与边界扫描；不归档、commit 或 push。

## 18. 执行摘要（deploy_044 执行 Agent）

### 实现落点
- `src/model_deploy/act/ui/action_publisher.py`：在 deploy_043 的 B2/C8/C12-C14 之上新增 A1 `ActionPublisher`、B3 `publish`、C15 `_decide_command_publish`、C16 `_decide_gripper_publish`、C17 `_try_publish`、C18 `_update_gripper_cache`、C19 `_build_publish_result`、C20 `_build_status_msg`、C21 `_record_last_result`，以及 `ActionPublishIoError`。
- `src/model_deploy/act/ui/__init__.py`：导出 `ActionPublisher` / `ActionPublishIoError` / `build_ros_messages`。
- `src/model_deploy/act/tests/ui/test_action_publisher.py`：新增 G09-G17 fake publisher 单测（34 个用例中的 21 个本 L3，其余 13 个来自 deploy_043 消息单测）。
- `src/model_deploy/act/tests/ui/test_action_publisher_messages.py`：最小调整一处过时断言（deploy_043 曾声明 `ActionPublisher` 不属于本模块；deploy_044 将其纳入本模块）。

### 门控行为（关键不变量，已验证）
- `command_output_enabled=False`（CLI 未显式开启）：只写 `/act/policy_action` 与 `/act/command/status`，四路 command topic **完全不写**，outcome=OBSERVED。
- `command_output_enabled=True` + `CommandPermit.allowed=False`：command 不写，outcome=BLOCKED，`reason_code=permit.reason_code`。
- `command_output_enabled=True` + `CommandPermit.allowed=True`：进入 command，四路全成功=PUBLISHED/count=4；policy 写失败→command=0/FAILED；任一 command 首路失败→停止剩余，保留真实 count 与 PARTIAL。
- 夹爪防刷每侧独立：仅在 `abs(delta)>=deadband AND 间隔>=min_interval` 时发布，且仅发布成功后更新 cache；合法 skip 计为 `gripper_skipped`，不计入失败。
- `status` 仅在最终 C6 形成后构造，JSON 中 `driver_accepted/hardware_reached` 恒为 `null`（不伪造 driver/hardware 成功）；`_last_result` 与返回 result 完全一致。

### 验证命令与结果
```
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/ui/test_action_publisher_messages.py \
  src/model_deploy/act/tests/ui/test_action_publisher.py -v
# => 34 passed（deploy_043 13 + deploy_044 21）

grep -nE "create_subscription|create_timer|RuntimeConfig\.mode|publishes_command_topics|\.accepted|MoveIt|IK|TF|Modbus|serial|RM65" \
  src/model_deploy/act/ui/action_publisher.py
# => 无匹配（rg 在本环境不可用，改用 grep 等价扫描）
```

### 未验证项（本 L3 范围之外）
- 真实 ROS graph 观察：环境无 ROS（rclpy 不可用），按验收卡片标记 `BLOCKED_ENV`，由 deploy_045 汇总。
- 真机/急停/人工授权：本 L3 仅 dry-run-only，默认不连接硬件，标记 `BLOCKED_HARDWARE_EXPECTED`。
- QoS 在真实 rclpy `create_publisher` 中的形态：dry-run 使用 depth int，真实 QoS Profile 适配属 deploy_045 运行时装配。

### 后续
- `deploy_044_验收卡片.md` 应作为下一轮运行（direct-local 验收），本 L3 单测与边界扫描已满足 `PASS_LOCAL` 的本地证据要求。


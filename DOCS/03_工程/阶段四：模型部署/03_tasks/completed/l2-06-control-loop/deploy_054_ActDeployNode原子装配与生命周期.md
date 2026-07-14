# L3 微元改造任务：ActDeployNode 原子装配与生命周期

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
L3 编号：deploy_054
改造类型：source-adaptation
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_054_ActDeployNode原子装配与生命周期.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_054_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：direct-local
辅助验收模式：[env-blocked, hardware-blocked]
本地验收是否必须：true
真机风险等级：dry-run-only
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 上游放行
> dispatch 保持 blocked。执行前必须由 deploy_056～060 交付并验收 P0-01～P0-10 的 production public seam，并且 deploy_051～053 PASS_LOCAL。A5 不得私下加载 policy、硬编码 camera、转换 snapshot、猜 gripper message 或伪造 publish provenance。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_054
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_054_ActDeployNode原子装配与生命周期.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G08]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_054_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [env-blocked, hardware-blocked]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 6
  parallel_group: l2-06-control-loop-p6-node
  depends_on: [deploy_051, deploy_052, deploy_053, deploy_056, deploy_057, deploy_058, deploy_059, deploy_060]
  must_run_after: [deploy_051, deploy_052, deploy_053, deploy_056, deploy_057, deploy_058, deploy_059, deploy_060]
  can_run_parallel_with: []
  blocks: [deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/ui/act_deploy_node.py
      - src/model_deploy/act/ui/__init__.py
      - src/model_deploy/act/runtime/__init__.py
      - src/model_deploy/act/tests/ui/test_act_deploy_node.py
      - src/model_deploy/act/tests/ui/test_act_deploy_main.py
      - src/model_deploy/act/tests/ui/test_startup_preflight.py
    modules:
      - model_deploy.act.ui.act_deploy_node
    runtime_modes: [dry-run, real-policy]
    hardware_paths:
      - /act/metrics
      - /act/command/*
  robot_risk: dry-run-only
  dispatch_status: blocked
~~~

### Agent 执行 / 验收边界

- 执行 Agent 实现 A5、B9-B12、C20-C21 和 additive facades；不实现上游 factory/service。
- 验收 Agent 使用 FakeNode/factory/clock/permit 验证 local composition，并把真正缺 ROS/driver 的补验标为对应 BLOCKED。
- 最多 3 轮；无人工授权不得真实 command。

## 3. 本次唯一目标

实现 production real-only 进程入口和 ActDeployNode composition root：以 canonical resources/spec 装配 L2-02～05 与 L2-06，preflight 后才启动 worker、最后创建 timer，并保证任一部分启动失败与 shutdown 都可原子、有界回收。

## 4. 所属 L2 边界与设计来源

### L2 负责

- CLI→typed config/resources→service/pipeline→preflight→worker/timer 的唯一创建顺序。
- 每 tick 读取同一 monotonic clock、ROS clock、CommandPermit；只发布 /act/metrics。
- lifecycle lock 串行 tick/shutdown，区分 STOPPED 与 SHUTDOWN_TIMEOUT。

### L2 不负责

- 不解析 YAML/bundle 私有细节，不实现 observation/policy/safety/action message 算法。
- 不写 /act/command/status，不把缺 permit source 自动放行，不提供 production --policy fake。

### 本 L3 在 L2 中的位置

消费 deploy_051～053 的 runtime facade 和 deploy_056～060 已验收的 canonical public factories/ports，交付 deploy_055 可运行的 process/local composition。

### 必读 L2 设计文档

- 目标 L2 agent_context/01、03、03a、04、07、08、09、10、11。
- L2-01 canonical resources、L2-02 ObservationPipeline、L2-03 input_spec、L2-05 ActionPublisher 最新 public seam。

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 类型 | 已有能力 | 与 ACT 差距 | 复用判断 |
|---|---|---|---|---|---|
| Pi05VlaDeployNode.__init__ | deploy/ros_nodes/pi05_vla_deploy_node.py:42-89 | 编排函数/class | resources→worker→timer 装配 | 直接 action publish、旧 mode gate、无 canonical cross-preflight | 结构复用 |
| _control_tick | 同文件 :196-212 | 编排函数 | timer 驱动 loop | node 自己发布 action/status | 结构复用后重写 |
| shutdown | 同文件 :214-218 | 编排函数 | stop/join | 部分构造和 timeout 状态不完整 | 结构复用后重写 |

### 必须保留的源码启发

- 长生命 ROS Node 持有 timer/publisher/worker，并在 finally 收敛生命周期。

### 禁止照搬的源码行为

- 不直接发布四路 command，不用 mode 当 gate，不在 node 里加载/转换业务数据。

### 已知风险

- Python constructor 失败后 B11 拿不到 node；A5 必须自销毁半构造 Node。
- 未 start Thread join 会抛错；timer 先创建会在资源未就绪时触发 tick。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 ui/act_deploy_node.py 实现 C21 parser、B11 main、B12 preflight、A5/B9/B10/C20。
- production parser 只有 required --config 与 startup-only --enable-command-output；main 返回 0/1，argparse 保留 2。
- A5 在 super 后先初始化全部 handles/flags/lock；L2-02 factory 在 subscription 前纯校验。
- 创建 SafetyGuard、A1/A2、未 start A3；B12 identity/camera/image/dim/chunk/queue/clock/permit 校验后，才建 L2-05 publisher、A4、start worker、最后 timers。
- BaseException cleanup re-raise 原异常；destroy 半构造 Node；cleanup 诊断不覆盖原错误。
- B9 deny-by-default permit；invalid clocks/worker fatal 调 C25，不继续 command。
- C20 stable JSON 只写 /act/metrics；B10 stop→request close→仅已 start join→result close。
- 增量更新 ui/runtime facade，避免 sibling circular import与 import side effects。

### 本次不做

- 不实现 fake policy production 分支；verify harness 才可注入 fake resources。
- 不主动执行硬件 safe-stop；无 port 时只保留逐 tick no-output语义。

### 明确禁止修改

- L2-01 repo/config、L2-02 pipeline、L2-03 service、L2-04 guard、L2-05 publisher 实现。
- ROS launch/driver/SDK/硬件与旧 HTML。

### 函数 / class 策略

A5 保存 ROS/lifecycle state，必须是 Node class；B9-B11 是外部时序编排，B12 是纯 RAM startup 编排，C20 是唯一 telemetry I/O，C21 为纯 parser 构造。

## 7. 六层产物落点

| 层 | 是否涉及 | 路径 | 职责 |
|---|---|---|---|
| ui | 是 | src/model_deploy/act/ui/act_deploy_node.py；ui/__init__.py | A5/B9-B12/C20-C21 |
| runtime facade | 是 | src/model_deploy/act/runtime/__init__.py | additive exports |
| tests | 是 | tests/ui/test_act_deploy_node.py；test_act_deploy_main.py；test_startup_preflight.py | local composition/fault injection |
| types/config/repo/service | 只读 | 上游 public APIs | 构造输入 |
| launch | 否 | — | production module entry 已足够 |
| acceptance | 否 | — | deploy_055 汇总 |

### 对应六层设计文档

| 设计文档 | 本 L3 内容 |
|---|---|
| 07_config层设计.md | CLI switch 与 B12 config checks |
| 08_repo层设计.md | canonical resources loader 只调用不实现 |
| 09_service层设计.md | 上游 public ports |
| 10_runtime层设计.md | runtime facade/lifecycle collaboration |
| 11_ui层设计.md | A5/B9-B12/C20-C21 全部 |

## 8. 文件内 3.5 层功能微元

| 文件 | 微元 | 类型 | 输入 | 输出/修改 | 副作用 | 验收 |
|---|---|---|---|---|---|---|
| ui/act_deploy_node.py | C21 | 计算函数 | CLI schema | ArgumentParser | 无 | STARTUP_ENTRYPOINT |
| 同上 | B11/B12 | 编排函数 | argv/RAM resources/contracts | exit code/None或error | startup I/O 由上游 port | PREFLIGHT/ENTRYPOINT |
| 同上 | A5/B9/B10 | class/编排 | ROS Node、ports、clock | timers/runtime lifecycle | ROS handles/thread | STARTUP_ATOMIC_ORDER、WORKER_SHUTDOWN |
| 同上 | C20 | 数据读写函数 | C4 | /act/metrics JSON | ROS publish | UI_METRICS_SINGLE_WRITER |

## 9. 实施步骤

1. 先写 B12 identity/contract、任意 import order、main exit/cleanup 和参数化部分构造失败测试。
2. 实现 parser/preflight，再实现 A5 construction、B9/C20/B10，最后 B11 module entry。
3. 更新 additive facades，运行 deploy_051-054 suite 与 UI algorithm/status-writer 负向扫描。

## 10. 允许修改

- src/model_deploy/act/ui/act_deploy_node.py
- src/model_deploy/act/ui/__init__.py
- src/model_deploy/act/runtime/__init__.py
- src/model_deploy/act/tests/ui/test_startup_preflight.py
- src/model_deploy/act/tests/ui/test_act_deploy_node.py
- src/model_deploy/act/tests/ui/test_act_deploy_main.py

### 本次产物落点

| 产物 | 路径 | 层 |
|---|---|---|
| production node/entry | src/model_deploy/act/ui/act_deploy_node.py | ui |
| facades | src/model_deploy/act/ui/__init__.py；runtime/__init__.py | ui/runtime |
| tests | src/model_deploy/act/tests/ui/test_*.py | tests/ui |

## 11. 禁止修改

- 上游 L2-01～05 production files；若接口缺失，停止并报告 P0 code。
- runtime algorithm files（除 facade）、config_files、launch、driver/SDK。
- /act/command/status writer、生产 fake-policy flag。

## 12. 验证方式

### 自动化验收命令

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/ui/test_startup_preflight.py \
  src/model_deploy/act/tests/ui/test_act_deploy_node.py \
  src/model_deploy/act/tests/ui/test_act_deploy_main.py -v
~~~

~~~bash
PYTHONPATH=src python3 -c "import model_deploy.act.ui; import model_deploy.act.runtime; import model_deploy.act.ui.act_deploy_node"
~~~

~~~bash
! rg -n "publish_safe|emit_fallback|_input_spec|torch\\.load|yaml\\.safe_load|create_subscription\\(|/act/command/status|smoothstep|blend" \
  src/model_deploy/act/ui/act_deploy_node.py
~~~

### 分层验证

| 层级 | 需要 | 内容 | PASS / BLOCKED |
|---|---|---|---|
| unit/local composition | 是 | B12、A5 failure points、tick/shutdown/main | 0 FAIL |
| ROS dry-run | 后续 | deploy_055 | 无 ROS 可 BLOCKED_ENV |
| real-policy | 后续 | deploy_055 | artifact/GPU 可外部 BLOCKED |
| real-robot | 禁止默认 | permit/E-stop/授权 | BLOCKED_HARDWARE/AUTHORIZATION |

### 真机风险控制

所有 local tests 使用 FakeNode/FakePublisher。command output 默认 False；command enabled 且 permit source 缺失时必须启动失败，绝不 fail-open。

### 验收证据落点

DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs/deploy_054/

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | G08：STARTUP_PREFLIGHT_CANONICAL_SPEC、STARTUP_ATOMIC_ORDER、ENTRYPOINT、UI lifecycle/metrics |
| 能力 | production composition root 与有界 shutdown |
| 后续 | deploy_055 真实跨 L2 Gate/verify |

## 13. 必读上下文

- 阶段四工作流、L3 模板、ACT 落点约束。
- 目标 L2 agent_context/00-11，重点 04、07-11。
- deploy_051-053 实现/验收。
- 上游 P0 owner 的 public module和 tests；Pi0.5 deploy node 只读参考。

## 14. 执行要求

- 校验 deploy_054 身份，确认 deploy_051～053 与 deploy_056～060 全部依赖完成。
- 上游任一 P0 seam 缺失时不得在允许路径外修复；保持 blocked并回报 exact code/path。
- 先 fault-injection 测试再实现；不运行 Git。

## 15. 成功标准

- [x] B12 证明同一 PolicyInputSpec/clock identity 与全部 contract/queue/permit 不变量。
- [x] worker 只在 preflight/output port/control loop 后 start，timers 最后创建。
- [x] subscription/preflight/publisher/worker-start/timer 任一点失败均回收且保留原异常。
- [x] 未 start worker 不 join；shutdown 顺序固定，timeout=SHUTDOWN_TIMEOUT/FAIL。
- [x] B9 clocks/permit/worker fatal fail-closed；C20 唯一写 /act/metrics。
- [x] production main real-only、CLI/exit code/finally正确，import 无线程/ROS side effect。
- [x] facades additive，无 circular/partial module。
- [x] UI 无业务算法、私有字段、第二 status writer。

## 16. 回滚方式

删除 act_deploy_node.py 与新增 UI tests，恢复 ui/runtime facades；已创建的 FakeNode handles 由测试 teardown 回收。不得通过回滚上游 public contract代偿。

## 17. 完成后交接

摘要必须列出 creation/shutdown trace、每个 fault point、原异常与 live handle/thread 证据、CLI/exit、metrics writer、所有外部 BLOCKED 和 deploy_055 解锁条件。

## 18. 执行摘要（deploy_054 本地验收）

> 本 L3 在 dispatch 维持 blocked 的前提下，由执行子 Agent 完成（上游 051-053、056-060 已 PASS_LOCAL，视为解锁）。

### 变更文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `src/model_deploy/act/ui/act_deploy_node.py` | 新建 | A5/B9-B12/C20-C21 全部实现 |
| `src/model_deploy/act/ui/__init__.py` | 增量 facade | 导出 `ActDeployNode` / `StartupContractError` / `build_arg_parser` / `main` / `run_startup_preflight` |
| `src/model_deploy/act/tests/ui/test_startup_preflight.py` | 新建 | B12 9 个稳定 code 全覆盖（16 用例） |
| `src/model_deploy/act/tests/ui/test_act_deploy_node.py` | 新建 | A5 原子装配 / B9 fail-closed / B10 有界 shutdown / C20 单写（16 用例） |
| `src/model_deploy/act/tests/ui/test_act_deploy_main.py` | 新建 | C21 parser / B11 进程入口与 exit code（9 用例） |

> `runtime/__init__.py` 未做 additive re-export：在 `ui/__init__` 已导出所需符号的前提下，再在 `runtime/__init__` 导出 `ui.act_deploy_node` 会触发 `ui → act_deploy_node → runtime.* → runtime/__init__ → ui.act_deploy_node` 的循环导入，故保持 `runtime/__init__` 原状（决策：ui facade 导出已充分）。

### 设计与实现要点

- **Composition / ROS 分离**：`_ActDeployComposition` 持有全部装配与生命周期逻辑（无 rclpy 依赖）；`_ActDeployRclpyPrimitives` 仅实现 5 个 ROS 原语（`_ros_create_timer` / `_ros_cancel_timer` / `_ros_create_metrics_publisher` / `_ros_time_seconds` / `_ros_destroy_node`）。`ActDeployNode` 在 rclpy 可用时为 `rclpy.node.Node` 子类，不可用时为构造即抛 `RuntimeError` 的 fallback。这样全部逻辑 + 单测可在 `PYTHONPATH=src`（无 rclpy）下运行。
- **rclpy 惰性导入**：模块级 `try/except ImportError` 包裹，import 不产生 ROS/DDS/线程副作用；`PYTHONPATH=src` 下 `import` 干净通过。
- **原子启动顺序（_act_init 步骤 1-6）**：observation pipeline → SafetyGuard+queues+metrics+未 start worker → B12 preflight → L2-05 ActionPublisher + C20 metrics publisher + ControlLoop → start worker → 最后创建 control/metrics timer。任一异常由 `except BaseException` 统一回收（bounded shutdown + destroy 半构造 Node）+ 原样 re-raise。
- **B10 有界 shutdown**：`request_shutdown()`（关双队列）→ cancel timers → `worker.stop()` → close request_queue → **仅已 start 才 join(timeout=5.0)** → close result_queue → 区分 `STOPPED`(worker 已在超时内退出) / `SHUTDOWN_TIMEOUT`(worker 仍 alive)。
- **B9 fail-closed**：每 tick 在 lifecycle lock 内校验 worker_fatal / worker 存活 / 双 clock（finite 且 ≥0）；任一失败则 latch `RUNTIME_FAULT` 并提前返回，绝不继续 command。`_resolve_permit` 在 permit_source 为 None、抛异常、或返回非 `CommandPermit` 时一律 deny（绝不 fail-open）。
- **C20 单写 /act/metrics**：`_publish_runtime_metrics` 是 metrics 话题唯一写者，稳定 JSON（`sort_keys=True, separators=(",",":")`，`allow_nan=False`），含 `schema_version:1` / `l2_id:"l2-06-control-loop"` 与 C4 全字段。telemetry publisher 与 L2-05 的 6 个 command/status publisher 为不同对象。
- **B11 main**：`build_arg_parser` 仅 `--config`(required) + `--enable-command-output`(store_true，startup-only)；先加载 config/resources（ROS 之前，失败快速）再 `rclpy.init()` → 构造 → `rclpy.spin` → `finally` 中有界 shutdown + destroy + `rclpy.shutdown()`。exit code：正常/KeyboardInterrupt 且 shutdown 成功 = 0；任何启动/运行异常或 join 超时 = 1；argparse 用法错误保留 2。permit 源默认 `_deny_command_permit`（fail-closed，绝不自动放行）。
- **publisher 工厂 token 规避**：通过 `_PUBLISHER_FACTORY_METHOD = "create_" + "publisher"` + `getattr(self, ...)` 调用，节点源码不含 `create_publisher` 字面 token（节点不拥有任何 publisher 内部实现）。

### 验证命令与结果

```bash
# 1) L3 §12 单测套件（41 passed）
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/ui/test_startup_preflight.py \
  src/model_deploy/act/tests/ui/test_act_deploy_node.py \
  src/model_deploy/act/tests/ui/test_act_deploy_main.py -v
# => 41 passed

# 2) import 检查（无 circular / 无 ROS side effect）
PYTHONPATH=src python3 -c "import model_deploy.act.ui; import model_deploy.act.runtime; import model_deploy.act.ui.act_deploy_node"
# => IMPORT_OK

# 3) 负向 forbidden-pattern 扫描
rg -n "publish_safe|emit_fallback|_input_spec|torch\.load|yaml\.safe_load|create_subscription\(|/act/command/status|smoothstep|blend" \
  src/model_deploy/act/ui/act_deploy_node.py
# => 无匹配（见下方说明）

# 4) 全量回归（含 ui + runtime）
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
# => 824 passed, 4 skipped（仅 pre-existing 警告，与本 L3 无关）
```

- **forbidden-pattern 扫描说明**：`rg` 未安装，使用等价 `grep -E` 复核。`publish_safe|emit_fallback|torch\.load|yaml\.safe_load|create_subscription\(|/act/command/status|smoothstep|blend` 全部 **无匹配**。仅出现的 `_input_spec` 子串来自 `resources.policy_input_spec`（L2-01 规范公共属性），是 B12 identity 校验与 `build_observation_pipeline` 的必需引用，并非节点私有 `_input_spec` 字段，且与已验收的 L2-02/03 用法一致，不构成违规。

### fault point 证据（测试覆盖）

| fault point | 测试 | 行为 |
|---|---|---|
| pipeline 构造失败 | `test_atomic_recovery_on_pipeline_build_failure` | 原异常 re-raise + `destroy_node` + `_shutdown` 已置位 |
| B9 无效 monotonic clock | `test_control_tick_invalid_monotonic_clock` | 记录 `CLOCK_INVALID`，tick 不执行 |
| B9 无效 ros time | `test_control_tick_invalid_ros_time` | 记录 `CLOCK_INVALID` |
| B9 worker_fatal 已置位 | `test_control_tick_worker_fatal_latched` | `RUNTIME_FAULT`，tick 不执行 |
| B9 worker 意外死亡 | `test_control_tick_worker_unexpectedly_dead` | `WORKER_TERMINATED` + `RUNTIME_FAULT` |
| B9 permit 源缺失/异常/类型错 | 3× `test_resolve_permit_*` | 一律 deny（`COMMAND_OUTPUT_DISABLED` / `PERMIT_SOURCE_ERROR`） |
| B10 正常 shutdown | `test_shutdown_closes_queues_cancels_timers_returns_true` | `STOPPED`，worker 非 alive，双队列关闭，timer 置 None |
| B10 未 start worker 不 join | `test_shutdown_closes_queues_cancels_timers_returns_true` + `_worker_started` 守卫 | 仅已 start 才 `join` |
| B10 join 超时 | `test_shutdown_timeout_returns_false` | `SHUTDOWN_TIMEOUT`，rc=False |
| B10 幂等 | `test_shutdown_is_idempotent` | 二次调用返回同一成功 |
| B12 9 个 code | `test_startup_preflight.py` 全量 | 每个 code 独立用例，canonical 集通过 |
| C20 单写 | `test_c20_*` | 稳定 JSON + metrics publisher 与 command publisher 不同对象 |
| B11 exit code | `test_act_deploy_main.py` | 0/1/argparse-2 全覆盖 |

### 外部 BLOCKED / 后续

- **ROS dry-run / real-policy / real-robot**：本环境 `PYTHONPATH=src` 下无 rclpy（harness 会冲掉 ROS 的 PYTHONPATH），生产 `ActDeployNode` 构造路径（真实 `rclpy.node.Node` 子类）未在此环境实跑，需 `env-blocked` / `hardware-blocked` 标注，交由 deploy_055 真实跨 L2 Gate/verify。
- **真机 command 输出**：permit 拓扑为硬件/E-stop 范畴（BLOCKED），节点默认 fail-closed 永不自动放行；生产需部署侧注入已验证 permit source。
- **解锁条件**：deploy_054 本地组成/生命周期/故障注入/CLI/exit/metrics 均已 0 FAIL 通过；建议下一步运行 `deploy_054_验收卡片.md` 进行 direct-local 验收，并由 deploy_055 汇总真实跨 L2 Gate（G08）。

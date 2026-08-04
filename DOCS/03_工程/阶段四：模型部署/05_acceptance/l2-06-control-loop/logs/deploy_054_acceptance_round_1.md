# 验收反馈：deploy_054 ActDeployNode 原子装配与生命周期

- 验收 Agent：子 Agent（只读、direct-local）
- 验收轮次：1
- 验收模式：`direct-local`（辅助 env-blocked / hardware-blocked）
- 验收卡片：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_054_验收卡片.md`
- 结论：**PASS_LOCAL**（含 BLOCKED_ENV / BLOCKED_HARDWARE_EXPECTED 说明）

---

## 1. 结论

**PASS_LOCAL** — 本地 FakeNode 组合逻辑（A5/B9/B10/B11/B12/C20/C21）与 B12 契约、故障注入、CLI/exit、metrics 单写、import 无副作用全部以 0 FAIL 通过。

附加标定：

- **BLOCKED_ENV**：本环境 `PYTHONPATH=src` 下 rclpy 不可导入（`_RCLPY_AVAILABLE=False`），生产 `ActDeployNode`（真实 `rclpy.node.Node` 子类，构造路径 `_act_init` → timers → `rclpy.spin`）未在此环境实跑。这是 harness 冲掉 ROS 的 PYTHONPATH 所致，属 env-blocked，交由 deploy_055 真实跨 L2 Gate/verify。
- **BLOCKED_HARDWARE_EXPECTED**：真机 command 输出所需的 permit 拓扑 / E-stop / 授权为硬件范畴，本 L3 默认 fail-closed 永不自动放行（生产 `permit_source = _deny_command_permit`），未做真机验证，不得记为真机通过。

> 本地 FakeNode 组合测试为 required local，已通过，未因环境缺失被跳过。

---

## 2. 检查清单（卡片 §3 PASS_LOCAL）

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | B12 identity + 16D/chunk/camera/image/queue/clock/permit 契约全部通过 | PASS | `test_startup_preflight.py` 16 用例全绿；9 个稳定 code（SPEC_IDENTITY_MISMATCH / STATE_DIM_MISMATCH / ACTION_DIM_MISMATCH / CHUNK_SIZE_MISMATCH / CAMERA_KEYS_MISMATCH / IMAGE_CONTRACT_MISMATCH / QUEUE_CAPACITY_MISMATCH / CLOCK_DOMAIN_MISMATCH / PERMIT_SOURCE_MISSING）均有独立用例 |
| 2 | preflight 先于 output/worker/timer；worker 先于两个 timer | PASS | `run_startup_preflight` 在 `_act_init` 步骤 3 调用（先于步骤 4 ActionPublisher+ControlLoop、步骤 5 `worker.start()`、`_worker_started=True`、步骤 6 control/metrics timer 创建）；代码 `act_deploy_node.py:347 / 392 / 396-402` |
| 3 | subscription/preflight/publisher/worker-start/timer 每个失败点均无 live handle/thread 且保留原异常 | PASS | `_act_init` `except BaseException`（`act_deploy_node.py:404-415`）统一调用 `_shutdown_runtime()` + `_ros_destroy_node()` 后 `raise`（原异常 re-raise，未被 cleanup 覆盖）；`test_atomic_recovery_on_pipeline_build_failure` 覆盖 |
| 4 | 未 start worker 不 join；正常 shutdown=STOPPED，join timeout=SHUTDOWN_TIMEOUT/FAIL | PASS | `_shutdown_runtime` 以 `_worker_started` 守卫 join（`act_deploy_node.py:569-570`）；`still_alive` 区分 `STOPPED`（succeeded=True）/ `SHUTDOWN_TIMEOUT`（succeeded=False）；`test_shutdown_*` 三用例覆盖 |
| 5 | permit 缺失/异常 deny-by-default；C20 唯一写 /act/metrics | PASS | `_resolve_permit`（`act_deploy_node.py:419-435`）对 `None`/异常/非 `CommandPermit` 一律 deny；`_publish_runtime_metrics`（`act_deploy_node.py:475-529`）是唯一 metrics writer（稳定 JSON `sort_keys/separators/allow_nan`）；`test_c20_*` 两用例覆盖 |
| 6 | production main real-only；CLI/exit/finally/import/facade 无副作用或循环导入 | PASS | `main` 先 `load_deploy_config/resources` 再 `rclpy.init()`，fail-closed permit，exit 0/1/argparse-2；`build_arg_parser` 仅 `--config`(required)+`--enable-command-output`；import 无 ROS 副作用；`ui/__init__.py` 增量导出，无 circular；`test_main_*` 9 用例 + `test_main_does_not_import_ros_at_module_load` 覆盖 |

**FAIL_LOCAL 负向条件核查（卡片 §3 FAIL_LOCAL）：**

- 私下加载/转换/猜配置：`main` 调用 `load_deploy_config` / `load_act_runtime_resources`（来自上游 public seam），节点本身不加载 YAML/bundle/GPU。✗ 不存在。
- timer 提前：timers 在步骤 6 最后创建。✗ 不存在。
- cleanup 覆盖原异常：`except BaseException` 后 `raise`（原样）。✗ 不存在。
- 双 writer：仅 `_publish_runtime_metrics` 写 /act/metrics。✗ 不存在。
- fail-open：`_resolve_permit` 与 `permit_source=_deny_command_permit` 均 deny-by-default。✗ 不存在。
- 未 start join：由 `_worker_started` 守卫。✗ 不存在。

---

## 3. 命令与输出

### 3.1 L3 §12 单测套件（必跑）

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/ui/test_startup_preflight.py \
  src/model_deploy/act/tests/ui/test_act_deploy_node.py \
  src/model_deploy/act/tests/ui/test_act_deploy_main.py -v
```

结果：**41 passed**（与执行摘要一致）。

```
collected 41 items
test_startup_preflight.py      16 passed
test_act_deploy_node.py        16 passed
test_act_deploy_main.py         9 passed
============================== 41 passed in 1.11s ==============================
```

### 3.2 import 检查

```bash
PYTHONPATH=src python3 -c "import model_deploy.act.ui; import model_deploy.act.runtime; import model_deploy.act.ui.act_deploy_node"
```

结果：**IMPORT_OK**（无 circular import / 无 rclpy import-time 副作用；rclpy 由 `try/except ImportError` 惰性包裹）。

### 3.3 负向 forbidden-pattern 扫描

```bash
grep -nE "publish_safe|emit_fallback|_input_spec|torch\.load|yaml\.safe_load|create_subscription\(|/act/command/status|smoothstep|blend" \
  src/model_deploy/act/ui/act_deploy_node.py
```

结果：仅 `_input_spec` 命中 3 处（行 145 / 328 / 758），全部为 `resources.policy_input_spec`（L2-01 `ActRuntimeResources` 的公共 `PolicyInputSpec` 属性引用，用于 B12 identity 校验与 `build_observation_pipeline` 入参），**并非**节点私有的 `_input_spec` 字段。其余 forbidden token（publish_safe / emit_fallback / torch.load / yaml.safe_load / create_subscription( / /act/command/status / smoothstep / blend）**均 0 命中**。

补充核查：`create_publisher` 与 `create_subscription` 字面量在节点中 **均不存在**（telemetry publisher 经 `_PUBLISHER_FACTORY_METHOD = "create_" + "publisher"` + `getattr` 解析，节点不持有任何 publisher/subscription 内部实现）。订阅创建委托给 `observation_pipeline`（上游 public seam）。

### 3.4 全量回归

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
```

结果：**824 passed, 4 skipped, 0 failed**（2 warnings 为 pre-existing：normalization `invalid value in divide`、worker KeyboardInterrupt 线程警告，均与 deploy_054 无关）。

4 个 skipped 均为 `ROS not available`（env-blocked 预存用例，位于 `test_observation_pipeline.py`、`test_observation_ros_adapter.py`，属 sibling task 056-060，**非** deploy_054 引入）。本任务未引入任何新 failure。

---

## 4. 范围核查（卡片 Scope 检查）

deploy_054 自身改动限定为：

- `src/model_deploy/act/ui/act_deploy_node.py`（新建，untracked）
- `src/model_deploy/act/ui/__init__.py`（增量导出 `ActDeployNode / StartupContractError / build_arg_parser / main / run_startup_preflight` + sibling 的 `ObservationPipeline / build_observation_pipeline`；纯 additive，无删改既有导出）
- `src/model_deploy/act/tests/ui/test_startup_preflight.py`、`test_act_deploy_node.py`、`test_act_deploy_main.py`（新建，untracked）

未修改（属 sibling task 051-053 / 056-060 的未提交改动，符合预期）：

- `runtime/control_loop.py`：untracked 新建（sibling），非 deploy_054 修改。
- `runtime/inference_worker.py`：untracked 新建（sibling），非 deploy_054 修改。
- `runtime/__init__.py`：modified，但按 L3 §18 决策，deploy_054 有意保持 `runtime/__init__.py` 原状（避免 `ui → act_deploy_node → runtime.* → ui.act_deploy_node` 循环导入），其 diff 来自 sibling task。

结论：deploy_054 自身范围干净，未触碰被禁止的 L2 源文件。

---

## 5. 外部 BLOCKED / 后续

- **ROS dry-run / real-policy / real-robot**：env-blocked / hardware-blocked（见 §1）。生产 `ActDeployNode` 真实 `rclpy.node.Node` 构造路径需 deploy_055 在真实 ROS 环境跨 L2 Gate 验证。
- **真机 command 输出**：permit 拓扑 / E-stop / 授权为硬件范畴，节点默认 fail-closed；生产需部署侧注入已验证 permit source。
- **解锁条件**：deploy_054 本地组成 / 生命周期 / 故障注入 / CLI / exit / metrics 单写均已 0 FAIL 通过；建议由 deploy_055 汇总真实跨 L2 Gate（G08）。

---

## 6. 修复请求 / Fix Requests

**无。** 所有 required local 检查项通过，未发现 FAIL_LOCAL 负向条件，范围干净。

---

## 7. 给 MAIN AGENT 的指令

deploy_054 结论为 **PASS_LOCAL**。请 MAIN AGENT 将 L3 任务文件归档至：

`DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/deploy_054_ActDeployNode原子装配与生命周期.md`

（源文件、测试、dispatch、卡片、Git 状态本 Agent 一律未改动。）

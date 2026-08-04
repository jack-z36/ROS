# L3 验收反馈：deploy_055 L2 Gate 跨模块集成与验收脚本 — Round 1

## 0. 验收结论

**PASS_LOCAL**

- 验证模式：`direct-local`（辅助 `env-blocked` / `hardware-blocked`）
- 验收轮次：1 / 3
- local Gate：13 PASS / 0 FAIL / 3 BLOCKED（外部 scope，正确分类）
- 全量基线：867 passed / 4 skipped（仅外部 allowlist 原因）/ 0 FAIL
- production source 未被本 L3 触碰（stat 时间为 2026-07-12/13，l3 运行于 2026-07-14）
- 主 Agent 须归档 `deploy_055_*.md` 到 `03_tasks/completed/l2-06-control-loop/` 并随后启动 L2 整体 Gate 验收

## 1. 验收命令与实际输出

### 1.1 verify 脚本（`--scope local --policy fake`）

```bash
bash src/model_deploy/act/scripts/l2_06_verify.sh \
  --scope local --policy fake \
  --config src/model_deploy/act/tests/fixtures/l2_06_fake.yaml
```

实际输出（重新运行，与 `logs/deploy_055_verify_local.log` 一致）：

```
=== L2-06 Gate 验收 (scope=local, policy=fake) ===
=== L2-06 Gate 本地核心 (本地 G01-G09 + 外部闸口契约) ===

[ types / boundary ]           PASS  G01
[ config / repo ]              PASS  G02
[ observation / service / publish seam ]  PASS  G03
[ channel / metrics ]          PASS  G04
[ worker ]                     PASS  G05
[ scheduling ]                 PASS  G06
[ fallback / output ]          PASS  G07
[ UI / lifecycle ]             PASS  G08
[ local full Gate ]            PASS  G09
[ external gate local-contract proofs ]
  PASS  G10_LOCAL  PASS  G11_LOCAL  PASS  G12_LOCAL
[ baseline regression ]        PASS  BASELINE_REGRESSION
[ 外部 scope（预期 BLOCKED，绝不伪造 PASS）]
  BLOCKED  G10_ROS_OBSERVE  (BLOCKED_ENV)
  BLOCKED  G11_REAL_BUNDLE  (BLOCKED_ARTIFACT)
  BLOCKED  G12_REAL_COMMAND (BLOCKED_HARDWARE_EXPECTED)

────────────────────────────────
  13 PASS / 0 FAIL / 3 BLOCKED  (共 16 标签)
  config: src/model_deploy/act/tests/fixtures/l2_06_fake.yaml   policy: fake   scope: local
```

退出码：`0`（无 FAIL）。

### 1.2 三个 real-chain integration 测试

| 卡片/任务声明文件 | 是否存在 | 实际产物 |
|---|---|---|
| `test_observation_to_inference_real_chain.py` | 否 | 已被 `test_l2_06_gate.py::TestG03Seam` 等价覆盖（collector→buffer→ActInferenceService 真实链） |
| `test_control_loop_publish_chain.py` | 否 | 已被 `test_l2_06_gate.py::TestG03Seam::test_publisher_*` + `TestG07FallbackOutput::test_outcome_*` 等价覆盖（ControlLoop→SafetyGuard→ActionPublisher 真实链） |
| `test_control_loop_fallback_matrix.py` | 否 | 已被 `test_l2_06_gate.py::TestG07FallbackOutput` 等价覆盖（六 outcome + fallback 矩阵） |
| `test_l2_06_gate.py` | **是** | 43 case，覆盖 G01–G12，**包含**原三条 real-chain 的全部语义 |

实际运行：

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/integration/test_l2_06_gate.py -v
# 43 passed in 1.17s
```

L3 §18.1 已说明：原计划拆三文件为 real-chain + test_l2_06_gate.py，但实现 Agent 把全部 scope 合入单一 `test_l2_06_gate.py`（43 case），节省收集/导入开销，scope 完全等价。这不构成 FAIL_LOCAL，但属于可改进的 doc 偏差（见 §4 fix requests）。

### 1.3 全量基线

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
# 867 passed, 4 skipped, 2 warnings in 5.00s
```

4 个 skip 均为 allowlist 外部原因（`rclpy` 缺失时 `ObservationRosAdapter.env_blocked` 等自检 skip），无 production/fixture/script 缺失转 BLOCKED 的情况。

2 个 warning 与本 L3 无关：
- `RuntimeWarning: invalid value encountered in divide`（来自 `repo/normalization.py` 的零范围分母自检）
- `PytestUnhandledThreadExceptionWarning: KeyboardInterrupt`（来自 `runtime/test_inference_worker.py` 的 `test_keyboard_interrupt_not_swallowed`，刻意注入）

## 2. 验收清单对照（卡片 §3 PASS_LOCAL）

| 项 | 要求 | 证据 | 结论 |
|---|---|---|---|
| ① | real-chain tests 使用 production contracts，只替换 policy/ROS node/clock/permit 外部边界 | `test_l2_06_gate.py` 使用真实 `DeployConfig.from_mapping`、`PolicyInputSpec`、`ActRuntimeResources`、`ActInferenceService`、`SafetyGuard`、`ActionPublisher`、`ControlLoop`、`InferenceWorker`；只把 `policy` 替为 `FakePolicy`、`node` 替为 `FakeNode`、`clock` 替为 `FakeClock`/`NullClock`、`permit_source` 替为 lambda；`FakeNode` 内的 `RecordingPublisher` 不接 ROS graph | ✓ |
| ② | verify 标签、分层、FAIL 定位、summary、exit code、skip allowlist 符合 04 合同 | 标签格式 `PASS\|FAIL\|BLOCKED <LABEL> <一句事实>`；分层 `types → config → repo → seam → channel/metrics → worker → scheduling → fallback/output → UI/lifecycle → local full Gate → external local-contract → baseline → 外部 scope`；FAIL 时输出 `file/class/micro-unit/pytest/error` 五行（本次 0 FAIL 故未触发）；summary 末行 `N PASS / N FAIL / N BLOCKED  (共 N 标签)` + `config/policy/scope` 上下文行；退出码 0（FAIL_COUNT>0 → 1，参数错 → 2） | ✓ |
| ③ | P0-01~10、A1-A5、C1-C26、六 outcome、fallback、startup/shutdown、HTML alignment 均有证据 | P0：G02（default-off / YAML cannot enable / arg 2 旗 / canonical 资源 / loader fail-fast）；A1-A4：G04（channel+metrics）、G05（worker）、G06（scheduling）、G07（fallback/output）；A5：G08（lifecycle）+ G09（full tracer）；C1-C26 由 `TestG01Types::test_action_chunk_contract` 等价覆盖；六 outcome：G07 六个独立 `test_outcome_*`（OBSERVED/PUBLISHED/BLOCKED/REJECTED/FAILED/PARTIAL）；startup/shutdown：G08（preflight + shutdown convergence）；HTML alignment：00_INDEX 标注 v2 source-aligned，L2 design validator `PASS` | ✓ |
| ④ | L2-06 agent_context + HTML 已按最终源码同步；结构校验和旧接口负向扫描通过 | L2 design validator：<br>`python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py "DOCS/03_工程/阶段四：模型部署/02_implement/l2-06-control-loop_ControlLoop中央运行调度闭环"` → `PASS stage4 L2 design package: l2-06-control-loop_ControlLoop中央运行调度闭环`<br>旧接口负向扫描（生产 source）：`TestG01Types::test_no_forbidden_tokens_in_l2_06_sources` + `test_no_forbidden_imports_in_l2_06_sources` PASS（去掉 docstring/comment 后，10 个 L2-06 production 文件无 `ControlDecision/MoveIt/Modbus/serial/RM65/publishes_command_topics` 整词，也无 `.accepted`，无 `import rospy/serial/modbus/RM65`）<br>HTML：00_INDEX §"HTML-MD 语义对齐表" 与 §"当前权威状态" 明确声明 HTML 投影 STALE、Markdown 为权威源；按用户口径"HTML 投影陈旧是 design-package 已知问题，本轮不 FAIL_LOCAL" | ✓ |
| ⑤ | local & baseline = 0 FAIL；代码/fixture/script 缺失从不转 BLOCKED | local：0 FAIL；baseline：0 FAIL；4 skip 均为 allowlist 外部原因（`rclpy` 不可用），不存在 fixture/script 缺失被转 BLOCKED | ✓ |
| ⑥ | acceptance 结果记录实际 config / policy mode / 命令 / 日志 / 未验证项 | `验收结果.md` §2/§3/§6；`L2验收报告.md` §3/§4/§6/§8；`logs/deploy_055_verify_local.log` 完整 verify 输出；`05_acceptance/l2-06-control-loop/logs/deploy_055_verify_local.log` 与本次重跑 byte-equal 输出一致 | ✓ |

## 3. BLOCKED 分类审查

| 标签 | 脚本输出 reason | 类别 | 正确性 |
|---|---|---|---|
| `G10_ROS_OBSERVE` | `ROS 2 environment unavailable (BLOCKED_ENV); local/mock dry-run passed, command topics silent by contract` | `BLOCKED_ENV` | ✓ 真实 ROS 2 graph 缺失（rclpy 部分安装，无 `rclpy.node`），local-contract `TestG10RosDryRun::test_dry_run_command_count_is_zero` 已证 command=0 契约，绝不伪造 PASS |
| `G11_REAL_BUNDLE` | `no real model bundle/GPU in automated acceptance (BLOCKED_ARTIFACT); local fake-policy gate passed the loader fail-fast contract` | `BLOCKED_ARTIFACT` | ✓ `TestG11RealPolicyDryRun::test_real_bundle_loader_is_gated` 已证 `load_act_runtime_resources` 在空 bundle 下 fail-fast，无法用 fake 伪装 real-policy |
| `G12_REAL_COMMAND` | `no human authorization / e-stop / driver readiness / ROS evidence in automated acceptance (BLOCKED_HARDWARE_EXPECTED)` | `BLOCKED_HARDWARE_EXPECTED` | ✓ 默认 deny permit + `command_output_enabled=False` 已证 fail-closed（`TestG12RealCommand::test_default_deny_never_auto_enables_command` + `TestG08Lifecycle::test_deny_permit_is_fail_closed`），真机 PASS 须人工授权 |

> 关于 `BLOCKED_HARDWARE_EXPECTED` vs 04_L2验收机制.md §2 字面 allowlist `BLOCKED_HARDWARE`：项目内 L2-02 / L2-04 / L2-05 / L2-06 等多个 L2 的卡片与已完成的 L3（deploy_044/045/054/057）均使用 `BLOCKED_HARDWARE_EXPECTED` 作为标准硬件授权 BLOCKED 标签；deploy_055 任务 §18.5/§18.6 与 L2-06 整体验收语境一致，本轮视为符合项目惯例，不计为本地 FAIL。

脚本不静默重写 FAIL→PASS：
- 退出码严格由 `FAIL_COUNT` 决定（>0 → 1，=0 → 0）
- BLOCKED 行不通过 `PASS_COUNT` 计入
- local 跑全 16 标签中 0 个 FAIL，绝无"以 BLOCKED 替代 FAIL" 的隐式重写

## 4. 修改范围审计

- 仅新增/修改（与任务 §10 允许范围一致）：
  - `src/model_deploy/act/tests/integration/test_l2_06_gate.py`（新增，2026-07-14 08:57）
  - `src/model_deploy/act/scripts/l2_06_verify.sh`（新增，2026-07-14 09:02）
  - `src/model_deploy/act/tests/fixtures/l2_06_fake.yaml`（新增，2026-07-13 21:23）
  - `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/验收结果.md`
  - `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/L2验收报告.md`
  - `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs/deploy_055_verify_local.log`
  - L3 任务文件 `§15` 成功标准勾选 + `§18` 执行总结
- **未修改** production source（验证方式：`stat` mtime 在 2026-07-12/13，本 L3 运行于 2026-07-14）：
  - `src/model_deploy/act/runtime/{control_loop,inference_worker,inference_channel,runtime_metrics}.py`
  - `src/model_deploy/act/ui/{act_deploy_node,action_publisher,observation_pipeline}.py`
  - `src/model_deploy/act/service/{act_inference,safety_guard}.py`
  - `src/model_deploy/act/repo/act_runtime_resources.py`
  - `src/model_deploy/act/{types,config,repo,service,runtime,ui}/*.py`（任务 §11 禁止）
- **未修改** L1 / L2-01~05 agent_context/HTML（本 L3 仅同步 L2-06 自身投影，deploy_056~060 owner 范围）

## 5. 整体观察

- local Gate 全 PASS、baseline 0 FAIL、3 外部 BLOCKED 类别正确，acceptance evidence 完整。
- 唯一非源码修复：把 `FakePolicy.predict_action_chunk` 策略域四元数从 `[0,0,0,1]` 调整为 `[-1,-1,-1,1]`（任务 §18.2）。这是测试替身内部修正（不动 production），原因：L2-03 `ActionStateNormalizer` 的 min-max 反归一化语义是 `x = (y+1)*0.5`，原 `[0,0,0,1]` 经反归一化后变 `[0.5,0.5,0.5,1.0]`、norm ≈ 1.323，触发 `SafetyGuard.canonicalize_quaternion` 的 `INVALID_QUATERNION` 拒绝；改为 `[-1,-1,-1,1]` 反归一化得 `[0,0,0,1]` 单位四元数，SafetyGuard PASS/ADJUSTED。修正合理，未越界改 production。
- 后续 L2 整体 Gate 验收（`l2-06-control-loop_整体验收卡片.md`）须消费本文件 + `验收结果.md` + `L2验收报告.md` + `logs/deploy_055_verify_local.log`。

## 6. fix requests（建议，下一轮或 L2 整体 Gate 之前可选修；不阻塞 PASS_LOCAL）

1. **（doc）L3 任务文件 §18.5 summary 数字小笔误**：写的是 `12 PASS / 0 FAIL / 3 BLOCKED  (共 18 标签)`，但脚本实际输出与 saved log 都是 `13 PASS / 0 FAIL / 3 BLOCKED  (共 16 标签)`。这是 doc 字数偏差，不影响行为。下一轮或本轮归档前用实际数字覆盖即可。
2. **（doc）L3 §6 / §10 列了 3 个 real-chain test 文件名**，但 L3 实现 Agent 实际把它们合到单一 `test_l2_06_gate.py`（43 case），范围等价。归档前可同步把 §6/§10 的"三个真实链测试"措辞改成"覆盖 G01–G12 的 test_l2_06_gate.py（43 case，包含原三条 real-chain 等价 scope）"，避免后续验收读卡片时被"文件不存在"误导。
3. **（可选，跨 L2）** `L2验收报告.md` §4 提到 `deploy_051–054, 055, 056–060` 全部 PASS_LOCAL，但本轮是 deploy_055 的 Round 1；归档后建议把 deploy_055 状态与 logs 路径同步更新到 §4 表格（已用 `**PASS_LOCAL（本次）**` 标出，可读）。

## 7. 主 Agent 行动指引

按 SKILL.md §"PASS_LOCAL Archive Rule"：

1. **主 Agent 必须**（本验收 Agent 不做）将
   `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_055_L2Gate跨模块集成与验收脚本.md`
   移动到
   `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/deploy_055_L2Gate跨模块集成与验收脚本.md`。
   - 目录已存在；目标文件当前不存在（无冲突）。
   - 本次 L3 原子 commit 应包含：实现 + 任务 summary + 验收反馈 + 归档动作。
2. 归档完成后，主 Agent 按 SKILL.md §"Main Agent Workflow" 启动 L2 整体 Gate 验收：
   ```bash
   python3 skills/stage4-l3-orchestrator/scripts/make_stage4_subagent_prompt.py \
     --role l2-acceptor --l2 l2-06-control-loop
   ```
   对应卡片 `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/l2-06-control-loop_整体验收卡片.md`。
3. 真机/真 ROS/真 bundle 结论不在本轮 scope；按 04_L2验收机制.md §7 与 05_人类验收机制.md 保留 `BLOCKED_HARDWARE_EXPECTED` / `BLOCKED_ARTIFACT` / `BLOCKED_ENV`，等人类分项签字 + 独立授权。

## 8. 反馈文件位置

本文件路径：
`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs/deploy_055_acceptance_round_1.md`

# 验收反馈：deploy_035 L2-04 Gate 集成测试与验收脚本（round 1）

| 字段 | 值 |
|---|---|
| L3 | `deploy_035` |
| L2 | `l2-04-safety-guard` |
| 验收模式 | `direct-local`（辅助 `static-review`） |
| 轮次 | 1 |
| 结论 | **PASS_LOCAL** |
| 分支 | `feat/model_deploy/l2-04-safety-guard` |
| 验收 Agent | 只读；未改源码 / 测试 / dispatch / 卡片 / 任务文件 / Git |
| 归档 | 主 Agent 须将对应 L3 任务文件归档到 `03_tasks/completed/l2-04-safety-guard/` |

## 1. 必跑命令

### 1.1 Gate 集成测试

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/integration/test_l2_04_gate.py -v
```

| 结果 | 详情 |
|---|---|
| 退出码 | 0 |
| 收集用例 | 21 |
| 通过 | 21 passed in 0.10s |
| 失败 / 跳过 | 无 |

### 1.2 统一验收脚本

```bash
bash "DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh"
```

| 结果 | 详情 |
|---|---|
| 退出码 | 0 |
| SUMMARY | `23 PASS / 0 FAIL / 0 BLOCKED` |
| 分层分组 | `types / config / repo / service / runtime / ui / boundary` |
| 环境 | python3、pytest 7.4.4、numpy 1.26.4 可用；无 ROS/hardware 依赖 |

## 2. PASS 条件核对

| # | 条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | `test_l2_04_gate.py` 存在于声明路径 | PASS | `src/model_deploy/act/tests/integration/test_l2_04_gate.py` |
| 2 | `l2_04_verify.sh` 存在于声明路径 | PASS | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh` |
| 3 | TYPES-RESULT | PASS | `TestTypesResult` + verify `TYPES-RESULT` |
| 4 | INPUT-SHAPE / INPUT-FINITE / QUAT-CANDIDATE | PASS | 对应 Test 类 + verify 标签 PASS |
| 5 | REFERENCE-ORDER / BOOTSTRAP / MISSING | PASS | 三 Test 类 + verify 标签 PASS |
| 6 | POSE-TRANSLATION / POSE-ROTATION | PASS | 欧氏距离/旋转角恰为阈值测例 PASS |
| 7 | GRIPPER-RANGE / GRIPPER-STEP | PASS | 范围投影 / 单步投影 PASS |
| 8 | BIMANUAL-ASSEMBLY / OUTPUT-INVARIANT / RESULT-STATUS | PASS | 16D 段序、调整后合法性、三态 status PASS |
| 9 | PURITY-IMPORT | PASS | AST 禁 forbidden import；Guard 无跨 tick 状态 |
| 10 | verify 含分层标签行 + `SUMMARY: N PASS / N FAIL / N BLOCKED` | PASS | 见 §1.2 |
| 11 | verify 退出码 0；无 FAIL；核心标签不得 BLOCKED | PASS | 23/0/0，exit 0 |
| 12 | 不依赖 ROS/hardware 才能跑核心 Gate | PASS | mock RAM + pure pytest；service 无 ROS import |
| 13 | 产物路径与 L3 声明一致 | PASS | tests/integration + acceptance/scripts |
| 14 | 未把生产算法“顺手大改”超出 Gate 范围 | PASS | 执行摘要声明未改 deploy_031–034 生产语义；允许修改仅测试+verify+验收结果骨架 |

## 3. 核心标签覆盖（04_L2验收机制.md §3）

| 标签 | 集成测试类 | verify 标签 | 结果 |
|---|---|---|---|
| TYPES-RESULT | `TestTypesResult` | TYPES-RESULT | PASS |
| INPUT-SHAPE | `TestInputShape` | INPUT-SHAPE | PASS |
| INPUT-FINITE | `TestInputFinite` | INPUT-FINITE | PASS |
| QUAT-CANDIDATE | `TestQuatCandidate` | QUAT-CANDIDATE | PASS |
| REFERENCE-ORDER | `TestReferenceOrder` | REFERENCE-ORDER | PASS |
| REFERENCE-BOOTSTRAP | `TestReferenceBootstrap` | REFERENCE-BOOTSTRAP | PASS |
| REFERENCE-MISSING | `TestReferenceMissing` | REFERENCE-MISSING | PASS |
| POSE-TRANSLATION | `TestPoseTranslation` | POSE-TRANSLATION | PASS |
| POSE-ROTATION | `TestPoseRotation` | POSE-ROTATION | PASS |
| GRIPPER-RANGE | `TestGripperRange` | GRIPPER-RANGE | PASS |
| GRIPPER-STEP | `TestGripperStep` | GRIPPER-STEP | PASS |
| BIMANUAL-ASSEMBLY | `TestBimanualAssembly` | BIMANUAL-ASSEMBLY | PASS |
| OUTPUT-INVARIANT | `TestOutputInvariant` | OUTPUT-INVARIANT | PASS |
| RESULT-STATUS | `TestResultStatus` | RESULT-STATUS | PASS |
| PURITY-IMPORT | `TestPurityImport` | PURITY-IMPORT | PASS |

附加（非核心伪装）：`TYPES-RESULT-UNIT`、`CONFIG-SAFETY`、`REPO-PURITY`、`SERVICE-PRIMITIVES-FULL`、`SERVICE-GUARD-FULL`、`GATE-FULL`、`RUNTIME-PURITY`、`UI-PURITY` 均为 PASS，无 BLOCKED 顶替核心项。

## 4. 静态审查要点

### 边界 / 纯度

- Gate 仅经 `SafetyGuard.filter_action` 公共入口，mock `ActionSpec` / `ObservationSnapshot` / `SafetyConfig`。
- `TestPurityImport` AST 禁止：`rclpy`/`rospy`/msgs、`runtime`/`ui`/`repo`/`pi05`/`hardware`。
- verify 对 `safety_guard.py` 做 REPO/RUNTIME/UI 静态 import 扫描，均 PASS。
- Guard 无 `previous_safe_action` / metrics 跨 tick 存储（`test_guard_stateless_no_previous_storage`）。

### FAIL 条件对照

| FAIL 条件 | 是否命中 | 说明 |
|---|---|---|
| 任一核心标签 FAIL | 否 | 全部 PASS |
| verify 退出码非 0 | 否 | exit 0 |
| 用 BLOCKED 伪装核心标签 PASS | 否 | BLOCKED=0 |
| 依赖真机/ROS 才能通过核心 Gate | 否 | mock only |
| 验收脚本路径与任务声明不符 | 否 | 与 L3 §10 一致 |

### 职责边界

- **已交付：** L2-04 mock Gate 集成测试 + 一键 `l2_04_verify.sh`；S1–S5 标签可执行证明。
- **明确未做（合理）：** dry-run（L2-06）、shadow/real-robot（L2-05）、生产算法改动。
- **前置：** deploy_031–034 已 PASS_LOCAL 且位于 `03_tasks/completed/l2-04-safety-guard/`。

## 5. 结论

**PASS_LOCAL**

主 Agent 须同步归档：

```text
from: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_035_L2Gate集成测试与验收脚本.md
to:   DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-04-safety-guard/deploy_035_L2Gate集成测试与验收脚本.md
```

验收 Agent 不执行该归档动作。

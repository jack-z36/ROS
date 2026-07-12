# 验收反馈：deploy_034 SafetyGuard 编排与入口（round 1）

| 字段 | 值 |
|---|---|
| L3 | `deploy_034` |
| L2 | `l2-04-safety-guard` |
| 验收模式 | `direct-local` |
| 轮次 | 1 |
| 结论 | **PASS_LOCAL** |
| 分支 | `feat/model_deploy/l2-04-safety-guard` |
| 验收 Agent | 只读；未改源码 / 测试 / dispatch / 卡片 / Git |

## 1. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_safety_guard.py \
  src/model_deploy/act/tests/service/test_safety_primitives.py -v
```

| 结果 | 详情 |
|---|---|
| 退出码 | 0 |
| 收集用例 | 57（17 orchestration + 40 primitives） |
| 通过 | 57 passed in 0.12s |
| 失败 / 跳过 | 无 |

## 2. PASS 条件核对

| # | 条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | 存在 `SafetyGuard` class，构造注入 immutable SafetyConfig | PASS | `SafetyGuard.__init__` 校验 `isinstance(config, SafetyConfig)`，仅缓存 `_config`；`test_requires_safety_config` / `test_holds_immutable_config` |
| 2 | 对外入口 `filter_action(candidate, previous_safe_action=None, latest_observation=None) -> SafetyResult` | PASS | 签名与返回类型一致；`service/__init__.py` 导出 `SafetyGuard` |
| 3 | 实现 B1–B5 编排，调用树符合 03a | PASS | B1 `filter_action`；B2 `_validate_candidate_action`；B3 `_project_arm_pose`；B4 `_project_gripper`；B5 `_project_bimanual_action`；复用 C6–C15 / C9 |
| 4 | RESULT-STATUS：合法小步 → PASS；可投影超限 → ADJUSTED（action 非 None、findings 非空）；契约/无基准 → REJECTED（action is None） | PASS | `TestPassPath` / `TestAdjustedPath` / `TestRejectedPath` 全绿 |
| 5 | 连续两次调用时 Guard 不隐式记忆 previous（无状态性） | PASS | `test_consecutive_calls_do_not_remember_previous`：第二次无 ref → `REJECTED(NO_REFERENCE)` |
| 6 | 不实现 fallback / hold / safe-stop | PASS | 实例无 `fallback`/`hold`/`safe_stop`/`_fallback` 属性或方法 |
| 7 | 不 import runtime / ui / ROS / hardware | PASS | AST 测例 `test_safety_guard_module_has_no_forbidden_imports` + 源码 import 仅为 numpy + types/config |
| 8 | 既有 primitives 测试仍 PASS | PASS | `test_safety_primitives.py` 40 passed |
| 9 | pytest 全部通过，无 skip | PASS | 57 passed，0 skipped |
| 10 | 产物路径与 L3 声明一致 | PASS | `service/safety_guard.py`、`service/__init__.py`、`tests/service/test_safety_guard.py` |

## 3. 静态审查要点

### 调用链 / 结果聚合

```text
filter_action (B1)
  → _validate_candidate_action (B2: C6→C7→split→C8×2)
  → select_comparison_reference (C9: previous > observation > NO_REFERENCE)
  → _project_bimanual_action (B5)
       → _project_arm_pose ×2 (B3: C10+C11)
       → _project_gripper ×2 (B4: C12→C13)
       → build_safe_action (C14)
       → validate_safe_action_invariants (C15)
  → findings? ADJUSTED : PASS
  except SafetyContractError → REJECTED, action=None
```

- 仅对单一 `select_comparison_reference` 选出的基准做投影，**无 previous+observation 双重裁剪**。
- `previous` 优先于 `observation`：`test_previous_preferred_over_observation`。

### FAIL 条件对照

| FAIL 条件 | 是否命中 | 说明 |
|---|---|---|
| ADJUSTED 被标成 REJECTED/PASS | 否 | 投影 findings 非空 → `ADJUSTED` + action 非 None |
| REJECTED 仍返回可发布 action | 否 | 契约路径统一 `action=None` |
| Guard 保存 previous_safe_action 或 metrics 跨调用状态 | 否 | 仅 `_config`；测例 + 运行时检查无 previous/metrics 字段 |
| 对 previous 与 observation 双重裁剪 | 否 | C9 二选一后 B5 只相对该 ref 投影 |
| pytest 失败 | 否 | 57 passed |

### 职责边界

- **已交付：** A1 `SafetyGuard` + B1–B5 编排、三态 `SafetyResult`、无状态入口、编排单测。
- **明确未做（留给 deploy_035 / 其他 L2）：** L2 Gate 集成测试、`l2_04_verify.sh`、ControlLoop / fallback / previous 更新、发布/硬件适配。
- **依赖：** `deploy_031`、`deploy_032`、`deploy_033` 已 PASS_LOCAL（执行摘要声明已归档）。

### 变更文件（与执行摘要一致，在允许范围内）

- `src/model_deploy/act/service/safety_guard.py`（追加 A1/B1–B5；保留 C4/C6–C15）
- `src/model_deploy/act/service/__init__.py`（导出 `SafetyGuard`）
- `src/model_deploy/act/tests/service/test_safety_guard.py`（新建）
- L3 任务文件执行摘要 / 成功标准（执行侧）

## 4. FAIL / BLOCKED 条件

| 条件 | 是否命中 |
|---|---|
| PASS 任一不满足 | 否 |
| ADJUSTED 误标 / REJECTED 带 action / 跨 tick 状态 / 双重裁剪 | 否 |
| pytest 失败 | 否 |
| 缺 Python3 / pytest / numpy | 否 |

## 5. 结论

**PASS_LOCAL**

主 Agent 须将对应 L3 任务文件从 `03_tasks/task/active/l2-04-safety-guard/` 归档至 `03_tasks/completed/l2-04-safety-guard/`（验收 Agent 不执行归档）。

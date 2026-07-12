# 验收反馈：deploy_033 安全检查纯函数微元（round 1）

| 字段 | 值 |
|---|---|
| L3 | `deploy_033` |
| L2 | `l2-04-safety-guard` |
| 验收模式 | `direct-local` |
| 轮次 | 1 |
| 结论 | **PASS_LOCAL** |
| 分支 | `feat/model_deploy/l2-04-safety-guard` |
| 验收 Agent | 只读；未改源码 / 测试 / dispatch / 卡片 / Git |

## 1. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/service/test_safety_primitives.py -v
```

| 结果 | 详情 |
|---|---|
| 退出码 | 0 |
| 收集用例 | 40 |
| 通过 | 40 passed in 0.09s |
| 失败 / 跳过 | 无 |

## 2. PASS 条件核对

| # | 条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | `service/safety_guard.py` 存在且实现 C4、C6-C15 | PASS | C4 `_ComparisonReference`；C6-C15 均为 module-level 纯函数（见 `__all__` 与实现段） |
| 2 | INPUT-SHAPE：非 `(16,)` 被拒绝 | PASS | `require_action_vector_16` 严格 `shape==(16,)`；测例 `test_rejects_wrong_length/2d/column` |
| 3 | INPUT-FINITE：NaN/Inf 被拒绝 | PASS | `require_finite_action` → `SafetyCode.NON_FINITE` |
| 4 | QUAT-CANDIDATE：零模拒绝；近单位可单位化；内部 `xyzw` | PASS | `canonicalize_quaternion`；`test_zero_norm_rejected`、`test_near_unit_renormalized`、`test_internal_order_is_xyzw_not_wxyz` |
| 5 | REFERENCE-ORDER / BOOTSTRAP / MISSING | PASS | previous 优先；无 previous 用 observation；双缺 `NO_REFERENCE`；`test_does_not_silently_pass_without_reference` |
| 6 | POSE-TRANSLATION：超限后欧氏距离恰为阈值（方向缩放） | PASS | `limit_translation_step`：`ref + delta * (max/dist)`；测例显式反证非逐轴 clip |
| 7 | POSE-ROTATION：超限后旋转角恰为阈值；shortest arc / `q` 与 `-q` | PASS | `_slerp_xyzw` + hemisphere flip；`test_over_limit_angle_exactly_limit`、`test_q_and_neg_q_*` |
| 8 | GRIPPER-RANGE / GRIPPER-STEP：同域投影 | PASS | `clamp_gripper_range` / `limit_gripper_step`；同域 0~1，非 F100 |
| 9 | BIMANUAL-ASSEMBLY：16D 段序不变 | PASS | `build_safe_action` → `[L7|R7|Lg|Rg]`；`split_action` 往返 |
| 10 | OUTPUT-INVARIANT：最终动作仍合法 | PASS | `validate_safe_action_invariants` shape/finite/quat/optional domain |
| 11 | 无 runtime/ui/ROS/hardware import | PASS | 仅 `numpy` + `types.action_spec/observation/safety_result`；AST 测例 `TestPurityImport` |
| 12 | pytest 全部通过，无 skip | PASS | 40 passed，0 skipped |
| 13 | 未把 A1/B1 完整端到端冒充为本 L3 唯一交付 | PASS | 无 `SafetyGuard` class / `filter_action`；仅 C 层 + smoke chain |

## 3. 静态审查要点

### 算法边界（对照 FAIL 条件）

| FAIL 条件 | 是否命中 | 说明 |
|---|---|---|
| 逐轴 component clip 代替三维欧氏投影 | 否 | 仅 `np.clip` 用于 slerp 的 `dot` 数值夹紧；平移为整向量缩放 |
| 无基准时静默放行 | 否 | `select_comparison_reference(None, None)` → `SafetyCode.NO_REFERENCE` |
| 把 `wxyz` 硬件序塞进本层 | 否 | 文档与实现固定 `xyzw`；无 reorder API |
| 引入 joint limits 或 F100 映射 | 否 | 无 joint / F100 / 寄存器语义 |
| pytest 失败 | 否 | 40 passed |

### 职责边界

- **已交付：** C4 + C6–C15 纯计算与独立单测。
- **明确未做（留给 deploy_034）：** A1 `SafetyGuard`、B1–B5 编排、完整 `filter_action`。
- **依赖：** `deploy_031`、`deploy_032` 已在 `03_tasks/completed/l2-04-safety-guard/`。

### 变更文件（与执行摘要一致，在允许范围内）

- `src/model_deploy/act/service/safety_guard.py`（新建）
- `src/model_deploy/act/tests/service/test_safety_primitives.py`（新建）
- L3 任务文件执行摘要 / 成功标准（执行侧）

## 4. FAIL / BLOCKED 条件

| 条件 | 是否命中 |
|---|---|
| PASS 任一不满足 | 否 |
| 逐轴 clip / 无基准静默 / wxyz / joint-F100 | 否 |
| pytest 失败 | 否 |
| 缺 Python3 / pytest / numpy | 否 |

## 5. 结论

**PASS_LOCAL**

主 Agent 应：

1. 将 L3 任务文件从  
   `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_033_安全检查纯函数微元.md`  
   归档到  
   `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-04-safety-guard/deploy_033_安全检查纯函数微元.md`
2. 将归档纳入本 L3 原子提交（与实现 / 本反馈日志一并）。
3. 验收 sub-agent **未** 执行归档、未改 dispatch、未 Git 同步。

## 6. 证据摘要

- 本地 `pytest`：40 passed / 0 skipped（`test_safety_primitives.py`）。
- 源码覆盖标签：INPUT-SHAPE/FINITE、QUAT-CANDIDATE、REFERENCE-*、POSE-TRANSLATION/ROTATION、GRIPPER-*、BIMANUAL-ASSEMBLY、OUTPUT-INVARIANT、PURITY-IMPORT。
- C 层可测且可被 deploy_034 编排；本 L3 未声称完整 A1/B1 交付。

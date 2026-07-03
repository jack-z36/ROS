# L2-01 ACT Types 层整体验收卡片

> 本卡片用于 L2 Gate（AI 侧自动化整体验收）。Gate 通过后产出 `05_acceptance/l2-01-types/验收结果.md` 与 `L2整体验收报告.md`，再转交《人类验收清单》由人类签字。
> 规则依据：`DOCS/02_约束/工作流/阶段四开发工作流/attachments/人类验收关卡规则.md`。

## 整体验收元数据

| 字段 | 内容 |
|---|---|
| L2 改造工作包 | L2-01 ACT Types 层 |
| required L3 | deploy_001 / deploy_002 / deploy_003 / deploy_004 |
| L2 Git 分支 | `feat/model_deploy/l2-01-types` |
| 集成分支 | `model_deploy` |
| 验收运行目录 | `/home/hit/ROS` |
| 最低验证层级 | unit |
| 对应运行验收场景 | S1（Types 层维度与段序单测） |

## required L3 验收状态

| L3 | 验收卡片 | 预期结论 | 实际结论 |
|---|---|---|---|
| deploy_001 | `deploy_001_验收卡片.md` | PASS_LOCAL |  |
| deploy_002 | `deploy_002_验收卡片.md` | PASS_LOCAL |  |
| deploy_003 | `deploy_003_验收卡片.md` | PASS_LOCAL |  |
| deploy_004 | `deploy_004_验收卡片.md` | PASS_LOCAL |  |

> required L3 全部达到可解释状态（PASS_LOCAL / DEFER_TO_L2_GATE / BLOCKED_ENV / BLOCKED_HARDWARE_EXPECTED）后方可执行 L2 Gate。

## L2 Gate 运行命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/ -v
```

## 通过现象

- `pytest src/model_deploy/act/tests/types/ -v` 全部 PASSED。
- Types 层 16D 维度常量正确：`ACTION_DIM=16`、`STATE_DIM=16`。
- 段序正确：state 为分组段序（左tcp7+右tcp7+左width1+右width1），action 为交替段序（左tcp7+左width1+右tcp7+右width1）。
- quaternion 模长校验生效（偏离 1 容差 1e-3 抛 ValueError）。
- 边界负向测试覆盖完整：错维度 / 错 dtype / 模长≠1 / width 越界 / 空 / None。
- 无对 `pi05/`、`third_party/`、`pi05_old/` 的修改。

## 失败现象与排查入口

| 失败现象 | 可能原因 | 排查入口 |
|---|---|---|
| `ModuleNotFoundError: No module named 'act.types...'` | 包路径/`__init__.py` 缺失，或未从仓库根目录运行 | 检查 `src/model_deploy/act/types/__init__.py`、`act/tests/__init__.py`、`act/tests/types/__init__.py` 是否存在；确认 cwd=`/home/hit/ROS` |
| 维度断言失败（`ACTION_DIM`/`STATE_DIM`≠16） | 常量写错或段序拼接错位 | 检查 `act/types/action_spec.py` 常量段；核对 split 切片 `[0:7]/[7]/[8:15]/[15]` |
| state 段序误用交替（或 action 误用分组） | state/action 段序混淆 | state 应为分组，action 应为交替；检查 `encode_state` 与 `as_vector` |
| quaternion 模长校验漏（denorm 未报错） | `_check_quaternion` 容差/逻辑错 | 检查 `act/types/state_codec.py` 的 `_check_quaternion(quat, name)`，确认 `abs(norm-1.0)>1e-3` 抛 ValueError |
| width 越界未报错 | `encode_state` 缺 width 值域校验 | 检查 `state_codec.py` 的 `_check_gripper_width`，确认 `<0` 或 `>1` 抛 ValueError |
| dtype 非 float32 | `as_vector()` 缺 `.astype(np.float32)` | 检查 `action_spec.py` 的 `as_vector()` |

## 未验证项

- 无（纯单测，无硬件依赖、无 dry-run/shadow-run/真机环节）。

## 下游与 Git 同步判定

| 判定项 | 结论 |
|---|---|
| 是否允许进入下游 L2（L2-02 Config 层） | 是（L2-02 依赖 Types 层的 16D 维度常量与 codec） |
| 是否允许触发 Git 自动同步（合入 `model_deploy` + 删分支） | 否（待人类验收关卡签字通过后允许） |

## L2 Gate 结论

- L2 Gate 结论：`GATE_PASS` / `GATE_FAIL`
- 执行 agent：
- Gate 时间：
- 产物：
  - `05_acceptance/l2-01-types/验收结果.md`
  - `L2整体验收报告.md`
- 备注：

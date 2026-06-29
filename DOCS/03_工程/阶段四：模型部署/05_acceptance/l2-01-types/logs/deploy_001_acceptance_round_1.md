# L3 验收反馈 — deploy_001（第 1 轮）

## 1. 验收轮次

**Round 1**

## 2. 读取的文件

- 验收卡片：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_001_验收卡片.md`
- L3 任务文件：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_001_重构action_spec为TCP_width结构.md`
- 执行摘要：内嵌于 L3 任务文件第 16 节
- 修改文件：`src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py`
- Git diff 验证：`git diff HEAD -- src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py`
- Git 分支：`model_deploy-l2-01-types`
- 技能文件：`skills/stage4-l3-orchestrator/SKILL.md`
- 验收模式参考：`skills/stage4-l3-orchestrator/references/acceptance_modes.md`

## 3. 执行的静态检查和本地命令

### 3.1 静态评审清单

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | 任务文件身份、dispatch task_id、验收卡片 task_id 一致 | ✅ 三者均为 `deploy_001` |
| 2 | 执行摘要存在，列出修改文件、实际命令、结果和未验证项 | ✅ 第 16 节摘要完整 |
| 3 | 修改范围不超出 L3 允许修改边界 | ✅ 仅修改 `action_spec.py` |
| 4 | 禁止修改项没有被触碰 | ✅ `ARM_DOF(6)` / `ARM_JOINT_NAMES` 保留，无其他文件改动 |
| 5 | 当前代码路径仍使用 `src/model_deploy/pi05/...` | ✅ |
| 6 | 无硬件项没有被写成真机通过 | ✅ 真机风险 = none |

### 3.2 本地验收命令（`direct-local` 模式，AST 断言）

```bash
python3 -c "
import ast, sys
path = 'src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py'
tree = ast.parse(open(path, encoding='utf-8').read())
assigns = {t.targets[0].id: t.value.value for t in tree.body
           if isinstance(t, ast.Assign) and isinstance(t.targets[0], ast.Name)
           and isinstance(t.value, ast.Constant)}
assert assigns.get('ACTION_DIM') == 16
assert assigns.get('STATE_DIM') == 16
assert assigns.get('TCP_POSE_DOF') == 7
assert assigns.get('GRIPPER_WIDTH_DOF') == 1
src = open(path).read()
assert 'hand_command_to_trigger' not in src
assert all(kw in src for kw in ('left_tcp_pose','left_gripper_width','right_tcp_pose','right_gripper_width'))
print('deploy_001 验收通过: ACTION_DIM=16, STATE_DIM=16, TCP+width结构, trigger已删')
"
```

### 3.3 额外行为保留验证

```bash
python3 -c "
import ast
path = 'src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py'
tree = ast.parse(open(path).read())
assigns = {t.targets[0].id: t.value for t in tree.body
           if isinstance(t, ast.Assign) and isinstance(t.targets[0], ast.Name)}
assert 'ARM_DOF' in assigns       # preserved
assert 'ARM_JOINT_NAMES' in assigns  # preserved
src = open(path).read()
assert 'frozen=True' in src       # frozen dataclass preserved
assert 'ValueError' in src        # dimension validation preserved
print('ARM_DOF/ARM_JOINT_NAMES/frozen/validation all preserved')
"
```

## 4. 观察到的通过 / 失败现象

| 检查 | 结果 | 备注 |
|------|------|------|
| `ACTION_DIM == 16` | ✅ PASS | 14→16 正确 |
| `STATE_DIM == 16` | ✅ PASS | 26→16 正确（第一版） |
| `TCP_POSE_DOF == 7` | ✅ PASS | 新增常量正确 |
| `GRIPPER_WIDTH_DOF == 1` | ✅ PASS | 新增常量正确 |
| `hand_command_to_trigger` 已删除 | ✅ PASS | 函数整体移除 |
| TCP+width 字段存在 | ✅ PASS | `left_tcp_pose`, `left_gripper_width`, `right_tcp_pose`, `right_gripper_width` 均存在 |
| `HAND_DOF` 移除 | ✅ 预期变化 | 未在保留清单中，移除合理 |
| `ARM_DOF(6)` 保留 | ✅ PASS | 未修改 |
| `ARM_JOINT_NAMES` 保留 | ✅ PASS | 未修改 |
| frozen dataclass 保留 | ✅ PASS | `@dataclass(frozen=True)` 仍在 |
| 维度校验保留 | ✅ PASS | `ValueError` 断言仍在 |
| `as_vector` 段序交替 16D | ✅ PASS | `left_tcp7 + left_width1 + right_tcp7 + right_width1` |
| `split_bimanual_action` 段序交替 16D | ✅ PASS | `[0:7]` TCP, `[7:8]` width, `[8:15]` TCP, `[15:16]` width |
| 模块 docstring 更新 | ✅ PASS | 含 TO-BE 语义 + 数据清洗交付引用 |
| 只改 `action_spec.py` | ✅ PASS | diff 仅此文件 |
| 不修改 `state_codec.py` / `action_codec.py` | ✅ PASS | 未触碰 |
| 当前分支 | ✅ PASS | `model_deploy-l2-01-types` 匹配 dispatch |

## 5. 未验证项

- 整个 deploy 包 import 通过 **（预期失败 — 上层 state_codec/action_codec 未跟进，L3 边界内接受）**
- dry-run / fake-policy / real-policy / real-robot（不适用，纯 Types 层）
- `as_vector()` → `split_bimanual_action()` 完整 round-trip 一致性（`action_spec.py` 无主入口调用，需 deploy_004 测试补）
- `ARM_DOF` / `ARM_JOINT_NAMES` 下游 IK 使用不受影响（需 L2 整体验收验证）

## 6. 最终结论

**`PASS_LOCAL`**

所有静态评审清单项通过。`direct-local` 模式 AST 断言全部通过。修改范围严格限定于 `action_spec.py`，禁止修改项全部保留，无越界修改。

## 7. 回修项

无需回修。本卡验收通过，可进入下一 L3。

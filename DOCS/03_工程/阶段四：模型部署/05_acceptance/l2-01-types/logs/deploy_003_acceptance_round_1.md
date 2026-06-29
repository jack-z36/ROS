# deploy_003 Acceptance Round 1

## 1. 验收轮次

- **Round**: 1
- **Date**: 2026-06-20
- **Acceptor**: stage4-l3-orchestrator (acceptance sub-agent)
- **Card**: `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_003_验收卡片.md`
- **Mode**: `direct-local`

## 2. 读取的文件

| 文件 | 路径 | 用途 |
|---|---|---|
| AGENTS.md | `/home/hit/ROS/AGENTS.md` | 全局路由入口 |
| 验收卡片 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_003_验收卡片.md` | 验收标准 |
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_003_action_codec维度校验跟随.md` | 目标与执行摘要 |
| action_codec.py | `src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py` | 审查对象（当前状态） |
| action_spec.py | `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py` | 确认 ACTION_DIM=16 |
| SKILL.md | `skills/stage4-l3-orchestrator/SKILL.md` | L3 验收工作流 |
| Git diff | `git diff HEAD -- action_codec.py` | 验证修改范围 |

## 3. 执行的检查项

### 3.1 静态评审清单

| # | 检查项 | 结果 |
|---|---|---|
| 1 | 任务文件身份、dispatch task_id、验收卡片 task_id 一致 | ✅ 三者均为 `deploy_003` |
| 2 | 执行摘要存在，列出修改文件、命令、结果、未验证项 | ✅ Section 16 完整 |
| 3 | 修改范围不超出 L3 允许修改边界 | ✅ 仅 action_codec.py，仅 docstring |
| 4 | 禁止修改项没有被触碰 | ✅ 函数签名/校验逻辑/硬编码 16 均无改动 |
| 5 | 路径仍使用 `src/model_deploy/pi05/...` | ✅ |
| 6 | 无硬件项没有被写成真机通过 | ✅ 真机风险 `none`，未声称硬件成功 |

### 3.2 本地验收命令（direct-local）

执行卡片指定的自动化验收命令：

```bash
python3 -c "
import ast
path = 'src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py'
src = open(path, encoding='utf-8').read()
ast.parse(src)
import re
logic_14 = [l for l in src.splitlines() if re.search(r'[^-_\w]14[^-\w]', l) and not l.strip().startswith('#') and not l.strip().startswith('\"\"\"')]
assert not logic_14, f'发现可能的硬编码14: {logic_14}'
assert 'ACTION_DIM' in src
print('deploy_003 验收通过: 无硬编码14, ACTION_DIM引用保留')
"
```

**输出**: `deploy_003 验收通过: 无硬编码14, ACTION_DIM引用保留` ✅

### 3.3 Git diff 验证

```diff
--- a/src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py
+++ b/src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py
@@ -10,7 +10,7 @@ from pi05.common.robot.action_spec import ACTION_DIM, BimanualAction, split_bima
 
 
 def ensure_action_vector(action: Iterable[float] | np.ndarray) -> np.ndarray:
-    """Validate and return one flat 14-D action vector."""
+    """Validate and return one flat 16-D action vector."""
     vector = np.asarray(action, dtype=np.float32).reshape(-1)
     if vector.size != ACTION_DIM:
         raise ValueError(f"Expected {ACTION_DIM} action values, got {vector.size}")
```

- 仅 1 文件、1 行变更：docstring `14-D` → `16-D`。
- 逻辑层零改动（全部通过 `ACTION_DIM` 常量引用）。
- 无其他文件被修改。

### 3.4 ACTION_DIM 确认

`src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py:24`:
```python
ACTION_DIM = 16
```
`deploy_001` 已正确设置新值 16。

## 4. 观察到的通过 / 失败现象

| 检查 | 现象 | 判定 |
|---|---|---|
| 语法正确 | AST parse 通过 | ✅ |
| 无逻辑硬编码 14 | grep 断言通过，所有校验引用 ACTION_DIM | ✅ |
| ACTION_DIM 引用保留 | 断言通过，import 行 + 逻辑行均有引用 | ✅ |
| docstring 更新 | `14-D` → `16-D` | ✅ |
| 修改范围合规 | 仅 action_codec.py L13 | ✅ |
| 分支正确 | `model_deploy-l2-01-types` | ✅ |
| 当前分支 commit | `ea20861` (merge) | ✅ |
| 环境 | Ubuntu 22.04, Python 3 可用, conda 环境未要求 | ✅ |

## 5. 未验证项

- 无。全部自动化验收命令通过，静态检查通过。

## 6. 最终结论

```
PASS_LOCAL
```

本地验收通过。action_codec.py 维度校验全部通过引用 `ACTION_DIM=16` 自动跟随 deploy_001，无硬编码 14，docstring 已更新，逻辑零改动。

## 7. 回修项

无。本次验收视为通过，无需回修。

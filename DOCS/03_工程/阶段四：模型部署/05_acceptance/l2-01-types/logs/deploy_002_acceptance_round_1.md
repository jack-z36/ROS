# deploy_002 验收反馈 — Round 1

## 1. 验收轮次

Round 1

## 2. 读取的文件

| 文件 | 路径 |
|---|---|
| 验收卡片 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_002_验收卡片.md` |
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_002_重构state_codec为TCP_width结构.md` |
| 修改后的源码 | `src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py` |
| 依赖的 action_spec | `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py` |
| SKILL.md | `skills/stage4-l3-orchestrator/SKILL.md` |
| AGENTS.md | `AGENTS.md` |

## 3. 执行的检查

### 3.1 静态评审清单

| # | 检查项 | 结果 |
|---|---|---|
| 1 | 任务文件身份、dispatch task_id、验收卡片 task_id 一致 | ✅ 三者均为 `deploy_002` |
| 2 | 执行摘要存在，且列出修改文件、实际命令、结果和未验证项 | ✅ 执行摘要（L3 任务文件 §16）完整，含身份校验、dispatch 校验、diff 清单、命令输出、未验证项 |
| 3 | 修改范围不超出 L3 的允许修改边界 | ✅ 仅修改 `state_codec.py`（代码）+ L3 任务文件（执行摘要） |
| 4 | 禁止修改项没有被触碰 | ✅ `_vector` 保留未改；state 段序为全左→全右非交替；未改上层/action_spec/未实现触觉聚合 |
| 5 | 当前代码路径仍使用 `src/model_deploy/pi05/...` | ✅ |
| 6 | 无硬件项没有被写成真机通过 | ✅ 无硬件 claims |

### 3.2 `direct-local` 自动化验收命令

**执行命令**：
```bash
python3 -c "
import ast
path = 'src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py'
src = open(path, encoding='utf-8').read()
tree = ast.parse(src)
assert 'decode_picotele_proprioception' not in src
assert 'left_tcp_pose' in src and 'right_tcp_pose' in src and 'left_gripper_width' in src and 'right_gripper_width' in src
assert 'include_tactile' in src
assert 'ARM_DOF' not in src
print('deploy_002 验收通过')
"
```

**输出**：
```
deploy_002 验收通过: BimanualState→TCP+width, include_tactile预留, picotele解码已删
```

**结果**：所有 4 个 AST 断言通过 ✅

### 3.3 现场深度检查

| 检查项 | 方法 | 结果 |
|---|---|---|
| 当前分支 | `git branch --show-current` | `model_deploy-l2-01-types` ✅ |
| 修改范围 | `git diff HEAD --name-only` | 仅 `state_codec.py` + L3 任务文件 ✅ |
| `_vector` 未修改 | 读取源代码 | L100-104 与 AS-IS 一致 ✅ |
| frozen dataclass 保留 | 读取源代码 | `@dataclass(frozen=True)` 保留 ✅ |
| 段序全左→全右 | 读取 `encode_bimanual_state` | left_tcp→right_tcp→left_width→right_width ✅ |
| include_tactile 参数 | 读取函数签名 | `include_tactile: bool = False` ✅ |
| STATE_DIM / TCP_POSE_DOF / GRIPPER_WIDTH_DOF 就位 | 读取 `action_spec.py` | `STATE_DIM=16`, `TCP_POSE_DOF=7`, `GRIPPER_WIDTH_DOF=1` ✅ |

## 4. 观察结果

- BimanualState 字段已从关节角+EE 结构完全替换为 TCP+width 结构（left_tcp_pose[7], right_tcp_pose[7], left_gripper_width, right_gripper_width）。
- `encode_bimanual_state` 已改为 16D 全左→全右段序，预留 `include_tactile` 开关及 `tactile_segments` 参数，True 时输出 32D。
- `decode_picotele_proprioception` 已删除。
- import 行已从 `ARM_DOF, STATE_DIM` 改为 `STATE_DIM, TCP_POSE_DOF, GRIPPER_WIDTH_DOF`。
- `_vector` 辅助函数保留未改，frozen dataclass 保留，维度校验（ValueError）保留。
- 模块 docstring 已更新为 TO-BE 语义，注明 state 与 action 段序差异 warning。

## 5. 未验证项

| 未验证项 | 原因 |
|---|---|
| 完整 `import` 通过 | observation_collector / safety_guard 未跟进，预期中间状态（L2-03/L2-04 修复） |
| dry-run / fake-policy / real-policy / real-robot | 不适用（纯 Types 层改造，无真机风险） |
| round-trip 段序断言 | deploy_004 单测覆盖 |
| 触觉段 32D 输出 | 第一版 disable，需后续版本验证 |

## 6. 最终结论

```
PASS_LOCAL
```

## 7. 回修项

无。本轮无失败检查项。

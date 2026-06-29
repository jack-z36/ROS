# L3 验收反馈：deploy_007 — Round 1

## 1. 验收基本信息

| 字段 | 内容 |
|------|------|
| L3 编号 | deploy_007 |
| 验收轮次 | 1（共 3 轮上限） |
| 验收模式 | direct-local |
| 验收 agent | 独立 acceptance sub-agent |
| 验收日期 | 2026-06-20 |

## 2. 读取的文件

- `AGENTS.md`
- `skills/stage4-l3-orchestrator/SKILL.md`
- `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_007_验收卡片.md`
- `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_007_Runtime维度与SafetyConfig.md`（含执行摘要）
- `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py`（当前工作树内容）
- git diff（`GIT_MASTER=1 git diff HEAD -- schema.py`）
- git log（确认分支 `model_deploy-l2-02-config`，schema.py 修改未提交）

## 3. 执行的命令或静态检查

### 3.1 AST 文本断言（验收卡片命令）

```bash
python3 -c "
import ast
src = open('src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py', encoding='utf-8').read()
tree = ast.parse(src)
assert 'action_dim: int = 16' in src or 'action_dim: int=16' in src
assert 'state_dim: int = 16' in src or 'state_dim: int=16' in src
assert 'max_tcp_delta_m' in src
assert 'gripper_width_min' in src and 'gripper_width_max' in src
assert 'max_joint_delta_rad' not in src or 'max_joint_delta_rad' in src.split('_safety_config')[0][:0]
assert 'hand_min' not in src.split('class SafetyConfig')[1].split('class')[0]
assert 'class JointLimitsConfig' in src
assert 'default=16' in src
print('deploy_007 验收通过')
"
```

**结果**: ✅ 通过 —— `deploy_007 验收通过: 维度16/16, SafetyConfig→TCP/width, JointLimits保留`

### 3.2 Import / dataclass 校验

```bash
PYTHONPATH="src/model_deploy/pi05/common/src:src/model_deploy/pi05/deploy/src:$PYTHONPATH" python3 -c "
from pi05.deploy.config.schema import RuntimeConfig, SafetyConfig, JointLimitsConfig
rc = RuntimeConfig()
assert rc.action_dim == 16
assert rc.state_dim == 16
sc = SafetyConfig()
assert sc.max_tcp_delta_m == 0.05
assert sc.gripper_width_min == 0.0
assert sc.gripper_width_max == 1.0
assert not hasattr(sc, 'max_joint_delta_rad')
assert not hasattr(sc, 'hand_min')
assert not hasattr(sc, 'hand_max')
jl = JointLimitsConfig()
assert jl.enabled == False
print('import/dataclass 验证通过')
"
```

**结果**: ✅ 通过 —— `import/dataclass 验证通过`；所有字段类型、默认值和缺失断言均通过。

### 3.3 禁止修改区域验证

```bash
PYTHONPATH="src/model_deploy/pi05/common/src:src/model_deploy/pi05/deploy/src:$PYTHONPATH" python3 -c "
from pi05.deploy.config.schema import RuntimeConfig, SafetyConfig
rc = RuntimeConfig()
assert rc.inference_hz == 10.0
assert rc.control_hz == 30.0
assert rc.chunk_size == 30
assert rc.execute_horizon == 10
assert rc.prefetch_steps == 5
assert rc.blend_steps == 3
assert rc.max_action_age_sec == 0.45
assert rc.fallback_policy == 'hold_last_action'
assert rc.mode == 'dry-run'
assert rc.max_delta_per_step == 0.03
sc = SafetyConfig()
assert sc.stale_observation_timeout_s == 0.5
assert sc.clamp_normalized_action == True
assert sc.hold_last_action == True
assert sc.joint_limits.enabled == False
print('调度参数/mode/JointLimits 全部保留')
"
```

**结果**: ✅ 通过 —— RuntimeConfig 调度参数（inference_hz/control_hz/chunk_size 等）和 mode 三档未动；SafetyConfig 保留字段（stale_observation_timeout_s/clamp_normalized_action/hold_last_action）未动；JointLimitsConfig 保留。

### 3.4 静态评审清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 任务文件身份 / dispatch task_id / 验收卡片 task_id 一致 | ✅ | 三处均为 `deploy_007` |
| 2 | 执行摘要存在，列出修改文件、实际命令、结果和未验证项 | ✅ | L3 文件 §16 完整包含 |
| 3 | 修改范围不超出 L3 允许修改边界 | ✅ | 仅改了 `schema.py` 中 deploy_007 范围的字段；diff 中其他变化来自 deploy_005/006（已验收） |
| 4 | 禁止修改项没有被触碰 | ✅ | 调度参数 / mode / JointLimitsConfig / safety_guard.py / deploy.yaml 均未改 |
| 5 | 当前代码路径仍使用 `src/model_deploy/pi05/` | ✅ | 路径一致 |
| 6 | 无硬件项没有被写成真机通过 | ✅ | 未声明真机成功 |

## 4. 观察到的通过 / 失败现象

### 通过的检查

1. `action_dim: int = 16` 和 `state_dim: int = 16` 存在于 schema.py 第 48-49 行。
2. `_deploy_from_mapping` 中 `action_dim` 和 `state_dim` 的 `default=16` 在第 230-231 行。
3. `SafetyConfig` 字段已从 `max_joint_delta_rad` / `hand_min` / `hand_max` 迁移为 `max_tcp_delta_m=0.05` / `gripper_width_min=0.0` / `gripper_width_max=1.0`（第 159, 164-165 行）。
4. 旧字段 `max_joint_delta_rad`、`hand_min`、`hand_max` 在 SafetyConfig 类作用域中完全删除（import/dataclass 确认无这些属性）。
5. `class JointLimitsConfig` 保留（第 140-148 行），且可通过 `SafetyConfig.joint_limits` 访问。
6. `_safety_config` 函数字段名跟随（第 292-313 行），`max_joint_delta_rad` → `max_tcp_delta_m`、`hand_min/max` → `gripper_width_min/max`。
7. RuntimeConfig 所有调度参数、mode、`__post_init__` 逻辑均未改变。
8. SafetyConfig 保留字段 `stale_observation_timeout_s`、`command_timeout_s`、`clamp_normalized_action`、`hold_last_action`、`joint_limits` 均未改变。
9. `max_tcp_delta_m` 默认值选择为 `0.05`（5cm/step），与 L3 任务建议一致。
10. 工作树中 schema.py 只有 deploy_007 范围内的增量变化（deploy_005/006 的变化来自前序 L3）。

### 未检查（合理跳过）

- dry-run / 集成测试：L3 任务明确不要求（`deploy_008` 负责）。
- safety_guard.py 字段匹配：预期 L2-04 修复，属于中间状态，不阻塞验收。

## 5. 未验证项

- 无。所有验收卡片列出的 direct-local 检查项均已执行并通过。

## 6. 最终结论

```
PASS_LOCAL
```

## 7. 回修项

无。本验收轮次未发现需要回修的问题。可进入下一 L3（deploy_008）或 L2 整体验收。

---

*验收 agent: independent acceptance sub-agent (stage4-l3-orchestrator)*
*时间: 2026-06-20*

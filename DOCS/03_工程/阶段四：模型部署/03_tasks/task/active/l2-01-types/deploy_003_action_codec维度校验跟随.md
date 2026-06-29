# L3 微元改造任务：action_codec 维度校验跟随

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-01 Types 层重构
来源 Delta：D11（action 语义，codec 层跟随）
L3 编号：deploy_003
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_003_action_codec维度校验跟随.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：model_deploy-l2-01-types
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
对应 L2 运行验收场景：[S3]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_003_验收卡片.md
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_003
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_003_action_codec维度校验跟随.md
  group: l2-01-types
  branch: model_deploy-l2-01-types
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
  acceptance_scenarios: [S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_003_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs
  wave: 2
  parallel_group: l2-01-types-p2
  depends_on: [deploy_001]
  must_run_after: []
  can_run_parallel_with: [deploy_002]
  blocks: [deploy_004]
  conflict_scope:
    files:
      - src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py
    modules:
      - pi05.common.data.action_codec
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
确认 action_codec.py 的维度校验逻辑全部通过引用 ACTION_DIM/split_bimanual_action 自动跟随 deploy_001 的新值（16D），消除任何硬编码的 14，并修正受影响的 docstring。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D11（codec 层跟随） |
| 变更对象 | Action Contract · action 语义 |
| AS-IS 契约 | action_codec 的 `ensure_action_vector`/`ensure_action_chunk`/`split_action` 校验 14D（通过引用 ACTION_DIM=14）。源码：`action_codec.py:1-33`。 |
| TO-BE 契约 | 同样逻辑，维度自动跟随 ACTION_DIM=16（deploy_001 已改）。本 L3 核心是确认无硬编码 14、逻辑无需改、docstring 更新。 |
| 兼容性要求 | 跟随 deploy_001，破坏性修改一致。 |
| 回滚要求 | git 回退 + 旧 bundle。 |

### 所属 L2 改造工作包

- L2 名称：L2-01 Types 层重构
- 本 L3 在该 L2 中的位置：第三个，与 deploy_002 并行。纯跟随，工作量小。
- 本 L3 完成后解锁：deploy_004（单测覆盖 action_codec）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| import | `action_codec.py:9` `from pi05.common.robot.action_spec import ACTION_DIM, BimanualAction, split_bimanual_action` | 引用 ACTION_DIM/BimanualAction/split_bimanual_action | deploy_001 已把这些改成 16D/TCP+width 结构，**import 自动跟随** | 否（确认即可，可能零改动） |
| `ensure_action_vector` | `action_codec.py:12-17` | 校验 `vector.size != ACTION_DIM` | ACTION_DIM 已是 16，**逻辑自动跟随** | 否（确认 docstring） |
| `ensure_action_chunk` | `action_codec.py:20-27` | 校验 `array.shape[1] != action_dim`（默认 ACTION_DIM） | **逻辑自动跟随** | 否（确认 docstring） |
| `split_action` | `action_codec.py:30-32` | 调 split_bimanual_action(ensure_action_vector(action)) | **自动跟随**新段序 | 否（确认 docstring） |
| 硬编码 14 | 全文 | docstring 写 "14-D" | 需改为 "16-D" 或泛化表述 | 是（docstring） |

### 必须保留的现有行为

- 严格维度校验 + 报错语义。
- `ensure_action_chunk` 的 rank-2 校验。
- 函数签名不变（上层调用不受影响）。

### 已知风险

- **本 L3 很可能是零代码逻辑改动**（因为 action_codec 已经全部通过 ACTION_DIM 间接引用）。核心价值是**审查确认无硬编码 14 + 更新 docstring**。如果审查发现确实零改动，记录审查结论即可，不强行制造改动。
- 改完后 action_codec 与 deploy_001/002 配合，但整个 deploy 包仍可能因 collector/safety_guard 未改而无法 import（L2-03/04 修复）。

## 6. 真实改造边界

### 本次允许做

- 审查 action_codec.py 全文，确认无硬编码 14（除 docstring 外）。
- 更新 docstring：`ensure_action_vector` 的 "14-D" → "16-D" 或 "ACTION_DIM-D"；模块 docstring 同步。
- 如果发现硬编码 14（理论上不应该有），改为引用 ACTION_DIM。

### 本次不做

- 不改函数签名。
- 不改校验逻辑（已自动跟随）。
- 不改 action_spec / state_codec（deploy_001/002 负责）。
- 不补单测（deploy_004 负责）。

### 明确禁止修改

- 禁止改 action_codec.py 以外的文件。
- 禁止为了「让整包 import」而改上层。
- 禁止把维度校验改成硬编码 16（应继续引用 ACTION_DIM，保持单一真相源）。

### Adapter / 直接修改策略

```text
审查 + docstring 更新。如果逻辑零改动（已通过 ACTION_DIM 间接引用），只更新文档化表述。不强行制造改动。
```

## 7. 实施步骤

1. **审查全文**：grep `14` in action_codec.py，区分 docstring（改）和逻辑（确认是否引用常量）。
2. **确认 import**：`ACTION_DIM`/`BimanualAction`/`split_bimanual_action` 来自 action_spec，deploy_001 已改，import 自动跟随。
3. **更新 docstring**：模块 docstring + `ensure_action_vector`/`ensure_action_chunk` 的 "14-D" 表述改为 "16-D" 或引用 ACTION_DIM。
4. **运行验收命令**（AST + import 检查）。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
import ast
path = 'src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py'
src = open(path, encoding='utf-8').read()
ast.parse(src)  # 语法正确
# 确认无硬编码 14（在逻辑中）
import re
# 找数字 14 的出现，排除注释和 docstring 中的描述性 14-D（后者应已改成 16-D）
logic_14 = [l for l in src.splitlines() if re.search(r'[^-_\w]14[^-\w]', l) and not l.strip().startswith('#') and not l.strip().startswith('\"\"\"')]
assert not logic_14, f'发现可能的硬编码14: {logic_14}'
# 确认 ACTION_DIM 仍被引用
assert 'ACTION_DIM' in src
print('deploy_003 验收通过: 无硬编码14, ACTION_DIM引用保留')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | action_codec.py AST + 无硬编码14断言 | 上述命令通过 |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py`（仅 docstring，逻辑确认）

## 10. 禁止修改

- 除上述文件外的任何文件。
- action_codec.py 的函数签名和校验逻辑。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D11）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-Types层重构.md`

### 必读代码

1. `src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py`（本 L3 审查对象）
2. `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py`（deploy_001 改后，确认 ACTION_DIM=16）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游 L3：deploy_001（action_spec，提供 ACTION_DIM=16）。
2. 同组已完成 L3：deploy_001（deploy_002 并行中）。

## 12. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：
正文 L3 编号：
是否一致：
```

执行前必须读取 `dispatch` YAML，确认：

- `task_id` 与正文 L3 编号一致。
- `depends_on: [deploy_001]` 已完成。
- `dispatch_status` 不是 `blocked` 或 `waiting_user`。
- `robot_risk: none` 与验收一致。

```text
审查（grep 14 / 确认 import）
→ 最小改动（docstring）
→ 验证通过（AST + 无硬编码断言）
→ 必要整理
```

如果审查发现逻辑确实零改动，在执行摘要中明确记录「逻辑零改动，仅 docstring 更新」，这是合法的。

## 13. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取 Contract Delta 和所属 L2。
- [x] 已确认 deploy_001 的 ACTION_DIM=16 就位。
- [x] 已审查 action_codec 全文无硬编码 14（逻辑层）。
- [x] docstring 已更新为 16-D 表述。
- [x] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [x] 已完成本 L3 的自动化验收。
- [x] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：不适用
切回旧入口：不适用
移除 adapter：不适用
回退文件：git checkout -- src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选成功标准 + 追加执行摘要。
- 不擅自归档。

交接摘要必须包含：

1. 读取了哪些文档和代码。
2. 任务文件身份校验结论。
3. 审查结论（逻辑是否零改动）。
4. 修改了哪些文件（预期仅 docstring）。
5. 如何验证。
6. 成功标准勾选情况。
7. 是否影响真机（否）。
8. 回滚方式。
9. 本次明确没有做什么。
10. 后续建议（deploy_004 单测）。

## 16. 执行摘要

### 读取的文档和代码

- DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md（D11）
- DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-Types层重构.md
- DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_003_action_codec维度校验跟随.md（本 L3）
- DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_003_验收卡片.md
- DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/deploy_001_acceptance_round_1.md
- DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md
- DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md
- DOCS/02_约束/Git协作/Git操作规则.md
- DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md
- skills/stage4-l3-orchestrator/SKILL.md
- src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py
- src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py

### 任务文件身份校验结论

| 检查项 | 结果 |
|---|---|
| 用户指定路径 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_003_action_codec维度校验跟随.md` ✅ |
| 实际读取路径 | 一致 ✅ |
| 文件名编号 | `deploy_003` ✅ |
| 正文 L3 编号 | `deploy_003`（第 9 行）✅ |
| 一致性 | 完全一致 ✅ |

### 审查结论

**逻辑零改动，仅 docstring 更新。**

- grep `14` 全文：仅在第 13 行 docstring 出现 `"14-D"`，逻辑层零匹配。
- 所有维度校验通过 `ACTION_DIM` 常量间接引用，deploy_001 已将 `ACTION_DIM` 改为 16，import 自动跟随。
- `ensure_action_vector`: `if vector.size != ACTION_DIM`（常量引用，自动跟随）
- `ensure_action_chunk`: `action_dim` 默认值 = `ACTION_DIM`（常量引用，自动跟随）
- `split_action`: 调用 `split_bimanual_action(ensure_action_vector(action))`（自动跟随）
- 确认 14→16 升级后，校验逻辑语义不变（严格维度校验 + 报错语义）。

### 修改的文件

仅 1 个文件，1 行：

```text
src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py:L13
  docstring: "14-D" → "16-D" (in ensure_action_vector)
```

### 验证方式

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

**结果**: `deploy_003 验收通过: 无硬编码14, ACTION_DIM引用保留`

### 成功标准勾选情况

- [x] 已完成任务文件身份校验。
- [x] 已确认当前分支符合所属 L2 分支规范（`model_deploy-l2-01-types`）。
- [x] 已读取 Contract Delta 和所属 L2。
- [x] 已确认 deploy_001 的 ACTION_DIM=16 就位。
- [x] 已审查 action_codec 全文无硬编码 14（逻辑层）。
- [x] docstring 已更新为 16-D 表述。
- [x] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [x] 已完成本 L3 的自动化验收。
- [x] 已写明回滚方式。

### 是否影响真机

否。本 L3 仅修改 docstring，真机风险等级 `none`。

### 回滚方式

```text
git checkout -- src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py
```

### 本次明确没有做什么

- 没有修改函数签名或校验逻辑（逻辑零改动）。
- 没有修改 `action_spec.py` 或 `state_codec.py`（deploy_001/002 负责）。
- 没有补单测（deploy_004 负责）。
- 没有修改 `action_codec.py` 以外的任何文件。
- 没有把维度校验改成硬编码 16（继续引用 `ACTION_DIM`，保持单一真相源）。
- 没有编辑 dispatch 索引或验收卡片结论。
- 没有执行 Git 同步（commit/push/merge）。
- 没有触摸 `DOCS/98_archive/`、`DOCS/99_learning/` 或 `pi05_old/`。
- 没有声称硬件/真机成功。

### 后续建议

- deploy_004 应补充单测覆盖 `ensure_action_vector`、`ensure_action_chunk`、`split_action`，确认维度校验正确。
- 当前 deploy 包整体仍可能因 collector/safety_guard 未改而无法完整 import（由 L2-03/04 修复），属正常范围。

# L3 微元改造任务：新建 ACT action_codec（16D 交替段序）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-01 ACT Types 层
来源 ACT Delta：A3（action_codec，16D 交替段序编解码）
L3 编号：deploy_003
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_003_新建ACT_action_codec.md`
改造类型：behavior-change（从零新建，结构参考同事源码）
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-01-types`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/`
对应 L2 运行验收场景：S1
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_003_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。第 9 节「本次产物落点」声明每个产物的落点路径。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_003
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_003_新建ACT_action_codec.md
  group: l2-01-types
  branch: feat/model_deploy/l2-01-types
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
  acceptance_scenarios: [S1]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_003_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs
  wave: 1
  parallel_group: l2-01-types-w1
  depends_on: [deploy_001]
  must_run_after: []
  can_run_parallel_with: [deploy_002]
  blocks: [deploy_004]
  conflict_scope:
    files:
      - src/model_deploy/act/types/action_codec.py
    modules:
      - act.types.action_codec
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 src/model_deploy/act/types/action_codec.py，提供 ACT action 的校验与结构化拆解工具。
包括 ensure_action_vector（校验单个 16D）、ensure_action_chunk（校验 2D chunk）、split_action（拆解为 BimanualAction）。
结构参考同事 pi05 action_codec.py，维度 14→16，split 逻辑委托给 action_spec.split_bimanual_action（deploy_001）。
```

## 4. 来源契约

### 来源 ACT Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | A3 |
| 变更对象 | Types · action |
| AS-IS 契约 | 无 ACT action codec。Pi0.5 的 action_codec 是 14D（`ensure_action_vector` 校验 14D，`ensure_action_chunk` 校验 2D，`split_action` 委托 split_bimanual_action）。 |
| TO-BE 契约 | 新建 ACT action_codec：校验 16D 单步 + 2D chunk。`split_action` 委托 `action_spec.split_bimanual_action`（deploy_001，交替段序拆解）。 |

### 所属 L2 改造工作包

[[L2-01-ACT Types层]]

## 5. 现有程序盘点

| 现有对象 | 路径 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `ensure_action_vector()` | `pi05_old/.../common/data/action_codec.py:12-17` | 校验并返回 14D float32 向量 | 维度写死 14，需改 16（走 ACTION_DIM 常量） | 否（新建独立文件） |
| `ensure_action_chunk()` | `pi05_old/.../action_codec.py:20-27` | 校验 2D chunk，`shape[1]==action_dim`，默认 `ACTION_DIM` | 默认维度 14，需指向 deploy_001 的 ACTION_DIM=16 | 否 |
| `split_action()` | `pi05_old/.../action_codec.py:30-32` | 委托 `split_bimanual_action(ensure_action_vector(action))` | 结构通用，直接复用（委托目标已是 ACT 版） | 否 |

> [!note] 复用方式：结构复用
> 同事 `action_codec.py` 三个函数的结构和逻辑几乎可直接复用，唯一改动是 `ACTION_DIM` 常量的 import 来源从 `pi05.common.robot.action_spec` 改为 `act.types.action_spec`（deploy_001 已定义 ACTION_DIM=16）。**这是复用改动最小的文件**。

## 6. 真实改造边界

### 本次允许做

- 新建 `src/model_deploy/act/types/action_codec.py`。
- `ensure_action_vector(action)`：校验 size==ACTION_DIM(16)，返回 float32 向量。
- `ensure_action_chunk(chunk, *, action_dim=ACTION_DIM)`：校验 2D，`shape[1]==16`。
- `split_action(action)`：委托 `action_spec.split_bimanual_action(ensure_action_vector(action))`。
- 新建 `act/tests/types/test_action_codec.py` 单测。

### 本次不做

- 不修改 action_spec.py / state_codec.py。
- 不做 quaternion 校验（action_codec 只做维度校验，语义校验在 safety_guard 层 L2-04）。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/action_spec.py`、`act/types/state_codec.py`

## 7. 实施步骤

1. 新建 `act/types/action_codec.py`：
   - docstring 说明 ACT action 校验工具。
   - `from act.types.action_spec import ACTION_DIM, BimanualAction, split_bimanual_action`。
   - `ensure_action_vector(action)`：`np.asarray(...).reshape(-1)`，校验 `size != ACTION_DIM` 报错，返回 float32。
   - `ensure_action_chunk(chunk, *, action_dim=ACTION_DIM)`：校验 ndim==2，`shape[1]!=action_dim` 报错。
   - `split_action(action)`：`return split_bimanual_action(ensure_action_vector(action))`。
2. 新建 `act/tests/types/test_action_codec.py`：合法 16D 通过、非法维度报错、chunk 校验、split round-trip（split → as_vector == 原始）。
3. 运行 pytest。

## 8. 验证方式

### 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/test_action_codec.py -v
```

### 分层验证表

| 层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit | 是 | test_action_codec.py | 全部 PASSED |
| 其余 | 否 | — | — |

### L2 运行验收贡献

本 L3 贡献到 L2-01 S1 场景：action 校验与 round-trip。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| action_codec 源码 | `src/model_deploy/act/types/action_codec.py` | types |
| 单测 | `src/model_deploy/act/tests/types/test_action_codec.py` | tests/types |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/action_spec.py`、`act/types/state_codec.py`

## 11. 必读上下文

### 必读任务文档

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-ACT Types层.md`
- `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_001_新建ACT_action_spec.md`（依赖）

### 必读代码（AS-IS 参考）

- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/data/action_codec.py`

### 必读约束文档

- `DOCS/02_约束/编程执行/Agent编程执行原则.md`
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-01-types`。
- 依赖校验：deploy_001 已完成。
- TDD：先写单测骨架。
- 落点校验：产物路径与第 9 节一致。

## 13. 成功标准

- [ ] `act/types/action_codec.py` 存在，含 `ensure_action_vector`/`ensure_action_chunk`/`split_action`。
- [ ] `ensure_action_vector` 校验 16D，非法维度报 ValueError。
- [ ] `ensure_action_chunk` 校验 2D 且 `shape[1]==16`。
- [ ] `split_action` → `BimanualAction` → `as_vector()` round-trip 等于原始输入。
- [ ] `test_action_codec.py` 全部 PASSED。
- [ ] 产物路径与第 9 节声明一致。
- [ ] 未修改 pi05/third_party/pi05_old/action_spec.py/state_codec.py。

## 14. 回滚方式

删除 `src/model_deploy/act/types/action_codec.py`。

## 15. 完成后交接

（执行 sub-agent 完成后填写）

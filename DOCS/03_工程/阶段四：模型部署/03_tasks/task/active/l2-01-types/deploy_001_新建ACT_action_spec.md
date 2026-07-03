# L3 微元改造任务：新建 ACT action_spec（16D TCP+width 结构）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-01 ACT Types 层
来源 ACT Delta：A3（action_codec + action_spec，16D 交替段序，绝对 TCP 目标）
L3 编号：deploy_001
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_001_新建ACT_action_spec.md`
改造类型：behavior-change（从零新建，结构参考同事源码）
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-01-types`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/`
对应 L2 运行验收场景：S1（Types 层维度与段序单测）
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_001_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。第 9 节「本次产物落点」声明每个产物的落点路径。验收 sub-agent 检查实际路径与声明不符时判 `FAIL_LOCAL`。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_001
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_001_新建ACT_action_spec.md
  group: l2-01-types
  branch: feat/model_deploy/l2-01-types
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
  acceptance_scenarios: [S1]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_001_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs
  wave: 1
  parallel_group: l2-01-types-w1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_002, deploy_003, deploy_004]
  conflict_scope:
    files:
      - src/model_deploy/act/types/action_spec.py
    modules:
      - act.types.action_spec
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 src/model_deploy/act/types/action_spec.py，定义 ACT 部署的 action/state 维度常量
（ACTION_DIM=16、STATE_DIM=16）和 16D action 的结构化拆解（BimanualAction + split_bimanual_action）。
action 段序为交替排列：left_tcp[7] + left_gripper_width[1] + right_tcp[7] + right_gripper_width[1]。
结构参考同事 pi05 action_spec.py，但维度从 14D 关节改为 16D TCP+width，删 hand_command_to_trigger。
```

## 4. 来源契约

### 来源 ACT Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | A3 |
| 变更对象 | Types · action |
| AS-IS 契约 | 无 ACT action codec。Pi0.5 的 action_spec 是 14D 关节空间（`ACTION_DIM=14`、`ARM_DOF=6`、`HAND_DOF=1`，段序 `[left_arm6, right_arm6, left_hand1, right_hand1]`）。 |
| TO-BE 契约 | 新建 ACT action_spec：`ACTION_DIM=16`/`STATE_DIM=16`。action 16D = `left_tcp[7] + left_gripper_width[1] + right_tcp[7] + right_gripper_width[1]`，**交替段序**。绝对 TCP 目标（`action_t = target at step t+1`）。语义依据：阶段二 `数据清洗交付说明.md` action 段。 |

### 所属 L2 改造工作包

[[L2-01-ACT Types层]]

## 5. 现有程序盘点

| 现有对象 | 路径 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `action_spec.py` 常量 | `pi05_old/.../common/robot/action_spec.py:15-19` | `ARM_DOF=6/HAND_DOF=1/ACTION_DIM=14/STATE_DIM=26/ARM_JOINT_NAMES` | 维度全错（14/26 vs 16/16）；`ARM_DOF`/`HAND_DOF` 语义不适用 TCP+width | 否（同事源码只读参考） |
| `BimanualAction` | `pi05_old/.../action_spec.py:22-39` | frozen dataclass，字段 `left_arm/right_arm/left_hand/right_hand`，`as_vector()` 拼 14D | 字段是关节/手，非 TCP/width；拼装段序是分组（左臂+右臂+双手）而非交替 | 否（新建独立文件） |
| `split_bimanual_action()` | `pi05_old/.../action_spec.py:42-52` | 14D → BimanualAction 拆解，按 `[left_arm6, right_arm6, hand×2]` 分组 | 段序分组，需改交替；维度校验写死 14 | 否（新建独立文件） |
| `hand_command_to_trigger()` | `pi05_old/.../action_spec.py:55-59` | 数据集手部尺度→trigger 0..1 | ACT 不用 trigger 语义，**不搬** | 否 |

> [!note] 复用方式：结构复用
> 同事 `action_spec.py` 的**结构骨架**（frozen dataclass + 常量定义 + split 函数）设计良好，作为模板参考。新建 `act/types/action_spec.py` 保留这个结构，但字段、维度、段序全部按 ACT 16D TCP+width 重写。**不是拷贝后改，是参考结构后新写**（因为字段和段序差异大）。

## 6. 真实改造边界

### 本次允许做

- 新建 `src/model_deploy/act/types/action_spec.py`。
- 新建 `src/model_deploy/act/types/__init__.py`（空包标记）。
- 定义常量：`ACTION_DIM=16`、`STATE_DIM=16`、`TCP_POSE_DOF=7`、`GRIPPER_WIDTH_DOF=1`。
- 定义 `BimanualAction` frozen dataclass：字段 `left_tcp_pose: np.ndarray[7]`、`left_gripper_width: float`、`right_tcp_pose: np.ndarray[7]`、`right_gripper_width: float`；`as_vector()` 按**交替段序**拼 16D。
- 定义 `split_bimanual_action(action)`：16D → BimanualAction，按交替段序拆解。
- 新建 `src/model_deploy/act/tests/types/test_action_spec.py` 单测。

### 本次不做

- 不修改 `src/model_deploy/pi05/` 任何文件（同事源码只读）。
- 不写 state_codec（deploy_002）、action_codec（deploy_003）。
- 不预留触觉段落（第一版不含）。
- 不做 quaternion 模长校验（本 L3 只定义结构，校验在 deploy_004 统一加）。

### 明确禁止修改

- `src/model_deploy/pi05/**`
- `src/model_deploy/third_party/**`
- `DOCS/03_工程/阶段四：模型部署/pi05_old/**`
- L2-02 及以后的任何代码

### Adapter 策略

无需 adapter。Types 层是地基，直接新建。

## 7. 实施步骤

1. 确认分支 `feat/model_deploy/l2-01-types` 已从 `model_deploy` 创建。
2. 新建目录 `src/model_deploy/act/types/` 和 `src/model_deploy/act/tests/types/`。
3. 新建 `act/types/__init__.py`（空文件）。
4. 新建 `act/types/action_spec.py`：
   - 模块 docstring：说明这是 ACT 部署的 action/state 维度契约，16D TCP+width。
   - 常量段：`TCP_POSE_DOF = 7`、`GRIPPER_WIDTH_DOF = 1`、`ACTION_DIM = 16`、`STATE_DIM = 16`。
   - `BimanualAction` dataclass：4 字段（left_tcp_pose/left_gripper_width/right_tcp_pose/right_gripper_width），`as_vector()` 交替拼接。
   - `split_bimanual_action(action)`：校验 size==16，按 `[0:7]→left_tcp, [7]→left_width, [8:15]→right_tcp, [15]→right_width` 拆解。
5. 新建 `act/tests/types/__init__.py` 和 `act/tests/__init__.py`（空文件，保证 pytest 收集）。
6. 新建 `act/tests/types/test_action_spec.py`：覆盖 split→as_vector round-trip、维度校验、段序正确性。
7. 运行 `pytest src/model_deploy/act/tests/types/test_action_spec.py -v`。

## 8. 验证方式

### 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/test_action_spec.py -v
```

### 分层验证表

| 层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit | 是 | test_action_spec.py | 全部 PASSED |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| real-robot | 否 | — | — |

### 验收证据落点

- 测试输出：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/deploy_001_pytest.txt`
- 执行摘要：写入本 L3 文件末尾「完成后交接」

### L2 运行验收贡献

本 L3 贡献到 L2-01 S1 场景：action 维度常量与结构化拆解。

## 9. 允许修改

> [!warning] 产物落点声明（必填）
> 本节每个产物必须标注落点路径，且符合 `ACT代码树分层与产物落点约束.md`。

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| action_spec 源码 | `src/model_deploy/act/types/action_spec.py` | types |
| 包标记 | `src/model_deploy/act/types/__init__.py` | types |
| 测试包标记 | `src/model_deploy/act/tests/__init__.py`、`src/model_deploy/act/tests/types/__init__.py` | tests/types |
| 单测 | `src/model_deploy/act/tests/types/test_action_spec.py` | tests/types |

## 10. 禁止修改

- `src/model_deploy/pi05/**`（同事源码，只读）
- `src/model_deploy/third_party/**`
- `DOCS/03_工程/阶段四：模型部署/pi05_old/**`
- L2-02 及以后所有代码

## 11. 必读上下文

### 必读任务文档

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-ACT Types层.md`
- `DOCS/03_工程/阶段四：模型部署/01_contracts/ACT部署契约.md`（action 段序契约）
- `DOCS/01_知识/阶段二：数据清洗/数据清洗交付说明.md`（action 16D 权威定义）

### 必读代码（AS-IS 参考）

- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/robot/action_spec.py`（结构参考）

### 必读约束文档

- `DOCS/02_约束/编程执行/Agent编程执行原则.md`
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：执行 sub-agent 确认当前分支为 `feat/model_deploy/l2-01-types`。
- dispatch YAML 校验：task_id/path/branch 与本文件一致。
- TDD：先写单测骨架（round-trip、维度校验），再实现 action_spec.py。
- 落点校验：产物路径必须与第 9 节声明一致。

## 13. 成功标准

- [ ] `src/model_deploy/act/types/action_spec.py` 存在，含 `ACTION_DIM=16`/`STATE_DIM=16` 常量。
- [ ] `BimanualAction` 字段为 left_tcp_pose/left_gripper_width/right_tcp_pose/right_gripper_width。
- [ ] `as_vector()` 输出 16D，段序交替（左tcp7+左width1+右tcp7+右width1）。
- [ ] `split_bimanual_action()` 正确拆解 16D。
- [ ] `test_action_spec.py` 全部 PASSED。
- [ ] 产物路径与第 9 节声明一致。
- [ ] 未修改 pi05/third_party/pi05_old。

## 14. 回滚方式

删除 `src/model_deploy/act/types/action_spec.py`。因分支隔离，可直接 `git checkout -- ...` 或放弃分支。

## 15. 完成后交接

（执行 sub-agent 完成后填写）

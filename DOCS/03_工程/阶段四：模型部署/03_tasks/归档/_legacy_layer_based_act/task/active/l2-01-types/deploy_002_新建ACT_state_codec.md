# L3 微元改造任务：新建 ACT state_codec（16D 分组段序）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-01 ACT Types 层
来源 ACT Delta：A2（state_codec，16D 分组段序，不含触觉，边界校验 quaternion 模长）
L3 编号：deploy_002
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_002_新建ACT_state_codec.md`
改造类型：behavior-change（从零新建，结构参考同事源码）
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-01-types`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/`
对应 L2 运行验收场景：S1
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_002_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。第 9 节「本次产物落点」声明每个产物的落点路径。验收 sub-agent 检查实际路径与声明不符时判 `FAIL_LOCAL`。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_002
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_002_新建ACT_state_codec.md
  group: l2-01-types
  branch: feat/model_deploy/l2-01-types
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
  acceptance_scenarios: [S1]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_002_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs
  wave: 1
  parallel_group: l2-01-types-w1
  depends_on: [deploy_001]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_004]
  conflict_scope:
    files:
      - src/model_deploy/act/types/state_codec.py
    modules:
      - act.types.state_codec
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 src/model_deploy/act/types/state_codec.py，定义 ACT 部署的 16D observation.state 编解码。
state 段序为分组排列：left_tcp_pose[7] + right_tcp_pose[7] + left_gripper_width[1] + right_gripper_width[1]。
结构参考同事 pi05 state_codec.py，但维度从 26D 关节改为 16D TCP+width，编码时校验 quaternion 模长≈1。
不含触觉。不搬 decode_picotele_proprioception。
```

## 4. 来源契约

### 来源 ACT Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | A2 |
| 变更对象 | Types · state |
| AS-IS 契约 | 无 ACT state codec。Pi0.5 的 state_codec 是 26D 关节语义（`BimanualState` 字段 left_arm_q/right_arm_q/left_hand_q/left_ee_pos/left_ee_rpy，`encode_bimanual_state` 拼 26D）。 |
| TO-BE 契约 | 新建 ACT state_codec：16D = `left_tcp_pose[7] + right_tcp_pose[7] + left_gripper_width[1] + right_gripper_width[1]`，**分组段序**。pose 用 quaternion xyzw 归一化（模长≈1）；position 单位 m；夹爪 width[0,1]。不含触觉。与阶段二数据清洗 observation.state（去掉触觉段后）同构。 |

### 所属 L2 改造工作包

[[L2-01-ACT Types层]]

## 5. 现有程序盘点

| 现有对象 | 路径 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `BimanualState` | `pi05_old/.../common/data/state_codec.py:13-24` | frozen dataclass，8 字段（arm_q/hand_q/ee_pos/ee_rpy），拼 26D | 字段全错（关节/rpy vs TCP/quaternion）；维度 26 vs 16 | 否（新建独立文件） |
| `encode_bimanual_state()` | `pi05_old/.../state_codec.py:27-43` | 拼 26D 向量，末尾校验 `vector.size != STATE_DIM` | 段序分组但内容不同；无 quaternion 模长校验 | 否 |
| `_vector()` 辅助 | `pi05_old/.../state_codec.py:56-60` | 校验向量维度，报错含 name | 通用，可参考 | 否 |
| `decode_picotele_proprioception()` | `pi05_old/.../state_codec.py:46-53` | 解码 picotele [right6,left6] 顺序 | picotele 遗留，**ACT 不搬** | 否 |

> [!note] 复用方式：结构复用
> 同事 `state_codec.py` 的结构（frozen dataclass + encode 函数 + `_vector` 维度校验辅助 + 末尾 `STATE_DIM` 校验）保留。新建 `act/types/state_codec.py` 沿用此结构，字段改为 TCP+width，维度 26→16，并在 encode 时新增 quaternion 模长校验。

## 6. 真实改造边界

### 本次允许做

- 新建 `src/model_deploy/act/types/state_codec.py`。
- 定义 `ActBimanualState` frozen dataclass：字段 `left_tcp_pose: np.ndarray[7]`、`right_tcp_pose: np.ndarray[7]`、`left_gripper_width: float`、`right_gripper_width: float`。
- 定义 `encode_state(state)`：按**分组段序**拼 16D（左tcp7+右tcp7+左width1+右width1）。
- 定义 `quaternion_norm(quat)` 辅助：计算四元数模长。
- encode 时校验 quaternion 模长≈1（容差 1e-3）；不通过抛 ValueError。
- 新建 `act/tests/types/test_state_codec.py` 单测。

### 本次不做

- 不修改 action_spec.py（deploy_001 已完成）。
- 不预留触觉段落。
- 不做 width 值域 [0,1] 校验（在 deploy_004 统一加，或按 config 开关）。

### 明确禁止修改

- `src/model_deploy/pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/action_spec.py`（deploy_001 产物）

## 7. 实施步骤

1. 新建 `act/types/state_codec.py`：
   - docstring 说明 ACT 16D state 契约（分组段序，不含触觉）。
   - `from act.types.action_spec import STATE_DIM, TCP_POSE_DOF`（引用 deploy_001 常量）。
   - `ActBimanualState` dataclass（4 字段）。
   - `encode_state(state)`：拼接 16D，过程中校验每段维度 + quaternion 模长。
   - `_vector(value, dim, name)` 辅助（参考同事实现）。
   - `_check_quaternion(quat, name)` 辅助：`norm = np.linalg.norm(quat)`，`abs(norm-1.0) > 1e-3` 则 raise。
2. 新建 `act/tests/types/test_state_codec.py`：合法 state 编码、维度校验、quaternion 模长校验、段序正确性。
3. 运行 pytest。

## 8. 验证方式

### 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/test_state_codec.py -v
```

### 分层验证表

| 层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit | 是 | test_state_codec.py | 全部 PASSED |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| real-robot | 否 | — | — |

### L2 运行验收贡献

本 L3 贡献到 L2-01 S1 场景：state 维度与段序单测、quaternion 模长校验。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| state_codec 源码 | `src/model_deploy/act/types/state_codec.py` | types |
| 单测 | `src/model_deploy/act/tests/types/test_state_codec.py` | tests/types |

## 10. 禁止修改

- `src/model_deploy/pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/action_spec.py`（deploy_001 产物）

## 11. 必读上下文

### 必读任务文档

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-ACT Types层.md`
- `DOCS/03_工程/阶段四：模型部署/01_contracts/ACT部署契约.md`（state 段序契约）
- `DOCS/01_知识/阶段二：数据清洗/数据清洗交付说明.md`（state 16D 定义，去掉触觉段）

### 必读代码（AS-IS 参考）

- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/data/state_codec.py`

### 必读约束文档

- `DOCS/02_约束/编程执行/Agent编程执行原则.md`
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`（第三节 shape 边界校验）
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-01-types`。
- 依赖校验：deploy_001 已完成（`act/types/action_spec.py` 存在且 `STATE_DIM`/`TCP_POSE_DOF` 可 import）。
- TDD：先写单测骨架，再实现。
- 落点校验：产物路径与第 9 节一致。

## 13. 成功标准

- [ ] `act/types/state_codec.py` 存在。
- [ ] `ActBimanualState` 字段为 left_tcp_pose/right_tcp_pose/left_gripper_width/right_gripper_width。
- [ ] `encode_state()` 输出 16D，段序分组（左tcp7+右tcp7+左width1+右width1）。
- [ ] quaternion 模长≠1（容差 1e-3）时抛 ValueError。
- [ ] `test_state_codec.py` 全部 PASSED。
- [ ] 产物路径与第 9 节声明一致。
- [ ] 未修改 pi05/third_party/pi05_old/action_spec.py。

## 14. 回滚方式

删除 `src/model_deploy/act/types/state_codec.py`。

## 15. 完成后交接

（执行 sub-agent 完成后填写）

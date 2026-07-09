# L3 微元改造任务：16D 状态规格 StateSpec

## 1. 任务定位

- 所属阶段：阶段四：模型部署
- 所属 L1：ACT
- 所属 L2：`l2-01-external-contract`（外部参数加载与契约校验闭环）
L3 编号：deploy_002
- 改造类型：`source-adaptation`
- 当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_002_16D状态规格StateSpec.md`
- 验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_002_验收卡片.md`
- 验收证据目录：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/evidence/deploy_002/`
- 验收模式：`direct-local`
- 辅助验收模式：`[]`
- 本地验收是否必须：`true`
- 真机风险等级：`none`
- L2 分支：`feat/model_deploy/l2-01-external-contract`
- 集成分支：`model_deploy`

本任务文件中所有路径均相对于仓库根目录 `/home/hit/ROS/worktrees/l2-01`，除非显式标注为绝对路径。执行 Agent 在引用任何路径时，须以仓库根为基准解析，不得使用相对当前工作目录的隐式推断。

本任务文件中的 callout（`> [!warning]`、`> [!info]`、`> [!note]`）为强制约束语义，非装饰性排版。Agent 须将 callout 内容纳入执行约束检查清单，不得跳过。

> [!warning] 产物落点约束
> 本 L3 的产物只能落在 `src/model_deploy/act/types/state_spec.py` 与 `src/model_deploy/act/tests/types/test_state_spec.py` 两个文件。任何超出此范围的文件写入均视为越界。`__init__.py` 的修改仅限于为新增模块补全 import 导出，不得引入额外逻辑。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_002
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_002_16D状态规格StateSpec.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S1, S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_002_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 1
  parallel_group: l2-01-external-contract-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_001, deploy_003]
  blocks: []
  conflict_scope:
    files: [src/model_deploy/act/types/state_spec.py, src/model_deploy/act/tests/types/test_state_spec.py]
    modules: [model_deploy.act.types.state_spec]
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行/验收边界

- 执行 Agent：在 `feat/model_deploy/l2-01-external-contract` 分支上完成本 L3 声明的全部产物，运行必跑命令，将证据归档至验收证据目录。
- 验收 Agent：只读模式，依据验收卡片逐条核验，不得修改源码、测试、dispatch 或 Git 状态。
- 本 L3 无真机风险，全部验证在本地完成。
- 本 L3 与 `deploy_001`、`deploy_003` 可并行执行，三者产物文件无交集，无须互相等待。

## 3. 本次唯一目标

定义 16D observation state 的维度、段序、字段语义和值域，封装为 `StateSpec` frozen dataclass，提供 `ensure_state_vector` 和 `encode_state` 两个纯函数，作为 ACT 模型部署链路上 state 维度契约的底层来源。

```text
STATE_DIM = 16
segment layout:
  left_tcp_pose        : [0:7)   xyz(3) + quaternion(4)
  right_tcp_pose       : [7:14)  xyz(3) + quaternion(4)
  left_gripper_width   : [14:15) float
  right_gripper_width  : [15:16) float
```

## 4. 所属 L2 边界与设计来源

所属 L2 `l2-01-external-contract` 负责：
- 将外部部署参数（模型路径、维度、段序、采样率等）加载为运行时配置对象。
- 对载入参数进行契约校验，确保维度、字段、值域符合模型推理期望。
- 暴露统一的 types 层契约常量与校验函数，供 config / runtime / service 层引用。

所属 L2 `l2-01-external-contract` 不负责：
- 模型推理执行（属于后续推理 L2）。
- 真机通讯与 topic 订阅（属于 service / runtime 层）。
- ActionChunk 采样与平滑策略（属于动作链路 L2）。

本 L3 在 L2 中的位置：
- 位于 types 层最底层，是 state 维度契约的唯一定义来源。
- 被 `deploy_008` RuntimeConfig 引用 `state_dim=16` 作为合法配置载入（S1）的依据。
- 被 `deploy_009` 契约校验引用 `ensure_state_vector` 作为非法维度失败（S2）的执行点。
- 本 L3 只产出契约定义与校验函数，不依赖任何 config / runtime / service 层产物。

必读 L2 设计文档：
1. `DOCS/03_工程/阶段四：模型部署/01_overview/L2总览.md`
2. `DOCS/03_工程/阶段四：模型部署/02_design/00_L2设计总纲.md`
3. `DOCS/03_工程/阶段四：模型部署/02_design/01_L2-01-external-contract设计.md`
4. `DOCS/03_工程/阶段四：模型部署/02_design/06_types层设计.md`
5. `DOCS/03_工程/阶段四：模型部署/02_design/08_契约校验设计.md`
6. `DOCS/03_工程/阶段四：模型部署/02_design/09_配置加载设计.md`
7. `DOCS/03_工程/阶段四：模型部署/03_tasks/dispatch/l2-01-external-contract_dispatch.yaml`

## 5. Pi0.5 源码盘点

| 源码路径 | 关键符号 | 维度/语义 | 处置 |
| --- | --- | --- | --- |
| `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/data/state_codec.py` | `STATE_DIM` | `26` | 不照搬，ACT 为 16D |
| 同上 | `BimanualState` | frozen dataclass，字段为 left_arm_q / right_arm_q / left_hand_q / right_hand_q / left_ee_pos / left_ee_rpy / right_ee_pos / right_ee_rpy | 保留 frozen dataclass 模式，字段语义替换为 TCP pose + gripper width |
| 同上 | `encode_bimanual_state(state) -> np.ndarray` | 26D float32，拼接 left_arm(6)+right_arm(6)+left_hand(1)+right_hand(1)+left_ee_pos(3)+left_ee_rpy(3)+right_ee_pos(3)+right_ee_rpy(3) | 保留 encode 拼接模式，维度重排为 16D TCP 布局 |
| `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/robot/action_spec.py` | `STATE_DIM` | `26` | 不照搬，ACT 为 16D |

必须保留的源码启发：
- `BimanualState` 使用 frozen dataclass 携带不可变契约定义，这一模式适用于 ACT 的 16D 段定义。
- `encode_bimanual_state` 作为纯函数将结构化字段拼接为 flat 向量并强制 float32，这一模式适用于 ACT 的 `encode_state`。

禁止照搬：
- 26D 维度布局（left_arm_q / right_arm_q 等关节角语义）。
- joint angle 语义字段命名。
- left_ee_rpy 的 RPY 表示（ACT 使用 quaternion）。

已知风险：
- TCP pose 中 quaternion 的分量顺序约定（wxyz 还是 xyzw）需与上游发布方及模型训练侧一致。本 L3 只定义段位与维度，不固化四元数内部顺序约定；四元数顺序约定由后续 runtime / service 层在订阅时对齐，并在 `deploy_009` 契约校验时以注释标注。

## 6. ACT 微元与真实实现边界

允许做：
- 定义 `STATE_DIM=16` 常量及四段维度常量（`LEFT_TCP_POSE_DIM=7`、`RIGHT_TCP_POSE_DIM=7`、`LEFT_GRIPPER_WIDTH_DIM=1`、`RIGHT_GRIPPER_WIDTH_DIM=1`）。
- 定义 `StateSpec` frozen dataclass，携带段名、段维度、段偏移的不可变元数据。
- 实现 `ensure_state_vector(flat) -> np.ndarray`：校验 flat 向量长度为 16，返回 float32 数组，长度不符时抛 `ValueError`。
- 实现 `encode_state(left_tcp_pose, right_tcp_pose, left_gripper_width, right_gripper_width) -> np.ndarray`：将四段结构化输入拼接为 16D float32 向量。

不做：
- 不订阅任何 ROS topic，不做新鲜度 / 超时检查。
- 不定义 ActionChunk 或动作平滑策略。
- 不固化 quaternion 内部分量顺序约定（仅定义段维度）。
- 不实现 TCP pose 的坐标系转换。

禁止修改：
- `pi05/` 目录下任何文件（READ-ONLY 参考）。
- config / repo / service / runtime / ui 层任何文件。
- 其他 L3 任务的产物文件。
- dispatch 文件与归档目录。

函数/class 策略：
- `StateSpec` 采用 frozen dataclass，因其承载 16D 段定义作为不可变契约，frozen 语义防止运行时被意外篡改。
- `ensure_state_vector` 与 `encode_state` 为纯函数，无副作用、无状态、可被任意层安全调用。

## 7. 六层产物落点

| 层 | 是否产物 | 产物文件 | 说明 |
| --- | --- | --- | --- |
| types | 是 | `src/model_deploy/act/types/state_spec.py` | StateSpec frozen dataclass + STATE_DIM + ensure_state_vector + encode_state |
| tests | 是 | `src/model_deploy/act/tests/types/test_state_spec.py` | 维度校验、encode 布局、frozen 语义单测 |
| config | 否 | — | 不涉及 |
| repo | 否 | — | 不涉及 |
| service | 否 | — | 不涉及 |
| runtime | 否 | — | 不涉及 |

对应六层设计文档：`DOCS/03_工程/阶段四：模型部署/02_design/06_types层设计.md`。

## 8. 文件内 3.5 层功能微元

| 产物文件 | 微元 | 类型 | 说明 |
| --- | --- | --- | --- |
| `src/model_deploy/act/types/state_spec.py` | `STATE_DIM` | 数据（常量） | `= 16`，ACT observation state 总维度 |
| 同上 | `LEFT_TCP_POSE_DIM` | 数据（常量） | `= 7`，xyz(3)+quaternion(4) |
| 同上 | `RIGHT_TCP_POSE_DIM` | 数据（常量） | `= 7`，xyz(3)+quaternion(4) |
| 同上 | `LEFT_GRIPPER_WIDTH_DIM` | 数据（常量） | `= 1` |
| 同上 | `RIGHT_GRIPPER_WIDTH_DIM` | 数据（常量） | `= 1` |
| 同上 | `StateSpec` | 数据（frozen dataclass） | 携带段名列表、段维度列表、段偏移列表的不可变元数据 |
| 同上 | `ensure_state_vector(flat)` | 计算函数 | 校验 flat 长度==16，返回 float32 np.ndarray，不符抛 ValueError |
| 同上 | `encode_state(left_tcp_pose, right_tcp_pose, left_gripper_width, right_gripper_width)` | 计算函数 | 拼接四段为 16D float32 np.ndarray |

段布局（load-bearing）：

```text
offset 0  : left_tcp_pose        dim 7   [0:7)
offset 7  : right_tcp_pose       dim 7   [7:14)
offset 14 : left_gripper_width   dim 1   [14:15)
offset 15 : right_gripper_width  dim 1   [15:16)
total                          dim 16
```

## 9. 实施步骤

1. 创建 `src/model_deploy/act/types/state_spec.py`，定义 `STATE_DIM=16` 及四段维度常量（`LEFT_TCP_POSE_DIM=7`、`RIGHT_TCP_POSE_DIM=7`、`LEFT_GRIPPER_WIDTH_DIM=1`、`RIGHT_GRIPPER_WIDTH_DIM=1`）。
2. 定义 `StateSpec` frozen dataclass，字段携带段名列表（`segment_names`）、段维度列表（`segment_dims`）、段偏移列表（`segment_offsets`），并提供 `total_dim` 属性返回 16。偏移依据段序计算：left_tcp_pose[0:7)、right_tcp_pose[7:14)、left_gripper_width[14:15)、right_gripper_width[15:16)。
3. 实现 `ensure_state_vector(flat) -> np.ndarray`：接受 list / tuple / np.ndarray，校验展平后长度==16，返回 `np.asarray(flat, dtype=np.float32)`；长度不符时抛 `ValueError` 并在消息中标注期望 16 与实际长度。
4. 实现 `encode_state(left_tcp_pose, right_tcp_pose, left_gripper_width, right_gripper_width) -> np.ndarray`：校验四段维度分别为 7/7/1/1，`np.concatenate` 为 16D float32 数组并返回；可复用 `ensure_state_vector` 对最终结果做一次维度校验。
5. 创建 `src/model_deploy/act/tests/types/test_state_spec.py`，覆盖：合法 16D 向量通过 `ensure_state_vector`；长度 15 与 17 抛 `ValueError`；`encode_state` 输出长度 16 且四段位于正确偏移；`encode_state` 输出 dtype 为 float32；`StateSpec` 实例不可变（赋值抛 `FrozenInstanceError`）；`STATE_DIM==16`。
6. 必要时补全 `src/model_deploy/act/types/__init__.py` 与 `src/model_deploy/act/tests/types/__init__.py` 的 import 导出，仅限新增模块声明，不引入逻辑。
7. 运行必跑命令，确认全部用例通过、无 skip。

## 10. 允许修改

> [!warning] 产物落点约束
> 允许修改的文件仅限下表所列。任何不在表中的文件若被修改，视为越界，验收直接 FAIL。

| 文件 | 修改类型 | 说明 |
| --- | --- | --- |
| `src/model_deploy/act/types/state_spec.py` | 新建 | StateSpec + STATE_DIM + ensure_state_vector + encode_state |
| `src/model_deploy/act/tests/types/test_state_spec.py` | 新建 | 单元测试 |
| `src/model_deploy/act/types/__init__.py` | 修改（仅 import 导出） | 补全 `from .state_spec import ...`，不引入逻辑 |
| `src/model_deploy/act/tests/types/__init__.py` | 修改（仅 import 导出或留空） | 若需要则补全，不引入逻辑 |

## 11. 禁止修改

- `pi05/` 目录下任何文件（READ-ONLY 参考源码）。
- config / repo / service / runtime / ui 层任何文件。
- 其他 L3 任务（`deploy_001`、`deploy_003`、`deploy_008`、`deploy_009` 等）的产物文件。
- dispatch 文件（`03_tasks/dispatch/` 下任何 yaml）。
- 归档目录（`03_tasks/task/archive/`、`03_tasks/cards/archive/`）。
- 任何 DOCS 下设计文档、知识文档、约束文档。

## 12. 验证方式

必跑命令：

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_state_spec.py -v
```

分层验证：

| 验证类型 | 是否必跑 | 说明 |
| --- | --- | --- |
| unit | 是 | 维度校验、encode 布局、frozen 语义 |
| import | 是 | `from model_deploy.act.types.state_spec import StateSpec, STATE_DIM, ensure_state_vector, encode_state` 可正常导入 |
| integration | 否 | 本 L3 不涉及跨层集成 |
| 真机 | 否 | 真机风险 none，不适用 |

真机风险：不适用（`none`）。本 L3 为纯 types 层契约定义，不触碰真机接口。

验收证据落点：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/evidence/deploy_002/`，至少包含 pytest 完整输出（`pytest_state_spec.log`）。

L2 Gate 贡献：

| 场景 | 贡献 | 是否可独立闭环 |
| --- | --- | --- |
| S1 合法配置载入 | 提供 `state_dim=16` 契约常量与 `encode_state`，使 `deploy_008` RuntimeConfig 可引用合法维度 | 否，仍需 `deploy_008` |
| S2 非法维度失败 | 提供 `ensure_state_vector`，使 `deploy_009` 契约校验可对非 16D 输入抛 `ValueError` | 否，仍需 `deploy_009` |

本 L3 提供局部命令级验证（pytest 通过），但 S1/S2 的完整闭环仍需 `deploy_008` 与 `deploy_009` 在集成分支上联调。

## 13. 必读上下文

必读任务文档：
1. `DOCS/03_工程/阶段四：模型部署/03_tasks/dispatch/l2-01-external-contract_dispatch.yaml`
2. `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_001_*.md`（同组并行任务，了解契约层整体布局）
3. `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_003_*.md`（同组并行任务，了解动作侧契约）
4. `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_002_验收卡片.md`（本 L3 验收卡片）
5. `DOCS/03_工程/阶段四：模型部署/02_design/06_types层设计.md`
6. `DOCS/03_工程/阶段四：模型部署/02_design/01_L2-01-external-contract设计.md`

必读代码（READ-ONLY）：
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/data/state_codec.py`（`BimanualState`、`encode_bimanual_state`、`STATE_DIM`）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/robot/action_spec.py`（`STATE_DIM`）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/config/schema.py`（了解 Pi0.5 配置 schema 中维度字段命名风格，用于后续 `deploy_008` 对齐；本 L3 只读参考）

必读约束文档：
1. `DOCS/02_约束/文档体系/`（路径约定、callout 语义）
2. `DOCS/03_工程/阶段四：模型部署/02_design/00_L2设计总纲.md`（L2/L3 边界与产物落点约束）

历史任务：
- 无直接上游依赖（`depends_on: []`）。
- 无同组已完成任务可参考（`deploy_001`、`deploy_003` 与本任务并行启动）。

## 14. 执行要求

> [!warning] 身份校验
> 执行 Agent 启动后须先确认：当前 L3 编号为 `deploy_002`，所属 L2 为 `l2-01-external-contract`，当前分支为 `feat/model_deploy/l2-01-external-contract`。三者任一不符须立即停止并上报，不得自行切换分支或修改 dispatch。

dispatch 校验（执行前逐条核对）：
- [ ] `l3_id` == `deploy_002`
- [ ] `l2` == `l2-01-external-contract`
- [ ] `wave` == 1
- [ ] `parallel_group` == `l2-01-external-contract-p1`
- [ ] `depends_on` == `[]`
- [ ] `can_run_parallel_with` 含 `deploy_001`、`deploy_003`
- [ ] `改造类型` == `source-adaptation`
- [ ] `验收模式` == `direct-local`
- [ ] `真机风险` == `none`
- [ ] `acceptance_scenarios` 含 `S1`、`S2`
- [ ] `conflict_scope.files` 仅含两个目标文件

全文检查（产出后逐条核对）：
- [ ] `STATE_DIM == 16`，无 26D / 14D 残留
- [ ] 段布局为 left_tcp_pose(7)+right_tcp_pose(7)+left_gripper_width(1)+right_gripper_width(1)
- [ ] `StateSpec` 为 frozen dataclass
- [ ] `ensure_state_vector` 对非 16D 抛 `ValueError`
- [ ] `encode_state` 输出 float32 np.ndarray
- [ ] 无 `blend_steps` / `smoothstep` / `cross_chunk` / `rtc_alignment` / `action_smoothing` 字段
- [ ] 无 `pi05/` 目录修改
- [ ] 无 config / repo / service / runtime / ui 层修改
- [ ] 无关节角（`arm_q` / `hand_q`）语义字段
- [ ] pytest 全通过、无 skip

> [!note] 测试优先
> 优先保证 `test_state_spec.py` 覆盖合法 16D、非法维度（15/17）、encode 布局正确性、frozen 语义、dtype float32 五类用例。用例须自包含，不依赖真机或外部数据。

## 15. 成功标准

- [ ] `src/model_deploy/act/types/state_spec.py` 存在且可导入
- [ ] `src/model_deploy/act/tests/types/test_state_spec.py` 存在且可导入
- [ ] `STATE_DIM == 16`
- [ ] 四段维度常量分别为 7/7/1/1
- [ ] `StateSpec` 为 frozen dataclass，实例不可变
- [ ] `ensure_state_vector` 对 16D 输入返回 float32 np.ndarray
- [ ] `ensure_state_vector` 对非 16D 输入抛 `ValueError`
- [ ] `encode_state` 输出 16D float32 np.ndarray，四段位于正确偏移
- [ ] pytest 全部通过、无 skip
- [ ] 未修改 `pi05/` 及其他层文件
- [ ] 无 26D / 14D / 关节角语义残留
- [ ] 无 `blend_steps` / `smoothstep` / `cross_chunk` / `rtc_alignment` / `action_smoothing` 字段

## 16. 回滚方式

删除以下文件即可完全回滚本 L3：

- `src/model_deploy/act/types/state_spec.py`
- `src/model_deploy/act/tests/types/test_state_spec.py`

若 `__init__.py` 中仅新增了本 L3 的 import 导出行，回滚时一并移除该行；若 `__init__.py` 原本为空且未改动，无须处理。本 L3 无数据库迁移、无配置文件改动、无 Git 历史改写，回滚无副作用。

## 17. 完成后交接

执行 Agent 完成本 L3 后须：
1. 在 `feat/model_deploy/l2-01-external-contract` 分支上提交产物，commit message 以 `deploy_002:` 前缀。
2. 将 pytest 完整输出归档至 `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/evidence/deploy_002/pytest_state_spec.log`。
3. 在验收卡片对应位置填写验收结论（PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV）。
4. 通知验收 Agent 介入只读核验；验收通过后，本 L3 进入集成分支 `model_deploy` 的联调队列，等待 `deploy_008` 与 `deploy_009` 就绪后共同闭环 S1/S2。

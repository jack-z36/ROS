# L3微元改造任务：deploy_003 16D 动作规格 ActionSpec

## 1. 任务定位

> [!info] 任务标识
> - **阶段**: stage4 (阶段四：模型部署)
> - **L1**: model_deploy
> - **L2**: l2-01-external-contract (外部参数加载与契约校验闭环)
> - L3 编号：deploy_003
> - **改造类型**: source-adaptation
> - **验收模式**: direct-local
> - **本地验收必需**: true
> - **真机风险**: none

**产物路径**:

| 类型 | 路径 |
|------|------|
| 源码 | `src/model_deploy/act/types/action_spec.py` |
| 测试 | `src/model_deploy/act/tests/types/test_action_spec.py` |

**分支策略**:
- 工作分支: `feat/model_deploy/l2-01-external-contract`
- 集成分支: `model_deploy`

> [!warning] 分支纪律
> 本任务必须在 `feat/model_deploy/l2-01-external-contract` 分支上执行，完成后合入 `model_deploy` 集成分支。禁止直接在 `model_deploy` 或主分支上提交。禁止跨 L2 分支操作。

> [!warning] 范围纪律
> 本任务仅定义 16D 单步动作规格 ActionSpec 及其 ensure/split 纯函数。不得扩展到 ActionChunk 生命周期、光标、平滑、混合或发布逻辑。不得修改 pi05/ 参考代码。

---

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_003
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_003_16D动作规格ActionSpec.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S1, S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_003_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 1
  parallel_group: l2-01-external-contract-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_001, deploy_002]
  blocks: []
  conflict_scope:
    files: [src/model_deploy/act/types/action_spec.py, src/model_deploy/act/tests/types/test_action_spec.py]
    modules: [model_deploy.act.types.action_spec]
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

> [!info] Agent执行/验收边界
> - **执行 Agent**: 负责按本任务文件完成代码改造和测试编写，仅限"允许修改"章节列出的文件。
> - **验收 Agent**: 负责按验收卡片执行验收，独立于执行 Agent，仅检查验收卡片"检查对象"列出的检查项。
> - **执行边界**: 仅限本文件第 10 节"允许修改"列出的文件，不得越界。
> - **验收边界**: 仅限验收卡片第 1 节"检查对象"列出的检查项，不扩展检查。
> - **反馈机制**: 验收不通过时，验收 Agent 将反馈写入 `acceptance_feedback_dir` 下 `deploy_003_feedback_roundN.md`，执行 Agent 据此修正。

---

## 3. 本次唯一目标

定义 16D single action 的维度、段序、字段语义和值域，封装为 `ActionSpec` frozen dataclass，提供 `ensure_action_vector` 和 `split_action` 两个纯函数。

ACT 使用 16D 动作向量，其布局为:

```text
left_tcp_action(7: xyz + quaternion) + right_tcp_action(7: xyz + quaternion) + left_gripper(1) + right_gripper(1) = 16
```

`ensure_action_vector(flat)` 校验输入扁平向量为 16D，返回 `np.ndarray`，维度不匹配时抛出 `ValueError`。

`split_action(flat)` 将 16D 扁平向量拆分为结构化部分: `left_tcp_action`、`right_tcp_action`、`left_gripper`、`right_gripper`。

本任务不涉及 ActionChunk（多步动作序列）的生命周期管理、光标推进、平滑、混合或发布逻辑。

---

## 4. 所属 L2 边界与设计来源

**L2 `l2-01-external-contract` 负责**:
- 外部参数（模型路径、维度配置、动作规格等）的结构化加载
- 维度契约定义与校验（ActionSpec / StateCodec / Schema）
- 非法维度/配置的失败路径闭环

**L2 `l2-01-external-contract` 不负责**:
- 模型推理执行
- 动作发布与真机控制
- ActionChunk 生命周期管理（属于后续 L2）

**本 L3 在 L2 中的位置**:

```text
l2-01-external-contract
├── deploy_001 (外部参数加载)        ← can_run_parallel_with
├── deploy_002 (Schema 定义)         ← can_run_parallel_with
├── deploy_003 (16D ActionSpec)      ← 本任务，types 底层
├── ...
├── deploy_008 (引用 action_spec)    ← 下游，引用 ActionSpec 类型
└── deploy_009 (契约校验)            ← 下游，引用 ACTION_DIM=16 契约
```

- 本 L3 是 types 底层微元，定义 16D 动作规格的维度契约。
- `ACTION_DIM=16` 被 deploy_009 契约校验引用，用于校验模型输出维度。
- `ActionSpec` 类型被 deploy_008 引用，作为动作结构化载体。

**必读 7 个 L2 设计文档**:

| 序号 | 文档 | 路径 |
|------|------|------|
| 1 | L2 边界与设计来源 | `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/01_L2边界与设计来源.md` |
| 2 | 外部参数加载设计 | `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/02_外部参数加载设计.md` |
| 3 | 维度契约设计 | `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/03_维度契约设计.md` |
| 4 | 状态编解码设计 | `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/04_状态编解码设计.md` |
| 5 | Schema 校验设计 | `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/05_Schema校验设计.md` |
| 6 | types 层设计 | `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/06_types层设计.md` |
| 7 | 集成与验收设计 | `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/07_集成与验收设计.md` |

---

## 5. Pi0.5 源码盘点

Pi0.5 参考代码为只读，路径: `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/robot/action_spec.py`

| 符号 | 值/签名 | 说明 |
|------|---------|------|
| `ARM_DOF` | `6` | 单臂自由度（关节角） |
| `HAND_DOF` | `1` | 单手自由度 |
| `ACTION_DIM` | `14` | 动作总维度 = 6+6+1+1 |
| `STATE_DIM` | `26` | 状态总维度 |
| `ARM_JOINT_NAMES` | 关节名列表 | 6 个关节角名称 |
| `BimanualAction` | frozen dataclass | 字段: `left_arm`, `right_arm`, `left_hand`, `right_hand` |
| `split_bimanual_action(action)` | `-> BimanualAction` | 校验 size==14，拆分: `left_arm[:6]`, `right_arm[6:12]`, `left_hand[12]`, `right_hand[13]` |
| `as_vector()` | `-> np.ndarray` | 拼接为 14D float32 |

**必须保留的模式**:
- frozen dataclass 作为动作结构化载体
- split function 先校验 size 再拆分的模式
- `as_vector()` 拼接为扁平向量的模式（如 ActionSpec 需要提供）

**禁止照搬**:
- 14D 布局（ACT 是 16D）
- 关节角语义（ACT 是 TCP 位姿 + gripper）
- `ARM_DOF=6`（ACT 单臂 TCP 是 7D: xyz + quaternion）
- `STATE_DIM=26`（ACT 状态维度不同，不属于本任务）

**已知风险**:
- TCP quaternion 约定（w,x,y,z vs x,y,z,w）: 本任务仅定义 7D 段（xyz+quaternion），不做 quaternion 内部约定转换，留给下游处理。

---

## 6. ACT 微元与真实实现边界

**允许做**:

| 项 | 说明 |
|----|------|
| `ActionSpec` frozen dataclass | 字段: `left_tcp_action`, `right_tcp_action`, `left_gripper`, `right_gripper` |
| `ACTION_DIM=16` 常量 | 动作总维度 |
| 段常量 | `LEFT_TCP_ACTION_DIM=7`, `RIGHT_TCP_ACTION_DIM=7`, `LEFT_GRIPPER_DIM=1`, `RIGHT_GRIPPER_DIM=1` |
| `ensure_action_vector(flat)` | 纯函数: 校验 16D，返回 np.ndarray float32，不匹配抛 ValueError |
| `split_action(flat)` | 纯函数: 校验后按 7+7+1+1 拆分，返回结构化部分 |

**不做**:

| 项 | 原因 |
|----|------|
| ActionChunk 生命周期 / 光标 / 平滑 / 混合 / 发布 | 属于后续 L2/L3，非本任务范围 |
| `blend_steps` / `smoothstep` / `cross_chunk` / `rtc_alignment` / `action_smoothing` | 平滑相关字段不属于单步动作规格 |
| TCP quaternion 转换 | 仅定义 7D 段维度，不做旋转约定转换 |
| 模型推理 / 动作执行 | 非 types 层职责 |

**禁止修改**:
- `pi05/` 目录下任何文件（只读参考）
- 其他 L3 产物文件
- 其他层代码（如 inference、publish 层）

**函数/class 策略**:
- `ActionSpec`: frozen dataclass — 数据载体，不可变
- `ensure_action_vector`: 纯函数 — 校验 + 类型规范化，无副作用
- `split_action`: 纯函数 — 校验 + 拆分，无副作用

---

## 7. 六层产物落点

| 层 | 是否本任务产物 | 文件 | 说明 |
|----|--------------|------|------|
| config | 否 | — | 非 types 层 |
| types | **是** | `src/model_deploy/act/types/action_spec.py` | 16D ActionSpec + ensure/split |
| codec | 否 | — | StateCodec 属于 deploy_008 |
| inference | 否 | — | 非本任务 |
| publish | 否 | — | 非本任务 |
| tests | **是** | `src/model_deploy/act/tests/types/test_action_spec.py` | 单元测试 |

对应设计文档: `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/06_types层设计.md`

---

## 8. 文件内 3.5 层功能微元

**目标文件**: `src/model_deploy/act/types/action_spec.py`

| 微元 | 层级 | 类型 | 说明 |
|------|------|------|------|
| `ACTION_DIM` | 数据 | 常量 | `= 16`，动作总维度 |
| `LEFT_TCP_ACTION_DIM` | 数据 | 常量 | `= 7`，左臂 TCP (xyz+quaternion) |
| `RIGHT_TCP_ACTION_DIM` | 数据 | 常量 | `= 7`，右臂 TCP (xyz+quaternion) |
| `LEFT_GRIPPER_DIM` | 数据 | 常量 | `= 1`，左夹爪 |
| `RIGHT_GRIPPER_DIM` | 数据 | 常量 | `= 1`，右夹爪 |
| `ActionSpec` | 数据 | frozen dataclass | 字段: `left_tcp_action`, `right_tcp_action`, `left_gripper`, `right_gripper` |
| `ensure_action_vector(flat)` | 计算函数 | 纯函数 | 校验 flat 为 16D，返回 np.ndarray float32，不匹配抛 ValueError |
| `split_action(flat)` | 计算函数 | 纯函数 | 校验后按 7+7+1+1 拆分，返回结构化部分 |

**布局**:

```text
|<--- left_tcp_action (7) --->|<--- right_tcp_action (7) --->|<-- left_gripper (1) -->|<-- right_gripper (1) -->|
|  x  y  z  qx qy qz qw      |  x  y  z  qx qy qz qw       |  g                     |  g                      |
|  [0:7]                      |  [7:14]                     |  [14]                  |  [15]                   |
|-------------------------------------------------------------------------------------------|
|                                       ACTION_DIM = 16                                     |
```

---

## 9. 实施步骤

1. **创建 `src/model_deploy/act/types/action_spec.py`**
   - 定义 `ACTION_DIM=16` 及段常量 (`LEFT_TCP_ACTION_DIM=7`, `RIGHT_TCP_ACTION_DIM=7`, `LEFT_GRIPPER_DIM=1`, `RIGHT_GRIPPER_DIM=1`)
   - 验证段常量之和等于 `ACTION_DIM`

2. **定义 `ActionSpec` frozen dataclass**
   - 字段: `left_tcp_action`, `right_tcp_action`, `left_gripper`, `right_gripper`
   - 使用 `@dataclass(frozen=True)`
   - 可选: 提供 `as_vector()` 方法拼接为 16D np.ndarray（参考 Pi0.5 `as_vector` 模式）

3. **实现 `ensure_action_vector(flat)`**
   - 接受 list / tuple / np.ndarray
   - 转为 np.ndarray float32
   - 校验 `size == ACTION_DIM`（即 16）
   - 不匹配抛出 `ValueError`，包含期望维度和实际维度信息
   - 匹配则返回 np.ndarray float32

4. **实现 `split_action(flat)`**
   - 调用 `ensure_action_vector` 校验并规范化
   - 按 7+7+1+1 拆分: `left_tcp_action=[0:7]`, `right_tcp_action=[7:14]`, `left_gripper=[14]`, `right_gripper=[15]`
   - 返回 `ActionSpec` 或结构化部分（含 left_tcp_action, right_tcp_action, left_gripper, right_gripper）

5. **创建 `src/model_deploy/act/tests/types/test_action_spec.py`**
   - 测试合法 16D 向量: `ensure_action_vector` 返回 np.ndarray float32，shape==(16,)
   - 测试非法维度: 14D, 15D, 17D 均抛出 ValueError
   - 测试 `split_action` 拆分正确性: 各段值与输入对应
   - 测试 `ActionSpec` frozen 不可变性: 赋值抛 FrozenInstanceError
   - 测试段常量之和等于 ACTION_DIM

6. **运行 pytest 验证**

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_action_spec.py -v
```

确保全部测试通过。

---

## 10. 允许修改

> [!warning] 修改范围
> 仅允许修改以下文件。任何超出此范围的修改必须先获得 L2 负责人批准。

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/model_deploy/act/types/action_spec.py` | 新建 | 16D ActionSpec + ensure/split |
| `src/model_deploy/act/tests/types/test_action_spec.py` | 新建 | 单元测试 |
| `src/model_deploy/act/types/__init__.py` | 修改（如需） | 导出 ActionSpec 等符号 |

**本次产物落点**:

```text
src/model_deploy/act/types/
├── __init__.py          (修改: 导出符号)
└── action_spec.py       (新建: ACTION_DIM=16, ActionSpec, ensure_action_vector, split_action)

src/model_deploy/act/tests/types/
└── test_action_spec.py  (新建: 单元测试)
```

---

## 11. 禁止修改

> [!warning] 禁止修改范围
> 以下文件/目录禁止修改，违反将导致验收失败。

| 范围 | 原因 |
|------|------|
| `pi05/` 及其所有子目录 | 只读参考代码 |
| `src/model_deploy/act/inference/` | 推理层，非本任务 |
| `src/model_deploy/act/codec/` | 编解码层，属于 deploy_008 |
| `src/model_deploy/act/publish/` | 发布层，非本任务 |
| 其他 L3 产物文件 | 跨 L3 修改禁止 |
| `DOCS/03_工程/阶段四：模型部署/03_tasks/` 下的调度文件 | 调度元数据只读 |
| `DOCS/03_工程/` 下的归档文件 | 历史归档只读 |

---

## 12. 验证方式

**必跑命令**:

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_action_spec.py -v
```

**验证项**:

| 验证类型 | 是否适用 | 说明 |
|---------|---------|------|
| 单元测试 | 是 | pytest 覆盖合法/非法维度、split 正确性、frozen 不可变性 |
| 导入测试 | 是 | `from model_deploy.act.types.action_spec import ActionSpec, ensure_action_vector, split_action, ACTION_DIM` |
| 真机测试 | 不适用 | 真机风险 none，本任务为纯 types 层定义 |
| 集成测试 | 不适用 | 集成验证在 deploy_009 契约校验中完成 |

**证据落点**:
- pytest 输出日志（终端输出或重定向文件）
- 验收卡片第 4 节验收结论

**L2 Gate 贡献**:

| Gate 场景 | 贡献 | 说明 |
|-----------|------|------|
| S1 (合法配置载入) | 是 | `ensure_action_vector` 接受合法 16D 向量，`split_action` 正确拆分 |
| S2 (非法维度失败) | 是 | `ensure_action_vector` 拒绝非 16D 向量，抛出 ValueError |

本 L3 定义 action 16D 契约，为 deploy_009 契约校验提供维度校验基础。S1/S2 的完整闭环仍需 deploy_009 契约校验 L3 配合。

---

## 13. 必读上下文

**任务文档 (6 个)**:

| 序号 | 文档 | 路径 |
|------|------|------|
| 1 | L2 任务定义 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_000_L2任务定义.md` |
| 2 | deploy_001 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_001_外部参数加载.md` |
| 3 | deploy_002 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_002_Schema定义.md` |
| 4 | deploy_008 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_008_状态编解码.md` |
| 5 | deploy_009 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_009_契约校验.md` |
| 6 | L3 调度计划 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_000_L3调度计划.md` |

**只读参考代码**:

| 文件 | 路径 | 用途 |
|------|------|------|
| Pi0.5 action_spec | `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/robot/action_spec.py` | frozen dataclass + split 模式参考 |
| Pi0.5 state_codec | `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/robot/state_codec.py` | 编解码模式参考（仅参考结构，不照搬维度） |
| Pi0.5 schema | `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/robot/schema.py` | Schema 模式参考 |

**约束文档 (2 个)**:

| 序号 | 文档 | 路径 |
|------|------|------|
| 1 | 编码规范 | `DOCS/02_约束/编码规范.md` |
| 2 | 测试规范 | `DOCS/02_约束/测试规范.md` |

**上游依赖**: 无（`depends_on: []`）

---

## 14. 执行要求

**身份校验**:
- 开始前确认 `task_id == deploy_003`，分支为 `feat/model_deploy/l2-01-external-contract`。
- 确认 `dispatch_status == ready`。

**dispatch 校验**:
- 确认 `depends_on` 为空，无前置 L3 阻塞。
- 确认 `can_run_parallel_with` 包含 deploy_001、deploy_002，可并行执行。
- 确认 `conflict_scope` 仅涉及 `action_spec.py` 和 `test_action_spec.py`。

**全文检查**:
- 完成后逐项检查第 15 节"成功标准"的所有 checkbox。
- 确认无 14D / 26D / joint angle 语义残留。
- 确认无 blend_steps / smoothstep / cross_chunk / rtc_alignment / action_smoothing 字段。
- 确认未修改 pi05/ 参考代码。

**测试优先**:
- 先编写测试用例（合法 16D、非法维度 14/15/17、split 正确性、frozen 不可变性），再实现 `action_spec.py`。
- 测试必须独立可运行，不依赖真机或其他 L3 产物。

---

## 15. 成功标准

- [ ] `src/model_deploy/act/types/action_spec.py` 已创建
- [ ] `src/model_deploy/act/tests/types/test_action_spec.py` 已创建
- [ ] `ACTION_DIM == 16` 已定义
- [ ] 段常量已定义（`LEFT_TCP_ACTION_DIM=7`, `RIGHT_TCP_ACTION_DIM=7`, `LEFT_GRIPPER_DIM=1`, `RIGHT_GRIPPER_DIM=1`）
- [ ] `ActionSpec` 为 frozen dataclass，字段: `left_tcp_action`, `right_tcp_action`, `left_gripper`, `right_gripper`
- [ ] `ensure_action_vector` 接受合法 16D 向量，返回 np.ndarray float32
- [ ] `ensure_action_vector` 拒绝非 16D 向量（14D/15D/17D），抛出 ValueError
- [ ] `split_action` 正确拆分为 7+7+1+1 布局
- [ ] 无 14D / 26D / joint angle 语义残留
- [ ] 无 blend_steps / smoothstep / cross_chunk / rtc_alignment / action_smoothing 字段
- [ ] 未修改 pi05/ 参考代码
- [ ] `python3 -m pytest src/model_deploy/act/tests/types/test_action_spec.py -v` 全部通过

---

## 16. 回滚方式

若任务失败或需要回滚，执行以下步骤:

```bash
# 1. 删除新建的源码文件
rm src/model_deploy/act/types/action_spec.py

# 2. 删除新建的测试文件
rm src/model_deploy/act/tests/types/test_action_spec.py

# 3. 还原 __init__.py（如被修改）
git checkout src/model_deploy/act/types/__init__.py
```

回滚后确认:
- `src/model_deploy/act/types/action_spec.py` 不存在
- `src/model_deploy/act/tests/types/test_action_spec.py` 不存在
- `__init__.py` 恢复原状
- pi05/ 目录无任何变更

---

## 17. 完成后交接

任务完成后，执行 Agent 须:

1. 确认第 15 节所有成功标准 checkbox 已勾选。
2. 运行必跑命令并保存输出证据。
3. 通知验收 Agent 按验收卡片执行验收。
4. 验收通过后，将分支合入 `model_deploy` 集成分支。
5. 在 L3 调度计划中更新 `deploy_003` 状态为 `completed`。
6. 向下游 L3（deploy_008、deploy_009）通知 `ActionSpec` 和 `ACTION_DIM=16` 已就绪。

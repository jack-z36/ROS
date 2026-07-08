# L3 微元改造任务：ACT Types 层边界校验完善与全量单测

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-01 ACT Types 层
来源 ACT Delta：A2/A3（边界校验：shape/dtype/quaternion 模长/width 值域/gripper 越界报错）
L3 编号：deploy_004
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_004_Types层边界校验与全量单测.md`
改造类型：test-coverage（补全边界校验与负向测试）
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-01-types`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/`
对应 L2 运行验收场景：S1
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_004_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。第 9 节「本次产物落点」声明每个产物的落点路径。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_004
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_004_Types层边界校验与全量单测.md
  group: l2-01-types
  branch: feat/model_deploy/l2-01-types
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
  acceptance_scenarios: [S1]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_004_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs
  wave: 2
  parallel_group: l2-01-types-w2
  depends_on: [deploy_001, deploy_002, deploy_003]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/types/action_spec.py
      - src/model_deploy/act/types/state_codec.py
      - src/model_deploy/act/types/action_codec.py
      - src/model_deploy/act/tests/types/test_action_spec.py
      - src/model_deploy/act/tests/types/test_state_codec.py
      - src/model_deploy/act/tests/types/test_action_codec.py
    modules:
      - act.types.action_spec
      - act.types.state_codec
      - act.types.action_codec
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
在 deploy_001~003 已建成的 action_spec/state_codec/action_codec 基础上，补全所有边界校验：
- dtype 校验（非 float32 输入的容错与报错）
- quaternion 模长校验（模长偏离 1 时报错）
- gripper width 值域校验（width∈[0,1]，越界报错或按策略处理）
- 全量负向测试（错 shape、错 dtype、模长≠1、width 越界、空输入、None 等均抛预期异常）
- 确保 L2-01 Gate 跑全部 types 测试通过。
```

## 4. 来源契约

### 来源 ACT Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | A2/A3（边界校验部分） |
| AS-IS 契约 | deploy_001~003 已建基本结构，但边界校验不全（缺 dtype 校验、width 值域校验、部分负向测试）。 |
| TO-BE 契约 | Types 层所有入口在边界处完成 shape/dtype/quaternion 模长/width 值域校验，对不完整数据生成结构化 ValueError，下游不靠猜测。对照《架构边界与机械约束原则》第三节。 |

### 所属 L2 改造工作包

[[L2-01-ACT Types层]]

## 5. 现有程序盘点

| 现有对象 | 路径 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `action_spec.py` | `act/types/action_spec.py`（deploy_001） | 常量 + BimanualAction + split_bimanual_action + 维度校验 | 缺 dtype 校验；split 无 quaternion 模长校验 | 是（补校验） |
| `state_codec.py` | `act/types/state_codec.py`（deploy_002） | encode_state 16D 分组段序 + quaternion 模长校验 | 缺 width 值域校验；dtype 校验可能不完整 | 是（补校验） |
| `action_codec.py` | `act/types/action_codec.py`（deploy_003） | ensure_action_vector/chunk/split + 维度校验 | chunk 校验无负向测试（错 ndim、空） | 是（补测试） |
| 各 test_*.py | `act/tests/types/`（deploy_001~003） | 正向测试（合法输入） | 缺负向测试覆盖 | 是（补测试） |

## 6. 真实改造边界

### 本次允许做

- 补充 `action_spec.py` 的 dtype 校验（`as_vector` 确保输出 float32）。
- 补充 `state_codec.py` 的 width 值域校验（`encode_state` 时 width∈[0,1]，越界抛 ValueError；提供 `check_gripper_width` 辅助）。
- 完善各 `_vector`/`_check_quaternion` 辅助的 dtype 处理。
- 在三个 test 文件中补全负向测试用例（见第 7 节清单）。
- 新建 `act/tests/types/conftest.py`（公共 fixture：合法/非法 state/action 构造器）。

### 本次不做

- 不改已通过的正面测试逻辑（只增不改）。
- 不改维度常量或段序定义（已固化）。
- 不动 action_codec 的函数签名。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- L2-02 及以后代码

## 7. 实施步骤

1. 补充 `action_spec.py`：
   - `BimanualAction.as_vector()` 确保返回 float32（`np.concatenate(...).astype(np.float32, copy=False)`）。
   - `split_bimanual_action` 入参 `np.asarray(action, dtype=np.float32)` 统一 dtype。
2. 补充 `state_codec.py`：
   - 新增 `_check_gripper_width(width, name)`：`width < 0.0 or width > 1.0` 时 raise ValueError。
   - `encode_state` 调用 `_check_gripper_width(state.left_gripper_width, ...)` 和 right。
3. 新建 `act/tests/types/conftest.py`：
   - `valid_tcp_pose()`：返回合法 quaternion（模长=1）。
   - `valid_bimanual_state()`：返回合法 ActBimanualState。
   - `valid_action_vector()`：返回合法 16D。
   - `denorm_quaternion()`：返回模长=2 的非法四元数。
4. 补充负向测试（每个 test 文件追加 `TestNegative` 类）：
   - `test_action_spec`：错维度（15D/17D）、None、空 list。
   - `test_state_codec`：quaternion 模长≠1（用 conftest denorm）、width=-0.1、width=1.5、错维度 tcp_pose。
   - `test_action_codec`：chunk ndim≠2、chunk shape[1]≠16、空 chunk。
5. 运行全量测试：`pytest src/model_deploy/act/tests/types/ -v`。

## 8. 验证方式

### 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/ -v
```

### 分层验证表

| 层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit | 是 | tests/types/ 全部（含负向） | 全部 PASSED，负向测试覆盖所有边界 |
| 其余 | 否 | — | — |

### 真机风险控制

无真机风险（纯数据结构单测）。

### 验收证据落点

- 全量测试输出：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/deploy_004_pytest_all.txt`

### L2 运行验收贡献

本 L3 是 L2-01 的收尾：全量测试通过后，Types 层可进入 L2 Gate。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| action_spec 补充 | `src/model_deploy/act/types/action_spec.py` | types |
| state_codec 补充 | `src/model_deploy/act/types/state_codec.py` | types |
| action_codec 补充 | `src/model_deploy/act/types/action_codec.py` | types |
| 公共 fixture | `src/model_deploy/act/tests/types/conftest.py` | tests/types |
| 负向测试 | `act/tests/types/test_action_spec.py`、`test_state_codec.py`、`test_action_codec.py` | tests/types |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- 已固化的维度常量、段序定义、函数签名

## 11. 必读上下文

### 必读任务文档

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-ACT Types层.md`
- deploy_001/002/003 任务文件（依赖产物）

### 必读代码

- `src/model_deploy/act/types/action_spec.py`、`state_codec.py`、`action_codec.py`（deploy_001~003 产物）

### 必读约束文档

- `DOCS/02_约束/编程执行/Agent编程执行原则.md`（第四节验收闭环）
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`（第三节 shape 边界校验）
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-01-types`。
- 依赖校验：deploy_001/002/003 全部 PASS_LOCAL。
- TDD：负向测试先写（先证明边界会漏），再补校验让测试通过。
- 落点校验：产物路径与第 9 节一致。

## 13. 成功标准

- [ ] `action_spec.as_vector()` 返回 float32。
- [ ] `state_codec.encode_state` 校验 width∈[0,1]，越界抛 ValueError。
- [ ] `conftest.py` 提供 valid/denorm fixture。
- [ ] 负向测试覆盖：错维度、错 dtype、quaternion 模长≠1、width 越界、空输入、None。
- [ ] `pytest src/model_deploy/act/tests/types/ -v` 全部 PASSED。
- [ ] 产物路径与第 9 节声明一致。
- [ ] 未修改 pi05/third_party/pi05_old。

## 14. 回滚方式

`git checkout -- src/model_deploy/act/types/ src/model_deploy/act/tests/types/`（回退 deploy_004 的补充，保留 001~003 基础）。

## 15. 完成后交接

（执行 sub-agent 完成后填写）

# L3 微元改造任务：Types 层单测覆盖

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-01 Types 层重构
来源 Delta：D8/D9/D11（state/action 结构改造的测试覆盖）
L3 编号：deploy_004
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_004_types层单测.md`
改造类型：test-coverage
真机风险等级：none

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_004
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_004_types层单测.md
  group: l2-01-types
  branch: model_deploy
  wave: 3
  parallel_group: l2-01-types-p3
  depends_on: [deploy_001, deploy_002, deploy_003]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - pi05_test/pi05/common/tests/test_action_spec_tcp.py
      - pi05_test/pi05/common/tests/test_state_codec_tcp.py
    modules:
      - tests.types_layer
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
为 deploy_001/002/003 改造后的 action_spec / state_codec / action_codec 编写单元测试，覆盖：维度正确性、段序正确性（state 全左→全右 vs action 交替）、round-trip 一致性、触觉预留开关、维度校验拒绝非法输入。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D8/D9/D11（测试覆盖） |
| 变更对象 | Input/Action Contract |
| AS-IS 契约 | 旧 26D state / 14D action 无针对 TCP+width 结构的测试。 |
| TO-BE 契约 | 新 16D/32D state + 16D action 结构需有单测守护，防止段序错位回归。 |
| 兼容性要求 | 新增测试文件，不改被测代码。 |
| 回滚要求 | 删除测试文件即可。 |

### 所属 L2 改造工作包

- L2 名称：L2-01 Types 层重构
- 本 L3 在该 L2 中的位置：最后一个，验收前三者的改造正确性。是 L2-01 完成的标志。
- 本 L3 完成后解锁：L2-01 整体完成，L2-02（Config）可以开始。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| 被测代码 action_spec | `action_spec.py`（deploy_001 改后） | ACTION_DIM=16, BimanualAction(TCP+width), split_bimanual_action(交替段序) | 缺测试守护 | 否（只测不改） |
| 被测代码 state_codec | `state_codec.py`（deploy_002 改后） | BimanualState(TCP+width), encode_bimanual_state(全左→全右, include_tactile) | 缺测试守护 | 否 |
| 被测代码 action_codec | `action_codec.py`（deploy_003 改后） | ensure_action_vector/chunk(跟随16D), split_action | 缺测试守护 | 否 |
| 现有测试目录 | `pi05_test/pi05/common/tests/`（待确认是否存在） | — | 需新建测试文件 | 是（新建测试） |

### 必须保留的现有行为

- 不改被测代码（action_spec/state_codec/action_codec）。
- 测试独立、可重复运行。

### 已知风险

- 测试需要能 import 被测模块。但 deploy_001/002 完成后，**整个 deploy 包可能仍无法 import**（collector/safety_guard 等上层未改）。因此测试必须**只 import common.data 和 common.robot 这两个 Types 层模块**，不触发 deploy 包的其他 import 链。
- 如果 common 包的 `__init__.py` 会级联 import deploy 侧代码，需要确认测试的 import 路径绕过 deploy。

## 6. 真实改造边界

### 本次允许做

- 新建测试文件（建议 pytest 风格）：
  - `test_action_spec_tcp.py`：测 BimanualAction 结构、as_vector 段序、split_bimanual_action 段序、ACTION_DIM、round-trip、拒绝非 16D。
  - `test_state_codec_tcp.py`：测 BimanualState 结构、encode_bimanual_state 维度（16/32）、**state 段序 ≠ action 段序**、include_tactile 开关、round-trip、拒绝非法维度。
- 测试只 import `pi05.common.robot.action_spec` 和 `pi05.common.data.state_codec` / `action_codec`（Types 层），不 import deploy。

### 本次不做

- 不改被测代码。
- 不测上层（collector/safety_guard）。
- 不写 dry-run/shadow-run 集成测试（那是 L2-03/04 的验收）。

### 明确禁止修改

- 禁止改 action_spec.py / state_codec.py / action_codec.py（前三 L3 的产物）。
- 禁止改 deploy 侧代码。
- 禁止 import deploy 包的非 Types 模块（会导致 import 失败）。

### Adapter / 直接修改策略

```text
纯新增测试文件。不碰被测代码。
```

## 7. 实施步骤

1. **确认 import 路径**：验证 `from pi05.common.robot.action_spec import ...` 和 `from pi05.common.data.state_codec import ...` 能独立 import（不触发 deploy）。如果不能，记录 import 链问题，可能需要调整测试的 sys.path 或标记为 blocked。
2. **写 test_action_spec_tcp.py**：
   - `test_action_dim_is_16`：`assert ACTION_DIM == 16`。
   - `test_bimanual_action_fields`：构造 BimanualAction(left_tcp_pose, left_gripper_width, right_tcp_pose, right_gripper_width)，确认字段。
   - `test_as_vector_alternating_order`：as_vector 输出 16D，段序 left_tcp[0:7]+left_width[7]+right_tcp[8:15]+right_width[15]。
   - `test_split_alternating_order`：split 16D 向量，确认段序对应。
   - `test_round_trip`：构造 BimanualAction → as_vector → split → 字段一致。
   - `test_split_rejects_wrong_dim`：传 14D/15D 向量，确认 ValueError。
3. **写 test_state_codec_tcp.py**：
   - `test_state_dim_is_16`：`assert STATE_DIM == 16`。
   - `test_encode_16d_no_tactile`：include_tactile=False 输出 16D。
   - `test_encode_32d_with_tactile`：include_tactile=True + 触觉数据 输出 32D。
   - **`test_state_segment_order_differs_from_action`**（关键防回归）：encode 的 state 段序（全左→全右：left_tcp+right_tcp+left_width+right_width）与 action 段序（交替）不同。构造已知数据，断言 state[0:7]=left_tcp 但 action[0:7]=left_tcp（这部分相同），state[7:14]=right_tcp 但 action[7]=left_width（**这里不同**）。
   - `test_encode_rejects_wrong_dim`。
   - `test_decode_picotele_removed`：确认 `decode_picotele_proprioception` 不再存在于模块。
4. **运行 pytest**。

## 8. 验证方式

### 自动化验收命令

```bash
cd pi05_test/pi05 && python3 -m pytest pi05/common/tests/test_action_spec_tcp.py pi05/common/tests/test_state_codec_tcp.py -v
```

测试目录路径可能需根据实际项目结构调整（执行时确认 pi05/common/tests/ 是否存在，不存在则创建）。

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | pytest 全部通过 | 所有测试 case pass |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 是纯测试，不触发真机动作。

## 9. 允许修改

- 新建 `pi05_test/pi05/common/tests/test_action_spec_tcp.py`
- 新建 `pi05_test/pi05/common/tests/test_state_codec_tcp.py`
- 如 tests 目录不存在，创建它和 `__init__.py`（如 pytest 需要）。

## 10. 禁止修改

- action_spec.py / state_codec.py / action_codec.py。
- 任何 deploy 侧代码。
- 禁止 import deploy 包非 Types 模块。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D8/D9/D11）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-Types层重构.md`
3. `DOCS/01_知识/阶段二：数据清洗/数据清洗交付说明.md`（段序差异 warning L35-36，测试断言依据）

### 必读代码

1. `pi05_test/pi05/common/src/pi05/common/robot/action_spec.py`（deploy_001 改后）
2. `pi05_test/pi05/common/src/pi05/common/data/state_codec.py`（deploy_002 改后）
3. `pi05_test/pi05/common/src/pi05/common/data/action_codec.py`（deploy_003 改后）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_001/002/003（全部完成）。
2. 同组已完成：deploy_001/002/003。

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

- `depends_on: [deploy_001, deploy_002, deploy_003]` 全部完成。
- `dispatch_status` 不是 `blocked`。

```text
确认 import 路径可行
→ 写测试（TDD: 先写断言，再确认被测代码满足）
→ pytest 通过
→ 必要整理
```

如果 import 被测模块失败（因 common __init__ 级联 deploy），记录问题，不强行改 __init__（可能需主 Agent 决策是否调整 import 结构）。

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已读取 Contract Delta 和所属 L2。
- [ ] 已确认 deploy_001/002/003 的被测代码就位。
- [ ] 已确认测试 import 路径可行（只 import Types 层）。
- [ ] pytest 全部通过。
- [ ] 段序差异测试（state ≠ action）通过（关键防回归）。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：不适用
切回旧入口：不适用
移除 adapter：不适用
回退文件：删除新建的两个测试文件即可（git clean 或 rm）
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选成功标准 + 追加执行摘要。
- 不擅自归档。

交接摘要必须包含：

1. 读取了哪些文档和代码。
2. 任务文件身份校验结论。
3. 新建了哪些测试文件，多少个 case。
4. pytest 运行结果（通过数/失败数）。
5. 段序差异测试结论（state vs action 段序确实不同）。
6. 成功标准勾选情况。
7. 是否影响真机（否）。
8. 回滚方式。
9. 本次明确没有做什么（没改被测代码、没测上层）。
10. 后续建议（L2-01 完成，可开始 L2-02 Config）。

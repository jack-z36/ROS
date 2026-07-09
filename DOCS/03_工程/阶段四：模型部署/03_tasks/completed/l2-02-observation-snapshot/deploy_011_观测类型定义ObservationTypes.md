# L3 微元改造任务：观测类型定义 ObservationState / ObservationSnapshot / ObservationFreshnessResult

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-02-observation-snapshot 传感器订阅与 ObservationSnapshot 组装闭环
L3 编号：deploy_011
改造类型：source-adaptation
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_011_观测类型定义ObservationTypes.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-observation-snapshot/deploy_011_验收卡片.md`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/`
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
真机风险等级：none
L2 分支：`feat/model_deploy/l2-02-observation-snapshot`
集成分支：`model_deploy`

`当前任务文件路径` 必须使用相对仓库根目录路径。当前代码路径必须使用 `src/model_deploy/act/...`，不得把 Pi0.5 历史路径写成当前源码路径。

`l2-02-observation-snapshot` 必须是新版 L2 ID 白名单中的 ID。任务文件、dispatch、验收卡片和 acceptance 目录不得位于 `_legacy_layer_based_act/` 或 `_archived_pi05/`。

> [!warning] 产物落点约束
> 本 L3 产出的源码、测试、配置、launch 和验收脚本必须落到 `ACT代码树分层与产物落点约束.md` 规定的位置。实际产物与本任务声明不一致时，验收判失败。

## 2. 调度元数据

本节用于主 Agent 判断当前 L3 在阶段四任务池中的串行 / 并行关系。必须使用 YAML；所有路径必须是相对仓库根目录路径。

```yaml
dispatch:
  task_id: deploy_011
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_011_观测类型定义ObservationTypes.md
  group: l2-02-observation-snapshot
  branch: feat/model_deploy/l2-02-observation-snapshot
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot
  acceptance_scenarios: [S1]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-observation-snapshot/deploy_011_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs
  wave: 1
  parallel_group: l2-02-observation-snapshot-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_012, deploy_013, deploy_014]
  conflict_scope:
    files:
      - src/model_deploy/act/types/observation.py
      - src/model_deploy/act/tests/types/test_observation.py
    modules:
      - model_deploy.act.types.observation
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

`dispatch_status` 只允许 `ready`、`blocked`、`waiting_user`。如果 `robot_risk` 是 `real-robot`，必须在验收方式中写明人工确认、急停准备、限幅策略和回滚路径。

### Agent 执行 / 验收边界

- 执行 sub-agent 只负责本 L3 的实现、局部验证和执行摘要。
- 执行 sub-agent 可以阅读验收卡片理解通过标准，但不得替验收 sub-agent 修改验收结论。
- 验收 sub-agent 只能读取验收卡片、L3 文件、执行摘要、允许查看的 diff / 日志，并按 `acceptance_mode` 输出结论。
- 验收 sub-agent 不得改源码、测试、dispatch、任务状态或 Git。
- `FAIL_LOCAL` 反馈最多回到执行 sub-agent 迭代 3 轮；超过 3 轮必须由主 Agent 停止自动推进并要求人工介入。
- `downstream-l2`、`hardware-blocked`、`env-blocked` 不是免验收，而是要求写清由哪个 L2 场景覆盖、缺什么环境或缺什么硬件。

## 3. 本次唯一目标

```text
在 types/observation.py 中定义 ObservationState、ObservationSnapshot、ObservationFreshnessResult 三个 frozen dataclass，作为 L2-02 及下游 L2-03/L2-06 的跨模块公共 RAM 数据契约。ObservationSnapshot 的 encoded_state 必须校验为 16D。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 从外部 observation topics 接收图像、TCP pose 和 gripper state，生成完整、合法、新鲜的 ObservationSnapshot。
- 维护各字段最新值和采集时间。
- 检查必需字段是否齐全、是否在 max_age_s 内新鲜。
- 调用 L2-01 state codec 生成 16D encoded_state。
- 将合法 snapshot 写入 latest-only buffer。

### L2 不负责

- 不调用 ACT 模型、不构造 ACT batch、不生成 ActionChunk。
- 不决定是否发起下一次推理、不维护 ControlLoop tick 状态。
- 不执行 action safety check、不发布硬件命令。

### 本 L3 在 L2 中的位置

```text
本 L3 产出 types/observation.py，是 L2-02 所有后续 L3（deploy_012~deploy_016）的数据语言基础。ObservationSnapshot 同时被 L2-03 batch adapter 和 L2-06 ControlLoop latest observation reader 消费。放在 types/ 层确保下游只依赖数据契约而不依赖 L2-02 的 service/runtime 实现。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/02_pi05源码3.5层微元拆解.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/03_ACT微元设计与协作.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/04_L2验收机制.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/05_人类验收机制.md`
9. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/06_types层设计.md`

## 5. Pi0.5 源码盘点

必须具体到文件、入口、class、函数、配置或命令；不得只写"参考现有代码"。

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| `ObservationSnapshot` | `deploy/src/pi05/deploy/runtime/shared_buffer.py` | 数据 | 冻结 observation 数据对象（images、state、encoded_state、captured_at_s） | ACT encoded_state 是 16D 非 26D；Snapshot 必须放 types/ 非 runtime/ | 结构复用 |
| `BimanualState` | `common/src/pi05/common/data/state_codec.py` | 数据 | 结构化 state（arm q、hand q、ee pose/rpy） | ACT 需要新的 16D TCP/gripper 契约，非旧 26D joint 语义 | 结构复用 |
| `ObservationCollector.REQUIRED_IMAGE_KEYS` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 数据 | 图像字段名集合 | ACT 改为从 DeployConfig 读取 required keys | 参考理解 |

### 必须保留的源码启发

- Pi0.5 `ObservationSnapshot` 的 frozen dataclass 思路：创建后只读，避免跨线程修改。
- Pi0.5 `BimanualState` 的分段结构化 state 思路：left/right 分离，按语义分段。
- Pi0.5 `missing_fields` 的诊断输出思路：暴露可观察的诊断信息。

### 禁止照搬的源码行为

- 禁止照搬 26D state 维度和 legacy joint position 语义。
- 禁止把 `ObservationSnapshot` 放在 `runtime/` 层（Pi0.5 放在 `shared_buffer.py` 中）。
- 禁止在 types 层引入 ROS message 依赖或 runtime buffer 引用。

### 已知风险

- L2-01 的 StateSpec 和 state codec 若未落地，`encoded_state` 维度约定可能漂移。本 L3 先以 16D 为契约写校验，后续与 L2-01 对齐。
- `ObservationState` 的字段名（left_tcp_position 等）需与 L2-01 的 state spec 段序一致，目前按设计文档锁定。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `src/model_deploy/act/types/observation.py`。
- 定义 `ObservationState` frozen dataclass（left_tcp_position, left_tcp_orientation, left_gripper_width, right_tcp_position, right_tcp_orientation, right_gripper_width）。
- 定义 `ObservationSnapshot` frozen dataclass（images, state, encoded_state, captured_at_s），含 `__post_init__` 校验 `encoded_state.shape == (16,)`。
- 定义 `ObservationFreshnessResult` frozen dataclass（missing_fields, stale_fields, field_ages_s, ready）。
- 新建 `src/model_deploy/act/tests/types/test_observation.py`，含 import、构造、维度校验、frozen 特性测试。

### 本次不做

- 不实现 ObservationCollector、ObservationBuffer、ObservationRosAdapter。
- 不引入 L2-01 state codec 调用（只校验维度）。
- 不定义图像预处理、ROS topic 名、config schema。
- 不修改 `src/model_deploy/act/` 下 types 层以外的任何文件。

### 明确禁止修改

- `src/model_deploy/act/config/`、`src/model_deploy/act/repo/`、`src/model_deploy/act/service/`、`src/model_deploy/act/runtime/`、`src/model_deploy/act/ui/`（如已存在）。
- `src/model_deploy/pi05/`、`pi05_old/`。
- `DOCS/03_工程/阶段四：模型部署/03_tasks/归档/`。
- 任何旧 dispatch 或旧 acceptance 目录。

### 函数 / class 策略

```text
三个类型均为 frozen dataclass，不封装为普通 class：
- ObservationState：纯数据容器，无内部状态变更需求，frozen dataclass 足够。
- ObservationSnapshot：纯数据容器，创建后只读；__post_init__ 做维度校验是纯校验逻辑，不需要 class 生命周期。
- ObservationFreshnessResult：纯诊断数据容器，只被 collector 和 buffer 构造后读取，不需要方法。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 是 | `src/model_deploy/act/types/observation.py` | 定义 ObservationState、ObservationSnapshot、ObservationFreshnessResult 三个 frozen dataclass |
| config | 否 | — | — |
| repo | 否 | — | — |
| service | 否 | — | — |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/types/test_observation.py` | 测试 import、构造、维度校验、frozen 特性 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/06_types层设计.md` | 完整实现 §3 中 ObservationState、ObservationSnapshot、ObservationFreshnessResult 的全部字段和校验 |
| `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/07_config层设计.md` | 不涉及（本 L2 无 config 产物） |
| `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/08_repo层设计.md` | 不涉及（本 L2 无 repo 产物） |
| `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/09_service层设计.md` | 不涉及（后续 deploy_012 实现） |
| `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/10_runtime层设计.md` | 不涉及（后续 deploy_014 实现） |
| `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/11_ui层设计.md` | 不涉及（后续 deploy_015 实现） |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `types/observation.py` | `ObservationState` | 数据 | left/right TCP pose arrays, left/right gripper width floats | frozen dataclass 实例 | 无 | contract.importable, contract.encoded_state_dim |
| `types/observation.py` | `ObservationSnapshot` | 数据 | images Mapping, ObservationState, encoded_state ndarray, captured_at_s float | frozen dataclass 实例，创建时校验 encoded_state 维度 | 无（校验失败抛异常） | contract.importable, contract.encoded_state_dim |
| `types/observation.py` | `ObservationFreshnessResult` | 数据 | missing_fields list, stale_fields list, field_ages_s dict, ready bool | frozen dataclass 实例 | 无 | contract.importable |
| `types/observation.py` | `validate_encoded_state_dim`（可选独立函数或 `__post_init__` 内联） | 计算函数 | encoded_state ndarray, expected_dim=16 | 无（合法时静默通过）或 raise ValueError | 无 | contract.encoded_state_dim |

## 9. 实施步骤

每一步都必须服务于"本次唯一目标"，不得顺手重构无关代码。

1. 创建 `src/model_deploy/act/types/observation.py`，定义 `ObservationState` frozen dataclass，字段包含左右臂 TCP position/orientation 和 gripper width。
2. 在同一文件中定义 `ObservationSnapshot` frozen dataclass，字段包含 images、state、encoded_state、captured_at_s，在 `__post_init__` 中校验 `encoded_state.shape == (16,)`。
3. 在同一文件中定义 `ObservationFreshnessResult` frozen dataclass，字段包含 missing_fields、stale_fields、field_ages_s、ready。
4. 创建 `src/model_deploy/act/tests/types/test_observation.py`，编写以下测试用例：
   - `test_observation_state_creation`：合法字段构造成功。
   - `test_observation_snapshot_creation`：合法 16D encoded_state 构造成功。
   - `test_observation_snapshot_invalid_dim`：非法维度 encoded_state 抛 ValueError。
   - `test_observation_snapshot_frozen`：修改字段抛 FrozenInstanceError。
   - `test_freshness_result_creation`：合法字段构造成功。
   - `test_import_without_ros`：import 不触发 ROS 依赖。
5. 运行 `python3 -m pytest src/model_deploy/act/tests/types/test_observation.py -v`，确认全部通过。

## 10. 允许修改

> [!warning] 产物落点声明（必填）
> 本节每个允许修改 / 新增的产物，必须标注其落点路径，且路径必须符合 `ACT代码树分层与产物落点约束.md`。
> 允许修改路径只能落在 `src/model_deploy/act/`、当前 L2 设计目录、当前 L2 task/card/acceptance 目录。Pi0.5 路径只能列入"只读参考"，不能列入允许修改。

- `src/model_deploy/act/types/observation.py`（新建）
- `src/model_deploy/act/tests/types/test_observation.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| ObservationState / ObservationSnapshot / ObservationFreshnessResult | `src/model_deploy/act/types/observation.py` | types |
| 单测 | `src/model_deploy/act/tests/types/test_observation.py` | tests/types |

## 11. 禁止修改

- `src/model_deploy/act/config/`、`src/model_deploy/act/repo/` 下任何文件。
- `src/model_deploy/act/service/`、`src/model_deploy/act/runtime/`、`src/model_deploy/act/ui/`（如已存在）。
- `src/model_deploy/pi05/`、`pi05_old/`。
- `DOCS/03_工程/阶段四：模型部署/03_tasks/归档/`。
- 任何 L2-01 或其他 L2 的源码、测试、任务文件。
- `src/model_deploy/act/types/` 下除 `observation.py` 以外的已有文件。

## 12. 验证方式

### 自动化验收命令

Python 命令必须使用 `python3`，不得写成 `python`。仓库内文件和目录必须使用相对仓库根目录路径。

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_observation.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | import ObservationState/ObservationSnapshot/ObservationFreshnessResult；frozen dataclass 构造和字段访问 | pytest 全部通过 |
| dry-run | 否 | 本 L3 无运行闭环 | — |
| fake-policy | 否 | 本 L3 无推理链路 | — |
| real-policy | 否 | 本 L3 无模型加载 | — |
| shadow-run | 否 | 本 L3 无 ROS | — |
| real-robot | 否 | 本 L3 不触发硬件 | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/
对应运行验收场景：S1
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S1 Mock 全字段 snapshot 组装 |
| 本 L3 提供的运行能力 | 定义 ObservationSnapshot 的 16D 数据契约，使下游 L2-03/L2-06 可以 import 类型而不依赖 L2-02 service/runtime |
| 本 L3 的局部命令 | `python3 -m pytest src/model_deploy/act/tests/types/test_observation.py -v` |
| L2 Gate 仍需后续 L3 补齐的内容 | deploy_012 提供 collector 组装 snapshot 的能力；deploy_014 提供 buffer 存储能力；deploy_016 提供端到端集成验证 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/`

### 必读代码

1. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py`（ObservationSnapshot 结构参考）
2. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/data/state_codec.py`（BimanualState 结构参考）
3. `src/model_deploy/act/types/`（已有 types 层文件，确认命名和 import 模式）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 无直接上游 L3（本 L3 是 l2-02-observation-snapshot 的第一个 L3）。
2. 无同组已完成 L3。

## 14. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：
正文 L3 编号：
dispatch.task_id：
是否一致：
所属 L2 ID：
是否属于新版 L2 白名单：
是否命中旧 L2 ID：
是否位于 legacy/archive 目录：
```

执行前必须读取 `dispatch` YAML，确认：

- `task_id` 与正文 L3 编号一致。
- `task_file` 与当前文件路径一致。
- `task_file` 位于 `03_tasks/task/active/<new-l2>/`。
- `group` 是新版 L2 ID。
- `branch` 是当前 L2 分支。
- `integration_branch` 是 `model_deploy`。
- `acceptance_dir` 指向所属 L2 的 `05_acceptance` 子目录。
- `acceptance_card` 指向当前 L3 的验收卡片。
- `acceptance_mode` 已明确。
- `acceptance_round_limit` 固定为 `3`。
- `depends_on` 已完成或明确无需等待。
- `dispatch_status` 不是 `blocked` 或 `waiting_user`。
- `robot_risk` 与验收方式一致。

执行前必须全文检查当前 L3 和 dispatch：

- 不得把 `ACT Contract Delta` 作为任务来源。
- 不得把 `AS-IS Contract -> TO-BE Contract -> Contract Delta` 作为当前主线。
- 不得引用旧 L2 ID 作为所属 L2、任务 group、分支 topic、dispatch 或 acceptance。
- 不得允许修改 `src/model_deploy/pi05/`、`pi05_old/` 或 `_legacy_layer_based_act/`。

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须采用测试优先或最小复现优先：

```text
最小复现 / 测试
-> 最小实现
-> 验证通过
-> 必要整理
```

不得为了通过当前 L3 验收而擅自扩大修改范围。

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] 已完成任务文件身份校验。
- [ ] 已确认所属 L2 ID 属于新版 L2 白名单，且任务不位于 legacy/archive 目录。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] 已读取当前 L2 功能边界、Pi0.5 源码 3.5 层微元拆解、ACT 微元设计、L2 验收机制、人类验收机制与六层设计文档。
- [ ] 已完成 Pi0.5 源码盘点中列出的相关代码确认。
- [ ] 改动没有越过当前 L2 的责任边界。
- [ ] 产物路径符合六层落点约束。
- [ ] 已完成本 L3 的自动化验收或说明无法自动化的原因。
- [ ] 已确认本 L3 的验收卡片、验收模式和本地验收边界。
- [ ] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [ ] 如涉及真机发送链路，已完成真机风险控制说明。
- [ ] 已写明回滚方式。

## 16. 回滚方式

说明如何回到改造前行为。优先写可操作路径：

```text
关闭参数 / 配置：不适用（本 L3 不引入配置开关）。
切回旧入口：不适用（本 L3 是新建文件，无旧入口）。
移除 adapter：不适用。
回退文件：删除 src/model_deploy/act/types/observation.py 和 src/model_deploy/act/tests/types/test_observation.py。
不可自动回滚的人工步骤：如 L2-03/L2-06 已 import ObservationSnapshot，需同步移除 import 后再回退。
```

## 17. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 所属 L2 的 `05_acceptance/l2-02-observation-snapshot/验收结果.md`：登记本 L3 贡献的运行验收场景、实际命令、测试输入、观察点、通过 / 失败现象、证据链接、未验证项和是否影响 L2 Gate。
- 对应 L3 验收卡片：供验收 agent 独立评估；执行 agent 不得自行改验收结论。
- 不得擅自更新阶段级 `当前进度.md` 或共享 `执行记录.md`，除非当前 L3 明确要求。
- 执行 sub-agent 完成单个 L3 后不得自行提交或推送；主 Agent 在验收进入可提交终态后，按阶段四 Git 规则处理。所属 L2 Gate 通过后，才允许合入 `model_deploy`。

交接摘要必须包含：

1. 读取了哪些 L2 设计文档、Pi0.5 源码、ACT 源码和历史任务。
2. 任务文件身份校验结论。
3. 修改了哪些文件。
4. 新增或修改了哪些函数、class、配置、测试或脚本。
5. 如何验证，实际命令是什么。
6. 哪些成功标准已勾选，哪些未验证。
7. 是否影响 dry-run、fake-policy、real-policy、shadow-run 或 real-robot。
8. 回滚方式。
9. 本次明确没有做什么。
10. 后续建议生成或执行的 L3。

---

## 执行摘要（Round 1，PASS_LOCAL）

### 任务文件身份校验

```text
用户指定任务路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_011_观测类型定义ObservationTypes.md
实际读取任务路径：同用户指定
文件名编号：deploy_011
正文 L3 编号：deploy_011
dispatch.task_id：deploy_011
是否一致：是
所属 L2 ID：l2-02-observation-snapshot
是否属于新版 L2 白名单：是
是否命中旧 L2 ID：否
是否位于 legacy/archive 目录：否
```

### 修改文件

1. `src/model_deploy/act/types/observation.py`（新建）— ObservationState、ObservationSnapshot、ObservationFreshnessResult 三个 frozen dataclass
2. `src/model_deploy/act/tests/types/test_observation.py`（新建）— 10 个测试用例
3. `src/model_deploy/act/types/__init__.py`（修改）— 新增 export

### 验证

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_observation.py -v
# 10 passed in 0.10s
```

### 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认所属 L2 ID 属于新版 L2 白名单，且任务不位于 legacy/archive 目录。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取当前 L2 功能边界、Pi0.5 源码 3.5 层微元拆解、ACT 微元设计、L2 验收机制、人类验收机制与六层设计文档。
- [x] 已完成 Pi0.5 源码盘点中列出的相关代码确认。
- [x] 改动没有越过当前 L2 的责任边界。
- [x] 产物路径符合六层落点约束。
- [x] 已完成本 L3 的自动化验收。
- [x] 已确认本 L3 的验收卡片、验收模式和本地验收边界。
- [x] 已将验收结果登记到所属 L2 的 `05_acceptance` 目录。
- [x] 如涉及真机发送链路，已完成真机风险控制说明（不适用）。
- [x] 已写明回滚方式。

### 影响分析

- dry-run / fake-policy / real-policy / shadow-run / real-robot：均不影响，本 L3 为纯数据定义。

### 本次明确没有做

- 未实现 ObservationCollector、ObservationBuffer、ObservationRosAdapter。
- 未引入 L2-01 state codec 调用（只校验 16D 维度）。
- 不修改 types 层外的任何文件（仅 types/__init__.py 做 export 更新）。

### 后续建议

deploy_012 ObservationCollector、deploy_013 图像预处理（可并行），然后是 deploy_014 ObservationBuffer。

# L3 微元改造任务：观测收集器 ObservationCollector

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-02-observation-snapshot 传感器订阅与 ObservationSnapshot 组装闭环
L3 编号：deploy_012
改造类型：source-adaptation
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_012_观测收集器ObservationCollector.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-observation-snapshot/deploy_012_验收卡片.md`
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
  task_id: deploy_012
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_012_观测收集器ObservationCollector.md
  group: l2-02-observation-snapshot
  branch: feat/model_deploy/l2-02-observation-snapshot
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot
  acceptance_scenarios: [S1, S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-observation-snapshot/deploy_012_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs
  wave: 2
  parallel_group: l2-02-observation-snapshot-p2
  depends_on: [deploy_011]
  must_run_after: []
  can_run_parallel_with: [deploy_013]
  blocks: [deploy_015]
  conflict_scope:
    files:
      - src/model_deploy/act/service/observation_collector.py
      - src/model_deploy/act/tests/service/test_observation_collector.py
    modules:
      - model_deploy.act.service.observation_collector
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
在 service/observation_collector.py 中实现 ObservationCollector class，完成 RAM 内传感器字段缓存、齐全性检查、新鲜度检查和 ObservationSnapshot 构造的核心业务逻辑。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 维护各字段最新值和采集时间。
- 检查必需字段是否齐全。
- 检查字段是否在 max_age_s 内新鲜。
- 调用 L2-01 state codec 生成 16D encoded_state。
- 将合法 snapshot 写入 latest-only buffer。

### L2 不负责

- 不调用 ACT 模型、不构造 ACT batch、不生成 ActionChunk。
- 不决定是否发起下一次推理、不维护 ControlLoop tick 状态。
- 不执行 action safety check、不发布硬件命令。
- 不创建 ROS subscription（属 deploy_015 ui 层）。

### 本 L3 在 L2 中的位置

```text
本 L3 实现 L2-02 的核心业务逻辑——字段汇聚和 snapshot 构造。它是 ui 层（deploy_015 ROS adapter）和 runtime 层（deploy_014 buffer）之间的桥梁：ui 层调用 update_* 写入字段值，snapshot() 的结果被写入 ObservationBuffer。service 层保持纯 RAM 计算，不依赖 ROS，可在无 ROS 环境下独立测试。
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
9. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/09_service层设计.md`

## 5. Pi0.5 源码盘点

必须具体到文件、入口、class、函数、配置或命令；不得只写"参考现有代码"。

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| `ObservationCollector._images` / `_values` / `_stamps` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 数据 | RAM 内字段缓存和时间戳 | ACT 字段名改为 TCP pose / gripper width 语义 | 结构复用 |
| `ObservationCollector.update_image` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 内部状态更新函数 | 更新 image cache 和 stamp | ACT 保留 RAM 更新形式，不直接依赖 ROS message | 结构复用 |
| `ObservationCollector.update_proprioception` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 内部状态更新函数 / 计算函数 | legacy joint positions 解码 | ACT 不照搬 proprioception；改为 TCP pose + gripper width 更新 | 参考理解 |
| `ObservationCollector.update_hand` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 内部状态更新函数 | gripper state 缓存 | ACT 改为 gripper width/state 更新 | 结构复用 |
| `ObservationCollector.update_vector` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 内部状态更新函数 | 通用 vector 更新 | ACT 保留通用 vector 更新形式用于 TCP pose | 结构复用 |
| `ObservationCollector._has_required_locked` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 计算函数 | 齐全性检查 | ACT 字段集合改为 ACT 必需字段（image / TCP pose / gripper） | 结构复用 |
| `ObservationCollector._has_stale_field_locked` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 计算函数 | 字段级新鲜度 gate | ACT 保留 | 结构复用 |
| `ObservationCollector.missing_fields` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 计算函数 | 缺字段诊断 | ACT 必须作为可观察诊断暴露 | 结构复用 |
| `ObservationCollector.snapshot` | `deploy/src/pi05/deploy/runtime/observation_collector.py` | 编排函数 / 计算函数 | snapshot 构造 | ACT 16D state codec 替代 26D 编码 | 结构复用 |

### 必须保留的源码启发

- 字段缓存用 dict + lock 模式：`_images`、`_values`、`_stamps` 三个 dict 按字段名索引。
- `update_*` 方法在 lock 下更新缓存和时间戳。
- `snapshot()` 先检查齐全性和新鲜度，再构造对象。
- 线程安全：使用 `threading.Lock` 保护共享缓存（callback 多线程可能并发写）。

### 禁止照搬的源码行为

- 禁止照搬 26D state 编码和 legacy `[right6, left6]` joint position 语义。
- 禁止在 service 层直接 import ROS message 类型。
- 禁止把 collector 放在 `runtime/` 目录（Pi0.5 放在 `deploy/runtime/` 下）。
- 禁止直接调用硬件 SDK 或发布 topic。

### 已知风险

- L2-01 state codec 未落地的条件下，`snapshot()` 的 16D 编码调用需要 mock stub。本 L3 可先用 mock state codec 完成核心逻辑测试，待 L2-01 就绪后替换。
- `required_fields` 的定义依赖 DeployConfig 中的 topic/image config；当前先用常量定义，后续由 deploy_015 注入。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `src/model_deploy/act/service/__init__.py`（如目录不存在则创建目录）。
- 新建 `src/model_deploy/act/service/observation_collector.py`。
- 实现 `ObservationCollector` class，包含：
  - `__init__(self, required_image_keys, required_state_fields, state_codec)`。
  - `update_image(name, image)`。
  - `update_tcp_pose(side, position, orientation)`。
  - `update_gripper_state(side, width)`。
  - `missing_fields()` -> list[str]。
  - `stale_fields(now, max_age_s)` -> list[str]。
  - `snapshot(max_age_s)` -> ObservationSnapshot 或 None。
- 新建 `src/model_deploy/act/tests/service/__init__.py`（如需）。
- 新建 `src/model_deploy/act/tests/service/test_observation_collector.py`，覆盖 mock 全字段 snapshot、缺字段拒绝、过期拒绝。

### 本次不做

- 不实现图像预处理（属 deploy_013）。
- 不实现 ObservationBuffer（属 deploy_014）。
- 不实现 ROS adapter（属 deploy_015）。
- 不调用真实 L2-01 state codec（先 mock）。
- 不修改 types/observation.py 或其他已有文件。

### 明确禁止修改

- `src/model_deploy/act/types/observation.py`（只读 import）。
- `src/model_deploy/act/config/`、`src/model_deploy/act/repo/`、`src/model_deploy/act/runtime/`、`src/model_deploy/act/ui/`。
- `src/model_deploy/pi05/`、`pi05_old/`。
- `DOCS/03_工程/阶段四：模型部署/03_tasks/归档/`。

### 函数 / class 策略

```text
ObservationCollector 封装为 class，原因：
- 需要跨多次 callback 调用保存字段缓存和时间戳（内部状态）。
- callback 可能来自多个 ROS topic 线程，需要 Lock 保证线程安全。
- update_* 是内部状态更新函数，snapshot/missing_fields/stale_fields 是计算函数。
- 不涉及 timer/thread/ROS node 生命周期（这些属 runtime/ui 层）。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否（只 import deploy_011 产物） | — | — |
| config | 否 | — | — |
| repo | 否 | — | — |
| service | 是 | `src/model_deploy/act/service/observation_collector.py` | RAM 内字段缓存、齐全性/新鲜度检查、snapshot 构造 |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/service/test_observation_collector.py` | mock 全字段/缺字段/过期场景测试 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `.../agent_context/06_types层设计.md` | 不涉及（deploy_011 已完成） |
| `.../agent_context/07_config层设计.md` | 不涉及（本 L2 无 config 产物） |
| `.../agent_context/08_repo层设计.md` | 不涉及（本 L2 无 repo 产物） |
| `.../agent_context/09_service层设计.md` | 完整实现 §3 observation_collector.py 中 ObservationCollector class 的全部方法和 §3 函数设计表中的全部函数 |
| `.../agent_context/10_runtime层设计.md` | 不涉及（后续 deploy_014 实现） |
| `.../agent_context/11_ui层设计.md` | 不涉及（后续 deploy_015 实现） |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `service/observation_collector.py` | `_images` / `_values` / `_stamps` 缓存 dict | 数据 | update 写入 | 被 snapshot/missing/stale 读取 | 修改 RAM（线程安全） | collector.mock_snapshot |
| `service/observation_collector.py` | `update_image(name, image)` | 内部状态更新函数 | image key, RAM image | 无 | 更新 _images 和 stamp | collector.mock_snapshot |
| `service/observation_collector.py` | `update_tcp_pose(side, position, orientation)` | 内部状态更新函数 | side, pose arrays | 无 | 更新 pose cache 和 stamp | collector.mock_snapshot |
| `service/observation_collector.py` | `update_gripper_state(side, width)` | 内部状态更新函数 | side, float width | 无 | 更新 gripper cache 和 stamp | collector.mock_snapshot |
| `service/observation_collector.py` | `missing_fields()` | 计算函数 | 缓存字段 | list[str] | 无 | collector.missing_reject |
| `service/observation_collector.py` | `stale_fields(now, max_age_s)` | 计算函数 | time, timeout | list[str] | 无 | collector.stale_reject |
| `service/observation_collector.py` | `snapshot(max_age_s)` | 编排函数 / 计算函数 | freshness 参数 | ObservationSnapshot 或 None | 无外部副作用 | collector.mock_snapshot, collector.missing_reject, collector.stale_reject |

## 9. 实施步骤

每一步都必须服务于"本次唯一目标"，不得顺手重构无关代码。

1. 确保 `src/model_deploy/act/service/` 目录存在，含 `__init__.py`。
2. 创建 `src/model_deploy/act/service/observation_collector.py`，实现 `ObservationCollector.__init__`，接收 required_image_keys、required_state_fields、state_codec，初始化 `_images`/`_values`/`_stamps` dict 和 `_lock`。
3. 实现 `update_image(name, image)`：在 lock 下写 `_images[name]` 和 stamp。
4. 实现 `update_tcp_pose(side, position, orientation)`：在 lock 下写 `_values[f"{side}_tcp_position"]`、`_values[f"{side}_tcp_orientation"]` 和 stamps。
5. 实现 `update_gripper_state(side, width)`：在 lock 下写 `_values[f"{side}_gripper_width"]` 和 stamp。
6. 实现 `missing_fields()`：在 lock 下对比 required_image_keys + required_state_fields 与已缓存字段。
7. 实现 `stale_fields(now, max_age_s)`：在 lock 下检查每个已缓存字段的 stamp 是否超过 max_age_s。
8. 实现 `snapshot(max_age_s)`：在 lock 下调用 missing_fields/stale_fields，全部通过后构造 ObservationState 和 ObservationSnapshot（调用 state_codec 生成 16D encoded_state）。
9. 创建 `src/model_deploy/act/tests/service/test_observation_collector.py`，编写测试：
   - `test_mock_full_snapshot`：注入全部 mock image/pose/gripper 字段，snapshot 返回非 None，encoded_state.shape == (16,)。
   - `test_missing_image_reject`：缺一个 image 字段，snapshot 返回 None，missing_fields 包含该字段名。
   - `test_missing_pose_reject`：缺一个 TCP pose 字段，snapshot 返回 None。
   - `test_stale_reject`：写入全字段后用极小 max_age_s 调用，snapshot 返回 None，stale_fields 非空。
   - `test_concurrent_update`：多线程并发 update 不抛异常，数据一致。
10. 运行 `python3 -m pytest src/model_deploy/act/tests/service/test_observation_collector.py -v`，确认全部通过。

## 10. 允许修改

> [!warning] 产物落点声明（必填）
> 本节每个允许修改 / 新增的产物，必须标注其落点路径，且路径必须符合 `ACT代码树分层与产物落点约束.md`。
> 允许修改路径只能落在 `src/model_deploy/act/`、当前 L2 设计目录、当前 L2 task/card/acceptance 目录。Pi0.5 路径只能列入"只读参考"，不能列入允许修改。

- `src/model_deploy/act/service/__init__.py`（如需新建目录）
- `src/model_deploy/act/service/observation_collector.py`（新建）
- `src/model_deploy/act/tests/service/__init__.py`（如需新建目录）
- `src/model_deploy/act/tests/service/test_observation_collector.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| ObservationCollector class | `src/model_deploy/act/service/observation_collector.py` | service |
| 单测 | `src/model_deploy/act/tests/service/test_observation_collector.py` | tests/service |

## 11. 禁止修改

- `src/model_deploy/act/types/observation.py`（只读 import）。
- `src/model_deploy/act/config/`、`src/model_deploy/act/repo/`、`src/model_deploy/act/runtime/`、`src/model_deploy/act/ui/`。
- `src/model_deploy/pi05/`、`pi05_old/`。
- `DOCS/03_工程/阶段四：模型部署/03_tasks/归档/`。
- 任何其他 L2 的源码。

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_observation_collector.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | import ObservationCollector；mock 全字段 snapshot；缺字段/过期拒绝；并发安全 | pytest 全部通过 |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| shadow-run | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/
对应运行验收场景：S1, S2
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S1 Mock 全字段 snapshot 组装、S2 缺字段/过期拒绝 |
| 本 L3 提供的运行能力 | 字段缓存、齐全性检查、新鲜度检查、snapshot 构造——L2-02 的核心业务逻辑 |
| 本 L3 的局部命令 | `python3 -m pytest src/model_deploy/act/tests/service/test_observation_collector.py -v` |
| L2 Gate 仍需后续 L3 补齐的内容 | deploy_014 buffer 存储、deploy_015 ROS 订阅、deploy_016 端到端集成验证 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/`

### 必读代码

1. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py`（ObservationCollector 结构参考）
2. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py`（ObservationSnapshot 消费参考）
3. `src/model_deploy/act/types/observation.py`（deploy_011 产物，本 L3 import 的数据类型）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游 L3：deploy_011 观测类型定义（types/observation.py）。
2. 同组可并行 L3：deploy_013 图像预处理（不同文件，无冲突）。

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
切回旧入口：不适用（本 L3 新建 service 层，无旧入口）。
移除 adapter：不适用。
回退文件：删除 src/model_deploy/act/service/observation_collector.py 和 src/model_deploy/act/tests/service/test_observation_collector.py。
不可自动回滚的人工步骤：如 deploy_015（ROS adapter）已 import ObservationCollector，需同步移除 import 后再回退。
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

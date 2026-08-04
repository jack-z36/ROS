# L3 微元改造任务：L2 Gate 集成测试与验收脚本 l2_02_verify.sh

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-02-observation-snapshot 传感器订阅与 ObservationSnapshot 组装闭环
L3 编号：deploy_016
改造类型：test-coverage
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_016_L2Gate集成测试与验收脚本.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-observation-snapshot/deploy_016_验收卡片.md`
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
  task_id: deploy_016
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_016_L2Gate集成测试与验收脚本.md
  group: l2-02-observation-snapshot
  branch: feat/model_deploy/l2-02-observation-snapshot
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot
  acceptance_scenarios: [S1, S2, S3, S4, S5, S6]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-observation-snapshot/deploy_016_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs
  wave: 5
  parallel_group: l2-02-observation-snapshot-p5
  depends_on: [deploy_011, deploy_012, deploy_013, deploy_014, deploy_015]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/tests/integration/test_l2_02_gate.py
      - src/model_deploy/act/scripts/l2_02_verify.sh
    modules:
      - model_deploy.act.tests.integration.test_l2_02_gate
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
编写 L2-02 的端到端集成测试（test_l2_02_gate.py）和统一验收脚本（l2_02_verify.sh），覆盖全部 12 个验证标签，实现 mock observation 全链路闭环验证，并在终端按分层分组格式输出 PASS/FAIL/BLOCKED 结果。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 从外部 observation topics 接收传感器数据，生成完整、合法、新鲜的 ObservationSnapshot。
- 维护各字段最新值和时间戳，检查齐全性和新鲜度。
- 将合法 snapshot 写入 latest-only buffer。
- 暴露缺字段、过期和 decode 失败的可观察诊断。

### L2 不负责

- 不调用 ACT 模型、不构造 ACT batch、不生成 ActionChunk。
- 不决定推理节奏、不维护 ControlLoop tick 状态。
- 不执行 action safety check、不发布硬件命令。

### 本 L3 在 L2 中的位置

```text
本 L3 是 L2-02 的最后一个 L3，负责把所有前序 L3（deploy_011~deploy_015）的产物串联成端到端可验证的闭环。集成测试 mock 全链路（无 ROS），验证 types → service → runtime 的完整数据流；验收脚本（l2_02_verify.sh）按 L2 Gate 的 12 个验证标签逐项运行并汇总输出，供人类验收使用。
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

## 5. Pi0.5 源码盘点

必须具体到文件、入口、class、函数、配置或命令；不得只写"参考现有代码"。

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| Pi0.5 dry-run / shadow-run 测试 | `pi05_test/tests/` 中的集成测试 | test-coverage | 端到端 mock 验证 | ACT 用 mock 替代 Pi0.5 的 ROS 集成，覆盖 12 个新标签 | 参考理解 |
| Pi0.5 deploy node 全链路 | `pi05_vla_deploy_node.py` | 编排函数 | callback → collector → snapshot → buffer 编排 | ACT 拆成 5 个独立 L3，需端到端集成测试验证协作 | 参考理解 |

### 必须保留的源码启发

- 端到端的 mock 数据构造方式：mock image (H, W, 3 uint8)、mock pose (7 floats)、mock gripper width (1 float)。
- 验证 `collector.snapshot()` → `buffer.set_observation()` → `buffer.latest_observation()` 的完整数据流。

### 禁止照搬的源码行为

- 禁止把 Pi0.5 的 ROS node 集成测试照搬为 L2-02 集成测试（无 ROS 环境）。
- 禁止在集成测试中直接调用模型推理或硬件命令。
- 禁止把 ROS topic 真实订阅写成通过（标记 env-blocked）。

### 已知风险

- 无 ROS 环境，真实 topic 订阅只能标记 `BLOCKED_ENV`。
- `l2_02_verify.sh` 依赖前序 L3 全部完成，任一 L3 未完成则对应标签 FAIL。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `src/model_deploy/act/tests/integration/test_l2_02_gate.py`。
- 实现端到端集成测试用例：
  - `test_full_mock_pipeline`：mock 全字段 → collector → snapshot → buffer → latest_observation，验证端到端闭环。
  - `test_missing_field_pipeline`：缺 image 字段 → collector 返回 None → buffer 不写入 → latest_observation 返回 None。
  - `test_stale_pipeline`：写入后用极小 max_age_s 读取 → latest_observation 返回 None。
  - `test_boundary_no_overreach`：源码扫描确认 L2-02 无越界实现（rg 检查）。
  - `test_boundary_no_config_repo`：确认 config/repo 目录无 L2-02 新增 .py 文件。
  - `test_import_without_ros`：整个 L2-02 模块栈在无 ROS 环境下可 import。
- 新建 `src/model_deploy/act/scripts/l2_02_verify.sh`。
- 实现统一验收脚本，按 `04_L2验收机制.md §4` 的格式规约输出：
  - 按层分组（types / service / runtime / ui / 边界）。
  - 每标签一行 `PASS|FAIL|BLOCKED` + 标签名 + 说明。
  - FAIL 附文件、微元、pytest 节点、错误摘要（缩进 `├─/└─`）。
  - 末行汇总 `N PASS / N FAIL / N BLOCKED`。
  - 退出码：全部 PASS（BLOCKED 可存在）→ 0；任一 FAIL → 1。

### 本次不做

- 不修改 deploy_011~deploy_015 的任何源码。
- 不创建 ROS launch 文件（属后续 L2-06）。
- 不发布 metrics/status topic。
- 不在无 ROS 环境声明真实 topic 订阅已通过。

### 明确禁止修改

- `src/model_deploy/act/types/observation.py`
- `src/model_deploy/act/service/observation_collector.py`
- `src/model_deploy/act/service/image_preprocess.py`
- `src/model_deploy/act/runtime/observation_buffer.py`
- `src/model_deploy/act/ui/observation_ros_adapter.py`
- `src/model_deploy/act/config/`、`src/model_deploy/act/repo/`
- `src/model_deploy/pi05/`、`pi05_old/`

### 函数 / class 策略

```text
集成测试使用 pytest fixture + mock 模式，不封装为 class。验收脚本是 bash 脚本，调用 pytest + rg/find 等工具，不涉及 Python class 判断。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否（只 import deploy_011 产物） | — | — |
| config | 否 | — | — |
| repo | 否 | — | — |
| service | 否（只 import deploy_012/003 产物） | — | — |
| runtime | 否（只 import deploy_014 产物） | — | — |
| ui | 否（只 import deploy_015 产物） | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/integration/test_l2_02_gate.py` | 端到端 mock 集成测试 |
| scripts | 是 | `src/model_deploy/act/scripts/l2_02_verify.sh` | 统一验收脚本 |
| acceptance | 是 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/scripts/`、`logs/` | 验收证据落点 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `.../agent_context/06_types层设计.md` | 验收覆盖 contract.encoded_state_dim、contract.importable |
| `.../agent_context/07_config层设计.md` | 验收覆盖 boundary.no_config_repo |
| `.../agent_context/08_repo层设计.md` | 验收覆盖 boundary.no_config_repo |
| `.../agent_context/09_service层设计.md` | 验收覆盖 collector.mock_snapshot、collector.missing_reject、collector.stale_reject、preprocess.image |
| `.../agent_context/10_runtime层设计.md` | 验收覆盖 buffer.latest_only、buffer.max_age |
| `.../agent_context/11_ui层设计.md` | 验收覆盖 adapter.no_ros_importable、adapter.real_subscription (BLOCKED_ENV) |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `tests/integration/test_l2_02_gate.py` | `test_full_mock_pipeline` | 编排函数（测试） | mock image/pose/gripper 数据 | pytest 结果 | 无（只读 L2-02 模块） | S1 |
| `tests/integration/test_l2_02_gate.py` | `test_missing_field_pipeline` | 编排函数（测试） | mock 缺字段数据 | pytest 结果 | 无 | S2 |
| `tests/integration/test_l2_02_gate.py` | `test_stale_pipeline` | 编排函数（测试） | mock 过期数据 | pytest 结果 | 无 | S2 |
| `tests/integration/test_l2_02_gate.py` | `test_boundary_no_overreach` | 编排函数（测试） | rg 扫描源码 | pytest 结果 | 无 | S6 |
| `tests/integration/test_l2_02_gate.py` | `test_import_without_ros` | 编排函数（测试） | 无 | pytest 结果 | 无 | S5 |
| `scripts/l2_02_verify.sh` | 统一验收脚本 | 编排函数（shell） | 仓库根路径 | 终端输出 + 退出码 | 调用 pytest + rg + find | 全部 12 标签 |

## 9. 实施步骤

每一步都必须服务于"本次唯一目标"，不得顺手重构无关代码。

1. 创建 `src/model_deploy/act/scripts/l2_02_verify.sh`。
2. 实现验收脚本结构：
   - 设置 cwd 为仓库根目录。
   - 按层分块输出（types / service / runtime / ui / 边界）。
   - 运行 pytest 子集并捕获输出，按标签判定 PASS/FAIL。
   - rg 扫描越界逻辑（`predict_action_chunk|ActionChunk|SafetyGuard|publish.*hardware` 等关键词在 service/runtime/ui 中）。
   - find 检查 config/repo 目录无新增 .py 文件。
   - 检查无 ROS 环境时 types/service/runtime/ui 全量 import 不失败。
   - 末行输出汇总和退出码。
3. 创建 `src/model_deploy/act/tests/integration/test_l2_02_gate.py`。
4. 实现 `test_full_mock_pipeline`：
   - 构造 mock ObservationCollector（注入 required fields + mock state_codec）。
   - 逐字段 update（2 image + 2 TCP pose + 2 gripper width）。
   - 调用 collector.snapshot(max_age_s=5.0)，断言非 None。
   - 创建 ObservationBuffer，set_observation(snapshot)。
   - latest_observation() 返回同一 snapshot。
   - 验证 encoded_state.shape == (16,)。
5. 实现 `test_missing_field_pipeline`：
   - 只注入部分字段（缺一个 image）。
   - collector.snapshot() 返回 None。
   - collector.missing_fields() 包含缺失字段名。
   - buffer 未被写入，latest_observation() 返回 None。
6. 实现 `test_stale_pipeline`：
   - 注入全字段后用 time.sleep 超过 max_age_s。
   - collector.snapshot(max_age_s=0.01) 返回 None。
   - collector.stale_fields() 非空。
7. 实现 `test_boundary_no_overreach`：
   - 用 rg 扫描 `src/model_deploy/act/service/`、`src/model_deploy/act/runtime/`、`src/model_deploy/act/ui/`。
   - 确认无 `predict_action_chunk|ActionChunk|SafetyGuard|publish.*hardware|driver` 实现。
8. 实现 `test_import_without_ros`：
   - import types/observation、service/observation_collector、service/image_preprocess、runtime/observation_buffer、ui/observation_ros_adapter。
   - 确认全部 import 成功。
9. 实现 `test_boundary_no_config_repo`：
   - 确认 config/ 和 repo/ 目录下无 L2-02 新增 .py 文件（或有明确豁免）。
10. 运行 `bash src/model_deploy/act/scripts/l2_02_verify.sh`，确认全部标签 PASS 或合理 BLOCKED，退出码 0。

## 10. 允许修改

> [!warning] 产物落点声明（必填）
> 本节每个允许修改 / 新增的产物，必须标注其落点路径，且路径必须符合 `ACT代码树分层与产物落点约束.md`。
> 允许修改路径只能落在 `src/model_deploy/act/`、当前 L2 设计目录、当前 L2 task/card/acceptance 目录。Pi0.5 路径只能列入"只读参考"，不能列入允许修改。

- `src/model_deploy/act/tests/integration/test_l2_02_gate.py`（新建）
- `src/model_deploy/act/scripts/l2_02_verify.sh`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| L2 Gate 集成测试 | `src/model_deploy/act/tests/integration/test_l2_02_gate.py` | tests/integration |
| 统一验收脚本 | `src/model_deploy/act/scripts/l2_02_verify.sh` | scripts |

## 11. 禁止修改

- `src/model_deploy/act/types/observation.py`
- `src/model_deploy/act/service/observation_collector.py`
- `src/model_deploy/act/service/image_preprocess.py`
- `src/model_deploy/act/runtime/observation_buffer.py`
- `src/model_deploy/act/ui/observation_ros_adapter.py`
- `src/model_deploy/act/config/`、`src/model_deploy/act/repo/`
- `src/model_deploy/pi05/`、`pi05_old/`
- `DOCS/03_工程/阶段四：模型部署/03_tasks/归档/`

## 12. 验证方式

### 自动化验收命令

```bash
# 运行集成测试
python3 -m pytest src/model_deploy/act/tests/integration/test_l2_02_gate.py -v

# 运行统一验收脚本
bash src/model_deploy/act/scripts/l2_02_verify.sh
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | import 全模块栈不失败；集成测试全部通过 | pytest 全部通过 |
| dry-run | 是 | l2_02_verify.sh 输出全部标签结果，退出码 0 | 无 FAIL（BLOCKED 可接受） |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| shadow-run | 否 | 需要 ROS 环境，当前标记 env-blocked | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/
对应运行验收场景：S1, S2, S3, S4, S5, S6
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S1 Mock 全字段 snapshot 组装、S2 缺字段/过期拒绝、S3 图像预处理、S4 Latest-only buffer 语义、S5 无 ROS 可 import、S6 边界不越界 |
| 本 L3 提供的运行能力 | 端到端 mock 全链路验证 + 统一验收脚本，覆盖全部 12 个 L2 Gate 标签 |
| 本 L3 的局部命令 | `bash src/model_deploy/act/scripts/l2_02_verify.sh` |
| L2 Gate 仍需后续 L3 补齐的内容 | 无（本 L3 是 L2-02 最后一个 L3） |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/`

### 必读代码

1. `src/model_deploy/act/types/observation.py`（deploy_011 产物）
2. `src/model_deploy/act/service/observation_collector.py`（deploy_012 产物）
3. `src/model_deploy/act/service/image_preprocess.py`（deploy_013 产物）
4. `src/model_deploy/act/runtime/observation_buffer.py`（deploy_014 产物）
5. `src/model_deploy/act/ui/observation_ros_adapter.py`（deploy_015 产物）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游 L3：deploy_011 观测类型定义、deploy_012 ObservationCollector、deploy_013 图像预处理、deploy_014 ObservationBuffer、deploy_015 ROS 适配器。
2. 无同组并行 L3（wave5 仅本 L3，且为最后一个 L3）。

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
关闭参数 / 配置：不适用。
切回旧入口：不适用（本 L3 新建集成测试和验收脚本，无旧入口）。
移除 adapter：不适用。
回退文件：
  - 删除 src/model_deploy/act/tests/integration/test_l2_02_gate.py
  - 删除 src/model_deploy/act/scripts/l2_02_verify.sh
不可自动回滚的人工步骤：无（集成测试和验收脚本不参与运行时链路，删除即可回滚）。
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

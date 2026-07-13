# L3 微元改造任务：Action 发布类型与输出配置契约

## 1. 任务定位

阶段：阶段四：模型部署  
L1：ACT 部署程序开发  
所属 L2：`l2-05-action-publisher` 单步 Action 到执行器 Topic 适配发送闭环  
L3 编号：deploy_041  
改造类型：`source-adaptation`  
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_041_Action发布类型与输出配置契约.md`  
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_041_验收卡片.md`  
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/`  
验收模式：`direct-local`  
辅助验收模式：[`downstream-l2`]  
本地验收是否必须：`true`  
真机风险等级：`none`  
L2 分支：`feat/model_deploy/l2-05-action-publisher`  
集成分支：`model_deploy`

> [!note] 生成权威
> 用户已明确要求忽略 HTML 与 L1 对齐阻断，本 L3 只以目标 L2 `agent_context/*.md` 为设计权威；HTML 不得作为实现来源。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_041
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_041_Action发布类型与输出配置契约.md
  group: l2-05-action-publisher
  branch: feat/model_deploy/l2-05-action-publisher
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher
  acceptance_scenarios: [G01, G02, G03]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_041_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [downstream-l2]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/logs
  wave: 1
  parallel_group: l2-05-action-publisher-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_042, deploy_043, deploy_044, deploy_045]
  conflict_scope:
    files:
      - src/model_deploy/act/types/action_publish.py
      - src/model_deploy/act/types/__init__.py
      - src/model_deploy/act/config/schema.py
      - src/model_deploy/act/config/__init__.py
      - src/model_deploy/act/config_files/deploy.yaml
      - src/model_deploy/act/tests/types/test_action_publish.py
      - src/model_deploy/act/tests/config/test_command_output_config.py
    modules:
      - model_deploy.act.types.action_publish
      - model_deploy.act.config.schema
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 sub-agent 只实现本 L3、运行局部测试并写执行摘要；不修改验收结论。
- 验收 sub-agent 只读任务、验收卡、diff 与日志；不修源码、dispatch 或 Git。
- `FAIL_LOCAL` 最多返回执行 Agent 修正 3 轮。
- 真实 CLI parser/launch 对接属 L2-06/UI 启动装配；本 L3 只提供“缺省 False + 显式 bool 覆盖”的配置装配契约。

## 3. 本次唯一目标

```text
实现 C1-C7 的冻结 RAM 契约与 CommandOutputConfig 默认关闭装配，使后续 B1/B2/B3 共用一套可校验数据语言。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 消费 L2-04 `SafetyResult` 与 L2-06 `CommandPermit`，返回真实发布事实 `ActionPublishResult`。
- 保证未显式启用 command output 时四路 command 永不写出。

### L2 不负责

- 不解析 CLI，不创建 publisher，不发布 Topic，不构造 L2-06 的原始 gate 事实。

### 本 L3 在 L2 中的位置

```text
deploy_041 交付 C1-C7；deploy_042 产出 C4，deploy_043 消费 C4，deploy_044 消费 C1/C2/C7 并产出 C6。
```

### 必读 L2 设计文档

1. `02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. 目标 L2 `agent_context/00_INDEX.md`
4. `01_L2功能边界.md`
5. `02_pi05源码3.5层微元拆解.md`
6. `03_ACT微元设计与协作.md`
7. `03a_功能微元总览与组织结构.md`
8. `04_L2验收机制.md`
9. `05_人类验收机制.md`
10. `06_types层设计.md`
11. `07_config层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层类型 | 已有能力 | 与 ACT 目标差距 | 复用判断 |
|---|---|---|---|---|---|
| `BimanualAction` | `common/src/pi05/common/robot/action_spec.py:22-39` | 数据 | frozen 动作对象 | 旧 14D，无 permit/result | 结构复用 |
| `Pi05CommandTopics` | `common/src/pi05/common/ros/topics.py:18-38` | 数据 | 冻结 topic 集 | 旧 topic，无 policy/status 契约 | 结构复用 |
| `RuntimeConfig.mode` | `deploy/src/pi05/deploy/config/schema.py:34-63` | 数据 | mode 选择 | 与 CLI+permit 边界冲突 | 不复用 |

### 必须保留的源码启发

- 跨模块对象用 frozen dataclass/Enum，topic 与输出配置由启动期注入。

### 禁止照搬的源码行为

- 禁止 14D、`accepted: bool`、mode 状态机、原始 deadman/gate 字段、持久化 `enabled: true`。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `types/action_publish.py`，实现 C1 `CommandPermit`、C2 `ActionPublishRequest`、C3 `ArmPoseTarget`、C4 `TopicPayloadBundle`、C5 `PublishOutcome`、C6 `ActionPublishResult`。
- 用 frozen dataclass/Enum 固定字段、tuple 可变性边界及 C1/C2/C6 组合不变量。
- 在 `config/schema.py` 增加 C7 `CommandOutputConfig` 及 `DeployConfig.command_output`，验证 frame、映射范围、deadband、间隔和 QoS。
- 装配 API 缺省 `command_output_enabled=False`；仅允许启动调用方传入显式 bool 覆盖。
- `deploy.yaml` 只写 frame/映射/deadband/QoS；若出现持久化 `enabled` 必须拒绝。
- 补 types/config 局部测试与稳定导出。

### 本次不做

- 不删除全局 `RuntimeConfig.mode`，但 L2-05 任何新对象不得消费它。
- 不新建 CLI parser/launch/node；真实 `--enable-command-output` 对接交给 L2-06 装配。
- 不实现 B1/B2/B3、ROS message 或 publisher。

### 函数 / class 策略

```text
C1-C4/C6/C7 使用 frozen dataclass；C5 使用 str Enum。配置装配为窄函数/类方法，不新建无状态配置 class。
```

## 7. 六层产物落点

| 层 | 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 是 | `src/model_deploy/act/types/action_publish.py` | C1-C6 公共 RAM 契约 |
| config | 是 | `src/model_deploy/act/config/schema.py` | C7 与默认关闭装配 |
| repo/service/runtime/ui | 否 | — | — |
| tests | 是 | `tests/types/test_action_publish.py` + `tests/config/test_command_output_config.py` | G01-G03 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现内容 |
|---|---|
| `06_types层设计.md` | C1-C6 字段与不变量 |
| `07_config层设计.md` | C7、YAML 与显式 enable 覆盖 |
| `08_repo层设计.md` | 无产物 |
| `09_service层设计.md` | 无；下游只消费类型 |
| `10_runtime层设计.md` | 不创建 permit/time |
| `11_ui层设计.md` | 无 ROS 产物 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 副作用 | 验收 |
|---|---|---|---|---|---|---|
| `types/action_publish.py` | C1-C6 | 数据 | 字段值 | frozen 对象/Enum | 无 | G01 |
| `config/schema.py` | C7 | 数据 | YAML 映射 + 显式 bool | frozen config | 无 | G02/G03 |

## 9. 实施步骤

1. 先写 C1-C6 合法/非法/frozen 测试，再实现 `types/action_publish.py`。
2. 先写 C7 默认关闭、显式开启、持久化 enabled 拒绝和参数校验测试，再扩展 schema/YAML。
3. 更新 types/config 导出，运行局部与既有 config/types 回归。

## 10. 允许修改

- `src/model_deploy/act/types/action_publish.py`
- `src/model_deploy/act/types/__init__.py`
- `src/model_deploy/act/config/schema.py`
- `src/model_deploy/act/config/__init__.py`
- `src/model_deploy/act/config_files/deploy.yaml`
- `src/model_deploy/act/tests/types/test_action_publish.py`
- `src/model_deploy/act/tests/config/test_command_output_config.py`
- 仅为保持既有 schema 回归，必要时可最小修改 `src/model_deploy/act/tests/config/test_schema.py`。

## 11. 禁止修改

- `src/model_deploy/act/repo/`、`service/`、`runtime/`、`ui/`
- `src/model_deploy/pi05/`、`DOCS/03_工程/阶段四：模型部署/pi05_old/`
- L2-06 启动入口、CLI parser 或 launch（未有明确对接点前）
- HTML 或 L1 文档

## 12. 验证方式

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_action_publish.py \
  src/model_deploy/act/tests/config/test_command_output_config.py \
  src/model_deploy/act/tests/config/test_schema.py -v
```

| 验证层级 | 需要 | 通过标准 |
|---|---|---|
| unit/import | 是 | C1-C7 冻结、不变量与配置校验通过 |
| downstream-l2 | 后续 | L2-06 真实 CLI parser 显式传入 `True` |
| real-robot | 否 | 本 L3 无 ROS/硬件副作用 |

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | G01-G03 |
| 提供能力 | C1-C7 公共语言与 CLI default-off 契约 |
| 后续补齐 | B1/B2/B3 与 L2-06 启动对接 |

## 13. 必读上下文

- 必读任务文档：阶段四工作流、ACT 落点约束、L3 模板、目标 L2 `agent_context/00-11`。
- 必读代码：`config/schema.py`、`types/action_spec.py`、`types/safety_result.py`及相关既有测试。
- Pi0.5 参考只读：`common/.../action_spec.py`、`deploy/.../config/schema.py`。
- Git 执行前另行读取 Git 约束；本任务不做 Git 操作。

## 14. 执行要求

- 执行前核对用户路径、文件名 ID、正文 ID、dispatch ID 均为 `deploy_041`。
- 确认 group/branch 为 `l2-05-action-publisher`、任务位于 active 新版目录。
- 按测试优先完成；不得为了通过测试引入 mode 或 `accepted`。

## 15. 成功标准

- [x] C1-C6 存在、冻结且非法字段组合在构造期失败。
- [x] C7 缺省 False，显式 bool 可覆盖，YAML 不能开启 command。
- [x] `DeployConfig.command_output` 可稳定 import，既有 config/types 回归通过。
- [x] 无 ROS、service、runtime 或硬件依赖。
- [x] 验收证据、回滚方式与未验证 CLI 对接已登记。

## 16. 回滚方式

```text
删除 types/action_publish.py 及两个新测试；还原 types/config __init__、schema.py 与 deploy.yaml 的本 L3 改动。
本 L3 不进行 Git 回滚；由主 Agent 按实际 diff 回退。
```

## 17. 完成后交接

- 更新成功标准和执行摘要，将命令与结果登记到 L2-05 验收目录。
- 不自行归档、commit 或 push；验收 Agent 独立给出 PASS/FAIL/BLOCKED。

## 18. 执行摘要 / Execution Summary（deploy_041）

执行 sub-agent：直接本地验证（`acceptance_mode: direct-local`）。仅实现本 L3，未触碰禁止修改区（repo/service/runtime/ui/pi05/CLI/launch/HTML），未引入 `RuntimeConfig.mode`、`accepted: bool`、状态机或原始 deadman/gate 字段。

### 已变更文件

- 新增 `src/model_deploy/act/types/action_publish.py`（C1-C6 冻结 RAM 契约）。
- 扩展 `src/model_deploy/act/config/schema.py`（C7 `CommandOutputConfig` + `DeployConfig.command_output` 默认关闭装配）。
- 新增 `src/model_deploy/act/config_files/deploy.yaml` 的 `command_output:` 段（仅 frame/映射/deadband/QoS，无 `enabled`）。
- 更新 `src/model_deploy/act/types/__init__.py`、`src/model_deploy/act/config/__init__.py` 导出。
- 新增 `src/model_deploy/act/tests/types/test_action_publish.py`（G01）。
- 新增 `src/model_deploy/act/tests/config/test_command_output_config.py`（G02/G03）。
- 既有 `src/model_deploy/act/tests/config/test_schema.py` 未修改，回归通过。

### 验证命令与结果

1. 导入检查（通过）：
   ```bash
   PYTHONPATH=src python3 -c "from model_deploy.act.types.action_publish import *; from model_deploy.act.config.schema import DeployConfig"
   ```
   结果：`IMPORT OK`（退出码 0）。

2. 局部测试（通过，78 passed / 0 failed）：
   ```bash
   PYTHONPATH=src python3 -m pytest \
     src/model_deploy/act/tests/types/test_action_publish.py \
     src/model_deploy/act/tests/config/test_command_output_config.py \
     src/model_deploy/act/tests/config/test_schema.py -v
   ```
   结果：`78 passed in 0.10s`。其中：
   - `test_action_publish.py`：C1-C6 合法/非法/frozen/tuple 边界/组合不变量，共 42 项。
   - `test_command_output_config.py`：C7 默认关闭、显式开启、持久化 `enabled` 拒绝、参数校验，共 18 项。
   - `test_schema.py`：既有 config 回归，共 18 项，全部通过。

### 关键实现点

- C1：allowed=True 要求 reason_code=None；allowed=False 要求非空 reason_code，否则构造期 `ValueError`。
- C2：时间 finite、monotonic_s≥0；请求不携带 `command_output_enabled`。
- C3/C4：position/quaternion/policy_action 经 `_as_float_tuple` 转不可变 tuple，拒绝 numpy 可变 view，长度校验（3/4/16），gripper 限定 0..100。
- C5：str Enum（REJECTED/OBSERVED/BLOCKED/PUBLISHED/PARTIAL/FAILED），无 mode/accepted。
- C6：command_publish_count∈0..4；REJECTED/OBSERVED/BLOCKED→count=0；PUBLISHED→command_plan_completed=True；PARTIAL→count>0 且未完成；driver_accepted/hardware_reached 恒为 None。
- C7：`command_output_enabled` 默认 False，仅由 `from_mapping(..., command_output_enabled=...)` 显式覆盖；YAML `command_output` 段出现 `enabled` 键即抛 `DeployConfigError`；frame/映射/deadband/interval/QoS 范围校验。

### 未验证项（Unverified）

- **L2-06 CLI 真实对接**：`--enable-command-output` 显式 bool 覆盖路径（置信为 L2-06 启动装配）本 L3 未实现也未运行；仅验证了 `from_mapping(command_output_enabled=True)` 装配开关可用。属下游 L2 Gate 贡献。
- **ROS / 真机**：本 L3 无 ROS、publisher、硬件副作用，不涉 real-robot 验证。
- **B1/B2/B3**：下游消费 C4/C1/C2/C7 的产出逻辑不在本 L3 范围。

### 回滚方式

删除 `src/model_deploy/act/types/action_publish.py` 及两个新测试文件；还原 `types/__init__.py`、`config/__init__.py`、`schema.py` 与 `deploy.yaml` 的本 L3 改动。由主 Agent 按实际 diff 回退，本 L3 不做 Git 操作。


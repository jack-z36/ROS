# L3 微元改造任务：deploy_006 experiment_config 加载器

## 1. 任务定位

L3 编号：deploy_006

本任务属于阶段四（模型部署），L1 ACT 模型部署线，L2 `l2-01-external-contract`（外部参数加载与契约校验闭环），改造类型 `source-adaptation`，验收模式 `direct-local`，真机风险 `none`，开发分支 `feat/model_deploy/l2-01-external-contract`，集成分支 `model_deploy`。

产物落点遵循六层架构规范：repo 层产物落在 `src/model_deploy/act/repo/`，对应测试落在 `src/model_deploy/act/tests/repo/`。repo 层不得向上引用 config/service/runtime/ui 层，不得执行维度业务校验。

> [!warning] 产物落点约束
> 本 L3 仅产出 repo 层源码与 repo 层单元测试两个文件。任何落在 config/service/runtime/ui 层的产物均视为越界。`experiment_config.yaml` 的解析结果以原值（dict/dataclass）形式对外暴露，维度字段保持原值，不得在 repo 层覆写或归一化。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_006
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_006_experiment_config加载器.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S4]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_006_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 2
  parallel_group: l2-01-external-contract-p2
  depends_on: [deploy_001, deploy_002, deploy_003]
  must_run_after: []
  can_run_parallel_with: [deploy_004, deploy_005, deploy_007]
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/repo/experiment_config_loader.py
      - src/model_deploy/act/tests/repo/test_experiment_config_loader.py
    modules:
      - model_deploy.act.repo.experiment_config_loader
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行

Agent 按本文件第 9 节实施步骤执行，严格遵守第 10 节允许修改与第 11 节禁止修改边界。实施完成后按第 12 节验证方式自测，自测通过后在 `acceptance_feedback_dir` 写入验收日志，并按第 17 节完成后交接规范回写状态。

### 验收边界

本 L3 采用 direct-local 验收模式：在本地开发环境通过单元测试与 L2 Gate 贡献检查直接验收，不需要真机部署、不需要端到端集成。验收范围为 `conflict_scope` 内的两个文件，验收轮次上限 3 轮，必须 local_acceptance_required 通过。

## 3. 本次唯一目标

```text
读取 experiment_config.yaml → dict/object。
只读不校验维度，保留原值供 config 层交叉校验。
ACT 不覆写维度，保留 experiment_config 中的 state_dim/action_dim 原值用于交叉校验。
```

本 L3 是 L2 `l2-01-external-contract` 外部契约校验闭环的输入侧加载器之一：把 bundle 中的 `experiment_config.yaml` 加载为可读结构，原样保留 `state_dim`/`action_dim` 等维度字段，供后续 config 层（L2 Gate S4）将 experiment_config 维度与 16D 契约、normalizer 维度进行交叉校验。本 L3 只负责“忠实加载”，不负责“判断对错”。

## 4. 所属 L2 边界与设计来源

### L2 负责

L2 `l2-01-external-contract` 负责外部参数（bundle 文件、experiment_config、normalizers）的加载与契约校验闭环：加载 bundle 目录结构、解析 experiment_config、解析 normalizers、并对加载得到的维度字段（state_dim/action_dim）进行交叉校验，确保 bundle 内部各来源维度一致并与 16D 契约对齐。

### L2 不负责

L2 不负责模型权重加载、不负责推理执行、不负责真机通信、不负责 action 平滑与跨块对齐、不负责维度归一化或回退。维度“应该是什么”由 L1 ACT 契约定义，L2 只校验“加载到的值是否互相一致”。

### 本 L3 在 L2 中的位置

本 L3 是 L2 加载链路中“experiment_config 来源”的加载节点。L2 的交叉校验（S4）需要 experiment_config 的 `state_dim`/`action_dim` 作为输入之一。本 L3 把该输入原样加载出来，不参与校验判断本身。本 L3 与 deploy_004（manifest 解析）、deploy_005（normalizers 解析）、deploy_007（bundle 目录检查）构成 L2 的并行加载集群。

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/01_L2功能边界.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/02_pi05源码3.5层微元拆解.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/03_ACT微元设计与协作.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`

## 5. Pi0.5 源码盘点

| 源码位置 | 关键符号 | 行为 | 是否借鉴 |
|---|---|---|---|
| `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/config/schema.py` | `load_experiment_config(path: Path) -> ExperimentConfig` | 加载 YAML 文件，要求根节点为 Mapping，调用 `ExperimentConfig.from_mapping(raw, base_dir=config_path.parent)` 构造 frozen dataclass | 借鉴加载入口与 Mapping 校验思路 |
| 同上 | `ExperimentConfig` | frozen dataclass，含 lora/data/model/training/logging/raw 字段，data 与 model 内嵌 state_dim=26/action_dim=14 | 借鉴结构形态，禁止照搬 26/14 |
| 同上 | `ConfigError(ValueError)` | 配置错误异常类 | 借鉴异常类型设计 |
| `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/runtime/bundle.py` | `EXPERIMENT_CONFIG_NAME = "experiment_config.yaml"` | experiment_config 文件名常量 | 直接借鉴文件名常量 |
| 同上 | manifest payload `experiment_config_path` | manifest 中记录 experiment_config 路径 | 借鉴路径来源，但本 L3 不解析 manifest |

### 必须保留的源码启发

- `EXPERIMENT_CONFIG_NAME = "experiment_config.yaml"` 作为标准文件名常量，本 L3 复用该文件名约定。
- 加载入口接受 `Path` 参数，读取 YAML 后校验根节点为 Mapping（dict），否则抛配置异常。
- 暴露的结构应包含原始字段（raw），以便上层交叉校验读取任意字段而不被裁剪。

### 禁止照搬的源码行为

- 禁止照搬 Pi0.5 `ExperimentConfig` 中硬编码的 `state_dim=26`/`action_dim=14`/`image_size=224`/`max_action_dim=14` 默认值。ACT 为 16D 契约，维度由 experiment_config 原值决定，repo 层不注入任何默认维度。
- 禁止照搬 Pi0.5 在 dataclass 构造时对字段的强类型转换或归一化（如把缺失维度补成 26/14）。本 L3 缺字段应抛配置异常，不得补默认值。
- 禁止照搬 Pi0.5 `from_mapping` 内嵌的校验逻辑（如 image_size 必须为 224）。repo 层不做维度业务校验。

### 已知风险

- experiment_config.yaml 可能存在字段缺失或类型错误。本 L3 必须区分“文件不可读/不是合法 YAML/根节点非 Mapping”（抛配置异常）与“字段缺失或维度异常”（原值保留，交由 config 层校验）。
- 不同 bundle 的 experiment_config 字段集可能存在差异，加载器不得对未知字段做丢弃或报错，必须原样保留。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 实现 `load_experiment_config(path: Path)` 加载函数，读取 YAML 文件并返回 dict 或轻量 dataclass（保留 raw）。
- 校验文件可读、内容为合法 YAML、根节点为 Mapping。
- 原样保留所有字段，包括 `state_dim`/`action_dim`/`image_size`/`max_action_dim` 等维度字段，不覆写、不归一化。
- 定义 `ExperimentConfigLoadError(ValueError)` 异常类，覆盖文件不存在、YAML 解析失败、根节点非 Mapping 三类错误。
- 提供 `EXPERIMENT_CONFIG_NAME` 常量。
- 编写 repo 层单元测试覆盖正常加载、文件缺失、非法 YAML、根节点非 Mapping、维度字段原值保留等场景。

### 本次不做

- 不做维度业务校验（不判断 state_dim 是否等于 16、不判断 action_dim 是否等于契约值）。
- 不做字段类型强转或归一化。
- 不做 config 层交叉校验（那是 L2 Gate S4 的职责）。
- 不加载 normalizers、不解析 manifest、不检查 bundle 目录结构（分别属于 deploy_005、deploy_004、deploy_007）。
- 不加载模型权重。

### 明确禁止修改

- 禁止修改 config/service/runtime/ui 层任何文件。
- 禁止修改 deploy_004/005/007 的产物文件。
- 禁止在 repo 层 import config/service/runtime/ui 层模块。
- 禁止在加载器内引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing 相关逻辑。
- 禁止覆写或补默认维度值。

### 函数 / class 策略

- `EXPERIMENT_CONFIG_NAME: str = "experiment_config.yaml"` 模块级常量。
- `class ExperimentConfigLoadError(ValueError)` 配置加载异常。
- `def load_experiment_config(path: Path) -> dict` 主加载函数，返回原始 mapping（推荐返回 dict 以最大程度保留原值；若用 dataclass 必须额外保留 raw 字段）。返回类型在文件内明确标注。
- 可选 `def load_experiment_config_mapping(path: Path) -> dict` 别名，供上层显式取 mapping。

## 7. 六层产物落点

| 层 | 是否产出 | 落点 |
|---|---|---|
| repo | 是 | `src/model_deploy/act/repo/experiment_config_loader.py` |
| tests | 是 | `src/model_deploy/act/tests/repo/test_experiment_config_loader.py` |
| config | 否 | — |
| service | 否 | — |
| runtime | 否 | — |
| ui | 否 | — |

### 对应六层设计文档

repo 层设计规范见 `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`。该文档定义 repo 层依赖方向（仅向内，禁止向上引用）、产物命名规范、测试组织规范，本 L3 必须严格遵守。

## 8. 文件内 3.5 层功能微元

| 微元 | 职责 | 输入 | 输出 | 备注 |
|---|---|---|---|---|
| EXPERIMENT_CONFIG_NAME 常量 | 固定 experiment_config 文件名 | — | str | 借鉴 Pi0.5 |
| 文件可读检查 | 确认 path 存在且为文件 | Path | bool 或抛异常 | 文件缺失抛 ExperimentConfigLoadError |
| YAML 解析 | 把文件内容解析为 Python 对象 | Path | dict | 非法 YAML 抛 ExperimentConfigLoadError |
| 根节点 Mapping 校验 | 确认解析结果为 dict | object | dict | 非 Mapping 抛 ExperimentConfigLoadError |
| 原值保留 | 原样返回所有字段 | dict | dict | 不裁剪不覆写 |
| load_experiment_config 入口 | 编排上述微元 | Path | dict | 对外主接口 |

## 9. 实施步骤

1. 切换到开发分支 `feat/model_deploy/l2-01-external-contract`。
2. 创建源文件 `src/model_deploy/act/repo/experiment_config_loader.py`。
3. 定义 `EXPERIMENT_CONFIG_NAME = "experiment_config.yaml"` 常量。
4. 定义 `ExperimentConfigLoadError(ValueError)` 异常类，docstring 说明三类触发场景。
5. 实现 `load_experiment_config(path: Path) -> dict`：文件不存在抛异常 → 读取文件 → YAML 安全加载（使用 `yaml.safe_load`）→ 非法 YAML 抛异常 → 根节点非 Mapping 抛异常 → 返回原始 dict。
6. 不对返回 dict 做任何字段裁剪、类型转换、维度覆写。
7. 创建测试文件 `src/model_deploy/act/tests/repo/test_experiment_config_loader.py`。
8. 编写测试用例：(a) 正常 YAML 加载返回 dict 且维度字段原值保留；(b) 文件不存在抛 ExperimentConfigLoadError；(c) 非法 YAML 抛 ExperimentConfigLoadError；(d) 根节点为列表/标量抛 ExperimentConfigLoadError；(e) 字段缺失时不补默认值（原 dict 不含该键）；(f) 含 experiment_config 中的 state_dim/action_dim 原值且不被改写。
9. 运行 `pytest src/model_deploy/act/tests/repo/test_experiment_config_loader.py` 全绿。
10. 运行 ruff/mypy（若仓库已配置）确保无 lint/类型错误。
11. 确认未修改 conflict_scope 之外任何文件。
12. 在 `acceptance_feedback_dir` 写入验收日志。

## 10. 允许修改

> [!warning] 产物落点约束
> 本 L3 仅允许新增/修改 conflict_scope 内的两个文件，不得触碰任何其他文件。

| 文件 | 操作 | 说明 |
|---|---|---|
| `src/model_deploy/act/repo/experiment_config_loader.py` | 新增 | repo 层加载器源码 |
| `src/model_deploy/act/tests/repo/test_experiment_config_loader.py` | 新增 | repo 层单元测试 |

允许在源文件内：定义常量、异常类、加载函数、docstring、类型注解。允许在测试文件内：使用 `pytest`、`tmp_path` fixture 构造临时 YAML 文件。

## 11. 禁止修改

- 禁止修改 config/service/runtime/ui 层任何文件。
- 禁止修改 `src/model_deploy/act/repo/` 下非本 L3 产物文件（如 deploy_004 的 manifest 解析器、deploy_005 的 normalizers 解析器、deploy_007 的 bundle 读取器）。
- 禁止修改 Pi0.5 只读参考源码（`DOCS/03_工程/阶段四：模型部署/pi05_old/...`）。
- 禁止修改任何 L2 设计文档、验收机制文档。
- 禁止修改仓库根配置文件（pyproject.toml/setup.cfg 等）除非确认是测试发现的必要修复且属于本 L3 边界。
- 禁止引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing 相关代码或依赖。

## 12. 验证方式

### 自动化验收命令

```bash
# 切换到仓库根
cd /home/hit/ROS/worktrees/l2-01

# 运行本 L3 单元测试
pytest src/model_deploy/act/tests/repo/test_experiment_config_loader.py -v

# 确认 conflict_scope 之外无改动
git status --porcelain | grep -v \
  "src/model_deploy/act/repo/experiment_config_loader.py\|src/model_deploy/act/tests/repo/test_experiment_config_loader.py" \
  && echo "WARN: 存在 conflict_scope 之外改动" || echo "OK: 仅 conflict_scope 内改动"

# 确认 repo 层未向上引用
grep -rn "from model_deploy.act.config\|from model_deploy.act.service\|from model_deploy.act.runtime\|from model_deploy.act.ui" \
  src/model_deploy/act/repo/experiment_config_loader.py \
  && echo "FAIL: repo 层向上引用" || echo "OK: repo 层未向上引用"

# 确认未引入禁止逻辑
grep -rn "blend_steps\|smoothstep\|cross_chunk\|rtc_alignment\|action_smoothing" \
  src/model_deploy/act/repo/experiment_config_loader.py \
  && echo "FAIL: 引入禁止逻辑" || echo "OK: 未引入禁止逻辑"

# 确认未硬编码 Pi0.5 维度默认值
grep -rn "state_dim.*=.*26\|action_dim.*=.*14\|image_size.*=.*224\|max_action_dim.*=.*14" \
  src/model_deploy/act/repo/experiment_config_loader.py \
  && echo "FAIL: 硬编码 Pi0.5 维度" || echo "OK: 未硬编码维度"
```

### 分层验证

| 层 | 验证项 | 命令/方式 | 期望 |
|---|---|---|---|
| repo | 加载正常 YAML 返回 dict | pytest 正常用例 | dict 包含原字段 |
| repo | 维度原值保留 | pytest 维度保留用例 | state_dim/action_dim 原值不变 |
| repo | 文件缺失抛异常 | pytest 缺失用例 | ExperimentConfigLoadError |
| repo | 非法 YAML 抛异常 | pytest 非法 YAML 用例 | ExperimentConfigLoadError |
| repo | 根节点非 Mapping 抛异常 | pytest 非 Mapping 用例 | ExperimentConfigLoadError |
| tests | 全部用例通过 | pytest -v | 全绿 |
| config | 不涉及 | — | — |
| service | 不涉及 | — | — |
| runtime | 不涉及 | — | — |
| ui | 不涉及 | — | — |

### 真机风险控制

本 L3 真机风险为 none：仅文件读取与 YAML 解析，不涉及硬件、不涉及模型推理、不涉及通信。无需真机回归。

### 验收证据落点

验收日志写入 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_006_验收日志.md`（或对应 round 文件）。日志记录：测试输出、conflict_scope 检查结果、repo 层依赖方向检查结果、禁止逻辑检查结果、维度硬编码检查结果。

### L2 Gate 贡献

| L2 Gate 场景 | 本 L3 贡献 | 说明 |
|---|---|---|
| S4 normalizer 维度不一致失败 | 提供输入 | 本 L3 加载 experiment_config 的 state_dim/action_dim 原值，供 config 层将 experiment_config 维度与 normalizers 维度、16D 契约交叉校验。本 L3 只提供数据，不做校验判断。 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/01_L2功能边界.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/03_ACT微元设计与协作.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`

### 必读代码

- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/config/schema.py`（只读参考：`load_experiment_config`、`ExperimentConfig`、`ConfigError`）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/runtime/bundle.py`（只读参考：`EXPERIMENT_CONFIG_NAME`）

### 必读约束文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`

### 相关历史任务

- deploy_001/002/003（本 L3 的 depends_on，提供 repo 层基础设施与测试基座）
- deploy_004（manifest 解析，与本 L3 并行，manifest 中记录 experiment_config_path）
- deploy_005（normalizers 解析，与本 L3 并行，S4 交叉校验的另一输入）
- deploy_007（bundle 目录检查，与本 L3 并行，检查 experiment_config.yaml 是否存在）

## 14. 执行要求

```
身份校验：你是 deploy_006 的执行 Agent。开始前确认：
- 当前分支为 feat/model_deploy/l2-01-external-contract
- depends_on（deploy_001/002/003）已完成
- conflict_scope 内文件未被其他并行 L3 占用
若任一条件不满足，停止并向调度层报告。
```

dispatch 校验：

- 确认 `dispatch_status: ready`，否则不执行。
- 确认 `acceptance_round_limit: 3` 未超限。
- 确认 `local_acceptance_required: true`，必须本地验收通过。
- 确认 `parallel_group: l2-01-external-contract-p2`，与同组 deploy_004/005/007 可并行。

全文检查：

- 本文件 17 节是否完整阅读。
- 第 10/11 节允许/禁止修改边界是否理解。
- 第 5 节 Pi0.5 借鉴与禁止照搬清单是否理解。
- 第 12 节验证命令是否可执行。

测试优先：

- 先写测试用例（红），再写加载器实现（绿），再重构。
- 测试必须覆盖正常加载、文件缺失、非法 YAML、根节点非 Mapping、维度原值保留五类场景。

## 15. 成功标准

- [ ] `src/model_deploy/act/repo/experiment_config_loader.py` 已创建，含 `EXPERIMENT_CONFIG_NAME` 常量、`ExperimentConfigLoadError` 异常类、`load_experiment_config(path: Path) -> dict` 函数。
- [ ] 加载函数原样返回 dict，不裁剪、不覆写、不补默认值。
- [ ] 加载函数不硬编码 Pi0.5 的 26/14/224 维度默认值。
- [ ] 文件缺失抛 `ExperimentConfigLoadError`。
- [ ] 非法 YAML 抛 `ExperimentConfigLoadError`。
- [ ] 根节点非 Mapping 抛 `ExperimentConfigLoadError`。
- [ ] `src/model_deploy/act/tests/repo/test_experiment_config_loader.py` 已创建，覆盖上述全部场景。
- [ ] `pytest src/model_deploy/act/tests/repo/test_experiment_config_loader.py -v` 全绿。
- [ ] 未修改 conflict_scope 之外任何文件。
- [ ] repo 层未 import config/service/runtime/ui 层。
- [ ] 未引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing 逻辑。
- [ ] 验收日志已写入 `acceptance_feedback_dir`。

## 16. 回滚方式

```text
回滚步骤：
1. git checkout -- src/model_deploy/act/repo/experiment_config_loader.py
2. git checkout -- src/model_deploy/act/tests/repo/test_experiment_config_loader.py
3. 若文件为新增（未提交），直接 rm 删除两个文件
4. 确认 git status 干净（仅可能保留分支切换前状态）
5. 在验收日志记录回滚原因与轮次
回滚触发条件：
- 单元测试连续 2 轮无法通过
- 发现设计偏差需回到 L2 重新拆解
- conflict_scope 被其他 L3 占用且无法合并
```

## 17. 完成后交接

实施与自测完成后，执行以下交接动作：

1. 在 `acceptance_feedback_dir`（`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/`）写入 `deploy_006_验收日志.md`，内容包含：测试输出摘要、各项检查结果、L2 Gate S4 贡献说明、遗留问题（无则注明）。
2. 更新本 L3 调度状态为 `done`（由调度层确认），等待 L2 整体验收。
3. 在交接说明中注明：本 L3 产物为 experiment_config 加载器，输出原始 dict，供 config 层交叉校验消费；未做维度业务校验；与 deploy_004/005/007 无文件冲突。
4. 若验收未通过，按第 16 节回滚并在日志记录失败轮次与原因，等待下一轮 dispatch。

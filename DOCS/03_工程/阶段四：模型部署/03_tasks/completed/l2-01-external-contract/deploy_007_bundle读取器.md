# L3 微元改造任务：deploy_007 bundle 读取器

## 1. 任务定位

本任务属于阶段四（模型部署），L1 ACT 模型部署线，L2 `l2-01-external-contract`（外部参数加载与契约校验闭环），L3 编号 `deploy_007`，改造类型 `source-adaptation`，验收模式 `direct-local`，真机风险 `none`，开发分支 `feat/model_deploy/l2-01-external-contract`，集成分支 `model_deploy`。

产物落点遵循六层架构规范：repo 层产物落在 `src/model_deploy/act/repo/`，对应测试落在 `src/model_deploy/act/tests/repo/`。repo 层不得向上引用 config/service/runtime/ui 层，不得执行维度业务校验。

> [!warning] 产物落点约束
> 本 L3 仅产出 repo 层源码与 repo 层单元测试两个文件。任何落在 config/service/runtime/ui 层的产物均视为越界。bundle 读取器只做目录结构存在性检查与 checkpoint 路径解析，不加载模型权重、不解析 manifest 内容（manifest 解析属 deploy_004）。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_007
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_007_bundle读取器.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_007_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 2
  parallel_group: l2-01-external-contract-p2
  depends_on: [deploy_001, deploy_002, deploy_003]
  must_run_after: []
  can_run_parallel_with: [deploy_004, deploy_005, deploy_006]
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/repo/bundle_reader.py
      - src/model_deploy/act/tests/repo/test_bundle_reader.py
    modules:
      - model_deploy.act.repo.bundle_reader
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
bundle 目录检查、checkpoint 路径解析。
检查 bundle 目录结构完整性（manifest.json, normalizers.json, experiment_config.yaml, adapter/ 目录, checkpoint 路径），不加载模型权重。
```

本 L3 是 L2 `l2-01-external-contract` 外部契约校验闭环的入口侧检查器：在加载任何内容之前，先确认 bundle 目录结构完整、所需文件齐全、checkpoint 路径可解析。它是 L2 Gate S3（bundle 缺文件失败）的直接实现载体。本 L3 只做“结构存在性”检查，不做“内容正确性”解析。

## 4. 所属 L2 边界与设计来源

### L2 负责

L2 `l2-01-external-contract` 负责外部参数（bundle 文件、experiment_config、normalizers）的加载与契约校验闭环：加载 bundle 目录结构、解析 experiment_config、解析 normalizers、并对加载得到的维度字段进行交叉校验，确保 bundle 内部各来源维度一致并与 16D 契约对齐。

### L2 不负责

L2 不负责模型权重加载、不负责推理执行、不负责真机通信、不负责 action 平滑与跨块对齐。bundle 内 manifest/normalizers/experiment_config 的内容解析分别由 deploy_004/005/006 负责，本 L3 只做文件存在性检查。

### 本 L3 在 L2 中的位置

本 L3 是 L2 加载链路的“前置守门”节点：在 deploy_004（manifest 解析）、deploy_005（normalizers 解析）、deploy_006（experiment_config 加载）之前，先确认 bundle 目录结构完整。若本 L3 报告缺文件，L2 Gate S3 直接失败，无需进入后续解析。本 L3 与 deploy_004/005/006 构成 L2 的并行加载集群，但逻辑上是最先执行的检查。

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
| `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/runtime/bundle.py` | `resolve_bundle_adapter_dir(bundle_dir) -> Path` | 返回 `bundle_dir/adapter`，若不存在抛 FileNotFoundError | 直接借鉴：adapter 目录解析 |
| 同上 | `BUNDLE_SCHEMA_VERSION = 1` | bundle schema 版本常量 | 借鉴：作为 manifest 检查的预期版本参考 |
| 同上 | manifest payload 结构 | 含 artifacts{adapter_dir, normalizers_path, experiment_config_path}、model{pretrained_path} | 借鉴：用于确定需检查的文件清单 |
| 同上 | 文件存在性检查模式 | 对 bundle_dir 下关键文件做 Path.exists() 检查 | 借鉴：检查思路 |
| 同上 | `EXPERIMENT_CONFIG_NAME = "experiment_config.yaml"` | experiment_config 文件名常量 | 借鉴：文件名约定 |

### 必须保留的源码启发

- `resolve_bundle_adapter_dir(bundle_dir) -> Path` 的解析约定：adapter 目录位于 `bundle_dir/adapter`，不存在时抛 FileNotFoundError。本 L3 复用该解析路径与异常约定。
- bundle 关键文件清单：`manifest.json`、`normalizers.json`、`experiment_config.yaml`、`adapter/` 目录、checkpoint 路径（来自 manifest 的 `model.pretrained_path` 或目录结构）。
- `BUNDLE_SCHEMA_VERSION = 1` 作为预期版本参考（本 L3 不解析 manifest 内容，但可记录预期版本供 deploy_004 校验）。

### 禁止照搬的源码行为

- 禁止照搬 Pi0.5 manifest 内容解析逻辑（解析 manifest JSON payload 属于 deploy_004 职责）。本 L3 的 `resolve_checkpoint_path` 可读取 manifest 中 checkpoint 路径字段以定位 checkpoint，但不得解析完整 manifest payload。
- 禁止照搬 Pi0.5 中加载模型权重、加载 normalizers 内容、加载 experiment_config 内容的逻辑。本 L3 只检查存在性。
- 禁止照搬 Pi0.5 的 26D/14D 维度假设。本 L3 不涉及维度。

### 已知风险

- bundle 目录可能存在符号链接或权限问题，导致 `Path.exists()` 返回 False 但文件实际可访问。检查应使用 `is_file()`/`is_dir()` 而非仅 `exists()`，并在缺文件时返回清晰的缺失文件名列表。
- checkpoint 路径可能在 manifest 中以相对路径记录，也可能直接放在 bundle 目录下。`resolve_checkpoint_path` 需处理两种来源，若均不可解析则抛异常。
- manifest.json 可能不存在或不可读，此时 `resolve_checkpoint_path` 应回退到目录结构扫描，若仍无 checkpoint 则抛异常。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 实现 `check_bundle_files(bundle_dir) -> list[str]`：检查 bundle 目录结构完整性，返回缺失文件/目录的相对路径列表（空列表表示完整）。
- 实现 `resolve_checkpoint_path(bundle_dir) -> Path`：从 manifest 或目录结构解析 checkpoint 路径。
- 实现 `resolve_bundle_adapter_dir(bundle_dir) -> Path`：返回 `bundle_dir/adapter`，不存在抛 FileNotFoundError（借鉴 Pi0.5）。
- 定义 `BUNDLE_SCHEMA_VERSION = 1` 常量（记录预期版本，不解析 manifest）。
- 检查的文件清单：`manifest.json`、`normalizers.json`、`experiment_config.yaml`、`adapter/` 目录、checkpoint 路径。
- 定义 `BundleStructureError(ValueError)` 异常类，覆盖目录不存在、checkpoint 不可解析等错误。
- 编写 repo 层单元测试覆盖完整目录、缺单个文件、缺多个文件、adapter 缺失、checkpoint 路径解析等场景。

### 本次不做

- 不加载模型权重（不 import torch、不加载 .pt/.safetensors）。
- 不解析 manifest 内容（manifest JSON payload 解析属 deploy_004）。`resolve_checkpoint_path` 仅读取 checkpoint 路径字段，不解析完整 payload。
- 不解析 normalizers 内容（属 deploy_005）。
- 不加载 experiment_config 内容（属 deploy_006）。
- 不做维度业务校验。
- 不做 config 层交叉校验（那是 L2 Gate S4 职责）。

### 明确禁止修改

- 禁止修改 config/service/runtime/ui 层任何文件。
- 禁止修改 deploy_004/005/006 的产物文件。
- 禁止在 repo 层 import config/service/runtime/ui 层模块。
- 禁止加载模型权重（禁止 import torch 加载权重、禁止读取权重文件内容）。
- 禁止解析完整 manifest payload。
- 禁止引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing 相关逻辑。
- 禁止硬编码 Pi0.5 的 26/14/224 维度。

### 函数 / class 策略

- `BUNDLE_SCHEMA_VERSION: int = 1` 模块级常量。
- `BUNDLE_REQUIRED_FILES` 模块级常量：需检查的文件/目录名清单。
- `class BundleStructureError(ValueError)` 结构异常。
- `def check_bundle_files(bundle_dir) -> list[str]`：返回缺失项相对路径列表，空列表表示完整。
- `def resolve_checkpoint_path(bundle_dir) -> Path`：解析 checkpoint 路径，不可解析抛 BundleStructureError。
- `def resolve_bundle_adapter_dir(bundle_dir) -> Path`：返回 adapter 目录 Path，不存在抛 FileNotFoundError。

## 7. 六层产物落点

| 层 | 是否产出 | 落点 |
|---|---|---|
| repo | 是 | `src/model_deploy/act/repo/bundle_reader.py` |
| tests | 是 | `src/model_deploy/act/tests/repo/test_bundle_reader.py` |
| config | 否 | — |
| service | 否 | — |
| runtime | 否 | — |
| ui | 否 | — |

### 对应六层设计文档

repo 层设计规范见 `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`。该文档定义 repo 层依赖方向（仅向内，禁止向上引用）、产物命名规范、测试组织规范，本 L3 必须严格遵守。

## 8. 文件内 3.5 层功能微元

| 微元 | 职责 | 输入 | 输出 | 备注 |
|---|---|---|---|---|
| BUNDLE_SCHEMA_VERSION 常量 | 记录预期 manifest schema 版本 | — | int | 借鉴 Pi0.5，本 L3 不校验 |
| BUNDLE_REQUIRED_FILES 常量 | 固定需检查的文件清单 | — | list[str] | manifest/normalizers/experiment_config/adapter |
| bundle_dir 存在性检查 | 确认 bundle 目录存在 | Path | bool 或抛异常 | 目录不存在抛 BundleStructureError |
| 单文件存在性检查 | 检查单个文件/目录是否存在 | Path | bool | 用 is_file/is_dir |
| check_bundle_files 入口 | 汇总缺失项 | Path | list[str] | 空列表=完整 |
| resolve_bundle_adapter_dir | 解析 adapter 目录 | Path | Path | 不存在抛 FileNotFoundError |
| checkpoint 路径解析（manifest 来源） | 从 manifest 读取 checkpoint 路径字段 | Path | Path 或 None | 只读路径字段，不解析 payload |
| checkpoint 路径解析（目录扫描回退） | 目录结构扫描定位 checkpoint | Path | Path 或 None | 回退策略 |
| resolve_checkpoint_path 入口 | 编排两种来源解析 checkpoint | Path | Path | 不可解析抛 BundleStructureError |

## 9. 实施步骤

1. 切换到开发分支 `feat/model_deploy/l2-01-external-contract`。
2. 创建源文件 `src/model_deploy/act/repo/bundle_reader.py`。
3. 定义 `BUNDLE_SCHEMA_VERSION = 1` 常量。
4. 定义 `BUNDLE_REQUIRED_FILES` 常量，包含 `manifest.json`、`normalizers.json`、`experiment_config.yaml`、`adapter`（目录）。
5. 定义 `BundleStructureError(ValueError)` 异常类。
6. 实现 `resolve_bundle_adapter_dir(bundle_dir) -> Path`：返回 `bundle_dir/adapter`，不存在抛 FileNotFoundError。
7. 实现 `check_bundle_files(bundle_dir) -> list[str]`：先确认 bundle_dir 存在（不存在抛 BundleStructureError），再逐项检查 BUNDLE_REQUIRED_FILES，用 `is_file()`/`is_dir()` 判断，收集缺失项相对路径，返回列表。
8. 实现 `resolve_checkpoint_path(bundle_dir) -> Path`：(a) 尝试从 `manifest.json` 读取 checkpoint 路径字段（如 `model.pretrained_path` 或 `artifacts.checkpoint_path`，按实际 manifest 结构），只读取该字段不解析完整 payload；(b) 若 manifest 不可读或字段缺失，回退到目录扫描（查找 `.pt`/`.safetensors`/`checkpoint` 等约定文件）；(c) 两路径均不可解析抛 BundleStructureError。
9. 不加载任何文件内容（权重/normalizers/experiment_config payload）。
10. 创建测试文件 `src/model_deploy/act/tests/repo/test_bundle_reader.py`。
11. 编写测试用例：(a) 完整 bundle 目录返回空缺失列表；(b) 缺 manifest.json 返回含 manifest.json 的列表；(c) 缺 normalizers.json；(d) 缺 experiment_config.yaml；(e) 缺 adapter 目录；(f) 缺多个文件；(g) bundle_dir 不存在抛 BundleStructureError；(h) resolve_bundle_adapter_dir 存在返回 Path、不存在抛 FileNotFoundError；(i) resolve_checkpoint_path 从 manifest 解析成功；(j) resolve_checkpoint_path 目录扫描回退成功；(k) resolve_checkpoint_path 不可解析抛 BundleStructureError。
12. 运行 `pytest src/model_deploy/act/tests/repo/test_bundle_reader.py` 全绿。
13. 运行 ruff/mypy（若仓库已配置）确保无 lint/类型错误。
14. 确认未修改 conflict_scope 之外任何文件。
15. 在 `acceptance_feedback_dir` 写入验收日志。

## 10. 允许修改

> [!warning] 产物落点约束
> 本 L3 仅允许新增/修改 conflict_scope 内的两个文件，不得触碰任何其他文件。

| 文件 | 操作 | 说明 |
|---|---|---|
| `src/model_deploy/act/repo/bundle_reader.py` | 新增 | repo 层 bundle 读取器源码 |
| `src/model_deploy/act/tests/repo/test_bundle_reader.py` | 新增 | repo 层单元测试 |

允许在源文件内：定义常量、异常类、检查与解析函数、docstring、类型注解。允许在测试文件内：使用 `pytest`、`tmp_path` fixture 构造临时 bundle 目录结构。`resolve_checkpoint_path` 允许使用标准库 `json` 读取 manifest.json 中的 checkpoint 路径字段，但不得解析完整 payload、不得加载权重。

## 11. 禁止修改

- 禁止修改 config/service/runtime/ui 层任何文件。
- 禁止修改 `src/model_deploy/act/repo/` 下非本 L3 产物文件（如 deploy_004 的 manifest 解析器、deploy_005 的 normalizers 解析器、deploy_006 的 experiment_config 加载器）。
- 禁止修改 Pi0.5 只读参考源码（`DOCS/03_工程/阶段四：模型部署/pi05_old/...`）。
- 禁止修改任何 L2 设计文档、验收机制文档。
- 禁止修改仓库根配置文件（pyproject.toml/setup.cfg 等）除非确认是测试发现的必要修复且属于本 L3 边界。
- 禁止 import torch 或任何模型权重加载库。
- 禁止解析完整 manifest payload（只读 checkpoint 路径字段）。
- 禁止引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing 相关代码或依赖。

## 12. 验证方式

### 自动化验收命令

```bash
# 切换到仓库根
cd /home/hit/ROS/worktrees/l2-01

# 运行本 L3 单元测试
pytest src/model_deploy/act/tests/repo/test_bundle_reader.py -v

# 确认 conflict_scope 之外无改动
git status --porcelain | grep -v \
  "src/model_deploy/act/repo/bundle_reader.py\|src/model_deploy/act/tests/repo/test_bundle_reader.py" \
  && echo "WARN: 存在 conflict_scope 之外改动" || echo "OK: 仅 conflict_scope 内改动"

# 确认 repo 层未向上引用
grep -rn "from model_deploy.act.config\|from model_deploy.act.service\|from model_deploy.act.runtime\|from model_deploy.act.ui" \
  src/model_deploy/act/repo/bundle_reader.py \
  && echo "FAIL: repo 层向上引用" || echo "OK: repo 层未向上引用"

# 确认未引入禁止逻辑
grep -rn "blend_steps\|smoothstep\|cross_chunk\|rtc_alignment\|action_smoothing" \
  src/model_deploy/act/repo/bundle_reader.py \
  && echo "FAIL: 引入禁止逻辑" || echo "OK: 未引入禁止逻辑"

# 确认未加载模型权重
grep -rn "import torch\|torch.load\|safetensors" \
  src/model_deploy/act/repo/bundle_reader.py \
  && echo "FAIL: 加载模型权重" || echo "OK: 未加载模型权重"

# 确认未硬编码 Pi0.5 维度
grep -rn "state_dim.*=.*26\|action_dim.*=.*14\|image_size.*=.*224\|max_action_dim.*=.*14" \
  src/model_deploy/act/repo/bundle_reader.py \
  && echo "FAIL: 硬编码 Pi0.5 维度" || echo "OK: 未硬编码维度"

# 确认关键符号存在
grep -n "BUNDLE_SCHEMA_VERSION" src/model_deploy/act/repo/bundle_reader.py
grep -n "def check_bundle_files" src/model_deploy/act/repo/bundle_reader.py
grep -n "def resolve_checkpoint_path" src/model_deploy/act/repo/bundle_reader.py
grep -n "def resolve_bundle_adapter_dir" src/model_deploy/act/repo/bundle_reader.py
# 期望：四处均有匹配
```

### 分层验证

| 层 | 验证项 | 命令/方式 | 期望 |
|---|---|---|---|
| repo | 完整 bundle 返回空缺失列表 | pytest 完整目录用例 | [] |
| repo | 缺单个文件返回含该文件列表 | pytest 缺文件用例 | 列表含缺失项 |
| repo | 缺多个文件返回多项列表 | pytest 缺多文件用例 | 列表含全部缺失项 |
| repo | bundle_dir 不存在抛异常 | pytest 不存在用例 | BundleStructureError |
| repo | adapter 目录解析 | pytest adapter 用例 | 存在返回 Path/不存在抛 FileNotFoundError |
| repo | checkpoint 路径解析（manifest） | pytest manifest 来源用例 | 返回 Path |
| repo | checkpoint 路径解析（回退） | pytest 目录扫描用例 | 返回 Path |
| repo | checkpoint 不可解析抛异常 | pytest 不可解析用例 | BundleStructureError |
| tests | 全部用例通过 | pytest -v | 全绿 |
| config | 不涉及 | — | — |
| service | 不涉及 | — | — |
| runtime | 不涉及 | — | — |
| ui | 不涉及 | — | — |

### 真机风险控制

本 L3 真机风险为 none：仅文件/目录存在性检查与路径解析，不涉及硬件、不涉及模型推理、不涉及通信。无需真机回归。

### 验收证据落点

验收日志写入 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_007_验收日志.md`（或对应 round 文件）。日志记录：测试输出、conflict_scope 检查结果、repo 层依赖方向检查结果、禁止逻辑检查结果、权重加载检查结果、维度硬编码检查结果。

### L2 Gate 贡献

| L2 Gate 场景 | 本 L3 贡献 | 说明 |
|---|---|---|
| S3 bundle 缺文件失败 | 直接实现 | 本 L3 的 `check_bundle_files` 是 S3 的直接实现载体。返回非空缺失列表即触发 S3 失败，L2 无需进入后续解析。本 L3 是 S3 的唯一数据来源。 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/01_L2功能边界.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/03_ACT微元设计与协作.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`

### 必读代码

- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/runtime/bundle.py`（只读参考：`resolve_bundle_adapter_dir`、`BUNDLE_SCHEMA_VERSION`、文件存在性检查模式、`EXPERIMENT_CONFIG_NAME`）

### 必读约束文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`

### 相关历史任务

- deploy_001/002/003（本 L3 的 depends_on，提供 repo 层基础设施与测试基座）
- deploy_004（manifest 解析，与本 L3 并行；本 L3 的 checkpoint 路径解析可读取 manifest 中路径字段但不解析完整 payload，与 deploy_004 职责不重叠）
- deploy_005（normalizers 解析，与本 L3 并行；本 L3 只检查 normalizers.json 存在性，不解析内容）
- deploy_006（experiment_config 加载器，与本 L3 并行；本 L3 只检查 experiment_config.yaml 存在性，不加载内容）

## 14. 执行要求

```
身份校验：你是 deploy_007 的执行 Agent。开始前确认：
- 当前分支为 feat/model_deploy/l2-01-external-contract
- depends_on（deploy_001/002/003）已完成
- conflict_scope 内文件未被其他并行 L3 占用
若任一条件不满足，停止并向调度层报告。
```

dispatch 校验：

- 确认 `dispatch_status: ready`，否则不执行。
- 确认 `acceptance_round_limit: 3` 未超限。
- 确认 `local_acceptance_required: true`，必须本地验收通过。
- 确认 `parallel_group: l2-01-external-contract-p2`，与同组 deploy_004/005/006 可并行。

全文检查：

- 本文件 17 节是否完整阅读。
- 第 10/11 节允许/禁止修改边界是否理解。
- 第 5 节 Pi0.5 借鉴与禁止照搬清单是否理解。
- 第 12 节验证命令是否可执行。
- 与 deploy_004 的职责边界是否清晰（本 L3 只读 checkpoint 路径字段，不解析 manifest payload）。

测试优先：

- 先写测试用例（红），再写读取器实现（绿），再重构。
- 测试必须覆盖完整目录、缺单文件、缺多文件、adapter 缺失、bundle_dir 不存在、checkpoint manifest 解析、checkpoint 目录扫描回退、checkpoint 不可解析八类场景。

## 15. 成功标准

- [ ] `src/model_deploy/act/repo/bundle_reader.py` 已创建，含 `BUNDLE_SCHEMA_VERSION` 常量、`BundleStructureError` 异常类、`check_bundle_files`、`resolve_checkpoint_path`、`resolve_bundle_adapter_dir` 函数。
- [ ] `check_bundle_files(bundle_dir) -> list[str]` 返回缺失项相对路径列表，空列表表示完整。
- [ ] `resolve_checkpoint_path(bundle_dir) -> Path` 支持 manifest 来源与目录扫描回退两种策略。
- [ ] `resolve_bundle_adapter_dir(bundle_dir) -> Path` 返回 `bundle_dir/adapter`，不存在抛 FileNotFoundError。
- [ ] 未加载模型权重（未 import torch 加载权重）。
- [ ] 未解析完整 manifest payload（只读 checkpoint 路径字段）。
- [ ] 未硬编码 Pi0.5 的 26/14/224 维度默认值。
- [ ] `src/model_deploy/act/tests/repo/test_bundle_reader.py` 已创建，覆盖上述全部场景。
- [ ] `pytest src/model_deploy/act/tests/repo/test_bundle_reader.py -v` 全绿。
- [ ] 未修改 conflict_scope 之外任何文件。
- [ ] repo 层未 import config/service/runtime/ui 层。
- [ ] 未引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing 逻辑。

## 16. 回滚方式

```text
回滚步骤：
1. git checkout -- src/model_deploy/act/repo/bundle_reader.py
2. git checkout -- src/model_deploy/act/tests/repo/test_bundle_reader.py
3. 若文件为新增（未提交），直接 rm 删除两个文件
4. 确认 git status 干净（仅可能保留分支切换前状态）
5. 在验收日志记录回滚原因与轮次
回滚触发条件：
- 单元测试连续 2 轮无法通过
- 发现设计偏差需回到 L2 重新拆解
- conflict_scope 被其他 L3 占用且无法合并
- 与 deploy_004 的 manifest 职责边界发生冲突且无法合并
```

## 17. 完成后交接

实施与自测完成后，执行以下交接动作：

1. 在 `acceptance_feedback_dir`（`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/`）写入 `deploy_007_验收日志.md`，内容包含：测试输出摘要、各项检查结果、L2 Gate S3 贡献说明、与 deploy_004 职责边界说明、遗留问题（无则注明）。
2. 更新本 L3 调度状态为 `done`（由调度层确认），等待 L2 整体验收。
3. 在交接说明中注明：本 L3 产物为 bundle 读取器，输出缺失文件列表与 checkpoint 路径；未加载模型权重；未解析完整 manifest payload；与 deploy_004/005/006 无文件冲突；`resolve_checkpoint_path` 只读取 manifest 中 checkpoint 路径字段，完整 payload 解析交由 deploy_004。
4. 若验收未通过，按第 16 节回滚并在日志记录失败轮次与原因，等待下一轮 dispatch。

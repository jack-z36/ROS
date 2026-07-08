```yaml
dispatch:
  task_id: deploy_009
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_009_契约交叉校验与配置编排.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S1, S3, S4]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_009_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 4
  parallel_group: l2-01-external-contract-p4
  depends_on: [deploy_001, deploy_002, deploy_003, deploy_004, deploy_005, deploy_006, deploy_007, deploy_008]
  must_run_after: [deploy_008]
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/config/schema.py
      - src/model_deploy/act/tests/config/test_contract_check.py
    modules:
      - model_deploy.act.config.schema
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

# deploy_009 — 契约交叉校验与配置编排

## 1. 任务标识

- **L3 编号**: deploy_009
- **L3 标题**: 契约交叉校验与配置编排
- **所属 L2**: l2-01-external-contract (外部参数加载与契约校验闭环)
- **Wave / 并行组**: Wave 4 / `l2-01-external-contract-p4`
- **分支**: `feat/model_deploy/l2-01-external-contract`
- **集成分支**: `model_deploy`
- **改造类型**: source-adaptation + observability
- **验收模式**: direct-local
- **真机风险**: none
- **验收场景**: S1 (合法配置载入)、S3 (bundle 缺文件失败)、S4 (normalizer 维度不一致失败)

## 2. 背景与上下文

L2 `l2-01-external-contract` 已通过 deploy_001 ~ deploy_008 搭建起完整的外部参数加载骨架：

- deploy_001 定义了契约结果容器 `types/contract_result.py`（`BundleContractResult` / `NormalizerContractResult` / `DeployConfigError`）。
- deploy_002 建立了 act 仓库根目录结构与 `repo` 层接口。
- deploy_003 定义了 `DeployConfig` 核心 dataclass 与 `DeployConfig.from_mapping` 的 schema 入口占位。
- deploy_004 ~ deploy_007 分别实现 repo 层的 manifest / normalizer / experiment_config / bundle 文件读取。
- deploy_008 在 `config/schema.py` 中落地了 `DeployConfig`、`DeployConfigError` 与各字段校验器（含 16D 契约的 dim 检查）。

至此，外部参数从「YAML → dataclass」的单向载入链路已通，但缺少把 repo 层读取结果（manifest、normalizer、experiment_config、bundle 文件）与 16D 契约「交叉校验」串联起来的编排入口，也缺少独立的 bundle 契约 / normalizer 契约校验函数。

deploy_009 正是补上这最后一块：在 deploy_008 已创建的 `config/schema.py` 上 **追加** `check_bundle_contract`、`check_normalizer_contract` 两个计算函数与 `load_deploy_config` 编排入口，把 repo 层读取结果与 16D 契约交叉校验串联成完整的启动期配置加载闭环。

> [!important] 与 deploy_008 的关系
> deploy_008 是本任务的直接前置（`must_run_after: [deploy_008]`）。两者操作同一文件 `src/model_deploy/act/config/schema.py`：deploy_008 **创建** schema.py 的 dataclass 与字段校验器；deploy_009 **追加** 契约校验函数与编排入口。禁止重新定义 dataclass 或字段校验器。

## 3. 目标

在 deploy_008 已创建的 `config/schema.py` 基础上，追加 `check_bundle_contract`、`check_normalizer_contract` 契约交叉校验函数和 `load_deploy_config` 编排入口，把 repo 层读取结果与 16D 契约交叉校验串联成完整启动期配置加载闭环。

完成后应满足：

1. `check_bundle_contract` 能独立判定 bundle 是否齐全（manifest.json / normalizers.json / experiment_config.yaml / adapter/ / checkpoint）并返回 `BundleContractResult`。
2. `check_normalizer_contract` 能独立判定 state / action normalizer 的 `vector_dim` 是否等于 16，返回 `NormalizerContractResult`。
3. `load_deploy_config` 能以单一入口完成 yaml 载入 → `from_mapping` → repo 层加载 → 契约交叉校验 → 失败即抛 `DeployConfigError` 的完整流程。
4. S1 / S3 / S4 三个验收场景由本任务直接贡献并可通过本地 pytest 验证。
5. deploy_008 已有的 dataclass 与字段校验器在追加后仍可正常导入、不受破坏。

## 4. 输入契约

- **输入文件（追加）**: `src/model_deploy/act/config/schema.py`（deploy_008 已创建，本任务只追加）
- **输入文件（新建）**: `src/model_deploy/act/tests/config/test_contract_check.py`
- **依赖的 deploy_001 产物**: `types/contract_result.py` 提供 `BundleContractResult`、`NormalizerContractResult`、`DeployConfigError`。
- **依赖的 deploy_003 产物**: `config/schema.py` 已提供 `DeployConfig` dataclass 与 `from_mapping`。
- **依赖的 deploy_004 产物**: `repo/manifest_parser.py` 的 `load_bundle_manifest(bundle_dir) -> ManifestInfo`。
- **依赖的 deploy_005 产物**: `repo/normalizer_loader.py` 的 `load_bundle_normalizers(bundle_dir) -> tuple[ActionStateNormalizer, ActionStateNormalizer]`（含 `vector_dim` 字段）。
- **依赖的 deploy_006 产物**: `repo/experiment_config_loader.py` 的 `load_experiment_config(path) -> ExperimentConfig`。
- **依赖的 deploy_007 产物**: `repo/bundle_reader.py` 的 `check_bundle_files(bundle_dir, required_files) -> BundleFileResult`。
- **Pi0.5 参考（只读）**: `deploy/src/pi05/deploy/config/schema.py` 的 `load_deploy_config`。

## 5. Pi0.5 源码盘点

| Pi0.5 现状 | ACT 增量 | 处理策略 |
| --- | --- | --- |
| `load_deploy_config(path)` 只做 `yaml.safe_load` → 要求根节点为 Mapping → `DeployConfig.from_mapping(raw, base_dir=config_path.parent)`，**不**做 bundle / normalizer 维度交叉校验 | 扩展 `load_deploy_config`：`from_mapping` 之后若 `bundle_dir` 已设置，加载 bundle 制品并跑契约交叉校验 | 保留 Pi0.5 的 entry pattern（yaml → from_mapping → base_dir 取父目录）；在尾部追加 ACT 增量分支 |
| bundle 文件检查、维度检查散落在 `bundle.py` 的各 load 函数内部，无独立的契约校验函数 | 新增 `check_bundle_contract` 与 `check_normalizer_contract` 两个独立计算函数，返回结构化 ContractResult | ACT 新增，Pi0.5 无对应物，需自行设计与命名 |
| 校验失败时各 load 函数抛出散落的 ValueError / FileNotFoundError | 校验失败集中通过 `DeployConfigError(reason=...)` 抛出，reason 取自 ContractResult.reason | ACT 增量：统一错误出口 |

- **必须保留**: `load_deploy_config(path) -> DeployConfig` 的入口签名、`yaml.safe_load` + 根节点 Mapping 校验 + `from_mapping(raw, base_dir=config_path.parent)` 的调用模式。
- **禁止照搬**: Pi0.5 在 load 函数内部零散做维度检查、无结构化 ContractResult、无独立 bundle 契约校验的做法。
- **已知风险**: deploy_009 与 deploy_008 共用 `schema.py`，追加内容必须与 deploy_008 已写好的 dataclass / 校验器并存而不破坏其导入与行为。

## 6. 边界

**允许做**:

- 在 `src/model_deploy/act/config/schema.py` 末尾**追加** `check_bundle_contract`、`check_normalizer_contract`、`load_deploy_config` 三个函数。
- 新建 `src/model_deploy/act/tests/config/test_contract_check.py` 测试文件。
- 引用 deploy_001 ~ deploy_007 已产出的类型与 repo 层加载器。

**不做**:

- **不**重新定义 `DeployConfig` dataclass 或任何字段校验器（那是 deploy_008 的职责）。
- **不**修改 repo 层（manifest_parser / normalizer_loader / experiment_config_loader / bundle_reader）的实现。
- **不**在本任务中引入任何 smoothing 字段（`blend_steps` / `smoothstep` / `cross_chunk` / `rtc_alignment` / `action_smoothing`）。

**禁止修改**:

- `pi05/` 目录（只读参考）。
- `types/`、`repo/`、`service/`、`runtime/`、`ui/` 层。
- deploy_008 已写入 schema.py 的既有内容（dataclass 定义、字段校验器、`from_mapping`）。

**函数 / class 策略**:

- `check_bundle_contract`：纯计算函数（输入 bundle 信息，输出 `BundleContractResult`）。
- `check_normalizer_contract`：纯计算函数（输入两个 normalizer，输出 `NormalizerContractResult`）。
- `load_deploy_config`：编排函数 + 数据读写函数（yaml 读取 + 调用 repo 加载器 + 调用契约校验 + 失败抛错）。

## 7. 六层落点

| 层 | 是否落点 | 说明 |
| --- | --- | --- |
| types | 否 | 仅引用 deploy_001 的 ContractResult，不修改 |
| repo | 否 | 仅调用 deploy_004~007 的加载器，不修改 |
| config | **是** | 追加到 `config/schema.py`；对应设计文档 `07_config层设计.md` |
| service | 否 | 本任务不涉及 |
| runtime | 否 | 本任务不涉及 |
| tests | **是** | 新建 `tests/config/test_contract_check.py` |

本任务对应 L2 设计文档 `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/07_config层设计.md`。

## 8. 微元清单

| 微元 ID | 名称 | 类型 | 文件 | 说明 |
| --- | --- | --- | --- | --- |
| 009-M1 | `check_bundle_contract` | 计算函数 | `src/model_deploy/act/config/schema.py` | 判定 bundle 文件齐全性 + manifest schema_version 兼容性，返回 `BundleContractResult` |
| 009-M2 | `check_normalizer_contract` | 计算函数 | `src/model_deploy/act/config/schema.py` | 判定 state/action normalizer 的 `vector_dim == 16`，返回 `NormalizerContractResult` |
| 009-M3 | `load_deploy_config` | 编排函数 + 数据读写函数 | `src/model_deploy/act/config/schema.py` | yaml 载入 → `from_mapping` → repo 加载 → 契约交叉校验 → 失败抛 `DeployConfigError` |
| 009-M4 | `test_contract_check.py` | 测试 | `src/model_deploy/act/tests/config/test_contract_check.py` | 覆盖合法 bundle 通过、缺文件失败、维度不一致失败、端到端编排 |

## 9. 实施步骤

1. **读取既有 schema.py 结构**：阅读 deploy_008 已写入的 `src/model_deploy/act/config/schema.py`，确认 `DeployConfig`、`DeployConfigError`、字段校验器、`from_mapping` 的位置与签名，确定追加锚点（在文件末尾追加，不插入既有代码块之间）。

2. **追加 `check_bundle_contract`**：
   - 签名：`check_bundle_contract(bundle_dir: Path, manifest_dict: Mapping[str, Any], required_files: Sequence[str]) -> BundleContractResult`
   - 逻辑：
     - 基于 `required_files`（manifest.json / normalizers.json / experiment_config.yaml / adapter/ / checkpoint）逐项检查 `bundle_dir` 下是否存在；缺失则收集到 `missing_files`。
     - 检查 `manifest_dict["schema_version"]` 与期望版本兼容（ACT 当前 schema_version 期望值参见 deploy_004 / L2 设计；不兼容则 reason 注明）。
     - 任一缺失或版本不兼容 → `passed=False`，`reason` 给出可读原因，`missing_files` / `schema_version` 如实填充。
     - 全通过 → `passed=True`。
   - 复用 `repo/bundle_reader.check_bundle_files` 的文件存在性结果作为输入信号，避免重复实现文件遍历。

3. **追加 `check_normalizer_contract`**：
   - 签名：`check_normalizer_contract(state_normalizer: ActionStateNormalizer, action_normalizer: ActionStateNormalizer, expected_dim: int = 16) -> NormalizerContractResult`
   - 逻辑：
     - 取 `state_normalizer.vector_dim` 与 `action_normalizer.vector_dim`。
     - 若任一不等于 `expected_dim`（默认 16）→ `passed=False`，`reason` 注明哪个 normalizer 的 dim 是多少、期望多少，`actual_dim` 如实填充。
     - 全通过 → `passed=True`，`expected_dim=16`。
   - normalizer 类型来自 deploy_005 的 `repo/normalizer_loader.py` 的 `ActionStateNormalizer`。

4. **追加 `load_deploy_config`**：
   - 签名：`load_deploy_config(path: str | Path) -> DeployConfig`
   - 流程：
     1. `path = Path(path)`，`raw = yaml.safe_load(path.read_text())`。
     2. 校验 `raw` 为 Mapping，否则抛 `DeployConfigError(reason="deploy.yaml root must be a mapping")`。
     3. `config = DeployConfig.from_mapping(raw, base_dir=path.parent)`。
     4. 若 `config.bundle_dir` 已设置：
        - `manifest = load_bundle_manifest(config.bundle_dir)`（deploy_004）
        - `state_norm, action_norm = load_bundle_normalizers(config.bundle_dir)`（deploy_005）
        - `exp_cfg = load_experiment_config(config.bundle_dir / "experiment_config.yaml")`（deploy_006）
        - `required_files = [...]`；调用 `check_bundle_files(config.bundle_dir, required_files)`（deploy_007）拿到缺失清单
        - `bundle_result = check_bundle_contract(config.bundle_dir, manifest.as_dict(), required_files)`
        - `norm_result = check_normalizer_contract(state_norm, action_norm, expected_dim=16)`
        - 若 `bundle_result.passed is False` → 抛 `DeployConfigError(reason=bundle_result.reason)`
        - 若 `norm_result.passed is False` → 抛 `DeployConfigError(reason=norm_result.reason)`
     5. 返回 `config`。
   - 失败原因必须取自 ContractResult.reason，保证错误出口统一、可读。

5. **新建 `tests/config/test_contract_check.py`**：
   - 用 `tmp_path` 构造 mock bundle 目录（写 manifest.json、normalizers.json、experiment_config.yaml、adapter/、checkpoint 文件）。
   - 测试用例：
     - `test_check_bundle_contract_passes_when_complete`：mock bundle 齐全 → `passed is True`。
     - `test_check_bundle_contract_fails_when_missing`：删掉 checkpoint → `passed is False`，`missing_files` 含 checkpoint。
     - `test_check_normalizer_contract_passes_at_dim_16`：两个 normalizer `vector_dim=16` → `passed is True`。
     - `test_check_normalizer_contract_fails_on_dim_mismatch`：把 action normalizer `vector_dim=8` → `passed is False`，`reason` 注明维度。
     - `test_load_deploy_config_end_to_end_pass`：合法 deploy.yaml + 合法 mock bundle → 返回 `DeployConfig`，不抛错。
     - `test_load_deploy_config_raises_when_bundle_incomplete`：mock bundle 缺文件 → 抛 `DeployConfigError`。
     - `test_load_deploy_config_raises_when_dim_mismatch`：mock normalizer 维度错 → 抛 `DeployConfigError`。
   - normalizer mock：直接构造 `ActionStateNormalizer` 实例或用 dataclass 替身（带 `vector_dim` 字段），以解耦对真实加载器内部实现的依赖。

6. **运行 pytest + rg 校验**：见第 12 节。

## 10. 允许修改的文件

> [!warning] 只允许修改下列文件
> 本任务只追加 / 新建以下两个文件。任何对 `pi05/`、`types/`、`repo/`、`service/`、`runtime/`、`ui/` 的修改都视为越界，将导致验收失败。

| 文件 | 操作 | 说明 |
| --- | --- | --- |
| `src/model_deploy/act/config/schema.py` | APPEND | 仅在文件末尾追加 3 个函数；**禁止**修改 deploy_008 已写入的 dataclass / 字段校验器 / `from_mapping` |
| `src/model_deploy/act/tests/config/test_contract_check.py` | NEW | 契约交叉校验 + 编排入口测试 |

> [!warning] conflict_scope 与 deploy_008 重叠
> `src/model_deploy/act/config/schema.py` 同时出现在 deploy_008 与本任务的 conflict_scope 中。这是 `must_run_after: [deploy_008]` 的根本原因：本任务必须等 deploy_008 完成、schema.py 的 dataclass 与校验器就位后，才能在文件末尾追加。严禁并行修改同一文件。

- conflict_scope files: `src/model_deploy/act/config/schema.py`、`src/model_deploy/act/tests/config/test_contract_check.py`
- conflict_scope modules: `model_deploy.act.config.schema`
- conflict_scope config_keys: `bundle`、`normalizer`、`experiment_config`

## 11. 测试策略

- **单元层**：`check_bundle_contract` / `check_normalizer_contract` 各自用纯 mock 输入测试 passed / reason / 缺失清单 / 维度字段的正确性，不依赖磁盘。
- **集成层**：`load_deploy_config` 用 `tmp_path` 构造完整的 mock bundle + deploy.yaml，走完 yaml → from_mapping → repo 加载 → 契约校验链路，覆盖成功与两类失败（缺文件、维度不一致）。
- **回归层**：跑 `tests/config/` 整目录，确保追加未破坏 deploy_008 的 schema.py 测试。
- **契约一致性**：所有失败路径统一抛 `DeployConfigError`，reason 取自 ContractResult，便于上层统一捕获与日志。

## 12. 验证

```bash
# 1. 本任务新增测试
python3 -m pytest src/model_deploy/act/tests/config/test_contract_check.py -v

# 2. config 层整目录回归（确保未破坏 deploy_008）
python3 -m pytest src/model_deploy/act/tests/config/ -v

# 3. 确认未引入任何 smoothing 字段
rg -n 'blend_steps|smoothstep|cross_chunk|rtc_alignment|action_smoothing' src/model_deploy/act/config/schema.py
```

- 期望：前两条 pytest 全绿；第三条 rg **无任何输出**（说明未引入 smoothing 字段）。
- 追加后 `python3 -c "from model_deploy.act.config.schema import DeployConfig, DeployConfigError, check_bundle_contract, check_normalizer_contract, load_deploy_config"` 应无 ImportError。

## 13. 完成标准

- [ ] `check_bundle_contract` 已追加，返回 `BundleContractResult`，缺文件 / 版本不兼容时 `passed=False`。
- [ ] `check_normalizer_contract` 已追加，返回 `NormalizerContractResult`，`vector_dim != 16` 时 `passed=False`。
- [ ] `load_deploy_config` 已追加，能完成 yaml → from_mapping → repo 加载 → 契约校验 → 失败抛 `DeployConfigError` 的全链路。
- [ ] `test_contract_check.py` 全绿，覆盖 S1 / S3 / S4。
- [ ] deploy_008 的 schema.py 既有内容未被改动，`tests/config/` 整目录回归全绿。
- [ ] rg 校验未引入任何 smoothing 字段。
- [ ] 未修改 `pi05/`、`types/`、`repo/`、`service/`、`runtime/`、`ui/`。

## 14. 风险与对策

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| 追加位置不当导致 schema.py 导入循环或语法错误 | config 层整体不可用 | 仅在文件末尾追加；新增 import 集中放在追加段顶部或复用文件已有 import；改动后立即跑 `tests/config/` 回归 |
| 与 deploy_008 同文件并行写入冲突 | 内容丢失或重复定义 | 严格 `must_run_after: [deploy_008]`，串行执行，不并行 |
| repo 加载器实际签名与本任务假设不符 | `load_deploy_config` 抛 TypeError | 实施第 1 步先阅读 deploy_004~007 的实际签名，按真实签名调用 |
| mock normalizer 与真实 `ActionStateNormalizer` 字段不一致 | 集成测试假阳性/假阴性 | 测试用最小 duck-type 替身（只需 `vector_dim` 属性），并在端到端用例中尽量贴近真实结构 |

## 15. 依赖关系

- **depends_on**: deploy_001、deploy_002、deploy_003、deploy_004、deploy_005、deploy_006、deploy_007、deploy_008（全部前置 L3 必须完成）。
- **must_run_after**: deploy_008（同文件 `config/schema.py`，必须严格后置）。
- **can_run_parallel_with**: []（无并行项；与 deploy_008 写同一文件，不能并行）。

## 16. 必读文档与代码

**必读 L2 设计文档**（与 deploy_008 相同的 7 篇，`07_config层设计.md` 为第 7 篇）：

1. `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/01_总览.md`
2. `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/02_契约模型.md`
3. `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/03_types层设计.md`
4. `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/04_repo层设计.md`
5. `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/05_加载流程.md`
6. `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/06_错误处理.md`
7. `DOCS/03_工程/阶段四：模型部署/02_design/l2-01-external-contract/07_config层设计.md`

**必读代码**：

- `src/model_deploy/act/config/schema.py`（deploy_008 产物，本任务追加目标）
- `src/model_deploy/act/types/contract_result.py`（deploy_001）
- `src/model_deploy/act/repo/manifest_parser.py`（deploy_004）
- `src/model_deploy/act/repo/normalizer_loader.py`（deploy_005）
- `src/model_deploy/act/repo/experiment_config_loader.py`（deploy_006）
- `src/model_deploy/act/repo/bundle_reader.py`（deploy_007）
- `deploy/src/pi05/deploy/config/schema.py`（Pi0.5 参考，只读）

## 17. 相关历史任务

- **直接上游**: deploy_008（同文件前置，本任务在其 schema.py 上追加）。
- **同组已完成**: deploy_001（契约结果容器）、deploy_002（act 仓库骨架）、deploy_003（DeployConfig core）、deploy_004（manifest 解析）、deploy_005（normalizer 加载）、deploy_006（experiment_config 加载）、deploy_007（bundle 文件检查）。
- **后续**: 本任务完成后，L2 `l2-01-external-contract` 的外部参数加载与契约校验闭环即具备完整入口（`load_deploy_config`），可进入 L2 级集成验收。

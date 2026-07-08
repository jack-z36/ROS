```yaml
dispatch:
  task_id: deploy_010
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_010_L2Gate集成测试.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S1, S2, S3, S4, S5]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_010_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 5
  parallel_group: l2-01-external-contract-p5
  depends_on: [deploy_001, deploy_002, deploy_003, deploy_004, deploy_005, deploy_006, deploy_007, deploy_008, deploy_009]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/tests/integration/test_l2_01_gate.py
    modules:
      - model_deploy.act.tests.integration.test_l2_01_gate
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

# deploy_010 — L2Gate集成测试

## 1. 元信息

| 字段 | 值 |
|---|---|
| L3 ID | deploy_010 |
| L3 名称 | L2Gate集成测试 |
| 所属 L2 | l2-01-external-contract（外部参数加载与契约校验闭环） |
| 改造类型 | test-coverage |
| 验收模式 | direct-local |
| 真机风险 | none |
| Wave | 5 |
| parallel_group | l2-01-external-contract-p5 |
| dispatch_status | ready |
| 本地验收轮次上限 | 3 |
| 本地验收强制 | true |
| 对应验收场景 | S1, S2, S3, S4, S5（全部 5 项） |

## 2. 上下文

本 L3 是 l2-01-external-contract 的最后一个 L3，负责关闭整个 L2 回路。前置 9 个 L3（deploy_001 至 deploy_009）已经分别落地了类型层（DeployConfig / StateSpec / ActionSpec / 错误类型）、配置加载层（deploy.yaml 解析、load_deploy_config 入口）、repo 层（bundle 目录发现、manifest/normalizers/checkpoint 文件校验）、service 层（NormalizerContract / 其他契约校验）以及各自的单元测试。

上述每一层都是分散的单元粒度测试，尚未有一个端到端的集成测试把 `load_deploy_config` 的完整管线（mock deploy.yaml + mock bundle → 类型构造 → 全部契约校验）串起来。本 L3 创建唯一的集成测试文件 `src/model_deploy/act/tests/integration/test_l2_01_gate.py`，作为 L2 Gate 的可执行载体：当 5 个测试函数全部通过时，L2-01 的 5 个验收项（S1-S5）即视为通过（等待人类验收确认）。

## 3. 目标

创建 L2 Gate 集成测试，端到端验证 L2-01 的 5 个验收项（S1-S5），覆盖：
- S1 合法配置载入：mock deploy.yaml + mock bundle → DeployConfig / StateSpec 16D / ActionSpec 16D 构造成功且契约通过
- S2 非法维度失败：state/action 维度非 16 → 抛出明确配置异常
- S3 bundle 缺文件失败：缺 manifest / normalizers / checkpoint → 抛出明确文件/契约异常
- S4 normalizer 维度不一致失败：normalizer 长度非 16 → 契约失败且原因可读
- S5 无平滑配置泄漏：静态扫描 schema / deploy.yaml / L2 设计文档，不存在第一版外平滑字段

## 4. 依赖

### 4.1 L3 级依赖

```yaml
depends_on:
  - deploy_001
  - deploy_002
  - deploy_003
  - deploy_004
  - deploy_005
  - deploy_006
  - deploy_007
  - deploy_008
  - deploy_009
can_run_parallel_with: []
```

说明：本 L3 必须在 deploy_001-009 全部完成后才能开始，因为它要集成调用各层暴露的类型与入口（DeployConfig / StateSpec / ActionSpec / DeployConfigError / NormalizerContractResult / load_deploy_config）。无可并行项——它是 L2 回路的收尾，必须串行在最后执行。

### 4.2 外部依赖

- pytest（已在仓库环境内）
- rg（ripgrep，用于 S5 静态扫描；若环境无 rg，降级为 Python 文件扫描）
- 无真机 / 无外部服务 / 无网络

## 5. Pi0.5 源码盘点

本 L3 为 ACT 增量测试，Pi0.5 无对应的契约校验集成测试可参照。

| Pi0.5 路径 | 用途 | 是否照搬 | 必须保留 | 已知风险 |
|---|---|---|---|---|
| （无） | Pi0.5 无对应集成测试 | 否 | 无 | mock bundle 结构必须与真实 bundle 结构预期一致，否则集成测试与真实加载路径脱节 |

禁止照搬：无。
必须保留：无。

ACT 增量说明：Pi0.5 的部署侧没有“外部契约校验 Gate”的概念，配置直接由训练侧注入。ACT 引入 `load_deploy_config` + 契约层后，需要一个集成测试作为 Gate 的可执行定义，这正是本 L3 的职责。

## 6. 边界

### 6.1 允许做

- 创建 `src/model_deploy/act/tests/integration/` 目录（若不存在）
- 创建 `src/model_deploy/act/tests/integration/test_l2_01_gate.py` 测试文件
- 在测试文件内编写 5 个测试函数 + 必要的 pytest fixture（tmp_path 派生的 mock bundle 构造）
- 使用 `subprocess` 调用 `rg` 或纯 Python 文件扫描实现 S5

### 6.2 不做

- 不修改 types/config/repo/service/runtime/ui 任一源码文件
- 不新增、不修改 deploy.yaml 模板或 schema.py
- 不触碰 `pi05/` 目录
- 不修改其他 L3（deploy_001-009）已落地的文件
- 不引入新的第三方依赖

### 6.3 禁止修改

| 范围 | 说明 |
|---|---|
| 所有源码 | types/ config/ repo/ service/ runtime/ ui/ 下任何 .py |
| pi05/ | 全目录只读 |
| 其他 L3 文件 | deploy_001-009 的实现与测试文件 |
| L2 设计文档 | 02_implement/ 与 01_设计/ 下文档只读 |

### 6.4 函数 / class 策略

仅使用测试函数，不需要 class。5 个测试函数 `test_s1` 至 `test_s5`，外加若干私有 helper / fixture（如 `_write_mock_bundle`、`_write_deploy_yaml`）用于构造 mock 输入。fixture 优先用 pytest 原生 `tmp_path` 派生，保证测试间隔离。

## 7. 六层落点

| 层 | 落点 | 说明 |
|---|---|---|
| types | 否 | 仅引用已有类型，不修改 |
| config | 否 | 仅引用 load_deploy_config / deploy.yaml schema，不修改 |
| repo | 否 | 仅触发 bundle 发现路径，不修改 |
| service | 否 | 仅触发契约校验路径，不修改 |
| runtime | 否 | 不涉及运行时 |
| ui | 否 | 不涉及 UI |
| **tests** | **是** | 创建 `src/model_deploy/act/tests/integration/test_l2_01_gate.py` |

本 L3 对应设计文档 `agent_context/04_L2验收机制.md`——该文档描述的 L2 Gate 机制，本 L3 是其可执行实现。

## 8. 微元

| 微元 ID | 名称 | 类型 | 输入 | 输出 | 对应场景 |
|---|---|---|---|---|---|
| M1 | test_s1_legal_config_loads | 测试/验证 | 合法 mock deploy.yaml + 完整 mock bundle（manifest.json / normalizers.json 16D / experiment_config.yaml / adapter/ / checkpoint） | DeployConfig 返回，StateSpec 16D，ActionSpec 16D，全部契约 passed==True | S1 |
| M2 | test_s2_invalid_dimension_fails | 测试/验证 | state_dim=15 或 action_dim=14 的配置 | 抛出 DeployConfigError，异常信息明确指向维度 | S2 |
| M3 | test_s3_bundle_missing_files_fails | 测试/验证 | 缺 manifest.json / normalizers.json / checkpoint 的 bundle 目录 | 抛出 DeployConfigError 或 FileNotFoundError，信息明确指向缺失文件 | S3 |
| M4 | test_s4_normalizer_dim_mismatch_fails | 测试/验证 | normalizers.json 含 14D normalizer | 抛出 DeployConfigError，且 NormalizerContractResult.passed==False，reason 文本提及维度不一致 | S4 |
| M5 | test_s5_no_smoothing_config_leakage | 测试/验证 | 扫描 schema.py / deploy.yaml / L2 设计文档 | forbidden 字段（smoothstep/blend_steps/cross_chunk/rtc_alignment/action_smoothing）在源码与配置中无匹配，仅在“禁止/不负责/去除”上下文出现 | S5 |

辅助微元（非场景对应，支撑上述 5 项）：

| 微元 ID | 名称 | 类型 | 说明 |
|---|---|---|---|
| H1 | _write_deploy_yaml fixture | 辅助 | 向 tmp_path 写入可控 deploy.yaml |
| H2 | _write_mock_bundle fixture | 辅助 | 向 tmp_path 写入完整/残缺/错维度的 mock bundle 目录 |
| H3 | FORBIDDEN_FIELDS 常量 | 辅助 | 平滑字段黑名单列表，供 M5 引用 |

## 9. 步骤

1. **建目录**：确保 `src/model_deploy/act/tests/integration/` 存在（必要时新增 `__init__.py`，若仓库其他 tests 子目录有 `__init__.py` 则保持一致，否则不加）。
2. **建测试文件骨架**：创建 `test_l2_01_gate.py`，写入 import（pytest、被测入口、相关类型、subprocess）与 `FORBIDDEN_FIELDS` 常量，以及两个 helper fixture（`_write_deploy_yaml` / `_write_mock_bundle`）。fixture 基于 `tmp_path`，参数化控制：维度、是否缺文件、normalizer 长度。
3. **实现 M1 test_s1_legal_config_loads**：构造合法 mock deploy.yaml（state_dim=16, action_dim=16）+ 完整 mock bundle（manifest.json 含正确字段、normalizers.json 16D、experiment_config.yaml、adapter/ 子目录、checkpoint 文件占位）。调用 `load_deploy_config(yaml_path, bundle_path)`，断言返回 DeployConfig、StateSpec.dim==16、ActionSpec.dim==16、各契约 passed==True。
4. **实现 M2 test_s2_invalid_dimension_fails**：参数化 state_dim∈{15,17}、action_dim∈{14,18}，调用 `load_deploy_config`，用 `pytest.raises(DeployConfigError)` 断言抛出，并断言异常信息包含 "dim" 或 "维度" 关键字。
5. **实现 M3 test_s3_bundle_missing_files_fails**：参数化缺失项 ∈ {manifest.json, normalizers.json, checkpoint}，调用 `load_deploy_config`，断言抛出 DeployConfigError 或 FileNotFoundError，异常信息明确指向缺失文件名。
6. **实现 M4 test_s4_normalizer_dim_mismatch_fails**：normalizers.json 写入 14D normalizer，调用 `load_deploy_config`，断言 DeployConfigError 抛出；若实现返回 ContractResult 而非抛异常，则断言 `NormalizerContractResult.passed is False` 且 `.reason` 文本包含维度不一致描述。
7. **实现 M5 test_s5_no_smoothing_config_leakage**：优先用 `subprocess.run(["rg", "-n", pattern, path])` 扫描 `src/model_deploy/act` 与 `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环`；对每个 forbidden 字段，源码与配置文件中匹配数必须为 0；设计文档中匹配仅允许出现在“禁止/不负责/去除”同行上下文。无 rg 时降级为 Python `pathlib` 递归读文件 + `in` 扫描，逻辑等价。
8. **运行集成测试**：`python3 -m pytest src/model_deploy/act/tests/integration/test_l2_01_gate.py -v`，确认 5 项全绿。
9. **运行全量测试**：`python3 -m pytest src/model_deploy/act/tests/ -v`，确认 deploy_001-009 的单元测试与本集成测试协同全绿，无回归。
10. **运行 rg 全树检查**：对 `src/model_deploy/act` 与 L2 设计文档目录执行 forbidden 字段扫描，确认源码与配置零泄漏。

## 10. 风险与对策

| 风险 | 等级 | 对策 |
|---|---|---|
| mock bundle 结构与真实 bundle 预期不一致，集成测试通过但真实加载失败 | 中 | 对照 deploy_003/004 的 bundle 发现与文件校验逻辑构造 mock，保持字段名/层级一致；在 fixture 注释中标明对应真实路径 |
| load_deploy_config 签名在 deploy_002 中与本文假设不同（参数名/返回类型） | 中 | 实现前先 import 检查签名；若不一致，以真实签名为准调整调用，不改被测代码 |
| 环境无 rg | 低 | M5 双路径：优先 rg，失败则降级 Python 扫描，断言逻辑等价 |
| M5 设计文档中“禁止”上下文匹配被误判为泄漏 | 中 | 仅在源码（src/）与配置（*.yaml / schema.py）中断言零匹配；设计文档单独走“上下文白名单”判定 |
| deploy_001-009 中某项未真正完成导致集成测试无法通过 | 中 | 本 L3 的 depends_on 已强制串行；若卡住，记录到 acceptance_feedback 并回退上游，不在本 L3 内修源码 |

## 11. 验收前自检

- [ ] 测试文件位于 `src/model_deploy/act/tests/integration/test_l2_01_gate.py`
- [ ] 5 个测试函数 `test_s1`-`test_s5` 均存在且独立可跑
- [ ] 未修改任何 src 下的源码（git diff 仅含新增测试文件）
- [ ] 未触碰 `pi05/`
- [ ] 未修改 deploy_001-009 的任何文件
- [ ] `pytest src/model_deploy/act/tests/ -v` 全绿

## 12. 验证

```bash
# 1. 集成测试单跑
python3 -m pytest src/model_deploy/act/tests/integration/test_l2_01_gate.py -v

# 2. 全量回归
python3 -m pytest src/model_deploy/act/tests/types \
                 src/model_deploy/act/tests/config \
                 src/model_deploy/act/tests/repo \
                 src/model_deploy/act/tests/integration -v

# 3. 平滑字段零泄漏扫描（源码 + 设计文档）
rg -n 'smoothstep|blend_steps|cross_chunk|rtc_alignment|action_smoothing' \
   src/model_deploy/act \
   DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环
```

**预期结果**：
- 命令 1：5 passed
- 命令 2：全部 passed（types + config + repo + integration）
- 命令 3：源码与配置文件中 0 匹配；设计文档中匹配仅出现在“禁止 / 不负责 / 去除”同行上下文（设计文档解释“已移除什么”属合法）

## 13. 回滚策略

本 L3 仅新增一个测试文件，无源码改动。

- 若集成测试失败：不改源码，记录失败现场到 `acceptance_feedback_dir`，将问题回退给对应上游 L3（deploy_001-009），本 L3 测试文件保留待上游修复后重跑。
- 若需整体撤销：`git checkout` 丢弃新增的 `test_l2_01_gate.py` 即可，无副作用。

## 14. 完成定义

- [ ] `src/model_deploy/act/tests/integration/test_l2_01_gate.py` 已创建
- [ ] test_s1-test_s5 五项测试存在并通过
- [ ] 全量 `pytest src/model_deploy/act/tests/ -v` 通过
- [ ] rg 平滑字段扫描：源码与配置零匹配
- [ ] git diff 仅含新增测试文件，无源码改动
- [ ] 验收卡片 PASS_LOCAL 全绿

## 15. 相关历史任务

| 关系 | 任务 |
|---|---|
| 直接上游（全部） | deploy_001, deploy_002, deploy_003, deploy_004, deploy_005, deploy_006, deploy_007, deploy_008, deploy_009 |
| 同组已完成 | deploy_001-009（同属 l2-01-external-contract） |
| 后续 | 无（本 L3 关闭 L2-01 回路，完成后进入人类验收） |

## 16. 必读 L2 设计文档

1. `01_L1_ACT功能模块边界.md`
2. `02_L1_ACT功能模块协作架构.md`
3. `agent_context/01_L2功能边界.md`
4. `agent_context/02_pi05源码3.5层微元拆解.md`
5. `agent_context/03_ACT微元设计与协作.md`
6. `agent_context/04_L2验收机制.md`（本 L3 是该文档描述的 L2 Gate 的可执行实现）
7. `agent_context/05_人类验收机制.md`

## 17. L2 Gate 贡献

本 L3 **即是** L2 Gate 的验证载体。

- **对应场景**：S1, S2, S3, S4, S5 全部 5 项。当 5 个测试函数全绿时，L2 Gate 的机器侧判定即视为通过。
- **本 L3 提供的运行能力**：端到端集成测试覆盖全部 5 项 Gate 验收项（合法载入 / 非法维度 / 缺文件 / normalizer 维度不一致 / 无平滑泄漏），把分散的单元测试串成一条 `load_deploy_config` 全管线用例。
- **L2 Gate 仍需后续 L3 补齐的内容**：**无**。本 L3 完成后，L2-01 回路可进入人类验收（对应 `05_人类验收机制.md`）。
- **人类验收前置条件**：本 L3 验收卡片 PASS_LOCAL 全绿 + 全量回归全绿 + rg 零泄漏。

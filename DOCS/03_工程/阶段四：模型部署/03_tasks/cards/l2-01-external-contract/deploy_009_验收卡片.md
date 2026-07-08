---
l2: l2-01-external-contract
l3: deploy_009
title: 契约交叉校验与配置编排 — 验收卡片
改造类型: [source-adaptation, observability]
验收模式: direct-local
真机风险: none
wave: 4
parallel_group: l2-01-external-contract-p4
branch: feat/model_deploy/l2-01-external-contract
integration_branch: model_deploy
acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
acceptance_round_limit: 3
local_acceptance_required: true
dispatch_status: ready
acceptance_scenarios: [S1, S3, S4]
status: pending
---

# deploy_009 验收卡片 — 契约交叉校验与配置编排

## 1. 任务概览

| 项 | 值 |
| --- | --- |
| L3 | deploy_009 |
| 标题 | 契约交叉校验与配置编排 |
| L2 | l2-01-external-contract (外部参数加载与契约校验闭环) |
| 改造类型 | source-adaptation + observability |
| 验收模式 | direct-local |
| 真机风险 | none |
| Wave / 并行组 | 4 / l2-01-external-contract-p4 |
| 分支 | feat/model_deploy/l2-01-external-contract |
| depends_on | deploy_001 ~ deploy_008 |
| must_run_after | deploy_008 |
| 验收场景 | S1 (合法配置载入)、S3 (bundle 缺文件失败)、S4 (normalizer 维度不一致失败) |
| 验收轮次上限 | 3 |
| local_acceptance_required | true |

**产出文件**:

- `src/model_deploy/act/config/schema.py`（APPEND：`check_bundle_contract`、`check_normalizer_contract`、`load_deploy_config`）
- `src/model_deploy/act/tests/config/test_contract_check.py`（NEW）

> [!warning] 与 deploy_008 共用 schema.py
> 本任务在 deploy_008 创建的 `src/model_deploy/act/config/schema.py` 末尾追加，禁止改动 deploy_008 已写入的 dataclass、字段校验器、`from_mapping`。追加后 schema.py 必须仍可被 deploy_008 的测试正常导入。

## 2. 验收范围

本卡片仅验收 deploy_009 自身产出：契约交叉校验函数、编排入口、对应测试，以及对 deploy_008 schema.py 既有内容的「不破坏」保证。

- S1（合法配置载入）：合法 deploy.yaml + 合法 mock bundle → `load_deploy_config` 返回 `DeployConfig`，两个契约校验 `passed=True`。
- S3（bundle 缺文件失败）：mock bundle 缺 checkpoint → `check_bundle_contract.passed=False` → `load_deploy_config` 抛 `DeployConfigError`。
- S4（normalizer 维度不一致失败）：mock normalizer `vector_dim != 16` → `check_normalizer_contract.passed=False` → `load_deploy_config` 抛 `DeployConfigError`。

不验收：repo 层加载器内部实现（deploy_004~007）、types 层容器（deploy_001）、DeployConfig 字段校验器（deploy_008）。

## 3. PASS_LOCAL 判据

以下条件全部满足方为 PASS_LOCAL：

- `check_bundle_contract` 存在于 `src/model_deploy/act/config/schema.py`，签名含 `bundle_dir` / `manifest_dict` / `required_files`，返回 `BundleContractResult`。
- `check_normalizer_contract` 存在，签名含 `state_normalizer` / `action_normalizer` / `expected_dim=16`，返回 `NormalizerContractResult`，且当 `vector_dim != 16` 时 `passed=False`。
- `load_deploy_config` 存在，能完成 yaml → `from_mapping` → repo 加载 → 契约校验的编排，失败统一抛 `DeployConfigError`。
- 合法 mock 配置 + 合法 mock bundle → 返回 `DeployConfig`，两个契约 `passed=True`（S1）。
- bundle 缺文件 → `DeployConfigError` 被抛出（S3）。
- normalizer `vector_dim != 16` → `DeployConfigError` 被抛出（S4）。
- deploy_008 的 schema.py 既有 dataclass / 字段校验器未被破坏，schema.py 仍可正常导入、`tests/config/` 整目录回归全绿。
- `src/model_deploy/act/tests/config/test_contract_check.py` 全绿。
- 未引入任何 smoothing 字段（`blend_steps` / `smoothstep` / `cross_chunk` / `rtc_alignment` / `action_smoothing`）。
- 未修改 `pi05/`、`types/`、`repo/`、`service/`、`runtime/`、`ui/`。

## 4. 验收配置

```yaml
l3: deploy_009
acceptance_mode: direct-local
real_hw_risk: none
local_acceptance_required: true
acceptance_round_limit: 3
dispatch_status: ready
acceptance_scenarios: [S1, S3, S4]
conflict_scope:
  files:
    - src/model_deploy/act/config/schema.py
    - src/model_deploy/act/tests/config/test_contract_check.py
  modules:
    - model_deploy.act.config.schema
  config_keys:
    - bundle
    - normalizer
    - experiment_config
dependencies:
  depends_on: [deploy_001, deploy_002, deploy_003, deploy_004, deploy_005, deploy_006, deploy_007, deploy_008]
  must_run_after: [deploy_008]
  can_run_parallel_with: []
products:
  - path: src/model_deploy/act/config/schema.py
    operation: APPEND
    functions: [check_bundle_contract, check_normalizer_contract, load_deploy_config]
  - path: src/model_deploy/act/tests/config/test_contract_check.py
    operation: NEW
feedback:
  dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
```

## 5. 验收执行

> [!warning] 执行前提
> deploy_008 必须先完成且其 schema.py 已合入当前分支。本任务在其末尾追加，不可与 deploy_008 并行。所有命令在仓库根目录 `/home/hit/ROS/worktrees/l2-01` 执行，路径相对仓库根。

**第 1 步 — 运行本任务测试**:

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_contract_check.py -v
```

**第 2 步 — config 层整目录回归（验证未破坏 deploy_008）**:

```bash
python3 -m pytest src/model_deploy/act/tests/config/ -v
```

**第 3 步 — 确认未引入 smoothing 字段**:

```bash
rg -n 'blend_steps|smoothstep|cross_chunk|rtc_alignment|action_smoothing' src/model_deploy/act/config/schema.py
```

**第 4 步 — 确认追加的三个函数可正常导入、deploy_008 既有内容仍在**:

```bash
python3 -c "from model_deploy.act.config.schema import DeployConfig, DeployConfigError, check_bundle_contract, check_normalizer_contract, load_deploy_config; print('import ok')"
```

**第 5 步 — 确认未越界修改 pi05/ 与其它层**:

```bash
git diff --name-only feat/model_deploy/l2-01-external-contract
```

> [!warning] 期望 diff 仅含两个文件
> `git diff --name-only` 的输出应**只**包含：
> - `src/model_deploy/act/config/schema.py`
> - `src/model_deploy/act/tests/config/test_contract_check.py`
>
> 任何 `pi05/`、`types/`、`repo/`、`service/`、`runtime/`、`ui/` 路径出现即判 FAIL。

## 6. 验收场景与预期

### S1 — 合法配置载入（PASS 期望）

前置：合法 deploy.yaml + 合法 mock bundle（manifest.json、normalizers.json、experiment_config.yaml、adapter/、checkpoint 齐全；两个 normalizer `vector_dim=16`）。

```text
test_load_deploy_config_end_to_end_pass
  -> load_deploy_config(deploy_yaml_path)
  -> returns DeployConfig instance
  -> check_bundle_contract.passed == True
  -> check_normalizer_contract.passed == True
  -> no exception raised
PASSED
```

### S3 — bundle 缺文件失败（FAIL 期望）

前置：合法 deploy.yaml + mock bundle 删除 checkpoint。

```text
test_check_bundle_contract_fails_when_missing
  -> check_bundle_contract(...) -> BundleContractResult(passed=False, missing_files=[checkpoint])
test_load_deploy_config_raises_when_bundle_incomplete
  -> load_deploy_config(deploy_yaml_path)
  -> raises DeployConfigError(reason contains missing-file hint)
PASSED
```

### S4 — normalizer 维度不一致失败（FAIL 期望）

前置：合法 deploy.yaml + mock bundle，但 action normalizer `vector_dim=8`。

```text
test_check_normalizer_contract_fails_on_dim_mismatch
  -> check_normalizer_contract(state_norm, action_norm_dim_8)
  -> NormalizerContractResult(passed=False, expected_dim=16, actual_dim=8)
test_load_deploy_config_raises_when_dim_mismatch
  -> load_deploy_config(deploy_yaml_path)
  -> raises DeployConfigError(reason contains dim hint)
PASSED
```

### 不破坏 deploy_008 回归（隐含判据）

```text
python3 -m pytest src/model_deploy/act/tests/config/ -v
  -> all green (deploy_008 schema tests + deploy_009 contract tests)
```

---

> [!warning] FAIL 处理
> 任一轮验收未通过时，将失败现场（命令输出、diff、报错堆栈）写入 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_009_round<N>.log`，并在不超过 `acceptance_round_limit: 3` 的前提下反馈给执行 agent 修复后重验。

---
l3_id: deploy_010
l3_name: L2Gate集成测试
l2: l2-01-external-contract
改造类型: test-coverage
验收模式: direct-local
acceptance_round_limit: 3
local_acceptance_required: true
dispatch_status: ready
acceptance_scenarios:
  - S1
  - S2
  - S3
  - S4
  - S5
---

# deploy_010 验收卡片 — L2Gate集成测试

> [!info] 卡片信息
> - **L3**：deploy_010 — L2Gate集成测试
> - **所属 L2**：l2-01-external-contract（外部参数加载与契约校验闭环）
> - **改造类型**：test-coverage
> - **验收模式**：direct-local（本地直接验收，无真机）
> - **验收场景**：S1, S2, S3, S4, S5（全部 5 项）
> - **角色定位**：本 L3 即 L2 Gate 的可执行验证载体，5 项全绿 = L2 Gate 机器侧通过

---

## 1. 验收目标

验证 `src/model_deploy/act/tests/integration/test_l2_01_gate.py` 端到端覆盖 L2-01 的 5 个验收项，且不引入任何源码改动。

- 仅新增测试文件，不修改任何源码、不触碰 `pi05/`
- 5 个测试函数 test_s1-test_s5 全部通过
- 全量回归（types + config + repo + integration）通过
- 平滑字段（smoothstep/blend_steps/cross_chunk/rtc_alignment/action_smoothing）在源码与配置中零泄漏

---

## 2. 前置条件

> [!warning] 前置必须全部满足，否则不得开始验收
> - [ ] deploy_001 至 deploy_009 全部已完成并通过各自验收
> - [ ] `load_deploy_config` 入口、`DeployConfig`/`StateSpec`/`ActionSpec`/`DeployConfigError`/`NormalizerContractResult` 类型已存在于源码
> - [ ] 测试文件 `src/model_deploy/act/tests/integration/test_l2_01_gate.py` 已创建
> - [ ] 当前分支为 `feat/model_deploy/l2-01-external-contract`
> - [ ] pytest 与 rg（或 Python 降级扫描）可用

```yaml
preconditions:
  upstream_l3_done: [deploy_001, deploy_002, deploy_003, deploy_004, deploy_005, deploy_006, deploy_007, deploy_008, deploy_009]
  target_file_exists: src/model_deploy/act/tests/integration/test_l2_01_gate.py
  source_untouched: true
  pi05_untouched: true
```

---

## 3. PASS_LOCAL 验收清单

> [!warning] 以下全部为 PASS_LOCAL 判据，必须逐项通过

### 3.1 文件与结构

- [ ] **F1** 测试文件存在于 `src/model_deploy/act/tests/integration/test_l2_01_gate.py`
- [ ] **F2** 文件内存在 5 个测试函数：`test_s1_legal_config_loads`、`test_s2_invalid_dimension_fails`、`test_s3_bundle_missing_files_fails`、`test_s4_normalizer_dim_mismatch_fails`、`test_s5_no_smoothing_config_leakage`

### 3.2 S1 — 合法配置载入（test_s1_legal_config_loads）

- [ ] **S1-a** 构造合法 mock deploy.yaml（state_dim=16, action_dim=16）+ 完整 mock bundle（manifest.json / normalizers.json 16D / experiment_config.yaml / adapter/ / checkpoint）
- [ ] **S1-b** 调用 `load_deploy_config` 返回 `DeployConfig` 对象
- [ ] **S1-c** `StateSpec` 维度为 16
- [ ] **S1-d** `ActionSpec` 维度为 16
- [ ] **S1-e** 相关契约校验 `passed == True`

### 3.3 S2 — 非法维度失败（test_s2_invalid_dimension_fails）

- [ ] **S2-a** 构造 state_dim=15 或 action_dim=14 的配置
- [ ] **S2-b** 调用 `load_deploy_config` 抛出 `DeployConfigError`
- [ ] **S2-c** 异常信息明确指向维度（包含 "dim" 或 "维度"）

### 3.4 S3 — bundle 缺文件失败（test_s3_bundle_missing_files_fails）

- [ ] **S3-a** 构造缺失 manifest.json / normalizers.json / checkpoint 之一的 bundle
- [ ] **S3-b** 调用 `load_deploy_config` 抛出 `DeployConfigError` 或 `FileNotFoundError`
- [ ] **S3-c** 异常信息明确指向缺失文件名

### 3.5 S4 — normalizer 维度不一致失败（test_s4_normalizer_dim_mismatch_fails）

- [ ] **S4-a** normalizers.json 写入 14D normalizer（非 16D）
- [ ] **S4-b** 调用 `load_deploy_config` 抛出 `DeployConfigError`
- [ ] **S4-c** `NormalizerContractResult.passed == False`
- [ ] **S4-d** 失败原因文本可读，提及维度不一致

### 3.6 S5 — 无平滑配置泄漏（test_s5_no_smoothing_config_leakage）

- [ ] **S5-a** 对 `src/model_deploy/act`（含 schema.py / deploy.yaml）执行 forbidden 字段扫描
- [ ] **S5-b** forbidden 字段（smoothstep / blend_steps / cross_chunk / rtc_alignment / action_smoothing）在源码与配置中 0 匹配
- [ ] **S5-c** 设计文档中的匹配仅出现在“禁止 / 不负责 / 去除”上下文（合法）

### 3.7 回归与零改动

- [ ] **R1** 5 项测试全部通过（pytest 5 passed）
- [ ] **R2** 全量测试套件通过（types + config + repo + integration）
- [ ] **R3** `git diff` 仅含新增测试文件，无源码修改
- [ ] **R4** 未修改 `pi05/` 目录

---

## 4. 验证命令

> [!warning] 按顺序执行，全部预期通过

### 4.1 集成测试单跑

```bash
python3 -m pytest src/model_deploy/act/tests/integration/test_l2_01_gate.py -v
```

预期输出：

```text
test_s1_legal_config_loads ... PASSED
test_s2_invalid_dimension_fails ... PASSED
test_s3_bundle_missing_files_fails ... PASSED
test_s4_normalizer_dim_mismatch_fails ... PASSED
test_s5_no_smoothing_config_leakage ... PASSED

===== 5 passed =====
```

### 4.2 全量回归

```bash
python3 -m pytest src/model_deploy/act/tests/types \
                 src/model_deploy/act/tests/config \
                 src/model_deploy/act/tests/repo \
                 src/model_deploy/act/tests/integration -v
```

预期：全部 passed，无 failed / error。

### 4.3 平滑字段零泄漏扫描

```bash
rg -n 'smoothstep|blend_steps|cross_chunk|rtc_alignment|action_smoothing' \
   src/model_deploy/act \
   DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环
```

预期：

```text
# src/model_deploy/act 下：0 匹配
# 设计文档目录下：仅 "禁止 / 不负责 / 去除" 上下文匹配（合法）
```

### 4.4 零源码改动校验

```bash
git status --short src/model_deploy/act
```

预期：仅 `?? src/model_deploy/act/tests/integration/test_l2_01_gate.py`（新增），无 `M`（modified）源码文件。

```bash
git diff --stat -- src/model_deploy/act/types src/model_deploy/act/config src/model_deploy/act/repo src/model_deploy/act/service src/model_deploy/act/runtime src/model_deploy/act/ui pi05
```

预期：

```text
（空输出 — 无任何改动）
```

---

## 5. 失败处理

> [!warning] 任何一项未通过，按下列路径处理，不得为通过测试而改源码

| 失败现象 | 根因定位 | 处理 |
|---|---|---|
| test_s1 失败（构造失败或契约不过） | 上游类型/bundle 结构/契约实现 | 记录到 `acceptance_feedback_dir`，回退 deploy_001-004，不在本 L3 改源码 |
| test_s2 未抛异常（静默通过） | 维度校验缺失 | 回退 deploy_001/002（类型/配置校验） |
| test_s3 未抛异常（进入半初始化） | bundle 文件校验缺失 | 回退 deploy_003/004（repo 层） |
| test_s4 原因不可读或 passed!=False | 契约结果对象缺失字段 | 回退 deploy_005/006（service 契约） |
| test_s5 源码出现 forbidden 字段 | 某上游 L3 误引入平滑配置 | 回退引入该字段的 L3，删除字段 |
| 全量回归出现 failed | 上游单元测试与本集成不兼容 | 记录并回退对应上游 L3 |

```yaml
failure_policy:
  max_rounds: 3
  on_fail: 记录到 DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/
  never: 为通过测试而修改被测源码
```

---

## 6. 签字

> [!info] 验收结论

```yaml
verdict: PASS_LOCAL | FAIL
scenarios:
  S1_合法配置载入: pass | fail
  S2_非法维度失败: pass | fail
  S3_bundle缺文件失败: pass | fail
  S4_normalizer维度不一致失败: pass | fail
  S5_无平滑配置泄漏: pass | fail
regression: pass | fail
source_untouched: true
pi05_untouched: true
round: 1/3
l2_gate_status: 5项全绿则 L2 Gate 机器侧通过，进入人类验收
```

**验收人**：_____________  **日期**：_____________  **轮次**：____ / 3

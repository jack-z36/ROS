# 验收卡片：deploy_006 experiment_config 加载器

> [!info] 归属
> L2：l2-01-external-contract（外部参数加载与契约校验闭环）
> L1：ACT　阶段：阶段四：模型部署
> Wave：2　parallel_group：l2-01-external-contract-p2
> 验收模式：direct-local　真机风险：none
> 验收轮次上限：3　local_acceptance_required：true
> 关联 L2 Gate 场景：S4（normalizer 维度不一致失败）

## 1. 检查对象

| 项 | 内容 |
|---|---|
| L3 编号 | deploy_006 |
| L3 标题 | experiment_config 加载器 |
| 改造类型 | source-adaptation |
| 源文件 | `src/model_deploy/act/repo/experiment_config_loader.py` |
| 测试文件 | `src/model_deploy/act/tests/repo/test_experiment_config_loader.py` |
| 冲突模块 | `model_deploy.act.repo.experiment_config_loader` |
| conflict_scope files | `src/model_deploy/act/repo/experiment_config_loader.py`、`src/model_deploy/act/tests/repo/test_experiment_config_loader.py` |
| 验收场景 | S4 |
| 验收目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract` |
| 验收日志目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs` |

## 2. 验收模式

direct-local：在本地开发环境直接验收，不依赖真机部署与端到端集成。验收手段为单元测试执行 + conflict_scope 边界检查 + repo 层依赖方向检查 + 禁止逻辑检查 + 维度硬编码检查。验收轮次上限 3 轮，必须 local_acceptance_required 通过。验收结论写入 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_006_验收日志.md`。

## 3. 必跑命令

```bash
cd /home/hit/ROS/worktrees/l2-01

# 1. 单元测试全绿
pytest src/model_deploy/act/tests/repo/test_experiment_config_loader.py -v

# 2. conflict_scope 边界检查（仅允许两个文件改动）
git status --porcelain
# 期望仅出现：
#   src/model_deploy/act/repo/experiment_config_loader.py
#   src/model_deploy/act/tests/repo/test_experiment_config_loader.py

# 3. repo 层未向上引用 config/service/runtime/ui
grep -rn "from model_deploy.act.config\|from model_deploy.act.service\|from model_deploy.act.runtime\|from model_deploy.act.ui" \
  src/model_deploy/act/repo/experiment_config_loader.py
# 期望：无匹配

# 4. 未引入禁止逻辑
grep -rn "blend_steps\|smoothstep\|cross_chunk\|rtc_alignment\|action_smoothing" \
  src/model_deploy/act/repo/experiment_config_loader.py
# 期望：无匹配

# 5. 未硬编码 Pi0.5 维度默认值
grep -rn "state_dim.*=.*26\|action_dim.*=.*14\|image_size.*=.*224\|max_action_dim.*=.*14" \
  src/model_deploy/act/repo/experiment_config_loader.py
# 期望：无匹配

# 6. 关键符号存在性检查
grep -n "EXPERIMENT_CONFIG_NAME" src/model_deploy/act/repo/experiment_config_loader.py
grep -n "class ExperimentConfigLoadError" src/model_deploy/act/repo/experiment_config_loader.py
grep -n "def load_experiment_config" src/model_deploy/act/repo/experiment_config_loader.py
# 期望：三处均有匹配
```

## 4. PASS / FAIL / BLOCKED 判断标准

**PASS**（全部满足）：

- 命令 1 单元测试全部通过（全绿），且覆盖以下场景：
  - 正常 YAML 加载返回 dict。
  - experiment_config 中 state_dim/action_dim 原值保留、未被覆写或补默认值。
  - 文件不存在抛 `ExperimentConfigLoadError`。
  - 非法 YAML 抛 `ExperimentConfigLoadError`。
  - 根节点非 Mapping（列表/标量）抛 `ExperimentConfigLoadError`。
- 命令 2 `git status` 仅显示 conflict_scope 内两个文件。
- 命令 3 repo 层未向上引用 config/service/runtime/ui。
- 命令 4 未引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing。
- 命令 5 未硬编码 Pi0.5 的 26/14/224 维度默认值。
- 命令 6 三个关键符号（`EXPERIMENT_CONFIG_NAME`、`ExperimentConfigLoadError`、`load_experiment_config`）均存在。

**FAIL**（任一触发）：

- 单元测试存在失败用例。
- 单元测试未覆盖上述 5 类必备场景之一。
- `git status` 显示 conflict_scope 之外的改动。
- repo 层出现向上引用。
- 出现禁止逻辑或硬编码 Pi0.5 维度。
- 关键符号缺失。
- 加载器对维度字段做了覆写、归一化或补默认值。

**BLOCKED**（任一触发）：

- depends_on（deploy_001/002/003）未完成，无法执行。
- conflict_scope 内文件被其他并行 L3 占用且无法合并。
- `dispatch_status` 非 ready。
- 验收轮次已达上限 3 轮仍未通过。
- 环境缺失（pytest/yaml 不可用）且非本 L3 职责。

## 5. 本 L3 是否影响 L2 Gate

| L2 Gate 场景 | 是否影响 | 影响方式 | 本 L3 角色 |
|---|---|---|---|
| S4 normalizer 维度不一致失败 | 是（间接） | 本 L3 加载 experiment_config 的 state_dim/action_dim 原值，作为 S4 交叉校验的输入之一。config 层将 experiment_config 维度与 normalizers 维度、16D 契约对比。 | 数据提供方：只加载不校验。若本 L3 加载失败或维度被覆写，S4 将拿到错误输入。 |
| S3 bundle 缺文件失败 | 否 | S3 由 deploy_007 负责 bundle 目录检查。本 L3 假设 experiment_config.yaml 已存在（由 deploy_007 确认）。 | 不参与。 |
| 其他 L2 Gate 场景 | 否 | 本 L3 仅负责 experiment_config 加载。 | 不参与。 |

## 6. 验收结论写入位置

验收结论写入：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_006_验收日志.md`

日志须包含：

- 验收轮次与日期。
- 第 3 节六组命令的实际输出摘要。
- PASS / FAIL / BLOCKED 结论。
- 若 FAIL：失败用例与根因分析、下一轮修复计划。
- 若 BLOCKED：阻塞原因与所需协调动作。
- L2 Gate S4 贡献说明：本 L3 提供的 experiment_config 维度原值是否正确加载、是否可供 config 层交叉校验消费。
- 遗留问题（无则注明“无”）。

验收日志命名规则：`deploy_006_验收日志_roundN.md`（N 为轮次，1..3）。最终通过轮次的日志作为归档结论。

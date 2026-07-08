# 验收卡片：deploy_007 bundle 读取器

> [!info] 归属
> L2：l2-01-external-contract（外部参数加载与契约校验闭环）
> L1：ACT　阶段：阶段四：模型部署
> Wave：2　parallel_group：l2-01-external-contract-p2
> 验收模式：direct-local　真机风险：none
> 验收轮次上限：3　local_acceptance_required：true
> 关联 L2 Gate 场景：S3（bundle 缺文件失败）

## 1. 检查对象

| 项 | 内容 |
|---|---|
| L3 编号 | deploy_007 |
| L3 标题 | bundle 读取器 |
| 改造类型 | source-adaptation |
| 源文件 | `src/model_deploy/act/repo/bundle_reader.py` |
| 测试文件 | `src/model_deploy/act/tests/repo/test_bundle_reader.py` |
| 冲突模块 | `model_deploy.act.repo.bundle_reader` |
| conflict_scope files | `src/model_deploy/act/repo/bundle_reader.py`、`src/model_deploy/act/tests/repo/test_bundle_reader.py` |
| 验收场景 | S3 |
| 验收目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract` |
| 验收日志目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs` |

## 2. 验收模式

direct-local：在本地开发环境直接验收，不依赖真机部署与端到端集成。验收手段为单元测试执行 + conflict_scope 边界检查 + repo 层依赖方向检查 + 禁止逻辑检查 + 权重加载检查 + 维度硬编码检查。验收轮次上限 3 轮，必须 local_acceptance_required 通过。验收结论写入 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_007_验收日志.md`。

## 3. 必跑命令

```bash
cd /home/hit/ROS/worktrees/l2-01

# 1. 单元测试全绿
pytest src/model_deploy/act/tests/repo/test_bundle_reader.py -v

# 2. conflict_scope 边界检查（仅允许两个文件改动）
git status --porcelain
# 期望仅出现：
#   src/model_deploy/act/repo/bundle_reader.py
#   src/model_deploy/act/tests/repo/test_bundle_reader.py

# 3. repo 层未向上引用 config/service/runtime/ui
grep -rn "from model_deploy.act.config\|from model_deploy.act.service\|from model_deploy.act.runtime\|from model_deploy.act.ui" \
  src/model_deploy/act/repo/bundle_reader.py
# 期望：无匹配

# 4. 未引入禁止逻辑
grep -rn "blend_steps\|smoothstep\|cross_chunk\|rtc_alignment\|action_smoothing" \
  src/model_deploy/act/repo/bundle_reader.py
# 期望：无匹配

# 5. 未加载模型权重
grep -rn "import torch\|torch.load\|safetensors" \
  src/model_deploy/act/repo/bundle_reader.py
# 期望：无匹配

# 6. 未硬编码 Pi0.5 维度默认值
grep -rn "state_dim.*=.*26\|action_dim.*=.*14\|image_size.*=.*224\|max_action_dim.*=.*14" \
  src/model_deploy/act/repo/bundle_reader.py
# 期望：无匹配

# 7. 关键符号存在性检查
grep -n "BUNDLE_SCHEMA_VERSION" src/model_deploy/act/repo/bundle_reader.py
grep -n "def check_bundle_files" src/model_deploy/act/repo/bundle_reader.py
grep -n "def resolve_checkpoint_path" src/model_deploy/act/repo/bundle_reader.py
grep -n "def resolve_bundle_adapter_dir" src/model_deploy/act/repo/bundle_reader.py
# 期望：四处均有匹配
```

## 4. PASS / FAIL / BLOCKED 判断标准

**PASS**（全部满足）：

- 命令 1 单元测试全部通过（全绿），且覆盖以下场景：
  - 完整 bundle 目录，`check_bundle_files` 返回空列表。
  - 缺 manifest.json，返回列表含 `manifest.json`。
  - 缺 normalizers.json，返回列表含 `normalizers.json`。
  - 缺 experiment_config.yaml，返回列表含 `experiment_config.yaml`。
  - 缺 adapter 目录，返回列表含 `adapter`。
  - 缺多个文件，返回列表含全部缺失项。
  - bundle_dir 不存在抛 `BundleStructureError`。
  - `resolve_bundle_adapter_dir` 存在返回 Path、不存在抛 FileNotFoundError。
  - `resolve_checkpoint_path` 从 manifest 解析成功返回 Path。
  - `resolve_checkpoint_path` 目录扫描回退成功返回 Path。
  - `resolve_checkpoint_path` 不可解析抛 `BundleStructureError`。
- 命令 2 `git status` 仅显示 conflict_scope 内两个文件。
- 命令 3 repo 层未向上引用 config/service/runtime/ui。
- 命令 4 未引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing。
- 命令 5 未加载模型权重（未 import torch 加载权重、未读 safetensors）。
- 命令 6 未硬编码 Pi0.5 的 26/14/224 维度默认值。
- 命令 7 四个关键符号（`BUNDLE_SCHEMA_VERSION`、`check_bundle_files`、`resolve_checkpoint_path`、`resolve_bundle_adapter_dir`）均存在。

**FAIL**（任一触发）：

- 单元测试存在失败用例。
- 单元测试未覆盖上述 11 类必备场景之一。
- `git status` 显示 conflict_scope 之外的改动。
- repo 层出现向上引用。
- 出现禁止逻辑或加载模型权重。
- 出现硬编码 Pi0.5 维度。
- 关键符号缺失。
- `check_bundle_files` 对完整目录返回非空列表（误报）。
- `check_bundle_files` 对缺文件目录返回空列表（漏报）。
- `resolve_checkpoint_path` 解析了完整 manifest payload（越界 deploy_004 职责）。

**BLOCKED**（任一触发）：

- depends_on（deploy_001/002/003）未完成，无法执行。
- conflict_scope 内文件被其他并行 L3 占用且无法合并。
- `dispatch_status` 非 ready。
- 验收轮次已达上限 3 轮仍未通过。
- 环境缺失（pytest 不可用）且非本 L3 职责。
- 与 deploy_004 的 manifest 职责边界发生冲突，需 L2 仲裁。

## 5. 本 L3 是否影响 L2 Gate

| L2 Gate 场景 | 是否影响 | 影响方式 | 本 L3 角色 |
|---|---|---|---|
| S3 bundle 缺文件失败 | 是（直接） | 本 L3 的 `check_bundle_files` 是 S3 的直接实现载体。返回非空缺失列表即触发 S3 失败，L2 无需进入后续解析（deploy_004/005/006）。 | 实现方：S3 的唯一数据来源。若本 L3 误报或漏报，S3 判断将错误。 |
| S4 normalizer 维度不一致失败 | 否（间接） | S4 依赖 deploy_005/006 的解析结果。本 L3 只保证 normalizers.json/experiment_config.yaml 存在，不解析内容。 | 前置守门：确保 S4 的输入文件存在。 |
| 其他 L2 Gate 场景 | 否 | 本 L3 仅负责 bundle 目录结构检查与 checkpoint 路径解析。 | 不参与。 |

## 6. 验收结论写入位置

验收结论写入：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_007_验收日志.md`

日志须包含：

- 验收轮次与日期。
- 第 3 节七组命令的实际输出摘要。
- PASS / FAIL / BLOCKED 结论。
- 若 FAIL：失败用例与根因分析、下一轮修复计划。
- 若 BLOCKED：阻塞原因与所需协调动作。
- L2 Gate S3 贡献说明：`check_bundle_files` 在完整目录与缺文件目录下的返回是否符合预期、是否可作为 S3 判断依据。
- 与 deploy_004 职责边界说明：`resolve_checkpoint_path` 是否仅读取 manifest 中 checkpoint 路径字段、是否未解析完整 payload。
- 遗留问题（无则注明“无”）。

验收日志命名规则：`deploy_007_验收日志_roundN.md`（N 为轮次，1..3）。最终通过轮次的日志作为归档结论。

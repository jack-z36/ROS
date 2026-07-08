# L3 微元改造任务：deploy_004 manifest 解析器

## 1. 任务定位

- 阶段：阶段四 模型部署
- L1：ACT 功能模块
- 所属 L2：l2-01-external-contract（外部参数加载与契约校验闭环）
- L3 编号：deploy_004
- 改造类型：source-adaptation
- 当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_004_manifest解析器.md`
- 验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_004_验收卡片.md`
- 验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs`
- 验收模式：direct-local
- 辅助验收模式：[]
- 本地验收是否必须：true
- 真机风险等级：none
- Wave：2
- parallel_group：l2-01-external-contract-p2
- L2 分支：`feat/model_deploy/l2-01-external-contract`
- 集成分支：`model_deploy`
- depends_on：`[deploy_001, deploy_002, deploy_003]`
- can_run_parallel_with：`[deploy_004, deploy_005, deploy_006, deploy_007]`

路径约定：本任务所有路径均相对于仓库根目录。源码产物落点为 `src/model_deploy/act/repo/manifest_parser.py`，测试产物落点为 `src/model_deploy/act/tests/repo/test_manifest_parser.py`。验收产物落点为 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/`。Pi0.5 参考源码为只读引用，不得修改。

> [!warning] 产物落点约束
> 本 L3 仅允许在 repo 层产出 `manifest_parser.py` 及其测试。不得在 types/config/service/runtime/ui 层创建或修改任何文件。不得修改 Pi0.5 参考源码（`DOCS/03_工程/阶段四：模型部署/pi05_old/` 下的所有文件均为只读）。本 L3 只做文件读取与 JSON 解析，不做维度业务校验。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_004
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_004_manifest解析器.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_004_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 2
  parallel_group: l2-01-external-contract-p2
  depends_on: [deploy_001, deploy_002, deploy_003]
  must_run_after: []
  can_run_parallel_with: [deploy_005, deploy_006, deploy_007]
  blocks: []
  conflict_scope:
    files: [src/model_deploy/act/repo/manifest_parser.py, src/model_deploy/act/tests/repo/test_manifest_parser.py]
    modules: [model_deploy.act.repo.manifest_parser]
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

本 L3 由单 Agent 执行，执行边界限定于 `manifest_parser.py` 的文件读取与 JSON 解析逻辑。验收边界为本地 pytest 直接执行，不依赖真机环境。Agent 不得越界修改 config/service/runtime/ui 层代码。维度业务校验（如 dim==16、字段完备性）不在本 L3 范围内，归 config 层负责。

## 3. 本次唯一目标

```text
读取 manifest.json 文件并解析为 dict 返回，遇到坏 JSON 或缺文件时抛出对应异常；只做纯文件读取与 JSON 反序列化，不做任何维度业务校验。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

l2-01-external-contract 负责外部参数（manifest.json、normalizers.json、experiment_config.yaml、adapter 权重）的加载与契约校验闭环。L2 覆盖 bundle 目录读取、文件缺失检测、格式解析、反序列化构造对象，以及后续 config 层的维度/字段契约校验。

### L2 不负责

L2 不负责模型推理执行、策略调度、action 平滑（blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing）、真机控制循环、训练侧 bundle 导出（Pi0.5 的 `export_deploy_bundle` 不在 ACT 部署范围内）。

### 本 L3 在 L2 中的位置

deploy_004 是 L2 参数加载链的入口节点，位于 repo 层最底层。manifest.json 是 bundle 的总清单文件，其解析结果是后续 normalizer 加载（deploy_005）、adapter 目录解析（deploy_006）等环节的依赖前提。本 L3 仅完成「读文件 → 解析 JSON → 返回 dict」这一纯 I/O+反序列化微元。

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/01_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/02_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/01_L2功能边界.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/02_pi05源码3.5层微元拆解.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/03_ACT微元设计与协作.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 所在文件 | 类型 | 启发用途 |
|---|---|---|---|
| `MANIFEST_NAME = "manifest.json"` | `pi05/common/runtime/bundle.py` | 常量 | 文件名约定，ACT 侧可定义同名常量 |
| `load_bundle_manifest(bundle_dir) -> dict[str, Any]` | `pi05/common/runtime/bundle.py` | 函数 | 读取 manifest.json 并返回解析后 dict |
| `BUNDLE_SCHEMA_VERSION = 1` | `pi05/common/runtime/bundle.py` | 常量 | schema 版本参考，非本 L3 校验对象 |

### 必须保留的源码启发

- `load_bundle_manifest` 的核心行为：接受 bundle 目录路径 → 拼接 manifest 文件全路径 → 读取文件内容 → `json.loads` 解析 → 返回 dict。这一「目录入参 + 固定文件名 + json 解析」的三段式结构必须保留。
- `MANIFEST_NAME` 作为模块级常量定义文件名的做法应保留。

### 禁止照搬的源码行为

- 禁止照搬 Pi0.5 任何与维度相关的硬编码（26D/14D 等），ACT 不使用 Pi0.5 的维度数值。
- 禁止在本 L3 中实现 `export_deploy_bundle`（训练侧导出逻辑），ACT 部署侧不实现此功能。
- 禁止在本 L3 中对 manifest dict 做 schema 版本校验、字段完备性校验、维度校验——这些都归 config 层契约校验。

### 已知风险

- manifest.json 可能包含恶意或超大内容，但本 L3 范围内不设限（防护由上层或运维负责）。
- manifest.json 文件编码假设为 UTF-8，若 bundle 产出端编码异常可能导致解码失败，此时应让异常自然抛出。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 定义 `MANIFEST_NAME = "manifest.json"` 常量。
- 实现 `load_bundle_manifest(bundle_dir) -> dict[str, Any]`：接受 `Path` 或 `str` 类型的 bundle 目录，拼接 manifest 全路径，读取文件，`json.loads` 解析，返回 dict。
- 文件不存在时抛出 `FileNotFoundError`（Python 标准异常）。
- JSON 格式损坏时抛出 `json.JSONDecodeError`（由 `json.loads` 自然产生）。
- 编写单元测试覆盖正常路径、缺文件、坏 JSON 三种场景。

### 本次不做

- 不做 manifest 字段完备性校验（如是否含 schema_version 等字段）。
- 不做维度业务校验（dim 数值检查归 config 层）。
- 不做 schema 版本校验。
- 不做 bundle 目录整体完整性校验（多文件联合检查）。
- 不做任何与 adapter / normalizers / experiment_config 相关的加载（各有独立 L3）。

### 明确禁止修改

- 禁止修改 Pi0.5 参考源码目录 `DOCS/03_工程/阶段四：模型部署/pi05_old/` 下任何文件。
- 禁止修改 types/config/service/runtime/ui 层任何文件。
- 禁止引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing 相关逻辑。
- 禁止引入 Pi0.5 的 26D/14D 维度常量。

### 函数 / class 策略

本 L3 实现为纯函数模块，不引入 class。核心函数 `load_bundle_manifest` 为无状态函数，模块级常量 `MANIFEST_NAME`。依赖方向：repo 层仅可依赖 types 层（若需类型定义），不得依赖 config/service/runtime/ui 层。本 L3 实际上不依赖 types 层，仅使用 Python 标准库 `json` 和 `pathlib`。

## 7. 六层产物落点

| 层 | 产物路径 | 说明 |
|---|---|---|
| types | — | 本 L3 不产出 |
| repo | `src/model_deploy/act/repo/manifest_parser.py` | manifest 解析器实现 |
| repo | `src/model_deploy/act/tests/repo/test_manifest_parser.py` | 对应测试 |
| config | — | 本 L3 不产出 |
| service | — | 本 L3 不产出 |
| runtime | — | 本 L3 不产出 |
| ui | — | 本 L3 不产出 |

### 对应六层设计文档

- repo 层设计：`DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`
- 六层总体架构：`DOCS/03_工程/阶段四：模型部署/02_implement/02_L1_ACT功能模块协作架构.md`

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `manifest_parser.py` | `MANIFEST_NAME` | 常量 | — | `"manifest.json"` | 否 | 间接覆盖 |
| `manifest_parser.py` | `load_bundle_manifest` | 函数 | `bundle_dir: Path` | `dict[str, Any]` | 是（读文件系统） | 正常路径用例 |
| `test_manifest_parser.py` | 缺文件场景 | 测试 | 不存在的目录 | 抛 `FileNotFoundError` | 否 | S3 场景覆盖 |
| `test_manifest_parser.py` | 坏 JSON 场景 | 测试 | 损坏的 manifest.json | 抛 `json.JSONDecodeError` | 否 | S3 场景覆盖 |
| `test_manifest_parser.py` | 正常解析场景 | 测试 | 合法 manifest.json | 返回 dict | 否 | 正常路径覆盖 |

## 9. 实施步骤

1. 确认当前分支为 `feat/model_deploy/l2-01-external-contract`，若否则切换。
2. 创建源码文件 `src/model_deploy/act/repo/manifest_parser.py`。
3. 定义模块级常量 `MANIFEST_NAME = "manifest.json"`。
4. 实现 `load_bundle_manifest(bundle_dir)`：拼接 `Path(bundle_dir) / MANIFEST_NAME`，读取文件文本，`json.loads` 解析返回。
5. 文件不存在时让 `Path.read_text` 自然抛出 `FileNotFoundError`（或在拼接后显式检查并抛出，保持行为一致）。
6. JSON 损坏时让 `json.loads` 自然抛出 `json.JSONDecodeError`，不捕获包装。
7. 创建测试文件 `src/model_deploy/act/tests/repo/test_manifest_parser.py`。
8. 编写正常路径用例：使用 `tmp_path` 写入合法 manifest.json，调用函数，断言返回 dict 内容与写入一致。
9. 编写缺文件用例：传入空 `tmp_path` 目录，断言抛出 `FileNotFoundError`。
10. 编写坏 JSON 用例：写入非 JSON 文本，断言抛出 `json.JSONDecodeError`。
11. 运行 pytest 确认全部通过。
12. 确认未引入任何维度常量或上层依赖。

## 10. 允许修改

> [!warning] 产物落点声明
> 本 L3 仅允许修改以下文件。任何超出此范围的修改（包括但不限于 types/config/service/runtime/ui 层文件、Pi0.5 参考源码、其他 L3 的产物）均视为越界。

- 新建 `src/model_deploy/act/repo/manifest_parser.py`（若目录不存在则创建目录）。
- 新建 `src/model_deploy/act/tests/repo/test_manifest_parser.py`（若目录不存在则创建目录）。
- 必要时创建 `src/model_deploy/act/repo/__init__.py` 和 `src/model_deploy/act/tests/repo/__init__.py`（若尚不存在且项目需要）。

### 本次产物落点

| 文件 | 操作 | 层 | 是否新建 |
|---|---|---|---|
| `src/model_deploy/act/repo/manifest_parser.py` | 新建 | repo | 是 |
| `src/model_deploy/act/tests/repo/test_manifest_parser.py` | 新建 | repo(test) | 是 |

## 11. 禁止修改

- 禁止修改 types/config/service/runtime/ui 层任何已有文件。
- 禁止修改 Pi0.5 参考源码 `DOCS/03_工程/阶段四：模型部署/pi05_old/` 下任何文件。
- 禁止修改其他 L3（deploy_001/002/003/005/006/007/008/009...）的产物文件。
- 禁止修改任何验收卡片、验收日志、L2 设计文档。
- 禁止在 manifest_parser.py 中引入维度校验、schema 校验、字段完备性校验逻辑。
- 禁止引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing。
- 禁止引入 Pi0.5 26D/14D 维度常量。

## 12. 验证方式

### 自动化验收命令

```bash
cd /home/hit/ROS/worktrees/l2-01
python -m pytest src/model_deploy/act/tests/repo/test_manifest_parser.py -v
```

### 分层验证

| 验证项 | 方法 | 预期结果 |
|---|---|---|
| 正常解析 | pytest 正常路径用例 | 返回 dict 内容正确 |
| 缺文件 | pytest 缺文件用例 | 抛出 `FileNotFoundError` |
| 坏 JSON | pytest 坏 JSON 用例 | 抛出 `json.JSONDecodeError` |
| 无上层依赖 | 静态检查 import 语句 | 不出现 config/service/runtime/ui 导入 |
| 无维度硬编码 | 静态检查源码 | 不出现 26/14 等维度数值 |

### 真机风险控制

本 L3 真机风险等级为 none。产物为纯文件读取与 JSON 解析，不涉及任何硬件 I/O、模型推理或控制输出，无需真机验证。

### 验收证据落点

- pytest 输出保存至 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_004_round_N.txt`（N 为轮次编号，1-3）。
- 验收结论写入 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/deploy_004_验收结论.md`。

### L2 Gate 贡献

| L2 Gate | 场景 | 本 L3 贡献 | 贡献方式 |
|---|---|---|---|
| S3 | bundle 缺文件失败 | 核心支撑 | manifest 缺文件时抛出 `FileNotFoundError`，使 S3 场景可被上层捕获 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/01_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/02_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/01_L2功能边界.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/03_ACT微元设计与协作.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`
6. `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_004_验收卡片.md`

### 必读代码（只读引用）

- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/runtime/bundle.py`（参考 `load_bundle_manifest` 和 `MANIFEST_NAME`）

### 必读约束文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/02_L1_ACT功能模块协作架构.md`

### 相关历史任务

- deploy_001（types 层类型定义，本 L3 依赖）
- deploy_002（types 层契约类型，本 L3 依赖）
- deploy_003（types 层基础设施，本 L3 依赖）

## 14. 执行要求

```text
身份校验：执行 Agent 必须确认 task_id == deploy_004，l2_id == l2-01-external-contract，
phase == 阶段四_模型部署，acceptance_mode == direct-local。任一不匹配则终止执行并报告。
```

dispatch 校验：

- [ ] 确认 dispatch_status == ready
- [ ] 确认 depends_on [deploy_001, deploy_002, deploy_003] 均已完成
- [ ] 确认当前分支 == feat/model_deploy/l2-01-external-contract
- [ ] 确认 conflict_scope 文件未被其他 L3 占用

全文检查：

- [ ] manifest_parser.py 中无 config/service/runtime/ui 层 import
- [ ] 源码中无 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing
- [ ] 源码中无 26/14 维度硬编码
- [ ] 源码中无 schema 版本校验或维度业务校验
- [ ] 源码中无 export_deploy_bundle 相关逻辑

测试优先：

本 L3 遵循 TDD 原则。建议先编写 `test_manifest_parser.py` 的三个用例（正常/缺文件/坏 JSON），再实现 `manifest_parser.py` 使其通过。若已有实现可跳过此步骤但必须确保三个用例全部覆盖。

## 15. 成功标准

- [ ] `src/model_deploy/act/repo/manifest_parser.py` 已创建
- [ ] `src/model_deploy/act/tests/repo/test_manifest_parser.py` 已创建
- [ ] `MANIFEST_NAME = "manifest.json"` 常量已定义
- [ ] `load_bundle_manifest(bundle_dir)` 函数已实现
- [ ] 正常路径用例通过（返回 dict 内容正确）
- [ ] 缺文件用例通过（抛出 `FileNotFoundError`）
- [ ] 坏 JSON 用例通过（抛出 `json.JSONDecodeError`）
- [ ] 无 config/service/runtime/ui 层 import
- [ ] 无维度硬编码（26/14）
- [ ] 无 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing
- [ ] pytest 全部通过且无 warning
- [ ] 未修改任何越界文件

## 16. 回滚方式

```text
回滚步骤：
1. 删除 src/model_deploy/act/repo/manifest_parser.py
2. 删除 src/model_deploy/act/tests/repo/test_manifest_parser.py
3. 若 __init__.py 仅为本 L3 新建且无其他内容，则一并删除
4. git checkout 对应文件（若已提交）
5. 确认工作区恢复到 deploy_004 执行前状态
6. 在验收日志中记录回滚原因
本 L3 无数据迁移、无配置变更、无硬件交互，回滚无副作用。
```

## 17. 完成后交接

本 L3 完成后，`load_bundle_manifest` 函数可供 L2 内下游 L3（如 manifest 字段契约校验、bundle 完整性检查）及 service 层调用。交接时需确认：
1. pytest 全绿且证据已落盘至验收日志目录。
2. 验收结论已写入 `deploy_004_验收结论.md`。
3. 函数签名 `load_bundle_manifest(bundle_dir: Path) -> dict[str, Any]` 稳定可供上层依赖。
4. 已通知 L2 调度器 deploy_004 状态为 completed。
5. 下游依赖方（deploy_005 normalizer 加载器、后续 manifest 字段校验 L3）可基于本函数返回值继续工作。

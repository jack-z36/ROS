# L3 微元改造任务：deploy_005 normalizer 加载器

## 1. 任务定位

- 阶段：阶段四 模型部署
- L1：ACT 功能模块
- 所属 L2：l2-01-external-contract（外部参数加载与契约校验闭环）
- L3 编号：deploy_005
- 改造类型：source-adaptation
- 当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_005_normalizer加载器.md`
- 验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_005_验收卡片.md`
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

路径约定：本任务所有路径均相对于仓库根目录。源码产物落点为 `src/model_deploy/act/repo/normalizer_loader.py`，测试产物落点为 `src/model_deploy/act/tests/repo/test_normalizer_loader.py`。验收产物落点为 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/`。Pi0.5 参考源码为只读引用，不得修改。

> [!warning] 产物落点约束
> 本 L3 仅允许在 repo 层产出 `normalizer_loader.py` 及其测试。不得在 types/config/service/runtime/ui 层创建或修改任何文件。不得修改 Pi0.5 参考源码（`DOCS/03_工程/阶段四：模型部署/pi05_old/` 下的所有文件均为只读）。本 L3 只做 normalizers.json 反序列化与 `ActionStateNormalizer` 对象构造，不做维度业务校验（dim==16 等检查归 deploy_009 config 层 `check_normalizer_contract`）。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_005
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_005_normalizer加载器.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S4]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_005_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 2
  parallel_group: l2-01-external-contract-p2
  depends_on: [deploy_001, deploy_002, deploy_003]
  must_run_after: []
  can_run_parallel_with: [deploy_004, deploy_006, deploy_007]
  blocks: []
  conflict_scope:
    files: [src/model_deploy/act/repo/normalizer_loader.py, src/model_deploy/act/tests/repo/test_normalizer_loader.py]
    modules: [model_deploy.act.repo.normalizer_loader]
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

本 L3 由单 Agent 执行，执行边界限定于 `normalizer_loader.py` 的 normalizers.json 读取、反序列化与 `ActionStateNormalizer` 对象构造。验收边界为本地 pytest 直接执行，不依赖真机环境。Agent 不得越界修改 config/service/runtime/ui 层代码。维度业务校验（如 dim==16、state 与 action 维度一致性）不在本 L3 范围内，归 deploy_009 config 层 `check_normalizer_contract` 负责。

## 3. 本次唯一目标

```text
读取 normalizers.json 并反序列化为 (state_normalizer, action_normalizer) 元组返回，通过 payload["state"] 和 payload["action"] 构造两个 ActionStateNormalizer 对象；只做反序列化与对象构造，不做维度业务校验。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

l2-01-external-contract 负责外部参数（manifest.json、normalizers.json、experiment_config.yaml、adapter 权重）的加载与契约校验闭环。L2 覆盖 bundle 目录读取、文件缺失检测、格式解析、反序列化构造对象，以及后续 config 层的维度/字段契约校验。

### L2 不负责

L2 不负责模型推理执行、策略调度、action 平滑（blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing）、真机控制循环、训练侧 bundle 导出（Pi0.5 的 `export_deploy_bundle` 不在 ACT 部署范围内）。

### 本 L3 在 L2 中的位置

deploy_005 是 L2 参数加载链中 normalizer 反序列化节点，位于 repo 层。normalizers.json 包含 state 和 action 两组归一化参数，本 L3 将其反序列化为两个 `ActionStateNormalizer` 对象。构造出的对象随后被 config 层 deploy_009 `check_normalizer_contract` 做维度契约校验，再供 service 层推理使用。本 L3 仅完成「读文件 → 解析 JSON → 构造对象」这一纯反序列化微元，不参与校验。

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
| `NORMALIZERS_NAME = "normalizers.json"` | `pi05/common/runtime/bundle.py` | 常量 | 文件名约定 |
| `load_bundle_normalizers(bundle_dir) -> tuple[ActionStateNormalizer, ActionStateNormalizer]` | `pi05/common/runtime/bundle.py` | 函数 | 读取 normalizers.json → 构造两个 normalizer 对象 |
| `ActionStateNormalizer` | `pi05/common/data/normalization.py` | class | normalizer 对象结构来源 |
| `ActionStateNormalizer.__init__(min_vals, max_vals, identity_indices=None)` | `pi05/common/data/normalization.py` | 构造函数 | 反序列化构造入口 |
| `ActionStateNormalizer` 字段: `min_vals/max_vals/range_vals/identity_mask/vector_dim` | `pi05/common/data/normalization.py` | 实例属性 | 对象内部结构，必须保留 |
| `ActionStateNormalizer` 方法: `normalize(data)/unnormalize(norm_data)` | `pi05/common/data/normalization.py` | 方法 | 归一化/反归一化逻辑，必须保留 |

### 必须保留的源码启发

- `load_bundle_normalizers` 的核心行为：读取 normalizers.json → `json.loads` 解析为 payload → 从 `payload["state"]` 和 `payload["action"]` 各取一组参数 → 用 `min`、`max`、`identity_indices` 三个键构造两个 `ActionStateNormalizer` → 返回 `(state_normalizer, action_normalizer)` 元组。这一「payload 双段拆分 + 三键构造」结构必须保留。
- `ActionStateNormalizer` 的对象结构（`min_vals`/`max_vals`/`range_vals`/`identity_mask`/`vector_dim` 字段，`normalize`/`unnormalize` 方法）必须完整保留——本 L3 负责构造此对象，对象本身的内部计算逻辑（如 `range_vals = max - min`、`identity_mask` 掩码生成）应随 class 一并迁移保留。
- `NORMALIZERS_NAME` 作为模块级常量定义文件名的做法应保留。
- 构造函数参数名 `min_vals`、`max_vals`、`identity_indices` 及 JSON 对应键名 `min`、`max`、`identity_indices` 的映射关系必须保留。

### 禁止照搬的源码行为

- 禁止照搬 Pi0.5 任何与维度相关的硬编码（26D/14D 等），ACT 不使用 Pi0.5 的维度数值。
- 禁止在本 L3 中对构造出的 normalizer 做维度校验（如断言 vector_dim==16 或 state/action 维度一致），这些归 deploy_009 config 层。
- 禁止在本 L3 中实现 `export_deploy_bundle`（训练侧导出逻辑），ACT 部署侧不实现此功能。
- 禁止在本 L3 中对 normalizers.json 做 schema 版本校验或字段完备性校验（归 config 层）。

### 已知风险

- normalizers.json 中 `min`/`max` 列表长度可能不一致，但本 L3 不校验长度（交给 `ActionStateNormalizer` 构造时的 numpy 操作自然处理或 config 层校验）。
- `identity_indices` 可能为 None 或缺失，需保持与 Pi0.5 构造函数相同的默认行为（`identity_indices=None`）。
- 若 `ActionStateNormalizer` class 尚未在 ACT types/repo 层定义，需确认其落点（应在 repo 层或 types 层定义，本 L3 引用之；若需在本 L3 内迁移该 class 定义，需在产物落点声明中注明）。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 定义 `NORMALIZERS_NAME = "normalizers.json"` 常量。
- 实现 `load_bundle_normalizers(bundle_dir) -> tuple[ActionStateNormalizer, ActionStateNormalizer]`：读取文件 → 解析 JSON → 从 `payload["state"]`/`payload["action"]` 提取 `min`/`max`/`identity_indices` → 构造两个 `ActionStateNormalizer` → 返回元组。
- 确保 `ActionStateNormalizer` class 结构完整保留：字段 `min_vals`/`max_vals`/`range_vals`/`identity_mask`/`vector_dim`，方法 `normalize(data)`/`unnormalize(norm_data)`。
- 文件不存在时抛出 `FileNotFoundError`。
- JSON 格式损坏时抛出 `json.JSONDecodeError`。
- payload 缺少 `state`/`action` 键时抛出 `KeyError`。
- 编写单元测试覆盖正常构造、缺文件、坏 JSON、缺键四种场景。

### 本次不做

- 不做 normalizer 维度校验（如 dim==16、state 与 action 维度一致性检查）——归 deploy_009 config 层 `check_normalizer_contract`。
- 不做 normalizers.json schema 版本校验。
- 不做 normalizer 数值范围合理性校验（如 min<max 检查）。
- 不做 manifest.json 或 experiment_config.yaml 加载（各有独立 L3）。
- 不做 adapter 权重加载。

### 明确禁止修改

- 禁止修改 Pi0.5 参考源码目录 `DOCS/03_工程/阶段四：模型部署/pi05_old/` 下任何文件。
- 禁止修改 config/service/runtime/ui 层任何文件。
- 禁止在 normalizer_loader 中引入任何维度断言或维度常量（26/14/16 等）。
- 禁止引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing 相关逻辑。
- 禁止修改 `ActionStateNormalizer` 的公开接口（构造函数签名、字段名、方法名必须与 Pi0.5 保持一致）。

### 函数 / class 策略

本 L3 实现为纯函数模块。`load_bundle_normalizers` 为无状态函数。`ActionStateNormalizer` class 的落点需遵循 repo 层设计文档约定：若 repo 层设计指定其归 types 层，则本 L3 从 types 层 import；若 repo 层设计指定其归 repo 层（如 repo 层自身的 data 子模块），则本 L3 可在同层定义或引用。依赖方向：repo 层仅可依赖 types 层，不得依赖 config/service/runtime/ui 层。本 L3 主要使用 Python 标准库 `json`、`pathlib` 以及 `numpy`（normalizer 内部数值运算）。

## 7. 六层产物落点

| 层 | 产物路径 | 说明 |
|---|---|---|
| types | — | 本 L3 不产出（若 ActionStateNormalizer 归 types 层则由 deploy_001/002 提供） |
| repo | `src/model_deploy/act/repo/normalizer_loader.py` | normalizer 加载器实现 |
| repo | `src/model_deploy/act/tests/repo/test_normalizer_loader.py` | 对应测试 |
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
| `normalizer_loader.py` | `NORMALIZERS_NAME` | 常量 | — | `"normalizers.json"` | 否 | 间接覆盖 |
| `normalizer_loader.py` | `load_bundle_normalizers` | 函数 | `bundle_dir: Path` | `tuple[ActionStateNormalizer, ActionStateNormalizer]` | 是（读文件系统） | 正常路径用例 |
| `normalizer_loader.py` | `ActionStateNormalizer`（若 repo 层定义） | class | `min_vals, max_vals, identity_indices=None` | normalizer 对象 | 否 | 结构保留覆盖 |
| `test_normalizer_loader.py` | 正常构造场景 | 测试 | 合法 normalizers.json | 返回 (state, action) 元组 | 否 | 正常路径覆盖 |
| `test_normalizer_loader.py` | 缺文件场景 | 测试 | 不存在的目录 | 抛 `FileNotFoundError` | 否 | S4 关联覆盖 |
| `test_normalizer_loader.py` | 坏 JSON 场景 | 测试 | 损坏的 normalizers.json | 抛 `json.JSONDecodeError` | 否 | S4 关联覆盖 |
| `test_normalizer_loader.py` | 缺键场景 | 测试 | 缺少 state/action 键 | 抛 `KeyError` | 否 | S4 关联覆盖 |

## 9. 实施步骤

1. 确认当前分支为 `feat/model_deploy/l2-01-external-contract`，若否则切换。
2. 确认 `ActionStateNormalizer` 的落点（types 层或 repo 层），依据 repo 层设计文档 08_repo层设计.md。
3. 若 `ActionStateNormalizer` 尚未定义，则在 repo 层（或按设计文档指定层）创建，完整保留 Pi0.5 结构：构造函数 `(min_vals, max_vals, identity_indices=None)`，字段 `min_vals/max_vals/range_vals/identity_mask/vector_dim`，方法 `normalize(data)/unnormalize(norm_data)`，内部 `range_vals = max_vals - min_vals`、`identity_mask` 生成逻辑一并保留。
4. 创建源码文件 `src/model_deploy/act/repo/normalizer_loader.py`。
5. 定义模块级常量 `NORMALIZERS_NAME = "normalizers.json"`。
6. 实现 `load_bundle_normalizers(bundle_dir)`：拼接文件全路径 → 读取文本 → `json.loads` 解析 payload → 从 `payload["state"]` 取 `min`/`max`/`identity_indices` 构造 state_normalizer → 从 `payload["action"]` 同法构造 action_normalizer → 返回 `(state_normalizer, action_normalizer)`。
7. 文件不存在时抛出 `FileNotFoundError`，JSON 损坏时抛出 `json.JSONDecodeError`，缺 `state`/`action` 键时抛出 `KeyError`（均不捕获包装）。
8. 创建测试文件 `src/model_deploy/act/tests/repo/test_normalizer_loader.py`。
9. 编写正常构造用例：使用 `tmp_path` 写入合法 normalizers.json（含 state/action 两段，各含 min/max/identity_indices），调用函数，断言返回元组长度为 2，两个对象类型正确，字段值与输入一致。
10. 编写缺文件用例：传入空 `tmp_path` 目录，断言抛出 `FileNotFoundError`。
11. 编写坏 JSON 用例：写入非 JSON 文本，断言抛出 `json.JSONDecodeError`。
12. 编写缺键用例：写入缺少 `state` 或 `action` 键的 JSON，断言抛出 `KeyError`。
13. 运行 pytest 确认全部通过。
14. 确认未引入任何维度常量、维度断言或上层依赖。

## 10. 允许修改

> [!warning] 产物落点声明
> 本 L3 仅允许修改以下文件。任何超出此范围的修改（包括但不限于 types/config/service/runtime/ui 层文件、Pi0.5 参考源码、其他 L3 的产物）均视为越界。

- 新建 `src/model_deploy/act/repo/normalizer_loader.py`（若目录不存在则创建目录）。
- 新建 `src/model_deploy/act/tests/repo/test_normalizer_loader.py`（若目录不存在则创建目录）。
- 若 repo 层设计文档指定 `ActionStateNormalizer` 归 repo 层且尚未定义，则在本 L3 同层创建其定义文件（如 `src/model_deploy/act/repo/normalization.py`），完整保留 Pi0.5 结构。
- 必要时创建 `src/model_deploy/act/repo/__init__.py` 和 `src/model_deploy/act/tests/repo/__init__.py`（若尚不存在且项目需要）。

### 本次产物落点

| 文件 | 操作 | 层 | 是否新建 |
|---|---|---|---|
| `src/model_deploy/act/repo/normalizer_loader.py` | 新建 | repo | 是 |
| `src/model_deploy/act/tests/repo/test_normalizer_loader.py` | 新建 | repo(test) | 是 |
| `src/model_deploy/act/repo/normalization.py`（条件性） | 新建（若 ActionStateNormalizer 归 repo 层且未定义） | repo | 条件性 |

## 11. 禁止修改

- 禁止修改 types/config/service/runtime/ui 层任何已有文件（若 ActionStateNormalizer 归 types 层，则只读引用不修改）。
- 禁止修改 Pi0.5 参考源码 `DOCS/03_工程/阶段四：模型部署/pi05_old/` 下任何文件。
- 禁止修改其他 L3（deploy_001/002/003/004/006/007/008/009...）的产物文件。
- 禁止修改任何验收卡片、验收日志、L2 设计文档。
- 禁止在 normalizer_loader 中引入维度校验、维度断言（dim==16 等）或维度常量。
- 禁止修改 `ActionStateNormalizer` 的公开接口（构造函数签名、字段名、方法名）。
- 禁止引入 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing。
- 禁止引入 Pi0.5 26D/14D 维度常量。

## 12. 验证方式

### 自动化验收命令

```bash
cd /home/hit/ROS/worktrees/l2-01
python -m pytest src/model_deploy/act/tests/repo/test_normalizer_loader.py -v
```

### 分层验证

| 验证项 | 方法 | 预期结果 |
|---|---|---|
| 正常构造 | pytest 正常路径用例 | 返回 (state_normalizer, action_normalizer) 元组，字段正确 |
| 缺文件 | pytest 缺文件用例 | 抛出 `FileNotFoundError` |
| 坏 JSON | pytest 坏 JSON 用例 | 抛出 `json.JSONDecodeError` |
| 缺键 | pytest 缺键用例 | 抛出 `KeyError` |
| ActionStateNormalizer 结构 | 对返回对象做字段检查 | 含 min_vals/max_vals/range_vals/identity_mask/vector_dim，normalize/unnormalize 可调用 |
| 无上层依赖 | 静态检查 import 语句 | 不出现 config/service/runtime/ui 导入 |
| 无维度硬编码 | 静态检查源码 | 不出现 26/14/16 等维度数值或断言 |

### 真机风险控制

本 L3 真机风险等级为 none。产物为纯文件读取、JSON 反序列化与对象构造，不涉及任何硬件 I/O、模型推理或控制输出，无需真机验证。

### 验收证据落点

- pytest 输出保存至 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_005_round_N.txt`（N 为轮次编号，1-3）。
- 验收结论写入 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/deploy_005_验收结论.md`。

### L2 Gate 贡献

| L2 Gate | 场景 | 本 L3 贡献 | 贡献方式 |
|---|---|---|---|
| S4 | normalizer 维度不一致失败 | 间接支撑（提供可校验对象） | 本 L3 只负责加载构造 normalizer 对象，不做维度校验；维度校验由 deploy_009 config 层 `check_normalizer_contract` 完成，S4 场景的维度一致性判断依赖本 L3 提供的 normalizer 对象 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/01_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/02_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/01_L2功能边界.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/03_ACT微元设计与协作.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`
6. `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_005_验收卡片.md`

### 必读代码（只读引用）

- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/runtime/bundle.py`（参考 `load_bundle_normalizers` 和 `NORMALIZERS_NAME`）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/data/normalization.py`（参考 `ActionStateNormalizer` class 定义、字段、方法）

### 必读约束文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/08_repo层设计.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/02_L1_ACT功能模块协作架构.md`

### 相关历史任务

- deploy_001（types 层类型定义，本 L3 依赖）
- deploy_002（types 层契约类型，本 L3 依赖）
- deploy_003（types 层基础设施，本 L3 依赖）
- deploy_004（manifest 解析器，同 Wave 2 并行，可参考其文件读取模式）
- deploy_009（config 层 `check_normalizer_contract`，下游维度校验消费者）

## 14. 执行要求

```text
身份校验：执行 Agent 必须确认 task_id == deploy_005，l2_id == l2-01-external-contract，
phase == 阶段四_模型部署，acceptance_mode == direct-local。任一不匹配则终止执行并报告。
```

dispatch 校验：

- [ ] 确认 dispatch_status == ready
- [ ] 确认 depends_on [deploy_001, deploy_002, deploy_003] 均已完成
- [ ] 确认当前分支 == feat/model_deploy/l2-01-external-contract
- [ ] 确认 conflict_scope 文件未被其他 L3 占用

全文检查：

- [ ] normalizer_loader.py 中无 config/service/runtime/ui 层 import
- [ ] 源码中无 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing
- [ ] 源码中无 26/14/16 维度硬编码或维度断言
- [ ] 源码中无 schema 版本校验或维度业务校验（只反序列化构造）
- [ ] 源码中无 export_deploy_bundle 相关逻辑
- [ ] ActionStateNormalizer 公开接口（构造函数签名、字段名、方法名）与 Pi0.5 一致

测试优先：

本 L3 遵循 TDD 原则。建议先编写 `test_normalizer_loader.py` 的四个用例（正常构造/缺文件/坏 JSON/缺键），再实现 `normalizer_loader.py` 使其通过。若已有实现可跳过此步骤但必须确保四个用例全部覆盖。

## 15. 成功标准

- [ ] `src/model_deploy/act/repo/normalizer_loader.py` 已创建
- [ ] `src/model_deploy/act/tests/repo/test_normalizer_loader.py` 已创建
- [ ] `NORMALIZERS_NAME = "normalizers.json"` 常量已定义
- [ ] `load_bundle_normalizers(bundle_dir)` 函数已实现，返回 `(state_normalizer, action_normalizer)` 元组
- [ ] `ActionStateNormalizer` 结构完整保留（min_vals/max_vals/range_vals/identity_mask/vector_dim 字段，normalize/unnormalize 方法）
- [ ] 正常构造用例通过（返回元组长度 2，对象类型与字段正确）
- [ ] 缺文件用例通过（抛出 `FileNotFoundError`）
- [ ] 坏 JSON 用例通过（抛出 `json.JSONDecodeError`）
- [ ] 缺键用例通过（抛出 `KeyError`）
- [ ] 无 config/service/runtime/ui 层 import
- [ ] 无维度硬编码/维度断言（26/14/16），无 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing
- [ ] pytest 全部通过且无 warning，未修改任何越界文件

## 16. 回滚方式

```text
回滚步骤：
1. 删除 src/model_deploy/act/repo/normalizer_loader.py
2. 删除 src/model_deploy/act/tests/repo/test_normalizer_loader.py
3. 若 normalization.py（ActionStateNormalizer 定义）仅为本 L3 新建且无其他引用，则一并删除
4. 若 __init__.py 仅为本 L3 新建且无其他内容，则一并删除
5. git checkout 对应文件（若已提交）
6. 确认工作区恢复到 deploy_005 执行前状态
7. 在验收日志中记录回滚原因
本 L3 无数据迁移、无配置变更、无硬件交互，回滚无副作用。
```

## 17. 完成后交接

本 L3 完成后，`load_bundle_normalizers` 函数可供 config 层 deploy_009 `check_normalizer_contract` 做维度契约校验，以及 service 层推理时使用。交接时需确认：
1. pytest 全绿且证据已落盘至验收日志目录。
2. 验收结论已写入 `deploy_005_验收结论.md`。
3. 函数签名 `load_bundle_normalizers(bundle_dir: Path) -> tuple[ActionStateNormalizer, ActionStateNormalizer]` 稳定可供上层依赖。
4. `ActionStateNormalizer` 公开接口（构造函数、字段、方法）与 Pi0.5 保持一致，可供 service 层放心调用。
5. 已通知 L2 调度器 deploy_005 状态为 completed。
6. 下游消费者 deploy_009（config 层 `check_normalizer_contract`）可基于本函数返回的 normalizer 对象进行维度校验，本 L3 明确不在此处做维度校验。

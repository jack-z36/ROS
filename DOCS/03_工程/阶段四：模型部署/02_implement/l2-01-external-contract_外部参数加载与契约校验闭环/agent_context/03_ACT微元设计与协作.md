# L2-01 ACT 微元设计与协作

> [!info] 产物归属
> - 类型：L2 设计包内的 ACT 微元设计文档（阶段四：模型部署）。
> - `l2_id`：`l2-01-external-contract`
> - 本文职责：把 Pi0.5 源码拆解结论映射成 ACT 版微元设计推荐，给出每个微元的 3.5 层类型、目标层、目标文件、函数/class 判定、输入输出、Pi0.5 参考；并说明本 L2 内部协作（创建顺序、状态归属、边界读写、编排点、失败传播）。
> - **本文设计推荐已经用户确认**（见第 5 节"已决策清单"），可进入 L3 生成。

## 0. 设计总则

- 本 L2 是**启动阶段装配者**，产出的对象在程序生命周期内视为不可变（构造并校验通过后只读）。
- 严格遵守六层依赖方向（`DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`）：`types → config → repo`，不反向。
- **读取（`repo/`）与校验（`config/`）分离**：`repo/` 只做"路径→RAM 对象"（含反序列化、存在性检查），不做业务校验；业务校验（类型/范围/关系/dim 一致）归 `config/`。这样 `repo/` 可独立单测，`config/` 校验逻辑可独立单测。
- 数据规格（`types/`）是最上游，`config/` 和 `repo/` 都依赖它，不反向。

## 1. 六层落点总览

| 层 | 是否落点 | 目标文件 | 一句话职责 |
|---|---|---|---|
| `types/` | 是 | `action_spec.py`、`state_spec.py`、`contract_result.py` | 16D action/state 维度常量、段序、字段语义、值域、codec、contract 结果对象 |
| `config/` | 是 | `schema.py`（含 `DeployConfig` + 子配置 + 校验器）、`load_deploy_config` 编排入口 | 配置 schema、配置对象树、配置校验、配置装配编排 |
| `repo/` | 是 | `bundle_reader.py`、`manifest_parser.py`、`normalizer_loader.py`、`experiment_config_loader.py` | 进程外资源读取与反序列化（含存在性检查） |
| `config_files/` | 是 | `deploy.yaml` | 运行配置实例（具体值） |
| `service/` | 否 | — | 本 L2 无 RAM 内业务计算 |
| `runtime/` | 否 | — | 本 L2 无时间/线程/队列/调度 |
| `ui/` | 否 | — | 本 L2 无 ROS node/topic |

> 六层每个目标文件的详细设计见对应子目录设计 `.md`。

## 2. ACT 微元表

> 所有设计决策已与用户确认（见第 5 节）。

| ACT 微元 | 3.5 层类型 | 目标层 | 目标文件 | 函数/class | 输入 | 输出/副作用 | Pi0.5 参考 | 备注 |
|---|---|---|---|---|---|---|---|---|
| `ACTION_DIM=16` 常量 | 数据 | types | `action_spec.py` | 模块常量 | — | `int=16` | `action_spec.py:17`（Pi0.5=14） | 段序已锁定 |
| `STATE_DIM=16` 常量 | 数据 | types | `state_spec.py` | 模块常量 | — | `int=16` | `action_spec.py:18`（Pi0.5=26） | 段序已锁定 |
| `ActionSpec`（段序/字段/值域定义） | 数据 | types | `action_spec.py` | frozen dataclass | — | 4 段定义（左TCP/左夹爪/右TCP/右夹爪，交替排列） | `BimanualAction`（模式） | 16D 段序见 types/README.md |
| `StateSpec`（段序/字段/值域定义） | 数据 | types | `state_spec.py` | frozen dataclass | — | 4 段定义（左TCP/右TCP/左夹爪/右夹爪，左全在前） | `BimanualState`（模式） | 16D 段序见 types/README.md |
| action/state codec（拆分/拼接/校验维度） | 计算函数 | types | `action_spec.py`/`state_spec.py` | 纯函数 | flat 向量 | 结构化视图 / 异常 | `action_codec.py`/`state_codec.py` | 校验总维==16 |
| `ContractResult`/`BundleContractResult`/`NormalizerContractResult` | 数据 | types | `contract_result.py` | frozen dataclass | — | pass/fail + reason | Pi0.5 无（用异常）；ACT 显式结果对象 | 便于 L2 Gate 观察 |
| `BundleConfig`（bundle_dir + 解析） | 数据 | config | `schema.py` | frozen dataclass | bundle_dir | resolved path | `BundleConfig`（复用） | |
| `RuntimeConfig` | 数据+计算 | config | `schema.py` | frozen dataclass + `__post_init__` | raw dict | 校验后配置 | `RuntimeConfig`（强复用） | dims=16 |
| `SafetyConfig` | 数据+计算 | config | `schema.py` | frozen dataclass + `__post_init__` | raw dict | 校验后配置 | `SafetyConfig`（部分） | **新增 TCP/quaternion 占位字段（具体值 L2-05 填）** |
| `TopicsConfig` + 子配置 | 数据+计算 | config | `schema.py` | frozen dataclass | raw dict | `/act/*` topic 配置 | `TopicsConfig`（模式） | namespace=`/act` |
| `ImageConfig` | 数据 | config | `schema.py` | frozen dataclass | raw dict | 图像预处理配置 | `ImageConfig`（复用） | |
| 类型化校验器群（`_str/_choice/_positive_int/...`） | 计算函数 | config | `schema.py` | 纯函数 | raw+key | 类型化值/异常 | 校验器群（强复用） | 异常类型用 ACT 自有 |
| `DeployConfig`（聚合根） | 数据+计算 | config | `schema.py` | frozen dataclass + `from_mapping` | raw dict+base_dir | 校验后配置树 | `DeployConfig`（强复用） | 去 bridge/mux |
| 配置装配编排 `_deploy_from_mapping` 等价物 | 编排函数 | config | `schema.py` | 纯函数 | raw dict | 调各子配置构造器 | `_deploy_from_mapping`（强复用） | 调用顺序固定 |
| `load_deploy_config(path)` 入口 | 编排函数 | config | `schema.py` | 纯函数 | yaml 路径 | `DeployConfig` | `load_deploy_config`（强复用） | 入口在 schema.py |
| bundle 文件存在性检查 | 数据读写函数 | repo | `bundle_reader.py` | 纯函数 | bundle_dir | 存在/`FileNotFoundError` | `_validate_bundle`（复用存在性段） | |
| `read_bundle_manifest` | 数据读写函数 | repo | `manifest_parser.py` | 纯函数 | bundle_dir | manifest dict | `load_bundle_manifest`（强复用） | |
| `read_bundle_normalizers` | 数据读写函数 | repo | `normalizer_loader.py` | 纯函数 | bundle_dir | `(state_norm, action_norm)` 对象 | `load_bundle_normalizers`（强复用） | 返回 ActionStateNormalizer |
| `read_experiment_config` | 数据读写函数 | repo | `experiment_config_loader.py` | 纯函数 | bundle_dir | `ExperimentConfig` | `load_experiment_config`（参考） | 不覆写 dims |
| checkpoint 路径解析 | 数据读写函数 | repo | `bundle_reader.py` | 纯函数 | bundle_dir | checkpoint path | Pi0.5 bundle 内（参考） | |
| bundle 元数据一致性校验 | 计算函数 | config | `schema.py` | 纯函数 | manifest+exp_config+runtime | `BundleContractResult` | **Pi0.5 无（补强）** | 交叉校验三处 dim 一致 |
| normalizer dim 契约校验 | 计算函数 | config | `schema.py` | 纯函数 | normalizers+ActionSpec/StateSpec | `NormalizerContractResult` | **Pi0.5 无（补强）** | 校验 normalizer dim==16 |
| `deploy.yaml` 配置实例 | 数据 | config_files | `deploy.yaml` | yaml 文件 | — | 运行配置值 | `deploy/config/deploy.yaml`（结构参考） | 具体值随 ACT 调整 |

## 3. 推荐方案（待用户确认）

### 3.1 `DeployConfig` 形态：frozen dataclass + `__post_init__` + `from_mapping`

**推荐**：采用 Pi0.5 模式——frozen dataclass 保证不可变，`__post_init__` 做关系校验（如 `execute_horizon ≤ chunk_size`），`from_mapping(raw, base_dir)` 做类型化装配，`base_dir` 用于解析相对路径（如 `bundle_dir`）。

子对象拆分：
```text
DeployConfig（聚合根）
├── bundle: BundleConfig          # bundle_dir + resolved path
├── runtime: RuntimeConfig        # mode/hz/chunk/dims=16/fallback
├── safety: SafetyConfig          # 含新增 TCP/quaternion 字段
├── topics: TopicsConfig          # namespace=/act + observation/command/...
├── image: ImageConfig            # 图像预处理
└── raw: dict                     # 原始 yaml（便于排查）
```

去掉 Pi0.5 的 `bridge`/`mux`（Pi0.5 专属的 picotele 适配，ACT 不需要）。

### 3.2 读取与校验分离

**推荐**：
- `repo/` 层函数只做"路径→RAM 对象"（读文件、反序列化、存在性检查），返回原始 dict 或已反序列化对象，**不做业务校验**。
- `config/` 层做类型化校验（类型/范围/关系/dim 一致），非法抛 ACT 配置异常。
- 这样 `repo/` 与 `config/` 可分别单测；`config/` 校验逻辑不依赖文件系统（可用 mock dict 单测）。

### 3.3 bundle contract 补强（Pi0.5 缺口）

**推荐**：ACT 的 bundle contract 校验分两层：
1. **存在性**（`repo/`）：manifest.json/normalizers.json/experiment_config.yaml/checkpoint 文件存在。
2. **元数据一致性**（`config/`）：交叉校验三处 dim 一致——`manifest.json["model"]["action_dim"/"state_dim"]` == `experiment_config.yaml` model/data dims == `RuntimeConfig.action_dim/state_dim`(==16)。不一致判 contract 非法。

产出显式 `BundleContractResult(pass, reason)` 对象，便于 L2 Gate 观察（优于 Pi0.5 的纯异常）。

### 3.4 normalizer contract 校验

**推荐**：校验 `ActionStateNormalizer` 的 state/action 维度分别 == `STATE_DIM`(16)/`ACTION_DIM`(16)。`ActionStateNormalizer` 类直接复用（算法无关），仅 dim 校验是新增。产出 `NormalizerContractResult`。

### 3.5 contract 校验失败策略

**推荐**：
- **配置非法**（deploy.yaml 缺字段/dim 非 16/topic 非法/hz 非法等）：**抛错阻止启动**（对应协作架构第 9 节"配置非法→抛错并阻止启动"）。
- **bundle/normalizer contract 非法**：**默认抛错阻止启动**；若 `runtime.mode` 允许 fake-policy 且用户显式配置 `bundle.allow_fake=true`，则切 fake-policy 并标 `env-blocked`（对应协作架构第 9 节"bundle contract 非法→抛错或 env-blocked，可切 fake-policy"）。此策略已经用户确认。

### 3.6 TCP/quaternion safety 字段（Pi0.5 无参考）

**推荐**（已确认）：在 `SafetyConfig` 新增字段占位，**具体字段名/默认值留待 L2-05 细化**（L2-05 是 safety 执行方，更清楚需要什么）。本 L2 只保证字段可被 L2-05 读取。

## 4. 内部协作说明

```text
创建顺序（启动阶段，同步、无并发）：
1. load_deploy_config(path) 读 deploy.yaml → raw dict（repo 边界读）
2. DeployConfig.from_mapping(raw, base_dir) 装配：
   a. BundleConfig（解析 bundle_dir）
   b. RuntimeConfig（校验 mode/hz/chunk/dims=16/fallback）
   c. ImageConfig
   d. TopicsConfig（namespace=/act，生成 topic 默认名）
   e. SafetyConfig（含 TCP/quaternion 占位）
3. 读 bundle 资源（repo 边界读）：
   a. read_bundle_manifest(bundle_dir) → manifest dict
   b. read_experiment_config(bundle_dir) → ExperimentConfig
   c. read_bundle_normalizers(bundle_dir) → (state_norm, action_norm)
   d. checkpoint 路径解析
4. contract 校验（config 计算）：
   a. bundle 元数据一致性 → BundleContractResult
   b. normalizer dim 一致性 → NormalizerContractResult
   c. 任一 fail → 按失败策略处理
5. 构造 StateSpec/ActionSpec（types，16D，来自 RuntimeConfig dims + 段序定义）
6. 返回 (DeployConfig, StateSpec, ActionSpec, BundleContractResult, NormalizerContractResult)

状态归属：
- DeployConfig / StateSpec / ActionSpec：构造后只读，所有权归"启动装配 Main"，被全部下游 import。
- BundleContractResult / NormalizerContractResult：构造后只读，记录启动期契约校验结论。
- 本 L2 无运行时状态更新（无 buffer/queue/cache/metrics）。

纯 RAM 计算：
- 类型化校验器（_str/_choice/...）、RuntimeConfig.__post_init__ 关系校验、bundle 元数据一致性校验、normalizer dim 校验、codec 拆分/拼接。

外部边界读写：
- 读：deploy.yaml、manifest.json、normalizers.json、experiment_config.yaml、checkpoint 文件（全部 repo 层，跨进程文件读）。
- 写：无（本 L2 不写任何文件/topic/hardware）。

运行时编排点：
- 本 L2 只在启动阶段被调用一次，不参与稳态 tick 调度。编排入口是 load_deploy_config。

失败传播：
- 配置非法 → 抛 ACT 配置异常 → 阻止启动（不进入运行循环）。
- bundle/normalizer contract 非法 → 抛错或切 fake-policy + env-blocked。
- 文件缺失 → FileNotFoundError（repo 层）。
- 所有失败在入口处终止，不进入半初始化状态。
```

## 5. 已决策清单（用户确认，可进 L3）

以下决策在交互检查点经用户确认：

1. **16D state / 16D action 段序**（源自阶段二数据清洗交付说明 `DOCS/01_知识/阶段二：数据清洗/数据清洗交付说明.md`）：
   - **16D state**（去触觉）：`left_tcp_pose(7) + right_tcp_pose(7) + left_gripper_width(1) + right_gripper_width(1)`，排列"所有左段→所有右段"。
   - **16D action**：`left_tcp_pose_t_plus_1(7) + left_gripper_width_t_plus_1(1) + right_tcp_pose_t_plus_1(7) + right_gripper_width_t_plus_1(1)`，排列"左pose+左夹爪→右pose+右夹爪"。
   - action 是绝对动作；quaternion xyzw 归一化；夹爪 [0,1]；左右手独立坐标系。详见 `types/README.md`。
2. **`DeployConfig` 形态**（3.1）：采纳推荐——frozen dataclass + `__post_init__` + `from_mapping` + 5 子配置（Bundle/Runtime/Safety/Topics/Image），去 bridge/mux。
3. **读取/校验分离**（3.2）：采纳——`repo/` 只读不校验、`config/` 做校验。
4. **bundle contract 补强**（3.3）：采纳——三处 dim 交叉校验。
5. **contract 失败策略**（3.5）：采纳——配置非法→阻止启动；bundle/normalizer 非法→默认阻止，可选 fake-policy + env-blocked。
6. **TCP/quaternion safety 字段**（3.6）：采纳——本 L2 占位，具体数值留 L2-05。
7. **`load_deploy_config` 入口**：放 `config/schema.py`。

> 所有待决策项已确认。设计包达到 "Ready For L3 Criteria"。

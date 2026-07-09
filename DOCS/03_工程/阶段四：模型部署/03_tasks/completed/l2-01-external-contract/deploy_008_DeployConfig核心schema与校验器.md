```yaml
dispatch:
  task_id: deploy_008
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_008_DeployConfig核心schema与校验器.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S1, S2, S5]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_008_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 3
  parallel_group: l2-01-external-contract-p3
  depends_on: [deploy_001, deploy_002, deploy_003]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/config/schema.py
      - src/model_deploy/act/config_files/deploy.yaml
      - src/model_deploy/act/tests/config/test_schema.py
    modules:
      - model_deploy.act.config.schema
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

# deploy_008 — DeployConfig 核心 schema 与校验器

L3 编号：deploy_008

## 1. 任务元信息

| 字段 | 值 |
|------|-----|
| task_id | deploy_008 |
| task_name | DeployConfig 核心 schema 与校验器 |
| L2 | l2-01-external-contract（外部参数加载与契约校验闭环） |
| 改造类型 | source-adaptation |
| 验收模式 | direct-local |
| 真机风险 | none |
| Wave | 3 |
| parallel_group | l2-01-external-contract-p3 |
| depends_on | deploy_001, deploy_002, deploy_003（types 层必须先完成） |
| can_run_parallel_with | []（无并行 — 配置为单文件，deploy_009 依赖本任务） |
| branch | feat/model_deploy/l2-01-external-contract |
| integration_branch | model_deploy |
| acceptance_dir | DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract |
| acceptance_card | DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_008_验收卡片.md |
| acceptance_feedback_dir | DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs |
| acceptance_round_limit | 3 |
| local_acceptance_required | true |
| dispatch_status | ready |
| acceptance_scenarios | S1, S2, S5 |

## 2. 上下文与依赖

### 2.1 L2 定位

本任务属于 L2 `l2-01-external-contract`（外部参数加载与契约校验闭环），负责构建 ACT 部署配置的结构化 schema 基础。L2 的目标是建立从 `deploy.yaml` 外部配置文件到运行时 `DeployConfig` 对象的完整加载与校验链路。

### 2.2 依赖链

- **depends_on: deploy_001, deploy_002, deploy_003** — types 层（数据类型定义）必须先完成。schema 中的 dataclass 字段类型（如 `Path`、维度 int）依赖 types 层的基础类型约定。
- **deploy_009 依赖本任务** — deploy_009 将在本任务产出的 schema 基础上实现 `load_deploy_config(path)` 编排入口、`check_bundle_contract` 和 `check_normalizer_contract` 契约交叉校验。因此本任务必须先完成且产出稳定接口。

### 2.3 在 L2 中的角色

deploy_008 是 L2 的**结构地基**：
- 定义 `DeployConfigError` 异常类型（所有配置校验错误的统一异常）
- 定义所有 frozen dataclass（BundleConfig、RuntimeConfig、SafetyConfig、TopicsConfig、ImageConfig、DeployConfig）
- 实现 typed validators（类型安全的字段提取与校验函数集）
- 实现 `DeployConfig.from_mapping(raw, *, base_dir)` 组装入口
- 产出 `deploy.yaml` 默认配置实例

deploy_009 在此基础上添加：YAML 文件加载编排、bundle 契约校验、normalizer 契约校验。

## 3. 目标与产出

### 3.1 目标文件

| 类型 | 路径 | 说明 |
|------|------|------|
| Source | `src/model_deploy/act/config/schema.py` | 核心 schema 定义：异常、frozen dataclass、typed validators、from_mapping |
| Config | `src/model_deploy/act/config_files/deploy.yaml` | 默认部署配置实例 |
| Test | `src/model_deploy/act/tests/config/test_schema.py` | schema 单元测试 |

### 3.2 产出物清单

1. `DeployConfigError(ValueError)` — 配置错误统一异常
2. 6 个 frozen dataclass：BundleConfig、RuntimeConfig、SafetyConfig、TopicsConfig（含 ObservationTopicsConfig、CommandTopicsConfig）、ImageConfig、DeployConfig
3. 12+ 个 typed validator 函数：`_required_mapping`、`_mapping`、`_path`、`_str`、`_optional_str`、`_choice`、`_bool`、`_positive_int`、`_non_negative_int`、`_int_value`、`_float`、`_positive_float`、`_float_list`
4. `DeployConfig.from_mapping(cls, raw, *, base_dir)` — 从 dict 组装 DeployConfig
5. `_deploy_from_mapping(raw, *, base_dir)` — 内部组装实现函数
6. `deploy.yaml` — 默认配置实例（dry-run 模式）
7. `test_schema.py` — 覆盖合法/非法路径的单元测试

### 3.3 不产出（deploy_009 负责）

- `load_deploy_config(path)` — YAML 文件加载编排入口
- `check_bundle_contract(config)` — bundle 契约交叉校验
- `check_normalizer_contract(config)` — normalizer 契约交叉校验

## 4. 验收场景映射

| 场景 | 描述 | deploy_008 贡献 | 验证方式 |
|------|------|----------------|----------|
| S1 | 合法配置载入 | `from_mapping` 从合法 mapping 成功构建 DeployConfig | pytest 构造合法 mapping 断言无异常 |
| S2 | 非法维度失败 | state_dim/action_dim != 16 时 from_mapping 抛出 DeployConfigError | pytest 断言 state_dim=26/action_dim=14 抛异常 |
| S5 | 无平滑配置泄漏 | deploy.yaml 和 schema.py 不含 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing | rg 搜索返回空 |

## 5. Pi0.5 源码盘点

**参考文件（READ-ONLY）**：`DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`

### 5.1 源码结构表

| Pi0.5 结构 | Pi0.5 内容 | ACT 改造动作 |
|------------|-----------|-------------|
| `DeployConfigError` | `class DeployConfigError(ValueError)` | **保留**，不改 |
| `BundleConfig` | frozen dataclass；field `bundle_dir: Path`；property `resolved_bundle_dir` | **保留**，不改 |
| `RuntimeConfig` | frozen dataclass；含 blend_steps=3, action_dim=14, state_dim=26 等字段；`__post_init__` 校验；property `publishes_command_topics` | **修改**：REMOVE blend_steps；action_dim 14→16；state_dim 26→16；`__post_init__` 移除 blend_steps>=0 校验 |
| `ObservationTopicsConfig` | frozen dataclass；观测话题字段 | **保留结构**，话题名改为 /act/* |
| `CommandTopicsConfig` | frozen dataclass；指令话题字段 | **保留结构**，话题名改为 /act/* |
| `BridgeTopicsConfig` | frozen dataclass；bridge 话题 | **REMOVE** — ACT 无 bridge |
| `MuxTopicsConfig` | frozen dataclass；mux 话题 | **REMOVE** — ACT 无 mux |
| `TopicsConfig` | frozen dataclass；namespace, observation, command, bridge_output, mux | **修改**：REMOVE bridge_output 和 mux；保留 namespace, observation, command；namespace /pi05_vla/* → /act/* |
| `JointLimitsConfig` | frozen dataclass；关节限位 | **REMOVE** — ACT 改用 TCP 限位 |
| `SafetyConfig` | frozen dataclass；max_joint_delta_rad, stale_observation_timeout_s, command_timeout_s, clamp_normalized_action, hold_last_action, hand_min=300.0, hand_max=1000.0, joint_limits | **修改**：REMOVE joint_limits/JointLimitsConfig 引用；REMOVE max_joint_delta_rad, stale_observation_timeout_s, command_timeout_s, clamp_normalized_action, hold_last_action；ADD max_tcp_delta_per_step=0.03, quaternion_check=True；保留 hand_min=300.0, hand_max=1000.0 |
| `BridgeConfig` | frozen dataclass；bridge 配置段 | **REMOVE** — ACT 无 bridge |
| `MuxConfig` | frozen dataclass；mux 配置段 | **REMOVE** — ACT 无 mux |
| `ImageConfig` | frozen dataclass；image_size=224, resize_mode="resize_pad", transport="raw" | **保留**，不改 |
| `DeployConfig` | frozen dataclass；bundle, runtime, image, topics, safety, bridge, mux, raw | **修改**：REMOVE bridge 和 mux 字段；保留 bundle, runtime, image, topics, safety, raw |
| typed validators | `_required_mapping`, `_mapping`, `_path`, `_str`, `_optional_str`, `_choice`, `_bool`, `_positive_int`, `_non_negative_int`, `_int_value`, `_float`, `_positive_float`, `_float_list` | **保留全部**，不改 |
| `_deploy_from_mapping` | 内部组装函数；顺序：bundle, runtime, image, topics, safety, bridge, mux, raw | **修改**：移除 bridge 和 mux 组装步骤；顺序改为 bundle, runtime, image, topics, safety, raw |
| `from_mapping` | `DeployConfig.from_mapping(cls, raw, *, base_dir) -> DeployConfig` | **保留签名**，内部调用修改后的 _deploy_from_mapping |
| `load_deploy_config` | `load_deploy_config(path) -> DeployConfig`；加载 YAML 调 from_mapping | **deploy_008 不实现** — 留给 deploy_009 |

### 5.2 明确 REMOVE 的 Pi0.5 字段/结构

| 移除项 | 原因 |
|--------|------|
| `BridgeConfig` | ACT 架构无 bridge 段 |
| `MuxConfig` | ACT 架构无 mux 段 |
| `BridgeTopicsConfig` | ACT 架构无 bridge 话题 |
| `MuxTopicsConfig` | ACT 架构无 mux 话题 |
| `TopicsConfig.bridge_output` | 无 bridge |
| `TopicsConfig.mux` | 无 mux |
| `JointLimitsConfig` | ACT 改用 TCP 限位，不用关节限位 |
| `SafetyConfig.joint_limits` | 同上 |
| `SafetyConfig.max_joint_delta_rad` | 被 max_tcp_delta_per_step 替代 |
| `SafetyConfig.stale_observation_timeout_s` | ACT 不需要 |
| `SafetyConfig.command_timeout_s` | ACT 不需要 |
| `SafetyConfig.clamp_normalized_action` | ACT 不需要 |
| `SafetyConfig.hold_last_action` | ACT 不需要（fallback_policy 已覆盖） |
| `RuntimeConfig.blend_steps` | REMOVE — 平滑已移除 |
| `RuntimeConfig` 中的 smoothstep_window, smoothstep_alpha, cross_chunk_fusion, chunk_blend_mode, rtc_alignment, action_smoothing | REMOVE — 全部平滑字段（Pi0.5 若有则移除，确保不泄漏） |
| state_dim=26 | 改为 16 |
| action_dim=14 | 改为 16 |
| namespace `/pi05_vla/*` | 改为 `/act/*` |
| `__post_init__` 中 `blend_steps >= 0` 校验 | REMOVE |

## 6. 边界与约束

### 6.1 允许做

- 创建 `src/model_deploy/act/config/schema.py`，定义 DeployConfigError、所有 frozen dataclass、typed validators、from_mapping
- 创建 `src/model_deploy/act/config_files/deploy.yaml` 默认配置实例
- 创建 `src/model_deploy/act/tests/config/test_schema.py` 单元测试
- 在 schema.py 中定义 `_deploy_from_mapping` 内部组装函数
- 在 schema.py 中定义 `DeployConfig.from_mapping` classmethod

### 6.2 不做（其他 L3 负责）

- `load_deploy_config(path)` YAML 文件加载编排入口 — **deploy_009 负责**
- `check_bundle_contract(config)` bundle 契约交叉校验 — **deploy_009 负责**
- `check_normalizer_contract(config)` normalizer 契约交叉校验 — **deploy_009 负责**
- 配置热重载 / 运行时覆盖逻辑 — 不在 L2 范围

### 6.3 禁止修改

- `pi05/` 目录下任何文件（READ-ONLY 参考）
- `src/model_deploy/act/types/` 层（deploy_001-003 产出）
- `src/model_deploy/act/repo/` 层
- `src/model_deploy/act/service/` 层
- `src/model_deploy/act/runtime/` 层
- `src/model_deploy/act/ui/` 层
- 其他 L3 任务的产出文件
- 任何 `__init__.py` 中的导出声明（除非仅添加 schema 模块自身导出）

## 7. 微元设计原则

### 7.1 frozen 不可变

所有 dataclass 必须使用 `@dataclass(frozen=True)`。配置对象一旦构建不可修改，确保运行时配置一致性。

### 7.2 类型安全校验

所有字段从 raw dict 提取时必须经过 typed validator，不接受裸 `raw["key"]` 访问。校验失败统一抛出 `DeployConfigError`。

### 7.3 显式组装顺序

`_deploy_from_mapping` 按固定顺序组装各配置段（bundle → runtime → image → topics → safety → raw），顺序不可随意调整。raw 原始 dict 保留在 DeployConfig.raw 中供下游（deploy_009 契约校验）使用。

### 7.4 无平滑字段原则

schema 中不得出现任何平滑相关字段：blend_steps、smoothstep_window、smoothstep_alpha、cross_chunk_fusion、chunk_blend_mode、rtc_alignment、action_smoothing。这些字段在 ACT 架构中被彻底移除。

### 7.5 维度对齐

state_dim 和 action_dim 必须为 16（ACT 双臂 + 夹爪维度）。Pi0.5 的 26D state / 14D action 不适用于 ACT。

## 8. 微元清单

### 8.1 数据微元（frozen dataclass）

| 微元 | 类型 | 字段/职责 | Pi0.5 来源 | 改造 |
|------|------|----------|-----------|------|
| `DeployConfigError` | 异常类 | 继承 ValueError；配置校验统一异常 | Pi0.5 同名 | 保留 |
| `BundleConfig` | frozen dataclass | `bundle_dir: Path`；property `resolved_bundle_dir` | Pi0.5 同名 | 保留 |
| `RuntimeConfig` | frozen dataclass | mode, device, inference_hz, control_hz, chunk_size, execute_horizon, prefetch_steps, action_dim=16, state_dim=16, max_action_age_sec, max_inference_requests, max_pending_chunks, fallback_policy, max_delta_per_step, warmup_steps, compile_model, compile_mode, publish_metrics_hz, task；property `publishes_command_topics`；`__post_init__` 校验 | Pi0.5 同名 | REMOVE blend_steps；dims 14/26→16/16；移除 blend_steps 校验 |
| `ObservationTopicsConfig` | frozen dataclass | 观测话题字段（arm_state, left_image, right_image 等） | Pi0.5 同名 | 话题 /pi05_vla/* → /act/* |
| `CommandTopicsConfig` | frozen dataclass | 指令话题字段（arm_command, hand_command 等） | Pi0.5 同名 | 话题 /pi05_vla/* → /act/* |
| `TopicsConfig` | frozen dataclass | namespace, observation, command | Pi0.5 同名 | REMOVE bridge_output, mux；namespace → /act |
| `SafetyConfig` | frozen dataclass | max_tcp_delta_per_step=0.03, hand_min=300.0, hand_max=1000.0, quaternion_check=True | Pi0.5 同名（部分） | REMOVE joint_limits/max_joint_delta_rad 等；ADD max_tcp_delta_per_step, quaternion_check |
| `ImageConfig` | frozen dataclass | image_size=224, resize_mode="resize_pad", transport="raw" | Pi0.5 同名 | 保留 |
| `DeployConfig` | frozen dataclass | bundle, runtime, image, topics, safety, raw | Pi0.5 同名 | REMOVE bridge, mux |

### 8.2 计算函数微元（typed validators）

| 微元 | 签名 | 职责 | Pi0.5 来源 |
|------|------|------|-----------|
| `_required_mapping` | `(raw: dict, key: str) -> dict` | 提取必需子 mapping，缺失抛 DeployConfigError | Pi0.5 同名 |
| `_mapping` | `(raw: dict, key: str, default: dict) -> dict` | 提取可选子 mapping，缺失返回 default | Pi0.5 同名 |
| `_path` | `(value, *, base_dir: Path, key: str) -> Path` | 字符串转 Path，相对路径基于 base_dir 解析 | Pi0.5 同名 |
| `_str` | `(value, key: str) -> str` | 校验并返回字符串 | Pi0.5 同名 |
| `_optional_str` | `(value, key: str, default) -> str` | 可选字符串 | Pi0.5 同名 |
| `_choice` | `(value, key: str, choices: set, default) -> str` | 枚举校验 | Pi0.5 同名 |
| `_bool` | `(value, key: str, default) -> bool` | 布尔校验 | Pi0.5 同名 |
| `_positive_int` | `(value, key: str, default) -> int` | 正整数校验（>0） | Pi0.5 同名 |
| `_non_negative_int` | `(value, key: str, default) -> int` | 非负整数校验（>=0） | Pi0.5 同名 |
| `_int_value` | `(value, key: str, default) -> int` | 整数校验 | Pi0.5 同名 |
| `_float` | `(value, key: str, default) -> float` | 浮点校验 | Pi0.5 同名 |
| `_positive_float` | `(value, key: str, default) -> float` | 正浮点校验（>0） | Pi0.5 同名 |
| `_float_list` | `(value, key: str, default) -> list` | 浮点列表校验 | Pi0.5 同名 |

### 8.3 编排函数微元

| 微元 | 签名 | 职责 | Pi0.5 来源 | 改造 |
|------|------|------|-----------|------|
| `_deploy_from_mapping` | `(raw: dict, *, base_dir: Path) -> DeployConfig` | 内部组装函数；按序调用各 dataclass 构造 | Pi0.5 同名 | 移除 bridge/mux 组装；顺序 bundle→runtime→image→topics→safety→raw |
| `DeployConfig.from_mapping` | `(cls, raw: dict, *, base_dir: Path) -> DeployConfig` | classmethod 入口；委托 `_deploy_from_mapping` | Pi0.5 同名 | 保留签名 |

## 9. 实施步骤

### 步骤 1：创建 schema.py 文件骨架

创建 `src/model_deploy/act/config/schema.py`，写入：
- 文件头注释（模块职责说明）
- import 语句（`dataclasses`、`pathlib.Path`、`typing`）
- `class DeployConfigError(ValueError)` 异常定义

### 步骤 2：定义 frozen dataclass — BundleConfig

```python
@dataclass(frozen=True)
class BundleConfig:
    bundle_dir: Path

    @property
    def resolved_bundle_dir(self) -> Path:
        ...
```

### 步骤 3：定义 frozen dataclass — RuntimeConfig

```python
@dataclass(frozen=True)
class RuntimeConfig:
    mode: str = "dry-run"
    device: str = "cuda:0"
    inference_hz: float = 10.0
    control_hz: float = 30.0
    chunk_size: int = 30
    execute_horizon: int = 10
    prefetch_steps: int = 5
    # blend_steps 已移除 — ACT 无平滑
    action_dim: int = 16   # Pi0.5 为 14，ACT 改为 16
    state_dim: int = 16    # Pi0.5 为 26，ACT 改为 16
    max_action_age_sec: float = 0.45
    max_inference_requests: int = 1
    max_pending_chunks: int = 1
    fallback_policy: str = "hold_last_action"
    max_delta_per_step: float = 0.03
    warmup_steps: int = 2
    compile_model: bool = True
    compile_mode: str = "reduce-overhead"
    publish_metrics_hz: float = 1.0
    task: str = "bimanual manipulation"
```

### 步骤 4：RuntimeConfig.__post_init__ 校验

```python
def __post_init__(self):
    if self.control_hz <= 0:
        raise DeployConfigError(...)
    if self.inference_hz <= 0:
        raise DeployConfigError(...)
    if self.prefetch_steps < 0:
        raise DeployConfigError(...)
    # blend_steps >= 0 校验已移除
    if self.execute_horizon > self.chunk_size:
        raise DeployConfigError(...)
    if self.prefetch_steps > self.execute_horizon:
        raise DeployConfigError(...)
    if self.max_action_age_sec <= 0:
        raise DeployConfigError(...)
    if self.max_inference_requests < 1:
        raise DeployConfigError(...)
    if self.max_pending_chunks < 1:
        raise DeployConfigError(...)
    if self.fallback_policy not in {"hold_last_action", "continue_old_chunk", "safe_stop"}:
        raise DeployConfigError(...)
```

同时实现 `publishes_command_topics` property。

### 步骤 5：定义其余 frozen dataclass

- `ObservationTopicsConfig` — 观测话题字段
- `CommandTopicsConfig` — 指令话题字段
- `TopicsConfig` — namespace, observation, command（无 bridge_output, 无 mux）
- `SafetyConfig` — max_tcp_delta_per_step=0.03, hand_min=300.0, hand_max=1000.0, quaternion_check=True
- `ImageConfig` — image_size=224, resize_mode="resize_pad", transport="raw"
- `DeployConfig` — bundle, runtime, image, topics, safety, raw（无 bridge, 无 mux）

### 步骤 6：实现 typed validators

实现以下全部校验函数（模块级私有函数）：

`_required_mapping`, `_mapping`, `_path`, `_str`, `_optional_str`, `_choice`, `_bool`, `_positive_int`, `_non_negative_int`, `_int_value`, `_float`, `_positive_float`, `_float_list`

每个函数接收 raw value 和 key 名称，校验失败时抛出 `DeployConfigError`，错误消息包含 key 名以便定位。

### 步骤 7：实现 _deploy_from_mapping 和 from_mapping

```python
def _deploy_from_mapping(raw: dict, *, base_dir: Path) -> DeployConfig:
    bundle = BundleConfig(...)       # 从 raw["bundle"] 组装
    runtime = RuntimeConfig(...)     # 从 raw["runtime"] 组装
    image = ImageConfig(...)         # 从 raw["image"] 组装
    topics = TopicsConfig(...)       # 从 raw["topics"] 组装
    safety = SafetyConfig(...)       # 从 raw["safety"] 组装
    # 无 bridge, 无 mux
    return DeployConfig(
        bundle=bundle,
        runtime=runtime,
        image=image,
        topics=topics,
        safety=safety,
        raw=raw,
    )
```

组装顺序严格为：**bundle → runtime → image → topics → safety → raw**。

```python
@classmethod
def from_mapping(cls, raw: dict, *, base_dir: Path) -> "DeployConfig":
    return _deploy_from_mapping(raw, base_dir=base_dir)
```

### 步骤 8：创建 deploy.yaml 默认配置实例

创建 `src/model_deploy/act/config_files/deploy.yaml`：

```yaml
bundle:
  bundle_dir: null  # must be set at runtime
runtime:
  mode: dry-run
  control_hz: 30.0
  inference_hz: 10.0
  chunk_size: 30
  execute_horizon: 10
  max_action_age_sec: 0.45
  fallback_policy: hold_last_action
  state_dim: 16
  action_dim: 16
image:
  image_size: 224
  resize_mode: resize_pad
  transport: raw
topics:
  namespace: /act
  observation:
    arm_state: arm_state
    left_image: left_image
    right_image: right_image
  command:
    arm_command: arm_command
    hand_command: hand_command
safety:
  max_tcp_delta_per_step: 0.03
  hand_min: 300.0
  hand_max: 1000.0
  quaternion_check: true
```

注意：deploy.yaml 中不得出现 bridge、mux、blend_steps 或任何平滑字段。

### 步骤 9：创建 test_schema.py 单元测试

创建 `src/model_deploy/act/tests/config/test_schema.py`，包含以下测试用例：

1. **test_valid_mapping_constructs** — 合法 mapping 成功构建 DeployConfig（S1）
2. **test_missing_required_field_raises** — 缺少必需字段（如 bundle）抛 DeployConfigError
3. **test_invalid_control_hz_raises** — control_hz <= 0 抛异常
4. **test_invalid_inference_hz_raises** — inference_hz <= 0 抛异常
5. **test_invalid_mode_raises** — mode 不在合法枚举中抛异常
6. **test_invalid_chunk_size_raises** — execute_horizon > chunk_size 抛异常
7. **test_invalid_state_dim_raises** — state_dim=26 抛 DeployConfigError（S2）
8. **test_invalid_action_dim_raises** — action_dim=14 抛 DeployConfigError（S2）
9. **test_invalid_fallback_policy_raises** — fallback_policy 不在枚举中抛异常
10. **test_no_blend_steps_field** — RuntimeConfig 无 blend_steps 属性（S5）
11. **test_no_bridge_mux_in_deploy_config** — DeployConfig 无 bridge/mux 字段
12. **test_topics_namespace_is_act** — namespace 为 /act 非 /pi05_vla

### 步骤 10：运行验证

执行 pytest 和 rg 检查（见第 12 节）。

## 10. 测试策略

### 10.1 测试分层

| 层级 | 范围 | 方法 |
|------|------|------|
| 单元测试 | schema.py 中每个 dataclass 构造与校验 | pytest，直接调用 from_mapping |
| 边界测试 | 非法值边界（hz=0, hz<0, chunk_size=0 等） | pytest，断言异常类型 |
| 回归测试 | 无平滑字段泄漏 | rg 搜索 + pytest 属性检查 |
| 结构测试 | frozen 不可变、无 bridge/mux | pytest，断言 frozen=True、无属性 |

### 10.2 测试覆盖目标

- from_mapping 合法路径：100%
- __post_init__ 每条校验分支：至少一个失败用例
- typed validators：每个函数至少一个合法 + 一个非法用例
- S1/S2/S5 场景：直接映射

### 10.3 测试隔离

测试不依赖真实 YAML 文件加载（那是 deploy_009 的职责）。测试直接构造 raw dict 调用 `from_mapping`，确保 deploy_008 的测试可独立运行。

## 11. 风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| Pi0.5 平滑字段泄漏到 schema | 高 | rg 检查 + pytest 属性检查双重防护 |
| state_dim/action_dim 遗留 26/14 | 高 | pytest 显式断言 16；rg 搜索 26/14 |
| bridge/mux 段残留 | 中 | rg 搜索 BridgeConfig/MuxConfig；pytest 断言无属性 |
| TopicsConfig 误保留 bridge_output/mux | 中 | pytest 断言 dataclass fields 不含这些字段 |
| from_mapping 组装顺序错误 | 中 | 代码审查 + 注释标注顺序 |
| typed validator 异常消息不包含 key | 低 | 实现时确保每条错误消息含 key 名 |
| frozen dataclass 被误改为可变 | 低 | pytest 断言 FrozenInstanceError |

## 12. 验证命令

### 12.1 pytest 单元测试

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_schema.py -v
```

预期：全部测试通过，0 failures。

### 12.2 平滑字段泄漏检查（S5）

```bash
rg -n 'blend_steps|smoothstep|cross_chunk|rtc_alignment|action_smoothing' src/model_deploy/act/config/schema.py src/model_deploy/act/config_files/deploy.yaml
```

预期：**无输出**（空输出 = 通过）。任何匹配行表示平滑字段泄漏，测试失败。

### 12.3 bridge/mux 残留检查

```bash
rg -n 'BridgeConfig|MuxConfig|BridgeTopicsConfig|MuxTopicsConfig|bridge_output' src/model_deploy/act/config/schema.py
```

预期：**无输出**。

### 12.4 维度残留检查

```bash
rg -n 'state_dim.*26|action_dim.*14' src/model_deploy/act/config/schema.py src/model_deploy/act/config_files/deploy.yaml
```

预期：**无输出**。

### 12.5 namespace 检查

```bash
rg -n 'pi05_vla' src/model_deploy/act/config/schema.py src/model_deploy/act/config_files/deploy.yaml
```

预期：**无输出**。

## 13. 完成定义

本任务完成当且仅当以下全部满足：

1. `src/model_deploy/act/config/schema.py` 存在且包含 DeployConfigError、6 个 frozen dataclass、全部 typed validators、from_mapping
2. `src/model_deploy/act/config_files/deploy.yaml` 存在且结构正确
3. `src/model_deploy/act/tests/config/test_schema.py` 存在且全部测试通过
4. 第 12 节全部验证命令返回预期结果
5. 无 bridge/mux/blend_steps/平滑字段残留
6. state_dim=16, action_dim=16
7. namespace 为 /act
8. 未修改 pi05/ 或 types/repo/service/runtime/ui 层
9. 验收卡片中 PASS_LOCAL 全部条件满足

## 14. 回滚策略

### 14.1 回滚条件

- pytest 失败且无法在 acceptance_round_limit（3 轮）内修复
- 验收卡片 PASS_LOCAL 条件不满足
- 修改了禁止修改的文件

### 14.2 回滚操作

```bash
git checkout -- src/model_deploy/act/config/schema.py
git checkout -- src/model_deploy/act/config_files/deploy.yaml
git checkout -- src/model_deploy/act/tests/config/test_schema.py
```

若文件为新增（git 未跟踪），直接删除：

```bash
rm -f src/model_deploy/act/config/schema.py
rm -f src/model_deploy/act/config_files/deploy.yaml
rm -f src/model_deploy/act/tests/config/test_schema.py
```

### 14.3 回滚后

将 dispatch_status 改为 `blocked`，在 acceptance_feedback_dir 记录失败原因，等待重新分派。

## 15. 必读设计文档

执行本任务前必须阅读以下 L2 设计文档：

| 序号 | 文档路径 | 阅读重点 |
|------|---------|---------|
| 1 | `DOCS/03_工程/阶段四：模型部署/01_L1_ACT功能模块边界.md` | ACT 功能模块边界，config 层职责范围 |
| 2 | `DOCS/03_工程/阶段四：模型部署/02_L1_ACT功能模块协作架构.md` | 模块协作架构，config 与 runtime/service 的交互 |
| 3 | `DOCS/03_工程/阶段四：模型部署/agent_context/01_L2功能边界.md` | L2 功能边界，外部参数加载与契约校验闭环范围 |
| 4 | `DOCS/03_工程/阶段四：模型部署/agent_context/02_pi05源码3.5层微元拆解.md` | Pi0.5 源码微元拆解，schema.py 的微元结构 |
| 5 | `DOCS/03_工程/阶段四：模型部署/agent_context/03_ACT微元设计与协作.md` | ACT 微元设计，schema 改造方向 |
| 6 | `DOCS/03_工程/阶段四：模型部署/agent_context/04_L2验收机制.md` | L2 验收机制，S1/S2/S5 场景定义 |
| 7 | `DOCS/03_工程/阶段四：模型部署/agent_context/07_config层设计.md` | config 层设计，schema 与 deploy.yaml 的详细设计规范 |

## 16. 提交与分支规范

### 16.1 分支

- 工作分支：`feat/model_deploy/l2-01-external-contract`
- 集成分支：`model_deploy`
- 在工作分支上完成开发后，合入集成分支

### 16.2 提交信息

```
feat(deploy_008): DeployConfig 核心 schema 与校验器

- 定义 DeployConfigError(ValueError) 异常
- 实现 BundleConfig, RuntimeConfig, SafetyConfig, TopicsConfig, ImageConfig, DeployConfig frozen dataclass
- 移除 bridge/mux 配置段（ACT 无 bridge/mux 架构）
- 移除 blend_steps 及所有平滑字段
- state_dim/action_dim 改为 16（Pi0.5 为 26/14）
- topics namespace 改为 /act（Pi0.5 为 /pi05_vla）
- 实现 12+ typed validators
- 实现 DeployConfig.from_mapping 组装入口
- 创建 deploy.yaml 默认配置实例
- 覆盖 S1/S2/S5 验收场景
```

### 16.3 提交范围

仅提交以下文件：
- `src/model_deploy/act/config/schema.py`
- `src/model_deploy/act/config_files/deploy.yaml`
- `src/model_deploy/act/tests/config/test_schema.py`

## 17. 备注

### 17.1 deploy_009 衔接点

本任务产出后，deploy_009 将依赖以下接口：
- `DeployConfig` dataclass（含 raw 字段）
- `DeployConfig.from_mapping` classmethod
- `DeployConfigError` 异常
- `RuntimeConfig` / `BundleConfig` / `SafetyConfig` 等子配置的 field 列表

deploy_009 将添加：
- `load_deploy_config(path: Path) -> DeployConfig` — 读取 YAML → 调 from_mapping
- `check_bundle_contract(config: DeployConfig) -> None` — 校验 bundle_dir 存在、normalizer 维度匹配
- `check_normalizer_contract(config: DeployConfig) -> None` — 校验 state_dim/action_dim 与 normalizer 一致

### 17.2 设计决策记录

- **max_tcp_delta_per_step 替代 max_joint_delta_rad**：ACT 使用 TCP 空间动作而非关节空间，限位改为 TCP 单步位移上限。字段名保留灵活性（不叫 tcp_joint_delta）。
- **quaternion_check 新增**：ACT 使用四元数表示末端姿态，需校验四元数模长。
- **raw 字段保留**：DeployConfig 保留原始 raw dict，供 deploy_009 契约校验读取未映射的扩展字段。
- **不实现 load_deploy_config**：严格遵循 L3 边界，文件加载编排属于 deploy_009 职责。

### 17.3 验收场景对应

| 场景 | 对应测试 | 对应验证命令 |
|------|---------|-------------|
| S1 | test_valid_mapping_constructs | pytest |
| S2 | test_invalid_state_dim_raises, test_invalid_action_dim_raises | pytest |
| S5 | test_no_blend_steps_field + rg 检查 | pytest + rg |

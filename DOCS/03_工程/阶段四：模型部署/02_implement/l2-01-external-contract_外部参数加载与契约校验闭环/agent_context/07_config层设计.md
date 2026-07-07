# config 层设计 — L2-01 外部参数加载与契约校验闭环

> `l2_id`：`l2-01-external-contract`
> 上游边界来源：`01_L1_ACT功能模块边界.md` L2-01 段 + `02_L1_ACT功能模块协作架构.md`。本文件任务边界继承自当前 L1/L2 功能边界，**不**来自旧 layer-based L2 卡片（`l2-02-config`）。

## 目标源码路径

```text
src/model_deploy/act/config/
└── schema.py
```

> 配置**实例**（具体 yaml 值）不放这里，放 `src/model_deploy/act/config_files/deploy.yaml`。

## 层职责（来自 ACT 代码树分层约束）

配置 schema、配置对象、配置校验。禁止业务计算、ROS node、模型推理。`config/` 依赖 `types`（不反向）。

## 文件设计

### schema.py

- 文件职责：定义 `DeployConfig` 聚合根 + 子配置 dataclass + 类型化校验器 + 配置装配编排 + bundle/normalizer contract 元数据校验 + `load_deploy_config` 入口。
- class 设计（全部 frozen dataclass + `__post_init__` 校验）：
  - `BundleConfig`：`bundle_dir`、`resolved_bundle_dir` 属性。
  - `RuntimeConfig`：`mode`/`device`/`dtype`/`inference_hz`/`control_hz`/`chunk_size`/`execute_horizon`/`prefetch_steps`/`blend_steps`/`action_dim`(=16)/`state_dim`(=16)/`fallback_policy`/`max_delta_per_step`/`max_action_age_sec` 等。`__post_init__` 校验：hz>0、`execute_horizon ≤ chunk_size`、`prefetch_steps ≤ execute_horizon`、`fallback_policy ∈ {hold_last_action, continue_old_chunk, safe_stop}` 等。
  - `SafetyConfig`：`max_delta_per_step`/`stale_observation_timeout_s`/`command_timeout_s`/`gripper_width_min`/`gripper_width_max` + **新增占位字段** `max_tcp_step`（TCP 单步位移上限，默认占位 None/由 L2-05 填）、`check_quaternion_norm`（quaternion 归一化检查开关，默认占位 True/阈值由 L2-05 填）。这些占位字段保证 L2-05 能读取，具体数值留待 L2-05 细化。
  - `TopicsConfig` + 子配置：`namespace`(=/act) + observation/command/status/metrics topic 名。
  - `ImageConfig`：`image_size`/`resize_mode`/`transport`。
  - `DeployConfig`（聚合根）：`bundle`/`runtime`/`image`/`topics`/`safety`/`raw`。`from_mapping(raw, base_dir)` classmethod。
- 函数设计（纯函数）：
  - 类型化校验器群：`_str`/`_choice`/`_bool`/`_positive_int`/`_positive_float`/`_non_negative_int`/`_float_list`/`_path`/`_mapping` 等（非法抛 `DeployConfigError` 等价物）。
  - 装配编排：`_deploy_from_mapping(raw, base_dir) -> DeployConfig`（调用顺序：bundle→runtime→image→topics→safety）。
  - 入口：`load_deploy_config(path) -> DeployConfig`（读 yaml + 委托 from_mapping）。入口位置已定：`config/schema.py`。
  - contract 校验：`check_bundle_contract(manifest, exp_config, runtime) -> BundleContractResult`、`check_normalizer_contract(state_norm, action_norm, state_spec, action_spec) -> NormalizerContractResult`。
- 输入/输出：
  - `load_deploy_config`：yaml 路径 → `DeployConfig`。
  - 校验器：raw dict + key → 类型化值/异常。
  - contract 校验：manifest/exp_config/normalizers + specs → `*ContractResult`。
- 副作用：`load_deploy_config` 读文件（跨进程），其余纯 RAM 计算。
- 依赖方向：`config` → `types`（用 ActionSpec/StateSpec/ContractResult）+ `repo`（load_deploy_config 调 repo 读文件）。不反向。
- Pi0.5 参考：`deploy/config/schema.py`（全套 frozen dataclass + 校验器 + `from_mapping`，**强复用**）；去 bridge/mux；dims 改 16。contract 元数据校验是 ACT 补强（Pi0.5 无）。
- 验收覆盖：单测——合法配置构造成功；各类非法配置（缺字段/dim 非 16/hz 非法/关系违反）抛异常；contract 三处 dim 不一致被判 fail。

## 边界继承声明

本文件的 `config/` 任务边界来自当前 L1/L2 功能边界（L2-01 负责配置 schema 与校验），不是旧 `l2-02-config` layer-based 卡片。旧卡片是隔离区历史快照，不作权威。

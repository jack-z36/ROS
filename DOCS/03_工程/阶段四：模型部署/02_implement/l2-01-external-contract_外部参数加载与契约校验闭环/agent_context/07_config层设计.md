# config 层设计：L2-01

## 1. 目标源码路径

```text
src/model_deploy/act/config/schema.py
src/model_deploy/act/config_files/deploy.yaml
```

## 2. 层职责

`config/` 定义配置 schema、配置对象和配置校验。具体 `.yaml` 配置实例放 `config_files/`。

## 3. schema.py 设计

### class 设计

- `DeployConfig`：聚合根配置对象。
- `BundleConfig`：bundle 路径和 checkpoint 路径。
- `RuntimeConfig`：`mode`、`control_hz`、`inference_hz`、`chunk_size`、`max_action_age_sec`、`fallback_policy` 等第一版最小运行时配置。
- `SafetyConfig`：单步 TCP 限制、quaternion 检查、gripper width 值域。
- `TopicsConfig`：`/act/*` observation、policy_action、status、metrics、command topic。
- `ImageConfig`：图像尺寸、resize、transport。

### 函数设计

- `load_deploy_config(path) -> DeployConfig`
- `DeployConfig.from_mapping(raw, base_dir) -> DeployConfig`
- `_str`、`_choice`、`_positive_int`、`_positive_float`、`_bool` 等类型化校验器。
- `check_bundle_contract(...) -> BundleContractResult`
- `check_normalizer_contract(...) -> NormalizerContractResult`

## 4. 明确不定义的平滑配置

第一版已去除独立平滑处理。`RuntimeConfig`、默认 `deploy.yaml` 和 schema 校验不得定义：

```text
blend_steps
smoothstep_window
smoothstep_alpha
cross_chunk_fusion
chunk_blend_mode
rtc_alignment
action_smoothing
```

如果未来需要这些能力，必须作为后续优化重新设计 L1/L2 边界和 Gate。

## 5. 依赖方向

`config` 可以依赖 `types` 和 `repo` 的读取结果；`types`、`repo`、`service`、`runtime`、`ui` 不得反向依赖 config 内部实现细节，只读取公开配置对象。

## 6. 验收覆盖

- 合法 mapping 构造成功。
- 缺字段、非法 hz、非法 mode、维度非 16 抛异常。
- `rg` 检查默认配置和 schema 不包含第一版外平滑字段。

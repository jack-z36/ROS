# repo 层设计：L2-03

## 1. 目标源码路径

```text
src/model_deploy/act/repo/policy_loader.py
```

bundle 读取复用 L2-01 的产物：

```text
src/model_deploy/act/repo/bundle_reader.py        # L2-01
src/model_deploy/act/repo/manifest_parser.py      # L2-01
src/model_deploy/act/repo/normalizer_loader.py    # L2-01
src/model_deploy/act/repo/experiment_config_loader.py  # L2-01
```

## 2. 层职责

`repo/` 负责进程外资源读取和反序列化。L2-03 在这一层加载 ACT policy runtime（真实权重或 fake）+ preprocessor + normalizer，把进程外 bundle 变成进程 RAM 里的 policy runtime 对象。

## 3. 文件设计

### policy_loader.py

- **职责**：根据 `DeployConfig` 加载真实或 fake 的 `ActPolicyRuntime`，持有统一推理接口 `predict_action_chunk`。
- **class 设计**：

```text
ActPolicyRuntime（真实 + fake 共用接口）
  封装微元：
    - 数据：model/policy/preprocessor/state_normalizer/action_normalizer/device/task/action_dim(16)/output_chunk_size/image_names/_predict_fn
    - 计算函数：_build_batch（snapshot→batch）、shape 校验
    - 编排函数：predict_action_chunk（build_batch→preprocess→device→predict→unnormalize→clamp→校验→截断）
    - 内部状态更新函数：_maybe_compile（可选 torch.compile）
  内部状态：model/policy/preprocessor/normalizer（稳定只读）；_predict_fn（可能被 compile 包裹）
  生命周期：启动期创建一次，稳态被 InferenceWorker 串行调用，无并发
  为什么 class：持有大量稳定状态（权重、normalizer），多次 predict 共享
  Pi0.5 参考：Pi05PolicyRuntime（结构复用；模型替换 Pi0.5 VLA → ACT；维度 14→16）
```

- **函数设计**：

| 函数 | 类型 | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|
| `load_act_policy_runtime(config)` | 编排+数据读写 | DeployConfig | ActPolicyRuntime（真实或 fake） | 读 bundle + 加载权重到 GPU（fake 跳过） | `load_policy_runtime`（结构复用） |
| `_build_act_policy_runtime_real(...)` | 编排+数据读写 | bundle artifacts + config | ActPolicyRuntime | 加载 ACT 权重 | `load_policy_runtime` 主干 |
| `_build_act_policy_runtime_fake(config)` | 编排 | DeployConfig | ActPolicyRuntime（fake） | 无（不加载权重） | ACT 增量 |
| `_validate_inference_bundle(bundle_dir)` | 数据读写 | bundle_dir | None / FileNotFoundError | stat 文件 | `_validate_bundle`（结构复用，复用 L2-01 bundle_reader） |
| `_resolve_act_policy(model)` | 计算 | model | policy object | 无 | `_resolve_policy`（简化，ACT 无 LoRA 包裹） |
| `_build_act_preprocessor(...)` | 计算 | config | preprocessor | 无 | `make_pi05_pre_post_processors`（替换为 ACT processor） |
| `_move_tensors_to_device(value, device)` | 内部状态更新 | Any | 同结构 device 已移动 | pin_memory + non_blocking | 直接复用 |
| `_require_cpu_float_tensor(tensor, name)` | 计算 | Tensor | CPU float Tensor | 无 | 直接复用 |
| `_configure_cuda_runtime(device)` | 内部状态更新 | device | None | 设全局精度/SDP | 直接复用 |
| `_manifest_image_names(manifest)` | 计算 | manifest dict | tuple[str,...] | 无 | 直接复用 |

- **不负责**：不做 ROS topic 读写（属 L2-02/L2-05）；不安排后台线程（属 runtime `InferenceWorker`）；不做 batch 构造的纯计算（可拆到 service 层 `batch_adapter.py`，或作为 `ActPolicyRuntime._build_batch` method 保留，见 `09_service层设计.md`）；不做单步选择/cursor（属 L2-06）；不做平滑。
- **依赖方向**：`repo` → `types`（16D 常量）、`config`（DeployConfig）；复用 L2-01 的 `bundle_reader`/`manifest_parser`/`normalizer_loader`/`experiment_config_loader`。禁止 import `service`/`runtime`/`ui`。
- **Pi0.5 参考**：`deploy/src/pi05/deploy/models/policy_loader.py`（结构复用，模型与维度重写）。
- **验收覆盖**：fake-policy 构造成功且 `predict_action_chunk` 返回 `(chunk_size,16)`；缺 bundle 文件抛异常；real-policy dry-run 输出同 shape。

## 4. 与 L2-01 的复用关系

L2-01 已经落地了 bundle 读取四件套。本 L2 的 `load_act_policy_runtime` 直接调用：

```text
L2-01 bundle_reader.resolve_bundle_dir / resolve_bundle_adapter_dir
L2-01 manifest_parser.load_manifest
L2-01 normalizer_loader.load_normalizers
L2-01 experiment_config_loader.load_experiment_config
```

不重复实现这些读取函数。normalizer 长度校验（==16）由 L2-01 契约层完成，本 L2 信任该结果。

## 5. 边界继承声明

本文件边界来自当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。不继承 Pi0.5 的 `build_pi05_with_lora`/`PI05Policy` 作为 ACT 模型构建方式。

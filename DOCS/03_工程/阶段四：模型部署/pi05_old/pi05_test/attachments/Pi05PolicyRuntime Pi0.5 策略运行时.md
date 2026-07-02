---
tags:
  - 附件
---

# Pi05PolicyRuntime Pi0.5 策略运行时

> [!abstract]
> 把"导出 bundle"装成"可调用的推理函数"——加载 LoRA adapter、构建 LeRobot preprocessor、配 min-max normalizer、（可选）`torch.compile` 优化。**部署侧**唯一调用点：`predict_action_chunk(observation) → np[chunk_size, 14]`。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `Pi05PolicyRuntime` |
| 数据类型 | `class`（`policy_loader.py:27-108`） |
| 数据结构 | 9 字段 + 1 个可调用推理方法 |
| 所在文件 | `pi05/deploy/src/pi05/deploy/models/policy_loader.py:27-108` |
| 现实含义 | 部署侧的"模型门面" |

## 9 字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `model` | `torch.nn.Module` | `build_pi05_with_lora()` 构造的 Pi0.5 + LoRA |
| `policy` | `Any` | 持有 `predict_action_chunk` 的对象（PEFT 包裹层） |
| `preprocessor` | `Any` | LeRobot `make_pi05_pre_post_processors()` 产出的 preprocessor（**CPU**） |
| `state_normalizer` | `Any` | 从 `normalizers.json` 加载的 min-max normalizer |
| `action_normalizer` | `Any` | 同上，动作侧反归一化器 |
| `device` | `torch.device` | `cuda:0`（默认）或 `cpu` |
| `task` | `str` | 语言指令，例 `"bimanual manipulation"` |
| `action_dim` | `int` | 14（由 bundle manifest 决定） |
| `output_chunk_size` | `int` | 30（与 `RuntimeConfig.chunk_size` 一致） |
| `clamp_normalized_action` | `bool` | 推理输出是否裁到 [-1, 1] |
| `image_names` | `tuple[str,...]` | bundle 要求的图像 key 列表 |
| `compile_enabled` | `bool` | `torch.compile` 是否成功启用 |

## 推理一次：7 步流水线

```python
# policy_loader.py:63-78
def predict_action_chunk(self, observation):
    batch = self.preprocessor(self._build_batch(observation))   # 1. CPU 端打包成 LeRobot batch
    batch = _move_tensors_to_device(batch, self.device)         # 2. pin_memory + non_blocking 搬运到 GPU
    with torch.inference_mode():
        norm_chunk = self._predict_fn(batch)                    # 3. 模型前向（可能被 torch.compile 包了）
    norm_chunk = norm_chunk.detach().cpu().to(torch.float32)[0] # 4. 回到 CPU + 去掉 batch 维
    if self.clamp_normalized_action:
        norm_chunk = norm_chunk.clamp(-1.0, 1.0)                # 5. 裁到归一化区间
    action_chunk = self.action_normalizer.unnormalize(norm_chunk).numpy().astype(np.float32)
    if action_chunk.ndim != 2 or action_chunk.shape[1] != self.action_dim:
        raise ValueError(...)                                   # 6. 形状校验
    return action_chunk[: self.output_chunk_size]               # 7. 截到 chunk_size
```

> 注释（`policy_loader.py:65-67`）明确警告：preprocessor 必须在 CPU 上跑，因为 `Pi05PrepareStateTokenizerProcessorStep` 用 NumPy 离散化 state，提前迁 GPU 会强制 sync 拖慢。

## _build_batch：构造模型输入

```python
batch = {
    "observation.state": state_normalizer.normalize(
        torch.as_tensor(observation.encoded_state, dtype=torch.float32)
    ),
    "task": self.task,
    "observation.images.<name>": observation.images[<name>]  # 每张图
}
```

> 注意：图像此时还是 raw `torch.float32[3,224,224]` 张量，**还没过** policy preprocessor 的 `NormalizeImageProcessorStep`（mean/std 归一化）；那是 `self.preprocessor(...)` 之后的事。

## 加载流程（load_policy_runtime）

1. `_validate_bundle()`：断言 `manifest.json / normalizers.json / experiment.yaml` 存在
2. `load_bundle_manifest()` → 读 `image_names`
3. `_load_bundle_experiment_config()`：用 bundle 内 `experiment.yaml` + `DeployConfig.runtime` 覆盖 device/dtype/chunk_size
4. `build_pi05_with_lora()` → 构造 base model + LoRA
5. `_load_adapter()` → `safetensors` 装 LoRA 权重
6. `model.to(device).eval()`
7. `_configure_cuda_runtime()`：开 Flash SDP / Mem-efficient SDP / float32 matmul high
8. `make_pi05_pre_post_processors()`（device=CPU）
9. `load_bundle_normalizers()` → state / action 归一化器
10. （可选）`_maybe_compile()` → `torch.compile(mode="reduce-overhead")`

## 在数据流中的位置

- 加载方：`Pi05VlaDeployNode.__init__()` 调 `load_policy_runtime(config)`
- 调用方：`InferenceWorker._run_request()` 调 `policy_runtime.predict_action_chunk(request.observation)`
- 返回值：被 `InferenceWorker` 装进 [[ActionChunk 动作块 dataclass]] 投入 `result_queue`

## 相关概念

- [[InferenceWorker 推理后台线程]]：唯一调用方
- [[ObservationSnapshot 冻结的观测]]：推理输入
- [[ActionChunk 动作块 dataclass]]：推理产物的容器
- [[ACTION_DIM 14D action schema]]：输出向量维度的契约
- [[STATE_DIM 26D state schema]]：输入 state 向量维度的契约
- [[ActionStateNormalizer min-max 归一化]]：state / action 归一化器

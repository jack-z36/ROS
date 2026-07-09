# config 层设计：L2-03

## 1. 本 L2 不在该层新增源码产物

原因：

- `config/` 只放配置 schema、配置对象、配置校验，不放业务计算、不放 ROS node、不放模型推理。
- L2-03 的推理参数（device / dtype / chunk_size / inference_hz / task / compile_model / compile_mode / clamp_normalized_action）全部来自 L2-01 的 `DeployConfig.runtime` 和 `DeployConfig.safety`。
- 本 L2 不新增配置 schema，直接 import 复用 `DeployConfig`。

## 2. 复用的 config 产物

| 对象 | 来源 | L2-03 使用方式 |
|---|---|---|
| `DeployConfig.bundle.resolved_bundle_dir` | L2-01 | 传给 `load_act_policy_runtime` 定位 bundle |
| `DeployConfig.runtime.device` / `dtype` | L2-01 | 决定模型加载设备与精度 |
| `DeployConfig.runtime.chunk_size` | L2-01 | 决定 `output_chunk_size`（输出截断） |
| `DeployConfig.runtime.inference_hz` / `control_hz` | L2-01 | `InferenceWorker` 限速 / `action_dt=1/control_hz` |
| `DeployConfig.runtime.task` | L2-01 | batch 中的 task 文本 |
| `DeployConfig.runtime.compile_model` / `compile_mode` | L2-01 | 可选 `torch.compile` 优化 |
| `DeployConfig.safety.clamp_normalized_action` | L2-01 | 推理后是否 clamp 到 [-1,1] |
| `DeployConfig.runtime.mode` | L2-01 | 决定 fake/real policy 分支（dry-run 默认 fake） |
| `DeployConfig.runtime.max_inference_requests` / `max_pending_chunks` | L2-01 | SharedBuffer 的 LatestQueue maxsize |

## 3. 明确不新增的配置

- 不新增 `blend_steps`、`smoothstep_window`、`cross_chunk_fusion`、`rtc_alignment`、`action_smoothing` 字段（第一版不做平滑）。
- 不新增独立的"inference config" schema，避免与 L2-01 的 `RuntimeConfig` 重复。
- 不覆写 `experiment_config.yaml` 的维度值（保留原值做交叉校验，与 Pi0.5 `_load_bundle_experiment_config` 覆写维度的行为不同——ACT 不死锁维度）。

## 4. 验收如何确认

- L2-03 不产生 `src/model_deploy/act/config/*.py` 产物。
- `rg` 检查 L2-03 代码中 `blend_steps`/`smoothstep` 等无作为可配置字段出现。

## 5. 边界继承声明

本文件边界来自当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

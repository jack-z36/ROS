---
tags:
  - learning/pi05
  - deploy/bundle
  - ros/pi05
aliases:
  - Pi05 deploy bundle
  - deploy bundle loading path
---

# Pi05 deploy bundle：作用与加载路径

关联契约：[[AS-IS Contract.md|AS-IS Contract]]

> [!abstract]
> 本文只回答一个问题：deploy bundle 是什么，它在 ROS2 部署拓扑网络中是如何被加载的，以及最终加载到哪个节点 / 对象里。

## 1. 一句话回答

deploy bundle 是训练后导出的模型运行包。它在 `Pi05VlaDeployNode` 初始化时被加载，被组装成 `Pi05PolicyRuntime` 对象，然后传入 `InferenceWorker` 做后台模型推理。

它不是由 `Pi05BridgeNode`、`CommandMuxNode` 或 picotele 加载的。

## 2. 它在部署拓扑网络中的位置

```text
deploy/config/deploy.yaml
  bundle.bundle_dir
        |
        v
Pi05VlaDeployNode.__init__()
        |
        v
load_policy_runtime(config)
        |
        v
Pi05PolicyRuntime
        |
        v
InferenceWorker
        |
        v
predict_action_chunk(observation)
        |
        v
ActionChunk -> ControlLoop -> SafetyGuard -> /pi05_vla/command/*
        |
        v
Pi05BridgeNode -> CommandMuxNode -> picotele / downstream execution stack
```

重要的边界是这样的：

```text
deploy bundle 在 Pi05VlaDeployNode 进程内被消费。
bridge / mux / picotele 只会看到模型产生 command 之后的 ROS topic。
```

## 3. 哪个节点加载？

触发 deploy bundle 加载的实际 ROS2 节点是：

```text
Pi05VlaDeployNode
```

在源代码中，它的初始化是这样的：

```python
self.get_logger().info(f"loading Pi0.5 policy bundle: {config.bundle.resolved_bundle_dir}")
policy_runtime = load_policy_runtime(config)
self.policy_image_names = policy_runtime.image_names
self.collector.set_required_image_keys(self.policy_image_names)
self.inference_worker = InferenceWorker(policy_runtime=policy_runtime, ...)
```

所以它的归属链是：

```text
Pi05VlaDeployNode
  owns InferenceWorker
    owns / receives Pi05PolicyRuntime
      contains model + preprocessor + normalizers + image_names
```

更准确地说，`Pi05VlaDeployNode` 创建 `policy_runtime`，然后把它注入 `InferenceWorker`。模型推理工作稍后在 worker 线程中进行，但加载由部署节点的 constructor 触发。

## 4. deploy bundle 里到底加载了什么？

| bundle 文件 | 加载函数 | 对运行时的影响 |
|---|---|---|
| `manifest.json` | `load_bundle_manifest(bundle_dir)` | 读取相机列表和动作维度。相机列表变为`policy_runtime.image_names`，然后控制`ObservationCollector`必须接收哪些图像 topic。 |
| `experiment_config.yaml` | `_load_bundle_experiment_config(bundle_dir, config)` | 重建 Pi0.5 模型和 LoRA 结构。某些字段会被`deploy.yaml.runtime`覆盖，例如设备、数据类型、chunk size、状态维度和action 维度。 |
| `adapter/adapter_model.safetensors` | `_load_adapter(model, resolve_bundle_adapter_dir(bundle_dir), device=device)` | 将经过训练的 LoRA adapter 权重加载到重建的 Pi0.5 模型中。 |
| `normalizers.json` | `load_bundle_normalizers(bundle_dir)` | 加载状态归一化器和动作归一化器。在模型推理之前对状态进行归一化；模型动作输出在控制前反归一化。 |

## 5. 为什么需要 deploy bundle

部署程序无法仅从代码运行经过训练的策略。它需要 deploy bundle，因为 deploy bundle 提供了四个合约：

| 契约 | 为什么部署需要它 |
|---|---|
| 模型结构契约 | `experiment_config.yaml` 告诉部署如何重建 Pi0.5 + LoRA 模型骨架。 |
| 权重契约 | `adapter_model.safetensors` 提供经过训练的特定于任务的 LoRA 权重。 |
| 输入契约 | `manifest.json` 告诉部署模型需要哪些相机。 |
| 尺度契约 | `normalizers.json` 告诉部署如何将物理状态/动作数字映射到模型尺度并返回。 |

如果没有 deploy bundle，节点可能仍然知道 ROS 拓扑，但它不知道训练的模型、adapter 权重、所需的相机名称或归一化尺度。

## 6. deploy bundle 不做什么

deploy bundle 不会：

- 自行创建 ROS topic；
- 自行订阅 sensor；
- 自行发布机器人 command；
- 决定 teleop 与 VLA 控制；
- 与硬件 SDK 对话；
- 运行 bridge、mux 或 picotele。

这些是 runtime 节点的职责。该 deploy bundle 只是 `Pi05VlaDeployNode` 加载的、被打包的模型侧知识。

## 7. 最小加载顺序

```text
1. deploy_ros CLI loads deploy.yaml
2. deploy.yaml gives config.bundle.resolved_bundle_dir
3. Pi05VlaDeployNode starts
4. Pi05VlaDeployNode calls load_policy_runtime(config)
5. load_policy_runtime validates bundle files
6. load_policy_runtime reads manifest.json
7. load_policy_runtime reads experiment_config.yaml
8. build_pi05_with_lora(...) rebuilds model structure
9. _load_adapter(...) injects LoRA weights
10. load_bundle_normalizers(...) loads state/action normalizers
11. Pi05PolicyRuntime is returned
12. Pi05VlaDeployNode passes Pi05PolicyRuntime into InferenceWorker
13. InferenceWorker uses it to call predict_action_chunk(...)
```

## 8. 最需要避免的误解

不要将 deploy bundle 想象为额外的 ROS2 节点。

它不是一个节点。它不是一个 topic。它不是一个 service。

它是磁盘上的一个目录，在 Pi05 部署启动期间读取一次，然后转换为 `InferenceWorker` 使用的内存中运行时对象。

## 9. 依据位置

- 图：“load_policy_runtime()”位于“pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py:L110”中。
- 图：`Pi05VlaDeployNode`位于“pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py:L29”中。
- 源码：`Pi05VlaDeployNode.__init__()` 在第 68-74 行左右调用 `load_policy_runtime(config)`。
- 源码：“load_policy_runtime()”在第 117-149 行左右验证 deploy bundle、加载清单、实验配置、适配器和归一化器。

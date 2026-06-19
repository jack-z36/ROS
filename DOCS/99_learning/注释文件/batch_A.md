---
tags:
  - ROS
  - Pi05
  - term
  - data-definition
---

# batch_A

> [!abstract] 核心定义
> `batch_A` 是 `_build_batch()` 从 `ObservationSnapshot` 翻译出来的 LeRobot/Pi0.5 原始输入字典。

## 数据结构

| 字段名                           | 类型             | 含义           | 是否必填                       |
| ----------------------------- | -------------- | ------------ | -------------------------- |
| `observation.state`           | `torch.Tensor` | 归一化后的机器人状态向量 | 是                          |
| `task`                        | `str`          | 当前任务文本       | 是                          |
| `observation.images.<camera>` | `torch.Tensor` | 每一路相机图像      | 是，具体相机由 bundle manifest 决定 |

## 生产者与消费者

| 角色 | 对象 |
|---|---|
| 生产者 | `Pi05PolicyRuntime._build_batch(observation)` |
| 消费者 | 官方 `preprocessor(batch_A)` |

## 运行逻辑

1. 读取 `ObservationSnapshot.encoded_state`。
2. 用 `state_normalizer.normalize()` 做状态归一化。
3. 写入 `observation.state`。
4. 写入 `task`。
5. 按 `image_names` 写入 `observation.images.<camera>`。

## 具象隐喻

> [!tip] 生活场景类比
> `ObservationSnapshot` 像一堆原材料，`batch_A` 像按官方菜单摆好的饭盒：米饭放一格，菜放一格，汤放一格。官方 processor 不认识“原材料袋”，但认识这种固定格式的饭盒。

## 源码证据

- `pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py:80-95`


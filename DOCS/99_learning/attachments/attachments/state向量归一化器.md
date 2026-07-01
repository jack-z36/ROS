---
tags:
  - 附件
---

# state向量归一化器

> [!abstract]
> 一句话说明：这是 `observation.state` 的 min-max 归一化器，负责把机器人状态向量映射到模型期望的尺度。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `state_normalizer`, `payload["state"]` |
| 参考系 | 模型特征尺度空间 |
| 相对原点 | 训练数据集中 `observation.state` 每个维度的 `min` |
| 物理锚点 | 物理对象状态；整体描述机器人状态向量，不是单一空间点 |
| 阶段属性 | 中间对象，其参数会序列化 |
| 是否最终输出 | 部分是；内存对象不是，参数进入 [[normalizers.json归一化契约]] |
| 数据类型 | `ActionStateNormalizer` |
| 数据结构 | 多个标量共同描述 state 向量各维度的 min/max/identity 规则 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:46,71-77,155-170` |
| 现实含义 | 部署时对观测 state 做与训练一致的尺度转换 |

## 关键澄清

### 1. 它在哪个参考系下？
在模型特征尺度空间下，不是 base/local 等几何坐标系。

### 2. 它相对哪个原点？
每个维度相对训练数据统计出的 `min_vals`；归一化公式把范围映射到 `[-1, 1]`。

### 3. 它对应哪个物理点 / 物理对象？
它对应机器人观测状态向量的尺度规则，不对应单一物理点。

### 4. 它是不是最终输出？
内存对象不是最终文件；其 `min/max/identity_indices` 是最终 JSON 的一部分。

### 5. 它不是什么？
它不是 state 数据本身，也不是模型权重；它只是 state 数据的尺度转换器。

## 对应源码

```python
state_normalizer, action_normalizer = build_state_action_normalizers(dataset)
...
state_payload = payload["state"]
state_normalizer = ActionStateNormalizer(
    min_vals=state_payload["min"],
    max_vals=state_payload["max"],
    identity_indices=state_payload.get("identity_indices"),
)
```

## 一句话说清楚

> `state_normalizer` 保存 `observation.state` 每个维度如何从物理/数据尺度进入模型尺度。

## 在数据流中的位置

- 上游：[[LeRobotDataset统计来源]]
- 下游：[[normalizers.json归一化契约]]、部署侧 `Pi05PolicyRuntime`


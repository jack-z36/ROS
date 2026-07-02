---
tags:
  - 附件
---

# action向量归一化器

> [!abstract]
> 一句话说明：这是 `action` 的 min-max 归一化器，部署时主要用于把模型输出从归一化尺度还原为机器人动作尺度。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `action_normalizer`, `payload["action"]` |
| 参考系 | 模型动作尺度空间 |
| 相对原点 | 训练数据集中 `action` 每个维度的 `min` |
| 物理锚点 | 物理对象动作命令集合；整体描述动作向量，不是单一空间点 |
| 阶段属性 | 中间对象，其参数会序列化 |
| 是否最终输出 | 部分是；参数进入 [[normalizers.json归一化契约]] |
| 数据类型 | `ActionStateNormalizer` |
| 数据结构 | 多个标量共同描述 action 向量各维度的 min/max/identity 规则 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:46,78-83,155-170` |
| 现实含义 | 让部署动作尺度与训练数据动作尺度一致 |

## 关键澄清

### 1. 它在哪个参考系下？
在模型动作特征尺度空间下，不是机器人几何坐标系。

### 2. 它相对哪个原点？
每个动作维度相对训练数据统计出的 `min_vals`。

### 3. 它对应哪个物理点 / 物理对象？
它对应动作向量的尺度规则，不对应单一物理点。

### 4. 它是不是最终输出？
内存对象不是；其可 JSON 化参数是最终输出的一部分。

### 5. 它不是什么？
它不是模型预测出的动作，也不是控制循环；它只是动作尺度转换器。

## 对应源码

```python
action_normalizer = ActionStateNormalizer(
    min_vals=action_payload["min"],
    max_vals=action_payload["max"],
    identity_indices=action_payload.get("identity_indices"),
)
```

## 一句话说清楚

> `action_normalizer` 保存模型动作维度和真实动作尺度之间的反归一化规则。

## 在数据流中的位置

- 上游：[[LeRobotDataset统计来源]]
- 下游：[[normalizers.json归一化契约]]、部署侧 `Pi05PolicyRuntime`


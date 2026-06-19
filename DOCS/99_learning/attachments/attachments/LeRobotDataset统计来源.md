---
tags:
  - 附件
---

# LeRobotDataset统计来源

> [!abstract]
> 一句话说明：这是导出时重新打开的训练数据集对象，只用于生成 state/action 归一化统计，不作为文件写入 bundle。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `dataset` |
| 参考系 | 数据集索引与特征命名空间 |
| 相对原点 | `config.data.resolved_dataset_path` 指向的数据集根目录 |
| 物理锚点 | 物理对象状态集合；每行样本描述机器人观测和动作 |
| 阶段属性 | 中间运行时对象 |
| 是否最终输出 | 否 |
| 数据类型 | `LeRobotDataset` |
| 数据结构 | 数据集对象，提供 `observation.state` 和 `action` 等向量特征 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:42-46` |
| 现实含义 | 训练数据的统计来源，用来恢复模型输入/输出尺度 |

## 关键澄清

### 1. 它在哪个参考系下？
不是几何坐标系；它处于 LeRobot 数据集的特征命名空间下。

### 2. 它相对哪个原点？
相对数据集根目录 `config.data.resolved_dataset_path`。

### 3. 它对应哪个物理点 / 物理对象？
它整体对应采集到的机器人状态与动作样本集合，不对应单一物理点。

### 4. 它是不是最终输出？
不是。它只在导出期间存在，用来生成 [[state向量归一化器]] 和 [[action向量归一化器]]。

### 5. 它不是什么？
它不是 bundle 的内容；bundle 不复制整个训练数据集。

## 对应源码

```python
dataset = LeRobotDataset(
    repo_id=config.data.resolved_dataset_path.name,
    root=config.data.resolved_dataset_path,
)
state_normalizer, action_normalizer = build_state_action_normalizers(dataset)
```

## 一句话说清楚

> `dataset` 是导出时临时打开的训练数据统计源，帮助 bundle 携带正确的归一化尺度。

## 在数据流中的位置

- 上游：[[ExperimentConfig训练打包配置]]
- 下游：[[state向量归一化器]]、[[action向量归一化器]]


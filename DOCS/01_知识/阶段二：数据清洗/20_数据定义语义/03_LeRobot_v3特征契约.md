# LeRobot v3 特征契约

## 定位

LeRobotDataset v3 是阶段二当前目标数据格式。阶段二负责把 aligned MCAP 中的语义字段组织成 LeRobot 可读取的 observation/action 数据，并为 PI0.5 / ACT 训练前检查提供输入。

## observation.state

`observation.state` 由启用的 state segments 顺序拼接而成。当前稳定概念包括：

- 左右 arm-base TCP pose。
- 左右夹爪宽度。
- 四路触觉统计。

左右 TCP pose 是必选段落。夹爪和触觉属于可配置段落，具体是否启用、维度和 offset 以当前 feature contract 为准。

## action

`action` 由启用的 action segments 顺序拼接而成。当前语义是下一 step 的绝对目标：

```text
action_t = target at step t+1
```

左右 TCP pose 目标是必选段落。夹爪目标可配置。最后一帧因为没有 `t+1` action，会在构建时被丢弃。

## 不写死维度

知识文档不得把 `observation.state=32` 或 `action=16` 当作唯一合格形态。训练前体检应按当前 job 的 LeRobot feature contract 判断实际维度是否匹配。

## 详细内容

- feature contract 源码：`src/data_clean/schemas/lerobot_features.py`
- Forge bridge 实现：`src/data_clean/service/forge_bridge.py`
- 训练前体检：`src/data_clean/service/training_readiness.py`

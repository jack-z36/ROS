---
tags:
  - 附件
---

# ACTION_DIM (14D action schema)

> [!abstract]
> 14 维动作向量，pi05 模型预测的输出，由左右臂各 6 维位置指令 + 左右手各 1 维张合指令拼接而成。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `ACTION_DIM` |
| 数据类型 | `int` (Python) / `float32[14]` (numpy) |
| 数据结构 | 标量（维度数）+ 14 维向量（实际动作） |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:167-170` |
| 现实含义 | 灵巧手双手机器人每个时间步要发给下位机的"目标关节角+张合量" |

## 维度拆分

```
action[0:6]   = left_arm_cmd_pos0..5   (左臂 6 DoF 目标关节角)
action[6:12]  = right_arm_cmd_pos0..5  (右臂 6 DoF 目标关节角)
action[12:13] = left_hand_cmd_pos0     (左手 1 DoF 张合指令)
action[13:14] = right_hand_cmd_pos0    (右手 1 DoF 张合指令)
```

派生自：`ARM_DOF=6`、`HAND_DOF=1`、`ACTION_DIM = 2*ARM_DOF + 2*HAND_DOF = 14`。

## 示例

```python
import numpy as np
action14 = np.array(
    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6,   # 左臂
     0.1, 0.2, 0.3, 0.4, 0.5, 0.6,   # 右臂
     0.7,                              # 左手中指张合 0~1
     0.7],                             # 右手中指张合
    dtype=np.float32,
)
```

## 在数据流中的位置

- **上游**：`_convert_one_mcap_into_dataset` 第 1989–1997 行将 `arm_cmd_value`（前 6 维）+ `arm_cmd_value`（后 6 维）+ 双手 cmd 张合拼成 `action14`
- **下游**：经 `_pack_action` 写入 `frame["action"]`，最终落到 `LeRobotDataset.add_frame`

## 关键约束

- **action 维度锁死 14**：即使 `observation.state` 因加入 EE pose 扩到 26 维，action 也不扩维（见源码第 169 行注释 "action 维度不随 observation.state 扩展变化"）
- **HAND_DOF=1 是当前灵巧手的简化**：未来升级到 6 DoF 独立手指时，只改 `HAND_DOF` 常量，action 维度会同步变化
- 与 [[STATE_DIM]] 形成对照

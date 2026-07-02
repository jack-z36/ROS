---
tags:
  - 附件
---

# BimanualState 双臂状态

> [!abstract]
> 双臂机器人的**结构化**状态描述——8 个字段把"左臂关节、左夹爪、左末端位姿、右臂关节、右夹爪、右末端位姿"显式列出来，再由 [[encode_bimanual_state|编码器]] 拼成 26 维向量喂给策略。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `BimanualState` |
| 数据类型 | `@dataclass(frozen=True)`（`state_codec.py:13-24`） |
| 数据结构 | 8 字段（4 个标量/向量） |
| 所在文件 | `pi05/common/src/pi05/common/data/state_codec.py:13-24` |
| 现实含义 | 机器人"此刻的物理快照" |

## 8 字段含义

| 字段 | 维度 | 含义 | 来自 |
| --- | --- | --- | --- |
| `left_arm_q` | 6 | 左臂 6 个关节角（rad） | `decode_picotele_proprioception()` |
| `right_arm_q` | 6 | 右臂 6 个关节角（rad） | 同上 |
| `left_hand_q` | 1 | 左手夹爪开合度（300-1000） | `update_hand("left", v)` |
| `right_hand_q` | 1 | 右手夹爪开合度（300-1000） | `update_hand("right", v)` |
| `left_ee_pos` | 3 | 左臂末端笛卡尔位置 `(x,y,z)` | `_point_cb("left_ee_pos")` |
| `left_ee_rpy` | 3 | 左臂末端姿态欧拉角 `(r,p,y)` | `_vec3_cb("left_ee_rpy")` |
| `right_ee_pos` | 3 | 右臂末端笛卡尔位置 | `_point_cb("right_ee_pos")` |
| `right_ee_rpy` | 3 | 右臂末端姿态欧拉角 | `_vec3_cb("right_ee_rpy")` |

> **6+6+1+1+3+3+3+3 = 26**，这正是 [[STATE_DIM 26D state schema]] 维度。

## 编码成 26 维向量

`encode_bimanual_state(state)`（同文件 `state_codec.py:27-43`）按固定顺序拼接：

```
[left_arm_q(6) | right_arm_q(6) | left_hand(1) | right_hand(1) |
 left_ee_pos(3) | left_ee_rpy(3) | right_ee_pos(3) | right_ee_rpy(3)]  # =26
```

每个分量都会用 `state_normalizer.normalize()` 做 min-max 归一化后送入模型。

## 在数据流中的位置

- **生产**：`ObservationCollector.snapshot()` 在锁内检查齐+未 stale 后，锁外构造 `BimanualState(...)`
- **打包**：连同 `images` 与 `captured_at_s` 一起装入 [[ObservationSnapshot 冻结的观测]]
- **消费**：
  - [[SafetyGuard 安全校验器]] 用 `state.left_arm_q / state.right_arm_q` 作为 delta 限速的"锚点"
  - [[Pi05PolicyRuntime Pi0.5 策略运行时]] 用 `state` 算出 `encoded_state` → 模型输入

## 关键不变量

> 1. 8 字段必须**全部到达**且**全部未 stale**，`snapshot()` 才返回（`observation_collector.py:113-131`）
> 2. `proprioception_order` 决定 12 维 JointState 如何拆左右：默认 `"right_left"`（pico 硬件约定），也支持 `"left_right"`
> 3. 任何字段长度不对（不是 6 / 1 / 3）→ `encode_bimanual_state` 抛 `ValueError`

## 相关概念

- [[ObservationCollector 观测收集器]]：唯一生产方
- [[ObservationSnapshot 冻结的观测]]：本结构被冻结后随 snapshot 流转
- [[STATE_DIM 26D state schema]]：本结构编码后的向量维度契约
- [[ACTION_DIM 14D action schema]]：与本结构互为配对（state=26D, action=14D）
- [[SafetyGuard 安全校验器]]：用本结构做限速锚点

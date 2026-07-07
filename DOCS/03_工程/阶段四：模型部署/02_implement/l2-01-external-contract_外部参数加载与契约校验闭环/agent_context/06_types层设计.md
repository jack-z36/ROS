# types 层设计 — L2-01 外部参数加载与契约校验闭环

> `l2_id`：`l2-01-external-contract`
> 上游边界来源：`01_L1_ACT功能模块边界.md` L2-01 段 + `02_L1_ACT功能模块协作架构.md`。本文件任务边界继承自当前 L1/L2 功能边界，**不**来自旧 layer-based L2 卡片（`l2-01-types`）。

## 目标源码路径

```text
src/model_deploy/act/types/
├── action_spec.py
├── state_spec.py
└── contract_result.py
```

## 层职责（来自 ACT 代码树分层约束）

数据结构、常量、维度、段序、codec、result 对象。禁止配置读取、ROS、硬件、模型加载。`types/` 无下游依赖（最上游）。

## 文件设计

### 16D 维度契约（已锁定，源自阶段二数据清洗交付说明）

ACT 部署用 16D state（**去掉触觉**，区别于训练数据的 32D）和 16D action。段序如下：

**observation.state（16D）** —— 段排列："所有左段 → 所有右段"：

| 索引范围 | segment ID | 维度 | 分量 | 单位 | 语义 | 坐标系 |
|:---:|:---|:---:|:---|:---|:---|:---|
| [0, 7) | `left_tcp_pose` | 7 | x, y, z, qx, qy, qz, qw | m + quaternion_xyzw | step t 时左手 arm-base TCP 位姿 | `left_arm_base` |
| [7, 14) | `right_tcp_pose` | 7 | x, y, z, qx, qy, qz, qw | m + quaternion_xyzw | step t 时右手 arm-base TCP 位姿 | `right_arm_base` |
| [14, 15) | `left_gripper_width` | 1 | width | normalized [0,1] | 左夹爪宽度（0=闭合, 1=全开） | - |
| [15, 16) | `right_gripper_width` | 1 | width | normalized [0,1] | 右夹爪宽度（0=闭合, 1=全开） | - |

> 注意：训练数据 state 是 32D（含 4 路触觉 4×4=16），但**部署用 16D**（去触觉）。触觉不进入 ACT 部署的 state。

**action（16D）** —— 段排列："左 pose + 左夹爪 → 右 pose + 右夹爪"（与 state 排列不同，见交付说明 warning）：

| 索引范围 | segment ID | 维度 | 分量 | 单位 | 语义 | 时间偏移 |
|:---:|:---|:---:|:---|:---|:---|:---:|
| [0, 7) | `left_tcp_pose_t_plus_1` | 7 | x, y, z, qx, qy, qz, qw | m + quaternion_xyzw | step t+1 左手绝对 TCP 目标位姿 | +1 step |
| [7, 8) | `left_gripper_width_t_plus_1` | 1 | width | normalized [0,1] | step t+1 左夹爪目标宽度 | +1 step |
| [8, 15) | `right_tcp_pose_t_plus_1` | 7 | x, y, z, qx, qy, qz, qw | m + quaternion_xyzw | step t+1 右手绝对 TCP 目标位姿 | +1 step |
| [15, 16) | `right_gripper_width_t_plus_1` | 1 | width | normalized [0,1] | step t+1 右夹爪目标宽度 | +1 step |

> action 是**绝对动作**（`action_t = target at step t+1`）。左右手 TCP pose 分属 `left_arm_base`/`right_arm_base` 两个独立坐标系。quaternion 用 xyzw 顺序、归一化。

### action_spec.py

- 文件职责：定义 16D action 的维度常量、段序、字段语义、值域，以及 action codec（拆分/拼接/维度校验）。
- class 设计：`ActionSpec`（frozen dataclass）——封装上表 4 个段定义（每段名称/起始/长度/值域）。
- 函数设计：`split_action(flat) -> 结构化视图`（左TCP/左夹爪/右TCP/右夹爪）、`ensure_action_vector(flat) -> 校验`（总维==16，各段长度正确）。
- 输入/输出：flat `[16]` 向量 ↔ 结构化视图。
- 副作用：无。
- 依赖方向：无下游依赖（types 最上游）。
- Pi0.5 参考：`common/robot/action_spec.py`（`BimanualAction`、`ACTION_DIM=14`）、`common/data/action_codec.py`（`ensure_action_vector`）。模式复用，dim 14→16，段语义从"关节角"改为"TCP 位姿+夹爪"。
- 验收覆盖：单测——合法 16D 通过、非法维度抛异常、4 段拼接/拆分正确（注意 action 的左右交替段序）。

### state_spec.py

- 文件职责：定义 16D state 的维度常量、段序、字段语义、值域，以及 state codec。
- class 设计：`StateSpec`（frozen dataclass）——封装上表 4 个段定义（左TCP/右TCP/左夹爪/右夹爪，注意"所有左段→所有右段"排列）。
- 函数设计：`encode_state(结构化) -> flat[16]`、`ensure_state_vector(flat) -> 校验`。
- 输入/输出：结构化状态 ↔ flat `[16]`。
- 副作用：无。
- 依赖方向：无下游依赖。
- Pi0.5 参考：`common/data/state_codec.py`（`BimanualState`、`encode_bimanual_state`、`STATE_DIM=26`）。模式复用，dim 26→16，去触觉，段语义从"关节角+EE"改为"TCP 位姿+夹爪"。
- 验收覆盖：单测——合法 16D 通过、非法维度抛异常、4 段正确（注意 state 的"左段全在前"段序，与 action 不同）。

### contract_result.py

- 文件职责：定义 bundle/normalizer contract 校验的结果对象（Pi0.5 用纯异常，ACT 用显式结果对象便于 L2 Gate 观察）。
- class 设计：`ContractResult`（frozen dataclass，基类）、`BundleContractResult`、`NormalizerContractResult`——字段：`passed: bool`、`reason: str | None`、`details: dict`。
- 函数设计：无（纯数据对象）。
- 输入/输出：—。
- 副作用：无。
- 依赖方向：无下游依赖。
- Pi0.5 参考：无（Pi0.5 无显式结果对象；这是 ACT 增量）。
- 验收覆盖：单测——构造 pass/fail 结果、字段可读。

## 边界继承声明

本文件的 `types/` 任务边界来自当前 L1/L2 功能边界（L2-01 负责数据规格定义），不是旧 `l2-01-types` layer-based 卡片。旧卡片是隔离区历史快照，不作权威。

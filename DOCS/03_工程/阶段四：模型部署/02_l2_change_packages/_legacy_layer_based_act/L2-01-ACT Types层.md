# L2-01 ACT Types 层

> [!info] 归属
> - 对应分层：Types（地基，不依赖任何层）
> - 关联 ACT Delta：A2（state_codec）、A3（action_codec + action_spec）
> - 关联契约：[[ACT部署契约]]、[[ACT Contract Delta]]
> - 上游数据依据：[[数据清洗交付说明]]

## 一句话定位

定义 ACT 部署的 state（16D 分组段序）和 action（16D 交替段序）数据结构与编解码函数，在边界处校验 shape/dtype/段序/quaternion 模长，下游不靠猜测。

## 本次唯一目标

- 新建 `src/model_deploy/act/types/state_codec.py`：16D 分组段序 state 编解码。
- 新建 `src/model_deploy/act/types/action_codec.py`：16D 交替段序 action 编解码。
- 新建 `src/model_deploy/act/types/action_spec.py`：维度常量 + 段序拆解。
- 纯单测覆盖：合法输入编码正确、非法输入报错、round-trip 一致。

## 同事源码复用边界

| ACT 目标 | 同事源文件 | 方式 | 复用要点 |
|---|---|---|---|
| `act/types/state_codec.py` | `pi05_old/.../common/data/state_codec.py` (60行) | **结构复用** | 保留 `BimanualState` frozen dataclass + `encode_bimanual_state()` 框架。改：字段从 `left_arm_q/right_arm_q/left_hand_q/left_ee_pos/left_ee_rpy` → `left_tcp_pose[7]/right_tcp_pose[7]/left_gripper_width/right_gripper_width`；维度 26→16；加 quaternion 模长校验 |
| `act/types/action_codec.py` | `pi05_old/.../common/data/action_codec.py` (32行) | **结构复用** | 保留 `ensure_action_vector()`/`ensure_action_chunk()`/`split_action()` 框架。改：维度 14→16；split 段序改交替（左tcp7+左width1+右tcp7+右width1） |
| `act/types/action_spec.py` | `pi05_old/.../common/robot/action_spec.py` (59行) | **结构复用** | 保留常量定义+`split_bimanual_action()` 框架。改：`ARM_DOF=6/HAND_DOF=1/ACTION_DIM=14/STATE_DIM=26` → `ACTION_DIM=16/STATE_DIM=16`；删 `hand_command_to_trigger()`（ACT 不用 trigger 语义） |

> [!note] 复用要点
> 同事的 Types 层结构（frozen dataclass + 编解码函数 + 维度常量）设计良好，只改字段和维度。**不要重写框架，只改内容**。`decode_picotele_proprioception()` 是 picotele 遗留，ACT 不需要，不搬。

## 明确不做

- 不抽象 PolicyBackend 接口。
- 不预留触觉段落逻辑（第一版不含触觉，升级时作为独立 L2 处理）。
- 不修改 `src/model_deploy/pi05/` 任何文件。
- 不依赖 Config / Repo / Service 层。
- 不搬运同事的 `decode_picotele_proprioception()`（picotele 遗留，ACT 不需要）。

## 维度定义（依据《数据清洗交付说明》）

### observation.state（16D，分组段序）

| 索引 | segment | dim | 分量 | 单位 | 坐标系 |
|:---:|:---|:---:|:---|:---|:---|
| [0,7) | `left_tcp_pose` | 7 | x,y,z,qx,qy,qz,qw | m + quaternion xyzw | `left_arm_base` |
| [7,14) | `right_tcp_pose` | 7 | x,y,z,qx,qy,qz,qw | m + quaternion xyzw | `right_arm_base` |
| [14,15) | `left_gripper_width` | 1 | width | normalized [0,1]（0=闭合,1=全开） | - |
| [15,16) | `right_gripper_width` | 1 | width | normalized [0,1] | - |

### action（16D，交替段序）

| 索引 | segment | dim | 分量 | 单位 | 时间偏移 |
|:---:|:---|:---:|:---|:---|:---:|
| [0,7) | `left_tcp_pose_t_plus_1` | 7 | x,y,z,qx,qy,qz,qw | m + quaternion xyzw | +1 step |
| [7,8) | `left_gripper_width_t_plus_1` | 1 | width | normalized [0,1] | +1 step |
| [8,15) | `right_tcp_pose_t_plus_1` | 7 | x,y,z,qx,qy,qz,qw | m + quaternion xyzw | +1 step |
| [15,16) | `right_gripper_width_t_plus_1` | 1 | width | normalized [0,1] | +1 step |

> [!warning] state 与 action 段序不同
> state 按「全左→全右」分组，action 按「左pose+左夹爪→右pose+右夹爪」交替。这是阶段二 `ACTION_SEGMENT_DEFINITIONS` 决定的，不是笔误。

## 边界校验要求（对照《架构边界与机械约束原则》第三节）

编解码函数必须在边界处校验：
- shape：state 必须 16D，action 必须 16D，否则报错。
- dtype：float32。
- quaternion 模长：pose 段的 [3:7]（state）/ [3:7] 和 [11:15]（action）四元数模长 ≈ 1（容差 1e-3），否则报错。
- gripper width：∈ [0,1]，越界报错（或按配置 clip）。

## L3 草案

| L3 | 目标 | 验收模式 |
|---|---|---|
| deploy_001 | 新建 action_spec.py：常量 `ACTION_DIM=16`/`STATE_DIM=16` + `split_bimanual_action()`（交替段序拆解） | direct-local 单测 |
| deploy_002 | 新建 state_codec.py：`ActBimanualState` dataclass + `encode_state()` 16D 分组段序 + quaternion 模长校验 | direct-local 单测 |
| deploy_003 | 新建 action_codec.py：`encode_action()` / `decode_action()` 16D 交替段序 + round-trip | direct-local 单测 |
| deploy_004 | 边界校验完善 + 全量单测（非法 shape/dtype/模长/width 越界均报错） | direct-local 单测 |

## 真机风险

低。纯数据结构定义与单测，不触碰硬件。

## 回滚方式

删除 `src/model_deploy/act/types/`。不影响 Pi0.5 代码。

## L2 Gate（AI 侧自动化）

- required L3：deploy_001 ~ deploy_004 全部 PASS_LOCAL。
- 运行命令：`pytest src/model_deploy/act/tests/types/ -v`
- 通过现象：所有单测通过；合法 state/action 编码维度正确、段序正确；非法输入（错 shape、模长≠1、width 越界）均抛 ValueError。

## 人类验收标准

验收清单写入 `05_acceptance/l2-01-types/人类验收清单.md`，验收性质全部为「机械」：

| 验收项 | 运行命令 | 通过现象 |
|---|---|---|
| 1 | `pytest src/model_deploy/act/tests/types/test_state_codec.py -v` | 全部 PASSED；encode_state 输出 shape [16]，段序 left_tcp[7]+right_tcp[7]+left_width[1]+right_width[1] |
| 2 | `pytest src/model_deploy/act/tests/types/test_action_codec.py -v` | 全部 PASSED；encode/decode round-trip 一致；action 段序交替排列 |
| 3 | `pytest src/model_deploy/act/tests/types/test_action_spec.py -v` | 全部 PASSED；split_bimanual_action 正确拆出 left/right tcp+width |
| 4 | 构造非法输入（模长=2 的 quaternion）单测 | 抛 ValueError，错误信息含 quaternion/normalize |

用户签字位置：`05_acceptance/l2-01-types/验收结果.md` 末尾「人类验收」段。

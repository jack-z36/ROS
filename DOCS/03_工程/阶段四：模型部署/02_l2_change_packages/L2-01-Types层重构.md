# L2-01 · Types 层重构

> [!info] 归属
> - 对应分层：**Types**（最底层基座，不依赖任何层）。
> - 上游：[[00_L2改造工作包总览]]。
> - 下游：L2-02（Config 依赖 Types）、L2-03（Service 依赖 Types）、L2-04（Service 依赖 Types）。
> - 关联 Delta：D8（臂状态语义）、D9（encoded_state）、D11（action 语义）。

## 一句话定位

定义新的 state/action 数据结构、维度常量和编解码函数，作为整个改造的地基。改完可纯单测，不依赖 ROS / 模型 / 硬件。

## 对应分层

**Types 层**。只含数据结构定义 + 纯函数编解码。零外部依赖（除 numpy）。这是所有上层（Config / Repo / Service / Runtime）的地基。

## 涉及的现有代码

| 文件 | 类/函数 | AS-IS 现状 |
|---|---|---|
| `common/data/state_codec.py` | `BimanualState`（L13-24）、`encode_bimanual_state`（L27-43）、`decode_picotele_proprioception`（L46-53） | state = 关节角 + EE pos/rpy；编码成 26D；`decode_picotele_proprioception` 解 [right6,left6] 顺序 |
| `common/robot/action_spec.py` | `BimanualAction`（L22-39）、`ACTION_DIM=14`、`STATE_DIM=26`、`split_bimanual_action`（L42-52）、`hand_command_to_trigger`（L55-59） | action = left_arm6/right_arm6/left_hand/right_hand；14D；trigger 转换 |
| `common/data/action_codec.py` | `ensure_action_vector`、`ensure_action_chunk`、`split_action` | 14D 校验和拆分 |

## 已有能力盘点

**保留的能力**：
- `BimanualState` / `BimanualAction` 作为「结构化视图」的设计模式（frozen dataclass + as_vector/split）——这个模式好，保留，只改字段。
- `encode_bimanual_state` / `split_action` 的「结构 → 向量」和「向量 → 结构」双向转换模式——保留，改维度和段序。
- 维度常量（`ACTION_DIM`/`STATE_DIM`）作为单一真相源的模式——保留，改数值。
- `_vector` 辅助函数（维度校验）——保留。

**必须保留的原始行为**：
- 编解码函数的「严格维度校验 + 报错」语义（不静默截断/补零）。
- frozen dataclass 的不可变性。

## 必须修正的数据语义

依据：阶段二 `数据清洗交付说明.md`（action_observation_schema）。

### state（observation）—— 第一版 16D，预留触觉

| 维度 | AS-IS | TO-BE（第一版 16D） | TO-BE（后续 32D，预留） |
|---|---|---|---|
| 结构 | left_arm_q6 + right_arm_q6 + left_hand_q1 + right_hand_q1 + left_ee_pos3 + left_ee_rpy3 + right_ee_pos3 + right_ee_rpy3 | left_tcp_pose7(quaternion xyzw+m) + right_tcp_pose7 + left_gripper_width1 + right_gripper_width1 | + tactile×4片(各4D) |

### action —— 16D（不变，不分版）

| 维度 | AS-IS | TO-BE |
|---|---|---|
| 结构 | left_arm_joint6 + right_arm_joint6 + left_hand1 + right_hand1 | left_tcp_pose7 + left_gripper_width1 + right_tcp_pose7 + right_gripper_width1（交替排列） |

> [!warning] state 和 action 段序不同
> state 按「全左→全右」分组（left_tcp + right_tcp + left_width + right_width）。
> action 按「左pose+左width → 右pose+右width」交替。
> 这是 `数据清洗交付说明.md:36` 明确的 warning，不是笔误。本 L2 必须严格遵循两套段序。

## 真实改造边界

### 改 `state_codec.py`

1. `BimanualState` 字段改为：`left_tcp_pose: np.ndarray[7]`（xyz+qx,qy,qz,qw）、`right_tcp_pose: np.ndarray[7]`、`left_gripper_width: float`、`right_gripper_width: float`。
2. 删除 `left_arm_q/right_arm_q/left_hand_q/right_hand_q/left_ee_pos/left_ee_rpy/right_ee_pos/right_ee_rpy` 字段。
3. `encode_bimanual_state` 改成拼 16D（第一版），预留触觉段追加位置（后续版加 [16,32)）。
4. 删除 `decode_picotele_proprioception`（picotele 专有，不再需要）。
5. 触觉段落的 enable/disable 通过参数控制（预留扩展，第一版 disabled）。

### 改 `action_spec.py`

1. `ACTION_DIM` 14→16；`STATE_DIM` 26→16（第一版，后续 32）。
2. `BimanualAction` 字段改为：`left_tcp_pose: np.ndarray[7]`、`left_gripper_width: float`、`right_tcp_pose: np.ndarray[7]`、`right_gripper_width: float`。
3. `split_bimanual_action` 改成按 16D 交替段序拆分（[0:7]左pose / [7:8]左width / [8:15]右pose / [15:16]右width）。
4. 删除 `hand_command_to_trigger`（trigger 转换不再需要，width↔angle 转换在 bridge 做）。
5. `ARM_JOINT_NAMES` 保留（可能 IK 兜底用），但标注「非 action 主路径」。

### 改 `action_codec.py`

1. `ensure_action_vector` 的维度校验 14→16。
2. `ensure_action_chunk` 的 action_dim 默认值 14→16。
3. `split_action` 跟随 `action_spec.split_bimanual_action`。

## adapter 优先策略

本 L2 是 Types 层，**直接修改**，不用 adapter。原因：Types 是地基，用 adapter 包裹旧结构会导致上层全部要适配两层语义，得不偿失。直接改干净。

旧结构的回滚靠 git + 旧 bundle（Q7 已确认三件套绑定回滚）。

## 真机风险

**低**。纯数据结构 + 纯函数，单测覆盖即可，不接触硬件。

## 验收路径

1. **单测**：对 `encode_bimanual_state` / `split_bimanual_action` 喂构造数据，断言输出维度和段序。
2. **段序一致性测试**：构造一个已知 16D 向量，split 后再 assemble，断言还原一致（round-trip）。
3. **归一化校验**：构造 quaternion 段，断言模长≈1（或文档约定归一化在边界做）。
4. **预留触觉测试**：第一版触觉段 disabled 时，encode 输出 16D；enabled 时输出 32D。

## 回滚方式

git 回退这三个文件 + 切回旧 bundle（26D state / 14D action）。

## 可拆分的 L3 草案

| L3 | 目标 | 改的文件 |
|---|---|---|
| L3-01a | 重构 `BimanualState` 为 TCP+width 结构，改 `encode_bimanual_state` 为 16D + 预留触觉 | state_codec.py |
| L3-01b | 重构 `BimanualAction` 为 TCP+width，改 `ACTION_DIM=16`，改 `split_bimanual_action` 段序，删 `hand_command_to_trigger` | action_spec.py |
| L3-01c | 跟随改 `action_codec` 维度校验 | action_codec.py |
| L3-01d | 补充单测：维度/段序/round-trip/触觉预留 | tests/ |

> [!note] L3 拆分原则
> L3-01a/b/c 可顺序执行（b 依赖 a 的 STATE_DIM，c 依赖 b 的 ACTION_DIM），也可合并成一个大 L3（如果 Agent 上下文够）。L3-01d 单测必须最后，验证前三者。

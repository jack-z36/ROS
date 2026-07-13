# types 层设计：L2-05

> [!info] 元信息
> - 消费对象：types 实现/验收 Agent。
> - 权威性：定义 L2-05 公共 RAM 数据语言；编号以 `03a` 为准。
> - 上游来源：`01_L2功能边界.md`、`03a_功能微元总览与组织结构.md`、L2-04 `SafetyResult`。
> - 不负责范围：不做 ROS、配置读取、映射或发布。
> - 读取时机：修改 `types/action_publish.py` 前。

## 1. 目标源码路径

```text
src/model_deploy/act/types/action_publish.py
src/model_deploy/act/types/__init__.py          # 仅导出公共对象
```

复用但不修改核心语义：

```text
src/model_deploy/act/types/action_spec.py       # ActionSpec / 16D layout
src/model_deploy/act/types/safety_result.py     # SafetyStatus / SafetyResult
```

## 2. 层职责与文件职责

`types/` 只回答“L2-04、L2-05、L2-06 之间传递的数据长什么样”。C1-C6 全部是跨层公共语言；创建后只读。

禁止：ROS import、YAML/CLI 解析、topic publish、command 决策、fallback、硬件对象。

## 3. 数据微元字段设计

### C1 `CommandPermit`（frozen dataclass）

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `allowed` | 标量字段 | `bool` |
| `reason_code` | 可空标量字段 | `str | None` |

约束：allowed=True 时 reason 必须为空；allowed=False 时 reason 必须为非空稳定 code。

### C2 `ActionPublishRequest`（frozen dataclass）

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `action_id` | 非空标量字段 | `str` |
| `safety_result` | frozen object reference | `SafetyResult` |
| `command_permit` | frozen object reference | `CommandPermit` |
| `ros_time_s` | 标量字段 | `float` |
| `monotonic_s` | 标量字段 | `float` |

时间必须 finite；`monotonic_s >= 0`。request 不重复存 `command_output_enabled`。

### C3 `ArmPoseTarget`（frozen dataclass）

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `frame_id` | 非空标量字段 | `str` |
| `position_xyz` | fixed tuple，长度3，单位 m | `tuple[float, float, float]` |
| `quaternion_xyzw` | fixed tuple，长度4 | `tuple[float, float, float, float]` |

左右 C3 必须使用同一个 `pose_frame_id`。C3 不执行 TF 或 quaternion 安全算法。

### C4 `TopicPayloadBundle`（frozen dataclass）

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `policy_action` | fixed tuple，长度16 | `tuple[float, ...]` |
| `left_arm` | frozen object reference | `ArmPoseTarget` |
| `right_arm` | frozen object reference | `ArmPoseTarget` |
| `left_gripper` | 标量，范围 `0..100` | `float` |
| `right_gripper` | 标量，范围 `0..100` | `float` |

C4 是 B1 的完整、不可部分返回的输出，不含 ROS message 和 status。

### C5 `PublishOutcome`（Enum）

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `REJECTED` | Enum value | `str` |
| `OBSERVED` | Enum value | `str` |
| `BLOCKED` | Enum value | `str` |
| `PUBLISHED` | Enum value | `str` |
| `PARTIAL` | Enum value | `str` |
| `FAILED` | Enum value | `str` |

### C6 `ActionPublishResult`（frozen dataclass）

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `action_id` | 非空标量 | `str` |
| `safety_status` | Enum reference | `SafetyStatus` |
| `command_output_enabled` | 标量 | `bool` |
| `command_permitted` | 标量 | `bool` |
| `outcome` | Enum reference | `PublishOutcome` |
| `policy_action_published` | 标量 | `bool` |
| `command_publish_count` | 整数，范围 `0..4` | `int` |
| `gripper_skipped` | immutable tuple of labels | `tuple[str, ...]` |
| `command_plan_completed` | 标量 | `bool` |
| `status_published` | 标量 | `bool` |
| `reason_code` | 可空标量 | `str | None` |
| `driver_accepted` | 固定未知 | `None` |
| `hardware_reached` | 固定未知 | `None` |

## 4. 结构不变量

- 所有 dataclass `frozen=True`。
- C4/C3 使用 tuple，不暴露 ndarray 可变 view。
- C6 `command_publish_count` 必须在 0..4。
- `REJECTED/OBSERVED/BLOCKED` 的 command count 必须为 0。
- `PUBLISHED` 要求 `command_plan_completed=True`；允许 deadband 导致 count<4，但 skip 必须列出。
- `PARTIAL` 要求 count>0 且 `command_plan_completed=False`。
- `driver_accepted`、`hardware_reached` 在 L2-05 永远为 None。
- C1-C6 不出现 mode、accepted、raw gate fields。

## 5. 输入、输出与副作用

| 输入 | 输出 | 副作用 |
|---|---|---|
| 标准库标量/tuple、`ActionSpec`、`SafetyResult` | C1-C6 frozen 对象 | 无 |

## 6. 依赖关系

允许：标准库、同层 `ActionSpec` / `SafetyResult`。

禁止：`config/repo/service/runtime/ui`、rclpy、geometry/std messages。types 是最上游数据语言层。

## 7. Pi0.5 参考

- `BimanualAction`：只复用强类型/frozen 结构思想，旧 14D 字段不复用。
- 旧 `ControlCommand` 字段不足，不复用。
- mux reason 说明许可需要可解释 code，但 raw mode/gate 状态不复用。

## 8. 验收覆盖

- frozen mutation 抛 `FrozenInstanceError`。
- C1-C6 合法/非法组合构造测试。
- `SafetyStatus.PASS/ADJUSTED/REJECTED` 全覆盖，无 accepted fixture。
- types 模块在无 ROS 环境可 import。
- C6 JSON 序列化前字段完整，unknown 不被改写为 success。

## 9. 边界继承声明

本文件继承当前 L1/L2 功能边界，不从旧 layer-based L2 卡片继承。它只定义公共 RAM 语言，不借 types 名义吞入 runtime 状态或 ROS message。

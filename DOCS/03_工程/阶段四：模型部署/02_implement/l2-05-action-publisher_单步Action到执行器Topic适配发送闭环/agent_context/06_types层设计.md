# types 层设计：L2-05

> [!info] 元信息
> - 消费对象：types 实现/验收 Agent。
> - 权威性：本文件定义 L2-05 公共 RAM 数据语言。
> - 上游来源：`01_L2功能边界.md`、`03_ACT微元设计与协作.md`、L2-04 `SafetyResult` 契约。
> - 不负责范围：不做 ROS、配置读取、映射或发布。
> - 读取时机：修改 `types/action_publish.py` 前。
> - 冲突处理：字段变更必须先同步主设计与 HTML；不得用动态 dict 替代跨 L2 契约。

## 1. 目标源码路径

```text
src/model_deploy/act/types/action_publish.py
src/model_deploy/act/types/__init__.py          # 仅导出公共对象
```

复用但不修改核心语义：

```text
src/model_deploy/act/types/action_spec.py       # ActionSpec / ensure_action_vector / split_action
src/model_deploy/act/types/safety_result.py     # 由 L2-04 提供
```

## 2. 层职责与文件职责

`types/` 只回答“L2-04、L2-05、L2-06 之间传递的数据长什么样”。`action_publish.py` 定义最终授权、单次请求、transport-neutral 四路目标、发布计划和逐调用结果；所有对象创建后只读。

禁止：ROS import、文件/YAML 读取、topic publish、mode 编排、fallback、硬件对象。

## 3. class 设计

| frozen dataclass | 字段 | 作用 |
|---|---|---|
| `PublishAuthorization` | `mode`、`command_allowed`、`reason` | L2-06 汇总后的最终授权，不暴露原始硬件信号。 |
| `ActionPublishRequest` | `action_id`、`safety_result`、`authorization`、`ros_time_s`、`monotonic_s` | 每次同步调用的完整 RAM 输入。 |
| `ArmPoseTarget` | `frame_id`、`position_xyz: tuple[3]`、`quaternion_xyzw: tuple[4]` | 与 ROS message 无关的单臂目标。 |
| `CommandTargets` | `left_arm`、`right_arm`、`left_gripper_command`、`right_gripper_command` | 四路全部构造成功后的 transport-neutral bundle。 |
| `ActionPublishPlan` | `request`、`safe_vector: tuple[16]`、`targets`、`publish_policy`、`publish_commands`、`reason` | ROS 之前的完整本地计划。 |
| `ActionPublishResult` | action/status 字段 | 逐调用事实，供 status 和 L2-06 消费。 |

### `ActionPublishResult` 最低字段

| 字段 | 类型 | 语义 |
|---|---|---|
| `action_id` | `str` | 与 L2-06 当前 tick/action 关联。 |
| `safety_ok` | `bool` | 输入是否带明确安全通过语义。 |
| `policy_action_published` | `bool` | 观测通道 publish 调用是否成功。 |
| `command_publish_count` | `int` | 本次成功调用的 command publisher 数，范围 0..4。 |
| `gripper_skipped` | `tuple[str, ...]` | 因 deadband/min interval 有意跳过的 side。 |
| `sent_to_driver` | `bool` | 本次计划的 command ROS publish 是否全部完成；不等于执行。 |
| `failure_reason` | `str | None` | 契约、授权、构造或 publish 失败原因。 |
| `driver_accepted` | `None` | 本 L2 无法判断，固定未知。 |
| `hardware_reached` | `None` | 本 L2 无法判断，固定未知。 |

## 4. 函数设计

本文件只允许轻量结构不变量检查，例如 dataclass `__post_init__`：

- mode 只能是 dry/shadow/safe 三值。
- 时间为 finite 且 `monotonic_s >= 0`。
- `ArmPoseTarget` 长度严格 3/4。
- command publish count 在 0..4。
- `sent_to_driver=True` 时不能同时存在 `failure_reason`。

业务映射、SafetyResult 复核和 mode 计划不放 types，见 service 设计。

## 5. 输入、输出与副作用

| 输入 | 输出 | 副作用 |
|---|---|---|
| 标准库标量/tuple、`ActionSpec`、`SafetyResult` | frozen 请求/授权/目标/计划/结果对象 | 无 |

为保持 frozen 对象的真实只读性，跨层目标用 tuple，不在 dataclass 内暴露可变 ndarray 引用。与 numpy 的转换留在 service/UI 层。

## 6. 依赖关系

允许：标准库、同层 `ActionSpec`/`SafetyResult`。

禁止：`config/`、`repo/`、`service/`、`runtime/`、`ui/`、rclpy、geometry/std messages。types 是最上游数据语言层。

## 7. Pi0.5 参考

- `common/src/pi05/common/robot/action_spec.py::BimanualAction`：仅结构复用 frozen 数据对象；旧 14D 字段不复用。
- `deploy/src/pi05/deploy/runtime/control_loop.py::ControlCommand`：字段不足，无授权/action_id/status 语义，仅作为反例。
- `CommandMuxNode` 的 mode/reason 说明授权需要可解释，但原始状态所有权不复用。

## 8. 验收覆盖

- 全部 dataclass frozen；赋值抛 `FrozenInstanceError`。
- 不合法 mode、时间、tuple 长度和互斥结果在构造时失败。
- types 模块在无 ROS 环境可 import。
- `ActionPublishResult` JSON 序列化前字段完整，unknown 不会被改写为 success。

## 9. 边界继承声明

本文件继承当前 L2-05 功能边界，不从旧 layer-based L2 卡片继承。它只定义公共 RAM 语言；不借“公共类型”名义吞入 runtime 状态或 ROS message。

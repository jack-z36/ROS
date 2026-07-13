# service 层设计：L2-05

> [!info] 元信息
> - 消费对象：service 实现/验收 Agent。
> - 权威性：定义 B1 与 C9-C11 的纯 RAM Topic 载荷生成。
> - 编号权威：`03a_功能微元总览与组织结构.md`。
> - 不负责范围：不 import ROS、不持有状态、不判断 CLI/permit、不 publish。
> - 读取时机：实现或审查 action output adapter 前。

## 1. 目标源码路径

```text
src/model_deploy/act/service/action_output_adapter.py
src/model_deploy/act/service/__init__.py       # 仅导出稳定公共函数
```

## 2. 层职责与文件职责

service 层接收当前进程 RAM 中的 `SafetyResult` 和 C7 配置，复核跨模块契约，拆分 16D，映射 gripper，构造 transport-neutral C4 `TopicPayloadBundle`。

文件完全无跨调用状态；不读取 ROS/文件/硬件；不构造 ROS msg；不判断是否发布 command。

## 3. B1 `build_topic_payloads`（编排函数）

```python
def build_topic_payloads(
    safety_result: SafetyResult,
    config: CommandOutputConfig,
) -> TopicPayloadBundle:
    ...
```

调用条件：B3 每次 `publish(request)` 的第一步。

顺序：

1. 调 C9 `require_publishable_action`。
2. 从 `ActionSpec` 得到 16D tuple。
3. 调 C10 ×2 构造左右 C3，统一使用 `config.pose_frame_id`。
4. 调 C11 ×2 把左右 gripper `[0,1]` 映射为 `0..100`。
5. 一次性构造 C4。

失败：任一子步骤异常，不返回部分 payload；B3 不进入 B2，policy/command 调用数为 0。

## 4. C9 `require_publishable_action`（计算函数）

```python
def require_publishable_action(result: SafetyResult) -> ActionSpec:
    ...
```

输入：

- RAM `SafetyResult(status, action, findings)`。

输出：

- `PASS/ADJUSTED` 且 action 合法：返回同一语义的 `ActionSpec`。
- `REJECTED`、action=None、shape/finite/爪域错误：抛 `ActionPublishContractError`。

复核内容：

```text
status in {PASS, ADJUSTED}
action is ActionSpec
vector shape exactly (16,)
all values finite
gripper[14], gripper[15] in [0,1]
```

不直接读写进程外资源；不重新做 quaternion/TCP delta 投影；不读取 `accepted`。

## 5. C10 `build_arm_pose_target`（计算函数）

```python
def build_arm_pose_target(
    tcp7: Sequence[float],
    pose_frame_id: str,
) -> ArmPoseTarget:
    ...
```

输入：RAM TCP7=`xyz(3)+xyzw(4)`、单一非空 frame。

输出：新的 frozen C3：

```text
frame_id
position_xyz tuple[3]
quaternion_xyzw tuple[4]
```

异常：长度错误、NaN/Inf、空 frame。

不直接读写进程外资源；不做 TF；不把相同数值分别贴成左右不同 frame。

## 6. C11 `map_gripper_command`（计算函数）

```python
def map_gripper_command(
    value: float,
    config: CommandOutputConfig,
) -> float:
    ...
```

输入：RAM 标量 `[0,1]` + C7 input/output 范围。

输出：新的 RAM `float`，默认 `0..100`：

```text
output_min + normalized_ratio * (output_max - output_min)
```

示例：`0 -> 0`、`0.5 -> 50`、`1 -> 100`。

异常：越域、NaN/Inf、配置范围非法。禁止 clip、双尺度猜测或兼容 50/100 输入。

不直接读写进程外资源。

## 7. C4 `TopicPayloadBundle` 构造

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `policy_action` | fixed tuple，长度16 | `float` elements |
| `left_arm` | frozen C3 reference | `ArmPoseTarget` |
| `right_arm` | frozen C3 reference | `ArmPoseTarget` |
| `left_gripper` | 标量，0..100 | `float` |
| `right_gripper` | 标量，0..100 | `float` |

B1 直接构造 C4，不需要额外无状态 class，也不新增第四个编排函数。

## 8. 输入、输出与副作用

| 输入 | 输出 | 副作用 |
|---|---|---|
| SafetyResult、CommandOutputConfig | TopicPayloadBundle | 无 |

## 9. 依赖关系

允许：types、config、numpy/标准库（仅 shape/finite 转换）。

禁止：repo/runtime/ui、rclpy、geometry_msgs、std_msgs、文件/网络/硬件 API。service 不得 import 下游层。

## 10. Pi0.5 参考

- `split_bimanual_action`：只参考入口拆分思想；旧 14D 数值不复用。
- `hand_command_to_trigger`：方向/量纲相反，不复用。
- bridge `_filter_joint_target`：混入安全与状态，不复用。
- 当前 B1 是新 ACT 纯 RAM 边界，不复用旧 node orchestration。

## 11. 验收覆盖

- PASS/ADJUSTED/REJECTED 三状态。
- 16D 左右段和 `xyzw` property tests。
- 单一 frame；无 TF/per-arm 假 frame。
- gripper 0/0.5/1 -> 0/50/100；50/100 输入失败。
- 任一子目标失败不返回部分 C4。
- 模块无 ROS import、无 module/global mutable state、无 CLI/permit/mode 逻辑。

## 12. 边界继承声明

本文件服务当前 L2-05 的 RAM 载荷职责，不从旧 layer-based service 卡片或 Pi0.5 bridge 推导边界。安全算法归 L2-04，运行编排归 L2-06，ROS 写出归 ui。

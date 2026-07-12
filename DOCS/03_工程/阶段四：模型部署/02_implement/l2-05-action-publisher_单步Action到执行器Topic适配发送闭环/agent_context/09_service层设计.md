# service 层设计：L2-05

> [!info] 元信息
> - 消费对象：service 实现/验收 Agent。
> - 权威性：本文定义 ROS 之前的纯 RAM 业务映射。
> - 上游来源：`ActionSpec`、`SafetyResult`、CommandOutputConfig 与功能边界。
> - 不负责范围：不 import ROS、不持有状态、不 publish、不决定 fallback。
> - 读取时机：实现或审查 action output adapter 前。
> - 冲突处理：出现 subscription/publisher/timer 或双尺度猜测时直接判越界。

## 1. 目标源码路径

```text
src/model_deploy/act/service/action_output_adapter.py
src/model_deploy/act/service/__init__.py       # 仅导出稳定函数
```

## 2. 层职责与文件职责

service 层接收当前进程 RAM 中的安全结果、授权、时间和只读配置，复核跨模块契约，拆分 16D，映射 gripper，构造 transport-neutral 四路目标和发布计划。

文件不持有任何跨 tick 状态；不读取 ROS/文件/硬件；不创建 message。

## 3. 函数设计

| 函数 | 输入 | 输出 | 副作用 | 错误行为 |
|---|---|---|---|---|
| `require_safe_action(result)` | SafetyResult | ActionSpec | 无 | 未 accepted/action None/shape/finite/爪域错误 -> `ActionPublishContractError` |
| `map_gripper_command(value, config)` | `[0,1]` float、output config | `0..100` float | 无 | 输入越域直接失败，不 clip/猜尺度 |
| `build_arm_target(tcp7, frame_id)` | xyz+quat、frame | ArmPoseTarget | 无 | 长度/finite/frame 错失败 |
| `build_command_targets(action, config)` | ActionSpec、output config | CommandTargets | 无 | 任一子目标失败时无部分结果 |
| `build_publish_plan(request, deploy_config)` | request/config | ActionPublishPlan | 无 | mode mismatch/非法授权失败或生成 blocked plan |
| `status_payload(result)` | ActionPublishResult | JSON-safe dict | 无 | unknown 保持 null，禁止填 true |

## 4. 权威算法

```text
require_safe_action:
  require SafetyResult.accepted is True and action is not None
  vector = ensure_action_vector(action.as_vector())
  require all finite
  require 0 <= vector[14] <= 1 and 0 <= vector[15] <= 1

build_command_targets:
  left  = ArmPoseTarget(frame=left_arm_base,
                        position=vector[0:3], quaternion=vector[3:7])
  right = ArmPoseTarget(frame=right_arm_base,
                        position=vector[7:10], quaternion=vector[10:14])
  left_gripper  = map(vector[14])
  right_gripper = map(vector[15])
  return one complete CommandTargets
```

不在此处重新归一化 quaternion、clamp TCP delta 或选择 fallback。L2-04 已负责安全算法；本层只检查输出契约的 shape/finite/爪域与 frame。

### mode 计划

| mode | publish policy | publish command | reason |
|---|---:|---:|---|
| dry-run | false | false | `dry_run` |
| shadow-run | true | false | `shadow_only` |
| safe-run + allowed=false | true | false | authorization reason / `not_authorized` |
| safe-run + allowed=true | true | true | null |

若 request 与 DeployConfig mode 不一致，command=false，reason=`mode_mismatch`。不能把任一方的 safe-run 当作足够授权。

## 5. class 设计

本文件不定义业务 class。所有微元无状态，使用函数更符合 3.5 层计算函数定义。禁止仅为“适配器”名字创建无状态 `ActionOutputAdapter` class。

## 6. 输入输出

| 输入 | 输出 |
|---|---|
| `SafetyResult`、ActionSpec、ActionPublishRequest、DeployConfig | ArmPoseTarget、CommandTargets、ActionPublishPlan、status dict |

所有输出在 RAM 中；无外部副作用。

## 7. 依赖关系

允许：types、config、numpy（仅转换/finite 检查）、标准库。

禁止：repo/runtime/ui、rclpy、geometry_msgs、std_msgs、文件/网络/硬件 API。service 不得 import 下游层。

## 8. Pi0.5 参考

- `action_codec.py::split_action`：仅参考入口拆分，ACT 直接复用现有 16D `types/action_spec.py`。
- `hand_command_to_trigger`：方向/量纲相反，明确不复用。
- `_joint_msg`：使用 JointState 且无有效 frame，不复用。
- bridge `_filter_joint_target`：混入安全与状态更新，不复用。

## 9. 验收覆盖

- 16D 左右段和 xyzw 顺序 property tests。
- gripper 0/0.5/1 -> 0/50/100；50/100 输入 -> 契约失败。
- action NaN/Inf、空 frame、mode mismatch 失败/blocked。
- 任一子目标构造失败不返回部分 bundle。
- 模块在无 ROS 环境可 import；无可变 module/global state。

## 10. 边界继承声明

本文件服务当前 L2-05 的 RAM 映射职责，不从旧 layer-based service 卡片或 Pi0.5 bridge 推导边界。安全算法仍归 L2-04，运行编排仍归 L2-06。

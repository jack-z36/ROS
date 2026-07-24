# act_interfaces 契约

关联总契约：[[TO-BE Contract]]、[[rm65_driver_node 状态发布契约]]、[[rm65_driver_node 命令执行契约]]

## 包定位

`act_interfaces` 是 model_deploy 栈的共享 ROS 2 接口包（ament_cmake + rosidl）。
当前只承载阶段四模型部署跨节点共享的两条消息：人工安全许可与硬件健康。

本包只定义消息结构，不含任何节点实现。所有硬件节点（rm65_dual_arm、
manual_safety_controller 等）与 ACT 节点通过这些消息解耦。

## 落点

`src/model_deploy/act_interfaces/`，模板照搬 `src/data_collection/hwk_pressure_interfaces/`。

## 消息定义

### CommandPermit

对齐 `src/model_deploy/act/types/action_publish.py:77` 的 frozen dataclass（C1）。
**只保留两个现有字段**，不引入 TTL/expiry——当前架构的过期机制是
"每 tick 重新求值 + fail-closed"（见 `act/ui/act_deploy_node.py:419` `_resolve_permit`）。

```
bool allowed
string reason_code
```

| 字段 | 不变量 |
|---|---|
| `allowed` | bool |
| `reason_code` | `allowed=true` 时必须为空；`allowed=false` 时必须为非空稳定 code |

**稳定 reason_code**（与 act 侧已定义的对齐，跨节点复用）：

| code | 含义 |
|---|---|
| `ESTOP_ACTIVE` | 急停激活 |
| `PERMIT_STALE` | permit 消息超过 `permit_stale_sec` 未更新（消费方判定） |
| `PERMIT_SOURCE_ERROR` | permit 字段自相矛盾（违反不变量） |
| `PERMIT_MISSING` | 消费方启动后从未收到 permit 消息 |
| `COMMAND_OUTPUT_DISABLED` | ACT 命令总开关关闭（act 侧） |

### HardwareHealth

全新设计，参考 `rm65_driver_node 状态发布契约.md` 的健康事实（连接状态、SDK 返回码、
控制器错误码、左右臂隔离）。

```
std_msgs/Header header
bool left_connected
bool right_connected
bool left_estop_active
bool right_estop_active
int32 left_sdk_code       # 最近一次左臂 SDK 返回码
int32 right_sdk_code
int32 left_controller_err  # 控制器错误码
int32 right_controller_err
string left_reason
string right_reason
```

| 字段 | 含义 |
|---|---|
| `*_connected` | 该侧 SDK handle 是否已连接 |
| `*_estop_active` | 该侧急停是否激活（含 service 触发的全局急停） |
| `*_sdk_code` | API 返回码：0 成功 / 1 控制器参数错误 / -1 发送失败 / -2 接收失败或超时 / -3 解析失败 / -4 到位校验失败 / -5 单线程阻塞超时 / -6 规划被停止（见睿尔曼 API2 错误代码附录） |
| `*_controller_err` | 控制器错误码（arm_err / sys_err，16 位）：0x0000 正常 / 0x1001 关节通信异常 / 0x1009 超速 / 0x100A 超加速度 / 0x100C 拖动超速 / 0x100D 碰撞 / 0x1010 关节掉使能 等（见 ROS2调用API接口功能包说明V1.0.0） |
| `*_reason` | 人类可读简短原因（连接失败 / 超时 / 急停 / DELTA_EXCEEDED / SDK 错误等） |

## 发布 / 消费方

| 消息 | 发布方 | 消费方 |
|---|---|---|
| `CommandPermit` | `manual_safety_controller`（待建，人工安全 GUI） | ACT L2-06 `ActDeployNode.permit_source`、`rm65_dual_arm_node` 的 `/act/command/permit` 订阅 |
| `HardwareHealth` | `rm65_dual_arm_node`（`/hardware/rm65/health`） | 监控/可视化、`manual_safety_controller` 的安全状态聚合 |

## 与 ACT 栈对齐

- ACT 节点（`src/model_deploy/act/`）当前用进程内 `CommandPermit` frozen dataclass
  （`types/action_publish.py:77`）。把 permit 暴露为 ROS topic 是补 L2-06 文档里
  "optional hardware safe-stop port（只有外部合同明确后）"的空白：manual_safety_controller
  发布 `/act/command/permit`，rm65_dual_arm 与 ACT 都订阅它，许可语义闭合。
- reason_code 复用 act 侧稳定码，确保跨节点日志一致。
- 字段不自洽（allowed=true 带 reason_code 等）由消费方按 fail-closed 处理
  （`PERMIT_SOURCE_ERROR`），不依赖发布方严格自检。

## 未验证项

- `manual_safety_controller` 包尚未建立，其发布 CommandPermit 的具体 GUI 与触发逻辑待该 PR 补。
- HardwareHealth 字段集为第一版最小可用集合；若后续需要关节级温度/电流等，另立 Contract Delta。

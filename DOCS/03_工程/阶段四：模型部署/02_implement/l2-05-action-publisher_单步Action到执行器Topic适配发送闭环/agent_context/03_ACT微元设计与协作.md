# ACT 微元设计与协作：L2-05

> [!info] 文档契约
> - 消费对象：L3 生成、实现、验收 Agent。
> - 权威性：本文是 Pi0.5 证据到 ACT 实现蓝图的主桥梁。
> - 编号权威：A/B/C 编号只以 `03a_功能微元总览与组织结构.md` 为准。
> - 上游来源：`01_L2功能边界.md`、`02_pi05源码3.5层微元拆解.md`、当前 `src/model_deploy/act/` 代码树。
> - 不负责范围：不生成 L3 文件、不实现源码、不决定 L2-06 fallback。
> - 读取时机：拆 L3 或修改 L2-05 class/function/文件落点前。

## 1. 已锁定设计决策

| 决策 | 结论 | 理由 |
|---|---|---|
| 主要封装 | `ActionPublisher` class | 需要长期持有六 ROS publisher、夹爪 deadband 状态、只读 config 和最近结果；无 subscription/timer。 |
| 三编排函数 | `build_topic_payloads`、`build_ros_messages`、`ActionPublisher.publish` | 分别隔离业务载荷、ROS message、决策与外部写出。 |
| 唯一公共入口 | `ActionPublisher.publish(request)` | L2-06 不得知道 B1/B2 内部步骤。 |
| 运行模式 | 删除 L2-05 的 `dry/shadow/safe` 枚举 | 它混合了测试方法、人工启用和动态许可。 |
| 人工启用 | CLI `--enable-command-output`，默认关闭 | 未显式人工传参时真实 command 永不写出。 |
| 动态许可 | `CommandPermit(allowed, reason_code)` | L2-06 汇总原始安全/driver 信号；L2-05 不重复携带 mode。 |
| 公共契约 | `types/action_publish.py` frozen dataclass/Enum | L2-04/L2-06/UI 只依赖 types，不依赖 service 实现。 |
| frame | 单一 `pose_frame_id` | `ActionSpec` 无 per-arm frame；没有 TF 计算时不能把同一数值改贴不同 frame。 |
| ROS transport | `Float32MultiArray` / `PoseStamped` / `Float64` / `String(JSON)` | 当前代码树不是 ROS interface package；内部强类型对象保证语义。 |
| gripper 域 | safe input `[0,1]`；B1 唯一映射点输出 `0..100` | 不做双尺度猜测，不把 50/100 再放大。 |
| status | B3 根据最终 `ActionPublishResult` 构造 | 发布成功数、partial 和 skip 在 B2 阶段尚未知。 |
| 时间 | L2-06 传 `ros_time_s` 与 `monotonic_s` | header 使用 ROS 时间；deadband 使用单调时间；L2-05 不拥有时钟。 |

## 2. ACT 微元设计

> [!note] 编号
> 本表不重复 A/B/C 编号；名称、父子关系和总量见 `03a_功能微元总览与组织结构.md`。

| ACT 微元 | 3.5 类型 | target layer | target file | function/class | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|---|---|---|
| `CommandPermit` | 数据 | types | `types/action_publish.py` | frozen dataclass | allowed、reason_code | 动态许可对象 | 无 | mux gate 事实仅参考，所有权改写给 L2-06 |
| `ActionPublishRequest` | 数据 | types | 同上 | frozen dataclass | action_id、SafetyResult、permit、两种时间 | 单次同步调用契约 | 无 | Pi0.5 无对应，ACT 新增 |
| `ArmPoseTarget` | 数据 | types | 同上 | frozen dataclass | frame、xyz、xyzw | transport-neutral 单臂目标 | 无 | 旧 BimanualAction 仅结构参考 |
| `TopicPayloadBundle` | 数据 | types | 同上 | frozen dataclass | policy16、两臂、两爪 | B1 完整输出 | 无 | 旧 split 思想结构复用 |
| `PublishOutcome` | 数据 | types | 同上 | Enum | 发布事实 | 稳定 outcome code | 无 | Pi0.5 无逐 action outcome |
| `ActionPublishResult` | 数据 | types | 同上 | frozen dataclass | 调用事实 | L2-06/status 契约 | 无 | mux JSON 只参考 transport |
| `CommandOutputConfig` | 数据 | config | `config/schema.py` | frozen dataclass | CLI enable + YAML 映射值 | 已校验输出配置 | 无 | frozen config 组织方式结构复用 |
| `build_topic_payloads` | 编排函数 | service | `service/action_output_adapter.py` | module function | SafetyResult、config | TopicPayloadBundle | 无 | 旧 split/publish 前处理仅结构参考 |
| `require_publishable_action` | 计算函数 | service | 同上 | function | SafetyResult | ActionSpec 或契约异常 | 无 | 旧 ControlCommand 无来源状态，ACT 新增 |
| `build_arm_pose_target` | 计算函数 | service | 同上 | function | TCP7、单一 frame | ArmPoseTarget | 无 | JointState 构造不复用 |
| `map_gripper_command` | 计算函数 | service | 同上 | function | `[0,1]`、config | `0..100` float | 无 | 旧 `hand_command_to_trigger` 方向相反 |
| `_RosMessageBundle` | 数据 | ui | `ui/action_publisher.py` | module-private data | 五个 ROS msg 引用 | B2 输出 | 无 | Pi0.5 无 bundle，ACT 新增 |
| `build_ros_messages` | 编排函数 | ui | 同上 | module function | payloads、ros_time_s | _RosMessageBundle | 无 | `_joint_msg` 只参考消息构造位置 |
| `_build_policy_msg` | 计算函数 | ui | 同上 | function | tuple[16] | Float32MultiArray | 无 | Pi0.5 无 policy_action |
| `_build_arm_msg` | 计算函数 | ui | 同上 | function | ArmPoseTarget、stamp | PoseStamped | 无 | Pi0.5 JointState 不复用 |
| `_build_gripper_msg` | 计算函数 | ui | 同上 | function | 0..100 | Float64 | 无 | 只复用 Float64 transport |
| `ActionPublisher` | 数据 + IO + 状态 + 编排 | ui | 同上 | class | node-like factory、config | `publish(request)->result` | 创建/调用 publisher，更新最小状态 | deploy node/bridge 只参考 publisher 生命周期 |
| `_decide_command_publish` | 计算函数 | ui | 同上 | method/function | enabled、permit | allow、reason | 无 | 旧 mode property 是反例 |
| `_should_publish_gripper` | 计算函数 | ui | 同上 | method | cache、target、monotonic_s | publish/skip + reason | 只读状态 | ACT 新增 |
| `_try_publish` | 数据读写函数 | ui | 同上 | method | label、publisher、msg | 成功事实或异常 | ROS topic 写出 | 旧 publisher API 结构复用 |
| `_record_gripper_success` | 内部状态更新函数 | ui | 同上 | method | side、target、time | 替换 cache | RAM 状态变化 | 旧 arm last 仅说明需成功后更新 |
| `_build_publish_result` | 计算函数 | ui | 同上 | function | permit、计数、错误、skip | ActionPublishResult | 无 | ACT 新增 |
| `_build_status_msg` | 计算函数 | ui | 同上 | function | ActionPublishResult | String(JSON) | 无 | mux JSON transport 参考 |
| `_record_last_result` | 内部状态更新函数 | ui | 同上 | method | result | 替换 `_last_result` | RAM 状态变化 | ACT 新增 |

## 3. 公共数据契约

### 3.1 `CommandPermit`

```text
allowed: bool
reason_code: str | None
```

- `allowed=True` 时 `reason_code` 应为 `None`。
- `allowed=False` 时必须有稳定 reason，例如 `ESTOP_ACTIVE`、`DRIVER_NOT_READY`、`DEADMAN_OPEN`。
- 不包含 mode，不携带原始 topic 值。

### 3.2 `ActionPublishRequest`

```text
action_id: str
safety_result: SafetyResult
command_permit: CommandPermit
ros_time_s: float
monotonic_s: float
```

`command_output_enabled` 属启动期 C7，只读保存在 A1 config 中，不在每 tick request 重复传递。

### 3.3 `TopicPayloadBundle`

```text
policy_action: tuple[float, ...]       # exactly 16
left_arm: ArmPoseTarget               # pose_frame_id + xyz + xyzw
right_arm: ArmPoseTarget              # same pose_frame_id
left_gripper: float                   # 0..100
right_gripper: float                  # 0..100
```

### 3.4 `PublishOutcome`

| 值 | 语义 |
|---|---|
| `REJECTED` | L2-04 结果不可发布；policy/command 为 0。 |
| `OBSERVED` | CLI command 总开关关闭；policy/status 观察链成功。 |
| `BLOCKED` | 总开关打开，但 L2-06 permit 不允许。 |
| `PUBLISHED` | 本次计划内 publisher 全部成功。 |
| `PARTIAL` | command 已有部分成功，随后失败，无法回滚。 |
| `FAILED` | B1/B2、本地契约、policy 或其他 ROS 写出失败。 |

### 3.5 `ActionPublishResult`

```text
action_id: str
safety_status: SafetyStatus
command_output_enabled: bool
command_permitted: bool
outcome: PublishOutcome
policy_action_published: bool
command_publish_count: int           # 0..4
gripper_skipped: tuple[str, ...]
command_plan_completed: bool
status_published: bool
reason_code: str | None
driver_accepted: None
hardware_reached: None
```

`command_plan_completed=True` 表示本次计划内 ROS command 调用全部成功或按 deadband 合法跳过；不等于 driver 接受或硬件到位。

## 4. 三编排函数

### 4.1 B1 `build_topic_payloads`

```text
调用条件：B3 每次 publish 入口首先调用。
步骤：
1. require_publishable_action：PASS/ADJUSTED -> ActionSpec；REJECTED -> 异常。
2. 复核 16D、finite、gripper [0,1]。
3. build_arm_pose_target ×2，使用同一 pose_frame_id。
4. map_gripper_command ×2，得到 0..100。
5. 组装 frozen TopicPayloadBundle。
失败：任何子步骤失败都不返回部分 payload，B3 不进入 B2，不调用 policy/command。
```

### 4.2 B2 `build_ros_messages`

```text
调用条件：B1 完整成功后由 B3 调用。
步骤：
1. policy tuple[16] -> Float32MultiArray。
2. left/right ArmPoseTarget -> PoseStamped ×2。
3. left/right 0..100 -> Float64 ×2。
4. 组装模块私有 _RosMessageBundle。
失败：任一消息失败不返回部分 bundle；B3 不调用 policy/command。
禁止：不构造最终 status，不读 CLI/permit，不调用 publisher。
```

### 4.3 B3 `ActionPublisher.publish`

```text
调用条件：L2-06 每 tick 在 L2-04 返回后同步调用。
步骤：
1. 调 B1 -> TopicPayloadBundle。
2. 调 B2 -> _RosMessageBundle。
3. 调 _decide_command_publish(config.enabled, request.permit)。
4. 先 _try_publish(policy)；失败则停止 command。
5. 若 command 允许，依次写 left_arm、right_arm、允许的 gripper。
6. gripper 成功后才更新对应 cache。
7. 汇总 ActionPublishResult。
8. 根据 result 构造并 best-effort 发布 status。
9. 记录 last_result，返回 L2-06。
跳过：CLI 关闭 -> OBSERVED；permit false -> BLOCKED；gripper deadband -> 合法 skip。
失败：首个 command 异常后停止剩余 command；已发不可回滚，outcome=PARTIAL。
```

## 5. 创建、状态与协作

```text
Creation order:
1. L2-01/启动装配创建 DeployConfig + CommandOutputConfig。
2. CLI 未显式开启时 command_output_enabled=False。
3. L2-06/UI 装配创建 ActionPublisher(node, config)。
4. A1 创建六 publisher；不创建 subscription/timer。

State owner:
- L2-06：action_id、两种时间、CommandPermit、fallback、retry、全局 metrics。
- L2-05/A1：publisher handles、gripper cache、last_result、只读 config。

Pure RAM calculations:
- B1 全部；B2 消息构造；C15/C16/C19/C20。

External boundary reads/writes:
- C17 只写六个 ROS topic；不读文件/topic/硬件。

Runtime orchestration point:
- L2-06 tick 同步调用 B3；L2-05 无 timer/thread/queue。

Failure propagation:
- B1/B2/ROS 异常 -> C6 + best-effort status。
- L2-06 根据 C6 决定 fallback/blocked/retry；L2-05 不自行切全局状态。
```

## 6. class / function 判断

| 候选 | 决定 | 原因 |
|---|---|---|
| `ActionPublisher` | class | 长生命周期 publisher + gripper cache + last result；适合 3.25 层打包。 |
| B1/B2 | module function | 无跨调用状态；一个编排业务载荷，一个编排 ROS message。 |
| B3 | A1 public method | 需要访问 publisher 与最小状态；是唯一外部入口。 |
| types 对象 | frozen dataclass/Enum | 跨 L2 RAM 语言，创建后不可变。 |
| C9-C16/C19/C20 | 计算函数 | RAM-in/RAM-out，无外部副作用。 |
| C17 | method/data I/O | 跨 ROS 外部边界，统一捕获 label/异常。 |
| C18/C21 | method/state update | 明确修改 A1 内部 RAM 状态。 |
| 单独 ROS Node | 不新增 | L2-06/UI 装配拥有 node 生命周期。 |

## 7. 六层产物表

| 层 | 是否需要 | 文件路径 | 职责 | 输入 | 输出 | 不负责 | Gate |
|---|---|---|---|---|---|---|---|
| types | 是 | `types/action_publish.py` | permit/request/payload/outcome/result | 安全结果、许可、事实 | 强类型对象 | ROS/config 读取 | frozen/schema/import tests |
| config | 是 | `config/schema.py` + 启动 CLI 装配 | enabled、frame、映射、deadband | CLI + YAML 映射 | CommandOutputConfig | publish/安全算法 | default-off/validator tests |
| repo | 否 | — | 无外部资源读取 | — | — | 文件/bundle | static no-artifact |
| service | 是 | `service/action_output_adapter.py` | B1 Topic 载荷生成 | SafetyResult/config | TopicPayloadBundle | ROS/状态/门控 | unit/property tests |
| runtime | 否 | — | 调度由 L2-06 | — | — | timer/fallback/permit 构造 | static no-artifact |
| ui | 是 | `ui/action_publisher.py` | B2 message + B3 select/publish/status | request/payload/config/node | ROS 副作用/result | subscription/硬件 SDK | mock/ROS observation tests |

## 8. 已知一致性风险与处理

| 风险 | 确定处理 |
|---|---|
| 当前 L1 仍写旧 mode、latest state、workspace/IK | 本包保持用户确认边界；L1 未同步前阻止 L3/Git Gate。 |
| 当前 config 仍有 `RuntimeConfig.mode` | L2-05 不消费；后续 L3/上游同步迁移旧测试和消费者。 |
| 当前 config 缺 `CommandOutputConfig` | config L3 必须先落地并保持 CLI default-off。 |
| 当前 `SafetyResult` 无 `accepted` | 统一使用 status/action/findings；文档/测试禁止 accepted fixture。 |
| ActionSpec 无 per-arm frame | 使用一个 `pose_frame_id`；需要不同 frame 时必须另立 TF 边界。 |
| ROS 多 Topic 可能部分成功 | C6 返回 PARTIAL 和真实 count；不声称事务回滚。 |
| 当前 HTML 仍是旧微元/mode | 标记 STALE；同步前不用于 L3。 |

## 9. 开放项

用户设计决定均已确认。剩余工作是同步 HTML/L1 与后续源码实现，不是未决的 L2-05 内部语义。

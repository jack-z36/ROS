# ACT 微元设计与协作：L2-05

> [!info] 文档契约
> - 消费对象：L3 生成、实现、验收 Agent。
> - 权威性：本文是 Pi0.5 证据到 ACT 实现蓝图的主桥梁。
> - 上游来源：`01_L2功能边界.md`、`02_pi05源码3.5层微元拆解.md`、当前 `src/model_deploy/act/` 代码树。
> - 不负责范围：不生成 L3 文件、不实现源码、不决定 L2-06 fallback。
> - 读取时机：拆 L3 或修改 L2-05 class/function/文件落点前。
> - 冲突处理：函数/class 或层落点与本文冲突时先更新本设计与 HTML；不得让实现自行漂移。

## 1. 已锁定设计决策

| 决策 | 结论 | 理由 |
|---|---|---|
| 主要封装 | `ActionPublisher` class | 需要长期持有 ROS publisher、夹爪 deadband 状态和最近结果；无 subscription/timer。 |
| 纯映射 | 独立函数，不包无状态 class | 16D 拆分、gripper 映射、授权矩阵和 publish plan 都是 RAM-in/RAM-out。 |
| 公共契约 | `types/action_publish.py` frozen dataclass | L2-04/L2-06/UI 只依赖 types，不依赖 service 实现。 |
| 输出配置 | `CommandOutputConfig` | 补齐 frame、输入/输出量纲、deadband、最小间隔；不复活 bridge/mux/hardware config。 |
| ROS transport | `Float32MultiArray` / `PoseStamped` / `Float64` / `String(JSON)` | 当前代码树不是 ROS interface package；内部强类型对象保证语义，后续可换 transport。 |
| gripper 域 | safe input `[0,1]`；唯一映射点输出 `0..100` | 与 `ActionSpec`、用户详细边界一致；不做双尺度猜测。 |
| 时间 | L2-06 传 `ros_time_s` 与 `monotonic_s` | header 使用 ROS 时间；deadband 使用单调时间；L2-05 不拥有时钟。 |
| action ID | L2-06 生成并随请求传入 | L2-05 不新增全局调度计数状态。 |

## 2. ACT 微元设计

| ACT 微元 | 3.5 层类型 | target layer | target file | function/class | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|---|---|---|
| `PublishAuthorization` | 数据 | types | `src/model_deploy/act/types/action_publish.py` | frozen dataclass | mode、最终 allowed、reason | 不可变授权对象 | 无 | mux gate 事实仅参考，所有权重写给 L2-06 |
| `ActionPublishRequest` | 数据 | types | 同上 | frozen dataclass | action_id、SafetyResult、authorization、ROS/单调时间 | 单次调用契约 | 无 | Pi0.5 无对应，ACT 新增 |
| `CommandTargets` | 数据 | types | 同上 | frozen dataclass | 两个 TCP7、两个 0..100 爪目标 | transport-neutral 四路目标 | 无 | `BimanualAction` 仅结构参考 |
| `ActionPublishPlan` | 数据 | types | 同上 | frozen dataclass | request、targets、mode | policy/command 是否计划发布、reason | 无 | Pi0.5 无显式 plan，ACT 为本地原子性新增 |
| `ActionPublishResult` | 数据 | types | 同上 | frozen dataclass | 调用事实 | action_id/safety/publish count/sent/failure | 无 | mux JSON status 只参考 transport |
| `CommandOutputConfig` | 数据 + 校验函数 | config | `src/model_deploy/act/config/schema.py` | frozen dataclass | YAML frame/scale/deadband/interval | 已校验输出配置 | 无 | topic/config 注入结构复用 |
| command output YAML | 数据 | config_files | `src/model_deploy/act/config_files/deploy.yaml` | mapping | 具体值 | 配置实例 | 文件由 L2-01 loader 读取 | Pi0.5 deploy.yaml 只参考字段组织 |
| `require_safe_action` | 计算函数 | service | `src/model_deploy/act/service/action_output_adapter.py` | function | SafetyResult | ActionSpec 或契约异常 | 无 | 旧 ControlCommand 无安全来源标记，ACT 新增 |
| `map_gripper_command` | 计算函数 | service | 同上 | function | `[0,1]`、CommandOutputConfig | `0..100` float | 无 | 旧 `hand_command_to_trigger` 方向相反，不复用 |
| `build_command_targets` | 计算函数 | service | 同上 | function | safe ActionSpec、config | `CommandTargets` | 无 | 旧 `split_action` 只参考拆分思想 |
| `build_publish_plan` | 计算函数 | service | 同上 | function | request、config | `ActionPublishPlan` | 无 | 旧 mode property 是反例 |
| ROS message builders | 计算函数 | ui | `src/model_deploy/act/ui/action_publisher.py` | module functions | plan/config | 6 个 ROS message RAM 对象 | 无 | `_joint_msg` 仅参考 message 构造位置 |
| `ActionPublisher` | 数据读写 + 状态更新 + 编排 | ui | 同上 | class | node-like publisher factory、DeployConfig | `publish(request)->ActionPublishResult` | 创建 publisher、publish ROS、更新最小状态 | Pi05VlaDeployNode/Bridge 的 publisher 生命周期仅结构复用 |
| `ActionPublisher._should_publish_gripper` | 计算函数 | ui | 同上 | method | side/target/monotonic_s | bool + reason | 只读最小状态 | Pi0.5 无对应，ACT 新增 |
| `ActionPublisher._record_gripper_success` | 内部状态更新函数 | ui | 同上 | method | side/target/time | 更新 last target/time | RAM 状态变化 | Pi0.5 只保存 arm last，语义不复用 |
| `ActionPublisher._publish_status` | 数据读写函数 | ui | 同上 | method | ActionPublishResult | `/act/command/status` | ROS publish | CommandMux JSON status 参考 transport |

## 3. 公共类型字段

### 3.1 `PublishAuthorization`

```text
mode: Literal["dry-run", "shadow-run", "safe-run"]
command_allowed: bool
reason: str | None
```

`command_allowed` 是 L2-06 汇总后的最终判决。L2-05 不通过这个对象读取 enable、急停或 driver topic 原值。

### 3.2 `ActionPublishRequest`

```text
action_id: str
safety_result: SafetyResult
authorization: PublishAuthorization
ros_time_s: float
monotonic_s: float
```

### 3.3 `ActionPublishResult`

```text
action_id: str
safety_ok: bool
policy_action_published: bool
command_publish_count: int       # 0..4，deadband 有意跳过的 gripper 单独记录
gripper_skipped: tuple[str, ...]
sent_to_driver: bool             # 本次计划的 command ROS publish 全部调用成功
failure_reason: str | None
driver_accepted: None            # L2-05 不知道；禁止伪造 True
hardware_reached: None           # L2-05 不知道；禁止伪造 True
```

`sent_to_driver` 表示消息已提交到 driver topic，不等于 driver accepted、硬件执行或到位。

## 4. 纯 RAM 算法

### 4.1 safe action 入口复核

```text
require_safe_action(result):
  if result.accepted is not True or result.action is None:
      raise UnsafeActionInput
  vector = result.action.as_vector()
  require shape == (16,) and all finite
  require gripper[14], gripper[15] within [0,1]
  return result.action
```

这里复核的是跨模块契约，不重新做 L2-04 的 quaternion/TCP delta 安全算法。若上游传来 gripper=50/100，即使 `accepted=True` 也整批失败，以暴露尺度漂移。

### 4.2 gripper 映射

```text
map_gripper_command(value):
  require 0 <= value <= 1
  return output_min + value * (output_max - output_min)
```

默认：`0 -> 0`、`0.5 -> 50`、`1 -> 100`。不根据数值大小猜测输入尺度，不兼容“可能是 0..100”的模糊输入。

### 4.3 模式计划

```text
dry-run:
  publish_policy = False
  publish_commands = False

shadow-run:
  publish_policy = True
  publish_commands = False

safe-run:
  publish_policy = True
  publish_commands = authorization.command_allowed
```

若 `authorization.mode != config.runtime.mode`，计划必须拒绝 command 并返回 `mode_mismatch`；不得选更宽松的一方。

## 5. `ActionPublisher.publish()` 编排

```text
1. require_safe_action(request.safety_result)
2. build_publish_plan（纯 RAM）
3. 构造 policy、status 草稿、左右 PoseStamped、左右 Float64
4. 任一 command 构造失败 -> 四路 command 调用 0；生成 failure result/status
5. dry-run -> 只返回 RAM result
6. shadow/safe -> publish policy_action
7. safe + authorization ->
     a. 决定左右 gripper 是否被 deadband/min interval 跳过
     b. 依次 publish 左臂、右臂、计划中的左爪、右爪
     c. 每次成功后计数；仅在 gripper publish 成功后更新对应 last state
8. 捕获 ROS publish 异常 -> partial_ros_publish:n/4；不能回滚已发消息
9. publish command status（若 ROS 可用）
10. 保存 last_result 并同步返回给 L2-06
```

status publisher 自身失败时，函数仍返回 `ActionPublishResult` 给 L2-06，并把 `failure_reason` 追加 `status_publish_failed`。

## 6. 内部协作

```text
Creation order:
1. L2-01 构造 DeployConfig（含 CommandOutputConfig）。
2. L2-06 创建 ROS node 和 ActionPublisher(node, config)。
3. ActionPublisher 创建六个 publisher；不创建 subscription/timer。
4. 每 tick L2-06 先调 L2-04，再构造 ActionPublishRequest 调 publisher.publish。

State owner:
- L2-06：action_id、时间、mode/gate 汇总、fallback、重试、全局 metrics。
- L2-05：publisher handle、左右夹爪最近成功发布目标/时间、last_result。

Pure RAM calculations:
- safe 来源复核、16D 拆分、frame/单位填充、[0,1] -> [0,100]、模式计划。

External boundary reads/writes:
- 只写六个 ROS topic；不读文件/topic/硬件。

Runtime orchestration point:
- L2-06 control tick 同步调用 publish；L2-05 无自主 timer/thread。

Failure propagation:
- 契约/构造/授权/ROS 异常 -> ActionPublishResult + command status。
- L2-06 根据结果选择 fallback/blocked/retry；L2-05 不自行切全局状态。
```

## 7. class / function 判断

| 候选 | 决定 | 原因 |
|---|---|---|
| `ActionPublisher` | class | 长生命周期 publisher + 最小 deadband 状态 + 最近结果；适合 3.25 层打包。 |
| `CommandOutputConfig` | frozen dataclass | 只读配置数据，不是业务服务。 |
| 请求/授权/目标/结果 | frozen dataclass | 跨 L2 RAM 语言，创建后不可变。 |
| safe 复核/映射/plan | function | 无状态纯计算；单测简单，禁止无状态 class。 |
| ROS message builder | function | 输入 plan 输出 message，无持久状态。 |
| 单独 ROS Node | 不新增 | L2-06 拥有 node/生命周期；L2-05 是被注入 node-like factory 的输出组件。 |

## 8. 六层产物表

| 层 | 是否需要 | 文件路径 | 职责 | 输入 | 输出 | 不负责 | Gate |
|---|---|---|---|---|---|---|---|
| types | 是 | `types/action_publish.py` | 公共 RAM 契约 | 安全结果/授权/时间 | request/targets/plan/result | ROS/config 读取 | import/frozen/schema tests |
| config | 是 | `config/schema.py`、`config_files/deploy.yaml` | 输出 frame/scale/deadband | YAML | CommandOutputConfig | publish/安全算法 | config validator tests |
| repo | 否 | — | 无外部资源读取 | — | — | 文件/bundle | static no-artifact |
| service | 是 | `service/action_output_adapter.py` | 纯 RAM 拆分/映射/计划 | request/config | targets/plan | ROS/状态 | unit + property tests |
| runtime | 否 | — | 调度由 L2-06 | — | — | timer/fallback/metrics | static no-artifact |
| ui | 是 | `ui/action_publisher.py` | ROS message/publish/status/deadband | plan/node/config | topic 副作用/result | subscription/硬件 SDK | mock + shadow tests |

## 9. 已知跨分支一致性风险

| 风险 | 本设计的确定处理 |
|---|---|
| 当前 checkout L1 仍写旧串行 bridge/workspace/IK | 以用户指定详细约束和本包为准；上游 L1 未同步前禁止 Gate 合入。 |
| 当前 config 缺 frame/output mapping | 本 L2 设计 `CommandOutputConfig` 窄扩展，不引入 BridgeConfig/HardwareConfig。 |
| 当前 `RuntimeConfig.publishes_command_topics` 让 shadow=true | L2-05 禁止使用；Gate 直接检查 shadow 四路调用数=0。 |
| L2-04 worktree 设计曾把 gripper clamp 写为 0..100 | 本 L2 只接受 `[0,1]`；给 50/100 时整批拒绝，推动上游修正。 |
| ROS 多 topic 运行期可能部分成功 | 如实返回 partial count；不声称可回滚或原子事务。 |

## 10. 开放项

无待用户决定项。环境缺 ROS 时 UI 实测为 `BLOCKED_ENV`；缺硬件时 real-robot 为 `BLOCKED_HARDWARE_EXPECTED`，均不改变设计。

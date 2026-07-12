# config 层设计：L2-05

> [!info] 元信息
> - 消费对象：config 实现/验收 Agent。
> - 权威性：本文定义 L2-05 必需的输出映射配置窄扩展。
> - 上游来源：用户详细边界中“DeployConfig 提供 topic/frame/mode/output mapping”的输入契约。
> - 不负责范围：不读取 YAML、不创建 publisher、不表达原始硬件 gate。
> - 读取时机：修改 schema/default YAML 前。
> - 冲突处理：若 L2-01 已提供等价字段，复用并迁移，不允许并存两个同义配置对象。

## 1. 目标源码路径

```text
src/model_deploy/act/config/schema.py
src/model_deploy/act/config/__init__.py
src/model_deploy/act/config_files/deploy.yaml
```

## 2. 层职责

config 层定义“输出映射有哪些静态参数、类型和合法值”。文件读取仍由 L2-01 完成；L2-05 只消费已经进入 RAM 的 `DeployConfig.command_output`。

当前 schema 有 command topics 与 runtime mode，但缺 frame、gripper output scale、deadband 和最小间隔。为了满足已确认输入契约，本 L2 增加 `CommandOutputConfig`；这是功能 L2 横跨 config 的窄补齐，不复活旧 bridge/mux/hardware 配置。

## 3. `CommandOutputConfig` class 设计

```text
left_arm_frame_id: str = "left_arm_base"
right_arm_frame_id: str = "right_arm_base"
gripper_input_min: float = 0.0
gripper_input_max: float = 1.0
gripper_output_min: float = 0.0
gripper_output_max: float = 100.0
gripper_deadband: float = 1.0
gripper_min_publish_interval_s: float = 0.05
qos_depth: int = 10
```

它是 frozen dataclass，作为 `DeployConfig.command_output` 字段。topics 继续使用现有 `TopicsConfig.command`；mode 继续使用 `RuntimeConfig.mode`。

## 4. 校验函数

| 校验 | 通过条件 | 失败行为 |
|---|---|---|
| frame | 非空、无空白-only | `DeployConfigError` |
| gripper input | 精确 `0.0 < 1.0`，且本版锁定 0/1 | `DeployConfigError`；禁止模糊尺度 |
| gripper output | `min < max`，本设备默认 0/100 | `DeployConfigError` |
| deadband | `>= 0` 且不超过 output span | `DeployConfigError` |
| min interval | `>= 0` | `DeployConfigError` |
| QoS depth | 正整数 | `DeployConfigError` |

## 5. mode 属性拆分

当前 `RuntimeConfig.publishes_command_topics` 把 shadow/safe 合并为 true，容易泄漏四路 command。设计改为两个只读属性：

```text
publishes_policy_observation:
  shadow-run / safe-run -> True
  dry-run -> False

may_attempt_driver_commands:
  safe-run -> True
  dry-run / shadow-run -> False
```

即使 `may_attempt_driver_commands=True`，仍必须再满足 L2-06 `PublishAuthorization.command_allowed=True`。属性不替代授权。

旧属性应删除或明确 deprecated，L2-05 代码不得调用。

## 6. YAML 设计

```yaml
command_output:
  left_arm_frame_id: left_arm_base
  right_arm_frame_id: right_arm_base
  gripper_input_min: 0.0
  gripper_input_max: 1.0
  gripper_output_min: 0.0
  gripper_output_max: 100.0
  gripper_deadband: 1.0
  gripper_min_publish_interval_s: 0.05
  qos_depth: 10
```

禁止在此段加入 workspace、IK、driver IP、deadman topic、RM65 SDK、Modbus 或 USB-485 参数。硬件执行配置属于外部 driver；原始授权汇总属于 L2-06。

## 7. 输入、输出与副作用

| 输入 | 输出 | 副作用 |
|---|---|---|
| 启动期 raw mapping（由既有 loader 提供） | frozen `CommandOutputConfig`、扩展后的 DeployConfig | 无；config 层不读文件 |

## 8. 依赖关系

允许：标准库、types、现有 config helper。

禁止：repo/service/runtime/ui、rclpy、硬件库。config 不执行业务映射或发布。

## 9. Pi0.5 参考

- `deploy/config/schema.py` 的 frozen config 和 validator 组织方式可结构复用。
- 旧 BridgeConfig/MuxConfig、14D、hand 300/1000 与 `publishes_command_topics` 不复用。
- `deploy.yaml` 仅参考分段布局，不继承旧 topic/gate/hardware 值。

## 10. 验收覆盖

- 默认值构造成功，字段进入 `DeployConfig.command_output`。
- 空 frame、反向范围、负 deadband/interval、非正 QoS 全失败。
- mode 属性矩阵严格为 dry(0/0)、shadow(1/0)、safe(1/1)。
- 配置不出现 bridge/mux/hardware 执行字段。

## 11. 边界继承声明

本层产物只服务当前 L2-05 已确认的输出配置输入。配置读取所有权仍属于 L2-01；新增 config 文件落点不把 L2-05 重新解释成旧 layer-based 任务。

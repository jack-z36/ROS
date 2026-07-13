# config 层设计：L2-05

> [!info] 元信息
> - 消费对象：config/启动装配实现与验收 Agent。
> - 权威性：定义 C7 输出映射配置及 CLI 人工总开关契约。
> - 上游来源：用户确认的 `--enable-command-output` + 单一 `pose_frame_id` 设计。
> - 不负责范围：不创建 publisher、不表达原始硬件 gate、不执行发布。
> - 读取时机：修改 schema、CLI 装配或默认配置前。

## 1. 目标源码路径

```text
src/model_deploy/act/config/schema.py
src/model_deploy/act/config/__init__.py
src/model_deploy/act/config_files/deploy.yaml        # 只含持久化映射值
L2-06/UI 启动装配入口                               # CLI -> final config
```

## 2. 层职责

config 层定义“输出映射有哪些静态参数、类型和合法值”。L2-05 只消费已经进入 RAM 的 C7 `CommandOutputConfig`，不读取 YAML，也不解析 CLI。

人工 command 总开关必须是启动期显式 CLI 决定，而不是持久化 YAML 默认值；这样旧配置文件不能意外开启真实 command。

## 3. C7 `CommandOutputConfig` 字段

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `command_output_enabled` | 启动期只读标量，默认 False | `bool` |
| `pose_frame_id` | 非空字符串，左右臂共用 | `str` |
| `gripper_input_min` | 常量型标量，首版 0.0 | `float` |
| `gripper_input_max` | 常量型标量，首版 1.0 | `float` |
| `gripper_output_min` | 标量，默认 0.0 | `float` |
| `gripper_output_max` | 标量，默认 100.0 | `float` |
| `gripper_deadband` | 非负标量，output 域 | `float` |
| `gripper_min_publish_interval_s` | 非负标量 | `float` |
| `qos_depth` | 正整数 | `int` |

`CommandOutputConfig` 是 frozen dataclass，并作为 `DeployConfig.command_output` 字段交付。

## 4. CLI 契约

唯一启用参数：

```text
--enable-command-output
```

语义：

```text
未显式传入：command_output_enabled=False
显式传入：  command_output_enabled=True
```

约束：

- 使用 `store_true` 或等价的“缺省 False”解析方式。
- YAML `command_output` 段不得包含 `enabled: true`；loader 应拒绝或忽略持久化 enable，并由启动装配显式覆盖。
- CLI 只提供人工静态总开关，不替代每 tick `CommandPermit`。
- L2-05 不读取 argv；CLI parser/launch 属启动 UI/装配协作点。
- 不再为 L2-05 定义 `dry-run / shadow-run / safe-run` mode。

## 5. YAML 设计

```yaml
command_output:
  pose_frame_id: base
  gripper_input_min: 0.0
  gripper_input_max: 1.0
  gripper_output_min: 0.0
  gripper_output_max: 100.0
  gripper_deadband: 1.0
  gripper_min_publish_interval_s: 0.05
  qos_depth: 10
```

禁止加入：

- `enabled: true`
- per-arm frame（除非引入显式 TF 设计）
- workspace、IK、driver IP、deadman topic
- RM65 SDK、Modbus、USB-485 参数
- bridge/mux/mode 段

## 6. 校验函数

| 校验 | 通过条件 | 失败行为 |
|---|---|---|
| CLI enabled | 类型严格 bool；缺省 False | `DeployConfigError` |
| pose frame | 非空、非 whitespace | `DeployConfigError` |
| gripper input | 首版严格 0.0/1.0 且 min<max | `DeployConfigError` |
| gripper output | finite、min<max | `DeployConfigError` |
| deadband | finite、>=0、不超过 output span | `DeployConfigError` |
| min interval | finite、>=0 | `DeployConfigError` |
| QoS depth | 正整数 | `DeployConfigError` |

## 7. 旧 `RuntimeConfig.mode` 迁移

当前源码仍存在 `RuntimeConfig.mode` 与 `publishes_command_topics`。本 L2 规则是：

- L2-05 实现不得读取这两个成员。
- `mode_mismatch` 分支删除。
- 后续上游迁移应更新 config tests 和其他消费者；在迁移完成前可暂时保留字段，但必须标记 deprecated。
- 验收脚本里的 dry-run/shadow-run 只能表示验证层级，不能成为 config 枚举。

## 8. 输入、输出与副作用

| 输入 | 输出 | 副作用 |
|---|---|---|
| 启动 CLI bool + loader 提供的 raw mapping | frozen C7、扩展后的 DeployConfig | 无；config 层不发布、不读硬件 |

## 9. 依赖关系

允许：标准库、types、现有 config helper。

禁止：repo/service/runtime/ui 核心实现、rclpy、硬件库。启动 UI 可以把 CLI bool 传给 config assembly，但 config 不反向 import UI。

## 10. Pi0.5 参考

- frozen config 和 validator 组织方式可结构复用。
- 旧 `publishes_command_topics`、BridgeConfig/MuxConfig、mode state 不复用。
- deploy.yaml 只参考分段布局，不继承旧 gate/hardware 值。

## 11. 验收覆盖

- CLI 缺省 False、显式参数 True。
- YAML 无法静默开启 command。
- 单一 frame、范围、deadband、interval、QoS 的合法/非法测试。
- L2-05 搜索不到 `RuntimeConfig.mode` / `publishes_command_topics` 消费。
- config 文件不出现 bridge/mux/hardware 执行字段。

## 12. 边界继承声明

本层只服务当前 L2-05 输出配置输入。文件读取所有权仍属于 L2-01；CLI parser 属启动装配。新增 config 落点不把 L2-05 重新解释成旧 layer-based 配置任务。

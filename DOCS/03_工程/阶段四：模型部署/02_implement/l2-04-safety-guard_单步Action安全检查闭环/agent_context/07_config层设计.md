# config 层设计：L2-04

## 1. 目标源码路径

```text
src/model_deploy/act/config/schema.py::SafetyConfig
src/model_deploy/act/config_files/deploy.yaml::safety
```

配置对象属于 L2-01；L2-04 只消费它。本文件记录跨 L2 的必要协调，不把配置加载逻辑迁入 service。

## 2. 所需静态契约

| 字段 | 类型/单位 | 供哪个微元使用 | 校验 |
|---|---|---|---|
| `max_translation_step_m` | float，m | C10 | `> 0` |
| `max_rotation_step_rad` | float，rad | C11 | `> 0` 且合理 |
| `gripper_min/max` | float，同部署 ActionDomain | C12 | `min <= max` |
| `max_gripper_step` | float，同部署 ActionDomain | C13 | `>= 0` |
| `quaternion_norm_tolerance` | float，无量纲 | C8/C15 | `> 0` |
| `pose_frame`、`quaternion_order`、`gripper_domain` | 静态 ActionDomain 元数据 | A1 前提 | 与 ActionSpec/Observation/L2-05 一致 |

现有 `max_tcp_delta_per_step`、`hand_min/max`、`quaternion_check` 不能被无条件继承：在实现 L3 中应迁移/兼容到上述语义，且不可把 F100 寄存器 `0~100` 当作模型 action 域默认值。

## 3. Class/函数与边界

本 L2 不在 config 层新增 Class。L2-01 的 schema/parser 负责：读取配置、校验 units/domain、创建 immutable `SafetyConfig`。A1 只做防御性构造期断言，不读文件。

副作用：L2-04 无。依赖方向：service 可依赖 config；config 不得依赖 service/runtime/ui。

## 4. Pi0.5 参考与验收

- Pi0.5 `SafetyConfig` 是“guard 持有不可变 policy”的结构参考。
- 关节限位字段、RM 原生夹爪数值、fallback policy 不进入 L2-04 SafetyConfig。
- 验收：config parser 对非法范围/单位域失败；A1 构造失败不进入运行循环。

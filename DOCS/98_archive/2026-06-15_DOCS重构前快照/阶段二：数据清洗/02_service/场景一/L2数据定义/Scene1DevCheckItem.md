# Scene1DevCheckItem

## 定义

`Scene1DevCheckItem` 是 `./start_data_clean.sh --dev -> 场景一` 下的一个功能检验菜单项。它描述开发者要检验哪个场景一功能、使用什么小样本输入、允许哪些临时覆盖、产生哪些测试产物和运行日志。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `scene_id` | string | 固定为 `service_s1` |
| `group_id` | string | `service-s1-g1` 到 `service-s1-g6` |
| `check_id` | string | 功能检验项稳定标识 |
| `label` | string | 开发者菜单中展示的名称 |
| `target_l2` | string | 对应 L2 能力模块 |
| `default_config` | path | 默认读取的生产配置 |
| `sample_input` | path/null | 默认小样本输入 |
| `allowed_overrides` | list | 本次运行允许临时覆盖的配置项 |
| `artifacts` | list | 预期 [[Scene1DevArtifact]] |
| `run_log` | object | [[Scene1DevRunLog]] |

## 有效性规则

- 每个功能组至少有一个 `Scene1DevCheckItem`。
- `check_id` 在场景一内必须唯一。
- 检验项不得要求开发者记忆内部脚本路径；菜单项负责调用脚本。
- 临时覆盖默认只对本次 [[Scene1DevRun]] 生效，除非开发者显式选择保存到配置文件。

## 相关链接

- [[Scene1DevRun]]
- [[Scene1DevArtifact]]
- [[Scene1DevRunLog]]
- [[Scene1DevConfigOverride]]

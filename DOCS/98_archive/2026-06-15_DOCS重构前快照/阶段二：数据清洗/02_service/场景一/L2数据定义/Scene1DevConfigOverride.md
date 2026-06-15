# Scene1DevConfigOverride

## 定义

`Scene1DevConfigOverride` 是开发者在 `--dev` 引导界面中为本次功能检验临时覆盖的配置项。默认只作用于当前 [[Scene1DevRun]]，不写回正式配置。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `key_path` | string | 被覆盖的配置路径 |
| `old_value` | any | 生产配置中的原值 |
| `new_value` | any | 本次运行使用的新值 |
| `scope` | enum | 默认 `current_run_only` |
| `save_to_config` | boolean | 是否显式写回正式配置 |

## 有效性规则

- 默认 `save_to_config=false`。
- 只有开发者明确选择“保存到配置文件”时，才允许写回正式配置。
- 所有覆盖项必须写入 [[Scene1DevRunLog]]。
- 覆盖后的有效配置必须保存为本次 run 的 `effective_config.yaml`。

## 相关链接

- [[Scene1DevRun]]
- [[Scene1DevRunLog]]

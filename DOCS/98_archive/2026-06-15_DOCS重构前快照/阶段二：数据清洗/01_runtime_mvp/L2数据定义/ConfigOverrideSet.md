# ConfigOverrideSet

## 定义

`ConfigOverrideSet` 是 Runtime MVP 本次运行临时覆盖配置项的集合。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[03_配置加载与配置快照模块]]

## 现实语义

`ConfigOverrideSet` 表示“这一次运行在原始配置文件基础上临时改了什么”。例如开发者临时指定输入目录、输出目录或 workers 数量，这些覆盖只对本次运行生效，但必须进入配置快照，方便复现。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `overrides` | map | 是 | 覆盖项路径到覆盖值的映射。 |
| `override_source` | string | 否 | 覆盖项来自命令行、交互入口、测试夹具或后续 UI。 |
| `applied_at` | datetime 或空 | 否 | 覆盖项应用到配置的时间。 |
| `empty_is_valid` | boolean | 是 | 无覆盖项是否仍是有效集合；第一版应为 true。 |

## 有效性规则

- `overrides` 可以为空；空集合表示使用原始配置文件内容。
- 覆盖项不得直接修改磁盘上的原始配置文件。
- 覆盖项必须能在 [[ConfigSnapshot]] 中追溯来源。
- 覆盖项是否字段合法、类型正确，由配置预检查模块或现有配置解析逻辑进一步判断。

## 上游来源

- Runtime 入口参数。
- 开发者模式交互选择。
- 后续 smoke test 任务提供的测试覆盖。

## 下游消费者

- [[EffectiveRuntimeConfig]]
- [[ConfigSnapshot]]
- 配置预检查模块。
- 结构化日志模块。

## 不负责

- 不定义全部配置字段 schema。
- 不负责判断某个覆盖值是否能用于真实业务处理。
- 不把覆盖项写回 `config/data_clean/` 下的正式配置文件。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 覆盖项路径使用点路径还是嵌套 map | 影响代码实现和快照可读性。 | L2 只要求能表达和追溯，L3 实现前再确定。 | L3 任务生成前确认。 |

## 相关链接

- [[RuntimeConfigSource]]
- [[EffectiveRuntimeConfig]]
- [[ConfigSnapshot]]
- [[03_配置加载与配置快照模块]]


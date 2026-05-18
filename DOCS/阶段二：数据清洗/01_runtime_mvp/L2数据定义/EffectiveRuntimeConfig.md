# EffectiveRuntimeConfig

## 定义

`EffectiveRuntimeConfig` 是 Runtime MVP 本次运行最终生效的配置语义对象。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[03_配置加载与配置快照模块]]

## 现实语义

`EffectiveRuntimeConfig` 表示“本次 Runtime 真正按什么配置执行”。它由 [[RuntimeConfigSource]] 指向的原始配置内容加上 [[ConfigOverrideSet]] 合并得到，后续配置预检查、输入产物预检查、Service 调度、日志和 manifest 都应消费这份生效配置，而不是重新猜测配置来源。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `config_source` | [[RuntimeConfigSource]] | 是 | 本次原始配置来源。 |
| `override_set` | [[ConfigOverrideSet]] | 是 | 本次临时覆盖项集合。 |
| `effective_data` | map | 是 | 合并覆盖后的配置内容。 |
| `loaded_at` | datetime 或空 | 否 | 配置读取完成时间。 |
| `config_format` | string | 是 | 第一版主要为 YAML。 |
| `content_hash` | string 或空 | 否 | 生效配置内容的可选摘要，用于追溯。 |

## 有效性规则

- 必须由一个存在的 [[RuntimeConfigSource]] 构造。
- 必须显式记录 [[ConfigOverrideSet]]，即使覆盖项为空。
- `effective_data` 必须是可序列化结构，能够写入 [[ConfigSnapshot]]。
- 生效配置只代表“已读取并合并”，不代表配置业务合法。

## 上游来源

- 配置加载与配置快照模块读取 [[RuntimeConfigSource]]。
- 配置加载与配置快照模块应用 [[ConfigOverrideSet]]。
- 现有配置解析能力可作为第一版实现参考。

## 下游消费者

- 配置预检查模块。
- 输入产物预检查模块。
- 场景注册与 Service 调度模块。
- [[ConfigSnapshot]]
- 结构化日志模块。
- Manifest 与错误摘要模块。

## 不负责

- 不负责创建 [[RunDirectory]]。
- 不负责把配置快照写入文件。
- 不负责判断输入产物是否存在。
- 不负责真实 Service 的业务参数解释。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要为生效配置建立独立代码 Type | 影响 L3 拆分粒度。 | L2 先固定语义，L3 实现时决定是否复用现有 `AppConfig` 或新增 Runtime 配置对象。 | L3 任务生成前确认。 |

## 相关链接

- [[RuntimeConfigSource]]
- [[ConfigOverrideSet]]
- [[ConfigSnapshot]]
- [[RunContext]]
- [[03_配置加载与配置快照模块]]


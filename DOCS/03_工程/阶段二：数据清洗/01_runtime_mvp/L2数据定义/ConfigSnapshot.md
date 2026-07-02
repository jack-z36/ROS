# ConfigSnapshot

## 定义

`ConfigSnapshot` 是写入 run 目录的本次生效配置快照文件及其内容语义。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[03_配置加载与配置快照模块]]

## 现实语义

`ConfigSnapshot` 表示“这一次运行可复现的配置证据”。它保存 [[EffectiveRuntimeConfig]] 的最终生效内容，并记录 [[RuntimeConfigSource]] 与 [[ConfigOverrideSet]]，使后续日志、manifest 和错误排查能知道本次运行实际使用了什么配置。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `snapshot_path` | [[RunArtifactPath]] | 是 | 快照文件路径，固定语义为 run 目录下 `config_snapshot.yaml`。 |
| `effective_config` | [[EffectiveRuntimeConfig]] | 是 | 本次最终生效配置。 |
| `written_at` | datetime 或空 | 否 | 快照写入时间。 |
| `snapshot_format` | string | 是 | 第一版为 YAML。 |
| `is_required` | boolean | 是 | Runtime 每次成功进入配置阶段后都必须写出。 |

## 有效性规则

- `snapshot_path` 必须来自 [[RunDirectoryLayout]] 中的配置快照路径。
- 快照必须写在 [[RunDirectory]] 内，不得写回 `config/data_clean/`。
- 快照内容必须反映最终生效配置，而不是只复制原始配置文件。
- 快照写入失败时不得继续执行后续预检查和调度。

## 上游来源

- [[RunDirectoryLayout]] 提供 `config_snapshot.yaml` 的目标路径。
- [[EffectiveRuntimeConfig]] 提供要写入的生效配置内容。

## 下游消费者

- 配置预检查模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不判断配置是否满足某个场景的业务必需字段。
- 不保存真实数据产物。
- 不替代 `processing_manifest.json`。
- 不负责修改原始配置文件。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 快照文件是否附带 hash 字段 | 影响长期追溯和 manifest 对账。 | 第一版可选记录，由 L3 实现时决定。 | Manifest 模块设计时确认。 |

## 相关链接

- [[RuntimeConfigSource]]
- [[ConfigOverrideSet]]
- [[EffectiveRuntimeConfig]]
- [[RunDirectory]]
- [[RunDirectoryLayout]]
- [[RunArtifactPath]]
- [[03_配置加载与配置快照模块]]


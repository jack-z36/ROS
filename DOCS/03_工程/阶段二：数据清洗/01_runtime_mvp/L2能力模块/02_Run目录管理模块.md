# L2 能力模块说明：Run 目录管理模块

## 1. 能力名称

```text
Runtime MVP / Run 目录管理模块
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：`runtime_mvp`  
场景：Runtime MVP，不归入 `02_service` 的具体业务场景  
模块类别：数据读写类  
来源功能模块清单：[[功能模块清单]]

## 3. 一句话目标

```text
为每次 Runtime 运行创建独立 run 目录，并向后续配置快照、日志、manifest、错误摘要和 fake service 输出提供稳定路径语义。
```

## 4. 能力角色

```text
本能力是 Runtime MVP 的运行记录容器管理能力，负责把一次运行从一开始就放进独立、可追溯、不可复用的目录中。
```

它承接 [[RunContext]] 中的运行身份、目标场景和运行模式，产出 [[RunDirectory]]、[[RunDirectoryLayout]] 和一组 [[RunArtifactPath]]。它不负责写具体运行记录文件内容。

## 5. 上游关系

- 来自 [[RunContext]] 的 `run_id`、目标 [[SceneName]]、[[RunMode]] 和输出位置语义。
- 来自阶段二文件存放规范的强制路径边界：Runtime 运行记录进入 `src/data_clean/runs/`。
- 来自用户确认的目录命名策略：日期 + 简单场景编号；不使用时分秒。
- 来自 Runtime MVP 功能模块清单的主干顺序：运行上下文定义之后，配置加载、预检查、调度、日志和 manifest 之前。

## 6. 下游关系

- 配置加载与配置快照模块依赖本能力提供 `config_snapshot.yaml` 的目标路径。
- 结构化日志模块依赖本能力提供 `run_log.json` 的目标路径。
- Manifest 与错误摘要模块依赖本能力提供 `processing_manifest.json`、`error_summary.json` 和 `run_result.json` 的目标路径。
- Fake Service 模块可以把调试输出写入本能力创建的 `outputs/`。
- Runtime smoke test 模块需要验证本能力在成功和失败路径中都不复用旧目录。

## 7. 职责边界

本能力负责：

1. 生成本次运行的最终 `run_id` 和 [[RunDirectory]]。
2. 创建独立 run 目录和 `outputs/` 子目录。
3. 声明 [[RunDirectoryLayout]] 中固定文件路径，供后续模块写入。
4. 在同一天同一场景重复运行时追加短序号，避免复用旧目录。

本能力不负责：

1. 写入 `run_log.json`、`config_snapshot.yaml`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json` 的内容。
2. 创建 raw、cleaned、validated、aligned、canonical dataset 或 exports 等真实数据产物。
3. 调用 fake service 或真实 service。
4. 判断输入 MCAP、配置文件或 Service 输出是否有效。

## 8. 读写职责

本能力负责的读写动作：

| 动作 | 读取来源 | 写入目标 | 格式 | 下游消费者 |
| --- | --- | --- | --- | --- |
| 读取运行身份语义 | [[RunContext]] | 无 | 内存对象 / 后续 Types | 本模块自身 |
| 检查 run 根目录 | `src/data_clean/runs/` | 无 | 文件系统目录 | 本模块自身 |
| 创建本次 [[RunDirectory]] | 日期、目标场景、已有目录列表 | `src/data_clean/runs/{run_id}/` | directory | 所有 Runtime 横切模块 |
| 创建调试输出目录 | [[RunDirectory]] | `outputs/` | directory | Fake Service、smoke test |
| 声明运行记录路径 | [[RunDirectory]] | [[RunDirectoryLayout]] | 路径语义，不写文件内容 | 配置快照、日志、manifest、错误摘要 |

## 9. 路径与命名规则

| 文件 / 目录 | 路径来源 | 命名规则 | 是否允许覆盖 | 创建时机 |
| --- | --- | --- | --- | --- |
| run 根目录 | 文件存放规范 | `src/data_clean/runs/` | 不适用 | Runtime 初始化时确保存在 |
| 单场景 run 目录 | [[RunContext]] + 日期 + 场景编号 | `{YYYY-MM-DD}_s{scene_number}` | 不允许 | 配置加载前 |
| 全流程 run 目录 | [[RunContext]] + 日期 | `{YYYY-MM-DD}_all` | 不允许 | 配置加载前 |
| 重复运行目录 | 已有目录冲突检测 | `{base_run_id}_002`、`{base_run_id}_003` | 不允许 | 发现冲突时 |
| 调试输出目录 | [[RunDirectory]] | `outputs/` | 仅新目录内允许创建 | run 目录创建后立即创建 |
| 日志路径 | [[RunDirectoryLayout]] | `run_log.json` | 本模块不写入 | 结构化日志模块执行时 |
| 配置快照路径 | [[RunDirectoryLayout]] | `config_snapshot.yaml` | 本模块不写入 | 配置快照模块执行时 |
| manifest 路径 | [[RunDirectoryLayout]] | `processing_manifest.json` | 本模块不写入 | Manifest 模块执行时 |
| 错误摘要路径 | [[RunDirectoryLayout]] | `error_summary.json` | 本模块不写入 | 失败路径由错误摘要模块写入 |
| 运行结果路径 | [[RunDirectoryLayout]] | `run_result.json` | 本模块不写入 | Manifest 与结果汇总模块写入 |

## 10. 文件格式与内容契约

| 文件 | 格式 | 必填内容 | 可选内容 | 校验方式 |
| --- | --- | --- | --- | --- |
| [[RunDirectory]] | directory | `outputs/` 子目录 | 后续模块写入的运行记录文件 | 路径存在且可写 |
| `outputs/` | directory | 无 | fake service 调试产物 | 路径存在且位于 [[RunDirectory]] 内 |
| `run_log.json` | JSON | 由结构化日志模块定义 | 本模块不定义 | 本模块只声明路径 |
| `config_snapshot.yaml` | YAML | 由配置加载与配置快照模块定义 | 本模块不定义 | 本模块只声明路径 |
| `processing_manifest.json` | JSON | 由 Manifest 模块定义 | 本模块不定义 | 本模块只声明路径 |
| `error_summary.json` | JSON | 由错误摘要模块定义 | 本模块不定义 | 本模块只声明路径 |
| `run_result.json` | JSON | 由 Manifest 与错误摘要模块定义 | 本模块不定义 | 本模块只声明路径 |

## 11. 覆盖策略与幂等性

- 重复运行时如何处理：同一天同一场景重复运行时自动追加 `_002`、`_003` 等短序号。
- 是否允许覆盖已有文件：不允许覆盖旧 run 目录，也不允许在已有 run 目录内重新初始化。
- 如何避免污染旧 run：创建前检查目标目录是否存在；存在则生成下一个短序号目录。
- 临时文件或半成品如何处理：第一版不引入临时目录；目录创建失败时返回 [[RuntimeErrorRef]]，不得继续调度。

## 12. 失败处理

| 失败情况 | 判断方式 | 处理策略 | 错误信息要求 | 是否写入报告 |
| --- | --- | --- | --- | --- |
| run 根目录不可创建 | 文件系统异常或权限不足 | 阻止后续 Runtime 执行 | 包含目标根目录路径和失败原因 | 后续错误摘要模块若可用则写入 |
| 目标 run 目录已存在且无法生成新序号 | 冲突检测超过实现限制 | 阻止后续 Runtime 执行 | 包含 base run id 和已尝试序号 | 后续错误摘要模块若可用则写入 |
| `outputs/` 创建失败 | 文件系统异常或权限不足 | 删除本次未完成目录或标记初始化失败 | 包含 outputs 路径和失败原因 | 后续错误摘要模块若可用则写入 |
| 生成路径逃逸 run 根目录 | 路径规范化后不在 `src/data_clean/runs/` 下 | 阻止创建 | 包含非法路径和期望根目录 | 是 |

## 13. 整体完成标准

- [ ] 已建立 [[RunDirectory]]、[[RunDirectoryLayout]] 和 [[RunArtifactPath]] 的原子数据定义。
- [ ] 本 L2 能力模块说明中出现的数据概念均使用 Obsidian 双向链接。
- [ ] 能从 [[RunContext]] 派生出单场景和全流程的 run 目录名。
- [ ] 同一天重复运行不会复用旧目录，而是追加短序号。
- [ ] 创建出的 run 目录至少包含 `outputs/`。
- [ ] 本 L2 没有混入日志、配置快照、manifest 或错误摘要内容写入职责。

## 14. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- |
| runtime_mvp_004 | 定义 Run 目录 Types 与命名规则 | 数据定义类 | 本 L2 与 [[RunDirectory]]、[[RunDirectoryLayout]]、[[RunArtifactPath]] | Run 目录相关 Types 或等价结构 | `src/data_clean/schemas/` 或后续确定的 Types 位置 | 构造单场景、全流程和重复运行命名测试通过 |
| runtime_mvp_005 | 实现 Run 目录创建器 | 数据读写类 | [[RunContext]] 与 Run 目录 Types | 新建 [[RunDirectory]] 和 `outputs/` | `src/data_clean/runtime/` 或 `src/data_clean/repo/` 中合适位置 | 临时目录下创建、不覆盖、冲突递增测试通过 |
| runtime_mvp_006 | 接入 RunContext 回填 run_dir | 数据读写类 | [[RunContext]]、Run 目录创建结果 | 带 `run_dir` 和路径布局的上下文 | Runtime 初始化边界 | 最小 Runtime 初始化测试通过 |

## 15. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| Run 目录创建器最终属于 Runtime 层还是 Repo 层 | 影响代码落点和依赖方向。 | L2 只固定语义；L3 实现前结合现有代码结构决定。 | L3 任务生成前确认。 |
| 是否允许用户通过配置指定 run 根目录 | 影响多人协作和临时磁盘使用。 | 第一版固定 `src/data_clean/runs/`。 | Runtime 入口设计时确认。 |
| 初始化失败时是否清理半成品目录 | 影响失败现场保留和目录整洁。 | 第一版倾向保留失败现场，但标记初始化失败。 | L3 实现前确认。 |

## 16. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 每个 L3 必须有明确输入、输出、修改边界、验收命令和成功标准。
4. 每个 L3 必须写明“本次不做什么”。
5. 每个 L3 不能跨越本 L2 的能力边界。
6. 如果需要修改本 L2 之外的模块，必须在 L3 文档中显式说明原因。

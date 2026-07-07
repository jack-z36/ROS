# 阶段四模型部署工程索引

本目录承载阶段四模型部署的工程推进材料。读取前先按根 `AGENTS.md` 选择任务类型，并读取对应上下文加载规则。

## 目录入口

| 目录 | 用途 | 读取条件 |
|---|---|---|
| `00_status/` | Ralph / OpenCode 循环状态上下文 | 启动或恢复阶段四循环工程时读取 |
| `01_contracts/` | 阶段四接口契约和数据约定参考库，不是当前 L2/L3 拆解权威 | 需要补充确认输入输出、topic、shape 或兼容边界时按需读取 |
| `02_implement/` | 当前 L1/L2 权威工作包；包含 L1 任务文档、L1 功能模块边界、L1 功能模块协作架构、人类可视化 HTML 和新版功能闭环 L2 设计目录 | 需要理解或规划阶段四 L2 范围 |
| `03_tasks/` | L3 任务、dispatch 与验收卡片 | 执行、调度或验收阶段四 L3 |
| `04_debug/` | 阶段四 debug 工程记录 | 定位阶段四异常或测试失败 |
| `05_acceptance/` | L2 Gate 运行验收材料 + 人类验收清单与签字 | 汇总 L2 验收、检查自动同步前置条件（含人类验收关卡） |
| `pi05_old/` | 旧实现参考材料 | 用户明确要求对照旧实现时读取 |

> [!warning] 当前权威主线
> 当前 ACT 第一版不再以 `AS-IS / TO-BE / Contract Delta` 聚类 L2。当前权威入口是：
> - `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
> - `02_implement/00_L1_ACT部署程序任务文档.md`（任务管理）
> - `02_implement/01_L1_ACT功能模块边界.md`（模块边界，Agent 权威）
> - `02_implement/02_L1_ACT功能模块协作架构.md`（模块协作，Agent 权威）
> - `02_implement/ACT架构交互可视化.html`（人类可视化）
> - 当前新版 L2 设计目录。
>
> `01_contracts/` 下契约只作为参考语义库。`ACT Contract Delta.md` 和旧 Pi0.5 Contract Delta 不得作为 L2/L3 生成权威。
| `ralph_stage4_prompt.md` | OpenCode 主 Agent 启动引导 | 每次 Ralph / OpenCode 阶段四循环最初加载 |
| `目标描述框架.md` | 旧 Contract Delta 目标描述方法，当前仅作历史参考 | 用户明确要求对照旧规划方法时读取 |

## 默认不读

- `pi05_old/` 默认不作为上下文入口。
- `03_tasks/归档/_archived_pi05/` 是已废弃的 Pi0.5 版 L2/L3/dispatch 归档，除非用户明确要求对照旧规划，否则不读。
- `02_implement/归档/`、`03_tasks/归档/_legacy_layer_based_act/`、`05_acceptance/_legacy_layer_based_act/` 是旧 layer-based ACT 产物隔离区，默认不读。
- `04_debug/` 只在 Debug / Bugfix 任务中按需读取。
- 阶段四循环工程启动时只从 `ralph_stage4_prompt.md`、循环工程加载规则和 `00_status/` 恢复状态，不默认读取全部 L3 正文。

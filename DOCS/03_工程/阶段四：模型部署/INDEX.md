# 阶段四模型部署工程索引

本目录承载阶段四模型部署的工程推进材料。读取前先按根 `AGENTS.md` 选择任务类型，并读取对应上下文加载规则。

## 目录入口

| 目录 | 用途 | 读取条件 |
|---|---|---|
| `00_status/` | Ralph / OpenCode 循环状态上下文 | 启动或恢复阶段四循环工程时读取 |
| `01_contracts/` | 阶段四接口契约和数据约定 | 需要确认模型部署输入输出、topic、shape 或兼容边界 |
| `02_l2_change_packages/` | L2 改造工作包 | 需要理解或规划阶段四 L2 范围 |
| `03_tasks/` | L3 任务、dispatch 与验收卡片 | 执行、调度或验收阶段四 L3 |
| `04_debug/` | 阶段四 debug 工程记录 | 定位阶段四异常或测试失败 |
| `05_acceptance/` | L2 Gate 运行验收材料 + 人类验收清单与签字 | 汇总 L2 验收、检查自动同步前置条件（含人类验收关卡） |
| `pi05_old/` | 旧实现参考材料 | 用户明确要求对照旧实现时读取 |

> [!note] ACT / Pi0.5 双契约并存
> `01_contracts/` 下当前两套契约并存：
> - **ACT 版（第一版主线）**：`ACT部署契约.md`、`ACT Contract Delta.md`、`ACT模型训练交付物契约.md`。
> - **Pi0.5 版（历史保留）**：`TO-BE Contract.md`、`Contract Delta.md`、`模型训练交付物契约.md`。
> 硬件相关契约（command_bridge / rm65 / elephant_gripper / fisheye_camera / tactile_sensor 节点契约）与模型无关，两套共用。
| `ralph_stage4_prompt.md` | OpenCode 主 Agent 启动引导 | 每次 Ralph / OpenCode 阶段四循环最初加载 |
| `目标描述框架.md` | 阶段四目标描述框架 | 需要确认阶段四目标表达边界 |

## 默认不读

- `pi05_old/` 默认不作为上下文入口。
- `03_tasks/_archived_pi05/` 是已废弃的 Pi0.5 版 L2/L3/dispatch 归档，除非用户明确要求对照旧规划，否则不读。
- `04_debug/` 只在 Debug / Bugfix 任务中按需读取。
- 阶段四循环工程启动时只从 `ralph_stage4_prompt.md`、循环工程加载规则和 `00_status/` 恢复状态，不默认读取全部 L3 正文。

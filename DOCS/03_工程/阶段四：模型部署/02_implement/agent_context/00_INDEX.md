# L1 ACT Agent 上下文索引

## 1. 定位

本目录是阶段四 ACT 部署程序 L1 架构协作包的 Agent 权威上下文。

```text
人类入口：../ACT架构交互可视化.html
Agent 权威上下文：本目录下 Markdown
```

`../ACT架构交互可视化.html` 只服务人类理解。Agent 做 L2 设计、L3 生成、L3 执行、验收或 Git 合入时，必须以本目录 Markdown 和阶段四工作流规则为准。

## 2. 路由表

| 读取目的 | 必读文件 |
|---|---|
| 确认 L1 总目标、L2 清单、开发顺序和 L1 验收口径 | `01_L1_ACT部署程序任务文档.md` |
| 确认每个 L2 的功能定义、输入、输出、负责/不负责、完成判据 | `02_L1_ACT功能模块边界.md` |
| 确认模块间数据流、RAM 对象所有权、同步/异步边界、失败传播和 metrics/status | `03_L1_ACT功能模块协作架构.md` |
| 确认 L2-04 raw action 的绝对位姿语义，以及 previous safe action / latest ObservationSnapshot 的比较基准边界 | `04_L2-04绝对位姿单步变化检查边界.md` |

## 3. HTML-MD 语义对齐表

| HTML view id | HTML view label | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `overview` | 整体架构 | L1 由哪些 L2 组成、开发顺序是什么 | `01_L1_ACT部署程序任务文档.md` | `L2 功能模块清单` / `L2 线性开发顺序` | L2 稳定 ID、依赖关系、L1 验收口径 |
| `boundary` | 模块边界 | 每个 L2 负责什么、不负责什么 | `02_L1_ACT功能模块边界.md`；L2-04 绝对位姿细则见 `04_L2-04绝对位姿单步变化检查边界.md` | 各 L2 边界章节；L2-04 比较基准见原子文档 §1-§4 | 输入输出、完成判据、代码层落点；L2-04 两类比较基准的语义差异 |
| `dataflow` | 宏观数据流 | observation、snapshot、chunk、action、status 如何流转 | `03_L1_ACT功能模块协作架构.md` | `宏观数据流契约` | RAM 对象所有权、同步/异步边界 |
| `control-loop` | ControlLoop 调控 | `ControlLoop.tick()` 在调度什么 | `03_L1_ACT功能模块协作架构.md` | `ControlLoop 调控契约` | 启动、稳态、fallback、失败传播 |
| `failure` | 失败传播 | 失败如何进入 fallback、blocked、status | `03_L1_ACT功能模块协作架构.md` | `失败传播关系` | 各 L2 失败来源和处理边界 |
| `metrics` | Metrics / status | 运行状态从哪里汇总和发布 | `03_L1_ACT功能模块协作架构.md` | `Metrics / status 汇总方式` | 每个 L2 的状态字段贡献 |

## 4. 污染检查

Agent 使用本目录时必须确认：

- 不从旧 `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware` 推导当前 L2 边界。
- 不把 `ACT Contract Delta`、`AS-IS Contract -> TO-BE Contract -> Contract Delta` 写成当前任务来源。
- 不把阶段二 L2/L3 模板作为阶段四 ACT 设计模板。
- `DOCS/03_工程/阶段四：模型部署/01_contracts/` 只能补充 topic、shape、bundle、hardware semantics、safety semantics，不能定义当前 L2/L3 拆分。

## 5. 更新规则

人类基于 `../ACT架构交互可视化.html` 提出优化建议时，Agent 必须先更新本目录中的权威 Markdown，再同步更新 HTML 投影。

若暂时无法同步 HTML，必须同时在本文件和 HTML 中标记 HTML 已过期，不得让后续 Agent 误用 HTML 生成 L3。

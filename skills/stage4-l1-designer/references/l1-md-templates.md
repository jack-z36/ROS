# L1 Agent Context Markdown Templates

This reference documents the exact section structure for the 4 L1 agent_context files. Use alongside the existing `agent_context/` files under `l2-01-external-contract_*` as concrete examples.

## File 1: `00_INDEX.md` — Agent Context Index

Routing hub for the entire L1 package. Agents read this first.

```
# L1 {{SYSTEM}} Agent 上下文索引

## 1. 定位与权威性
> Declaration: this directory is Agent-authoritative context
> HTML is human entry; conflict → MD wins
> Baseline date

## 2. 必读顺序
| 顺序 | 文件 | 唯一职责 | 读完后必须能回答 |
|---:|---|---|---|
| 1 | 01_L1_{{SYSTEM}}部署程序任务文档.md | ... | ... |
| 2 | 02_L1_{{SYSTEM}}功能模块边界.md | ... | ... |
| 3 | 03_L1_{{SYSTEM}}功能模块协作架构.md | ... | ... |

## 3. 设计成熟度与绑定规则
| L2 | 当前成熟度 | L1 文档允许固定的内容 | L1 文档禁止提前固定的内容 |
### 3.1 稳定名称与逻辑名称
- Confirmed contract names (can be used directly)
- Logical terms only (must NOT assume class/file structure)

## 4. {{N}} 个 L2 的一句话索引
| L2 ID | 当前中文边界名 | 一句话责任 |

## 5. HTML-MD 语义对齐表
| HTML 视图 | 人类视图 | 权威 Markdown | 权威章节 | HTML 省略但 Markdown 必须保留的内容 |

## 6. 污染检查
> Bullet list of forbidden legacy patterns

## 7. 无上下文 Agent 的进入检查
> 6 numbered questions an agent must answer before any L2 work
```

## File 2: `01_L1_{{SYSTEM}}部署程序任务文档.md` — Task Document

```
# L1 {{SYSTEM}} 部署程序任务文档

> [!info] 文档职责: task management only; boundary → 02; collaboration → 03; baseline date

## 1. L1 总目标
> End-to-end ASCII pipeline

## 2. 第一版任务约束
> Bullet list of L1-scope constraints

## 3. {{N}} 个 L2 功能模块
| 开发顺序 | L2 ID | 当前边界名 | L1 级唯一目标 | 当前状态 |

## 4. 开发顺序
> ASCII chain + table of ordering reasons

## 5. L2 依赖关系
| L2 | 直接依赖 | 依赖目的 |

## 6. 第一版范围
### 6.1 必须交付
### 6.2 明确不进入第一版

## 7. L1 验收口径
### 7.1 文档 Gate
### 7.2 本地能力 Gate
### 7.3 集成 dry-run / shadow-run Gate
### 7.4 real-robot Gate

## 8. 下游阶段 Gate
### 8.1 进入具体 L2 设计前
### 8.2 进入 L3 前
```

## File 3: `02_L1_{{SYSTEM}}功能模块边界.md` — Module Boundary Document

```
# L1 {{SYSTEM}} 功能模块边界

> [!info] 文档职责: per-module boundary authority; collaboration → 03; baseline date

## 1. 使用规则
### 1.1 L1 边界不是内部实现设计
### 1.2 四类功能角色 (Table: 启动资源 / RAM业务 / ROS输出 / 中央运行)
### 1.3 外部副作用边界 (Table: allowed vs forbidden per L2)
### 1.4 时间、线程和状态原则
### 1.5 {{N}}D 语义连续性 (Table: segment semantics + scale conversion boundaries)

## 2..N+1. Per-L2 sections (one per module)
### {{X}}.1 功能定义
### {{X}}.2 输入
### {{X}}.3 输出
### {{X}}.4 负责内容
### {{X}}.5 不负责内容
### {{X}}.6 状态与生命周期 (Table)
### {{X}}.7 失败边界
### {{X}}.8 完成判据
### {{X}}.9 允许代码层
### {{X}}.10 上下游

## N+2. 边界矩阵
> Table: Responsibility | L2-01 | L2-02 | ... (拥有/禁止/只消费/只调用)

## N+3. 不可破坏的不变量
> Numbered list
```

## File 4: `03_L1_{{SYSTEM}}功能模块协作架构.md` — Collaboration Architecture

```
# L1 {{SYSTEM}} 功能模块协作架构

> [!info] 文档职责: collaboration/ownership/sync-async/failure; boundaries → 02; baseline date

## 1. 协作总原则 (1.1–1.4)
## 2. 六个模块的协作角色 (Table)
## 3. 启动期协作 (3.1 顺序, 3.2 资源传播 mermaid, 3.3 失败传播 table)
## 4. 稳态宏观数据流 (mermaid flowchart)
## 5. 关键对象与所有权 (5.1 启动/业务, 5.2 运行调度, 5.3 安全/发布, 5.4 ND连续性)
## 6. Observation 事件轴 (6.1 调用方向, 6.2 snapshot时机, 6.3 时间语义)
## 7. Inference 运行轴 (7.1 为什么异步, 7.2 请求产生, 7.3 latest-only, 7.4 调用与结果包装)
## 8. Control Tick 调度轴 (8.1 tick语义顺序, 8.2 active chunk语义)
## 9. Safety 与 Publish 协作 (9.1 必经路径, 9.2/9.3 责任分界table, 9.4 原子性边界)
## 10. 运行模式协作 (dry-run, shadow-run, safe-run)
## 11. 同步与异步边界 (Table)
## 12. 失败传播与禁止行为 (Table)
## 13. Fallback 所有权 (13.1 固定原则, 13.2 未固定策略)
## 14. Status 与 Metrics 协作 (14.1 所有权, 14.2 指标来源table, 14.3 外部状态语义)
## 15. Shutdown 协作 (numbered sequence)
## 16. 成功路径时序 (mermaid sequence diagram)
## 17. 第一版安全与硬件现实边界 (17.1 保证, 17.2 不保证, 17.3 外部保护)
## 18. 面向后续 L2 设计的读取要求
## 19. 协作不变量 (numbered list)
```

## Cross-Reference Rules

1. `00_INDEX.md` routing table must list all other files in agent_context/
2. `00_INDEX.md` §3 maturity table must match §2-N+1 sections in 02 file
3. `02` file §1.5 ND semantics must match `03` file §5.4 continuity chain
4. `03` file §2 role table must match `02` file per-module sections
5. All module IDs must be identical across all 4 files
6. HTML `data-agent-source` attributes must point to exact MD file paths
7. Pollution check in `00_INDEX.md` §6 must cover all legacy patterns mentioned in `01`–`03`

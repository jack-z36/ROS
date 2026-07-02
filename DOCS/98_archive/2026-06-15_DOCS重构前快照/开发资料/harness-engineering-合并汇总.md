# Harness Engineering 知识库汇总

> 本文档由目录下所有 md 文件按逻辑顺序合并而成
>
> 生成日期：2026-05-03


---

> **来源文件：`harness-engineering-md/README.md`**

中文 | [English](README.en.md)

# Harness Engineering 学习指南

> 一个从概念理解到独立实践的 Harness Engineering 深度学习档案

## 前言

这是一个不断生长的学习项目。**Harness Engineering**（驭缰工程）是 OpenAI 在 2026 年 2 月提出的工程范式：工程师不再写代码，而是设计环境、明确意图、构建反馈回路，让 AI 智能体可靠地完成工作。

> **人类掌舵，智能体执行。**

本仓库记录了从阅读原文、拆解概念、形成思考、动手实践到输出作品的完整学习过程。希望对同样关注 AI 工程化的朋友有所帮助。

来源：[OpenAI — Harness Engineering: Harnessing Codex in an Agent-First World](https://openai.com/zh-Hans-CN/index/harness-engineering/)

> **注意：** 以下经验分享并非普遍适用，请在具体实践中结合场景，辩证采纳。

## ⚡ 一句话理解

```
传统工程：人类写代码 → 机器执行代码
Harness Engineering：人类设计约束 → 智能体写代码 → 机器执行代码
```

核心转变：**工程师的产出从代码变成了约束系统**——AGENTS.md、架构规则、自定义 linter、反馈回路。

## 🧭 六大核心概念

<details>
<summary><b>1. 仓库即记录系统</b> — 不在仓库里的东西，对智能体不存在</summary>

Slack 讨论、Google Docs、脑子里的知识 = 对智能体不可见。一切决策、规范、计划都必须以版本化工件提交到仓库。

→ 详见 [concepts/01-repo-as-source-of-truth.md](concepts/01-repo-as-source-of-truth.md)
</details>

<details>
<summary><b>2. 地图而非手册</b> — AGENTS.md 是目录页，不是百科全书</summary>

~100 行的入口文件，指向更深层的文档。渐进式披露：智能体从小入口点开始，被指导下一步该看什么。巨型指令文件的三个死因：挤占上下文、无法维护、无法机械验证。

→ 详见 [concepts/00-overview.md](concepts/00-overview.md)
</details>

<details>
<summary><b>3. 机械化执行</b> — 文档会腐烂，lint 规则不会</summary>

自定义 linter + 结构测试 = 不变量的守护者。lint 错误信息里内嵌修复指令，智能体可以自我纠正。在中央层面强制执行边界，在本地层面允许自主权。

→ 详见 [concepts/02-mechanical-enforcement.md](concepts/02-mechanical-enforcement.md)
</details>

<details>
<summary><b>4. 智能体可读性</b> — 优先为智能体的推理能力优化</summary>

选"无聊"技术（API 稳定、训练集覆盖好）。有时重新实现子集比包装不透明的上游行为更划算。让应用可以按 git worktree 启动。

→ 详见 [concepts/04-agent-readability.md](concepts/04-agent-readability.md)
</details>

<details>
<summary><b>5. 吞吐量改变合并理念</b> — 纠错成本低，等待成本高</summary>

PR 生命周期很短。测试偶发失败通过后续重跑解决。在智能体吞吐量远超人类注意力的系统中，这通常是正确的选择。

→ 详见 [concepts/05-throughput-changes-merge.md](concepts/05-throughput-changes-merge.md)
</details>

<details>
<summary><b>6. 熵管理 = 垃圾回收</b> — 技术债是高息贷款</summary>

智能体会复现仓库中已有的模式——包括坏模式。将"黄金规则"编码进仓库，定期后台任务扫描偏差、更新质量评分、发起重构 PR。

→ 详见 [concepts/03-entropy-and-garbage-collection.md](concepts/03-entropy-and-garbage-collection.md)
</details>

## 🔑 关键数据点

| 指标 | 数据 |
|------|------|
| 团队规模 | 3 人 → 7 人 |
| 时间跨度 | 5 个月 |
| 代码量 | ~100 万行 |
| PR 数量 | ~1,500 个 |
| 人均日 PR | 3.5 个（扩展后仍在增长） |
| 单次运行时长 | 6+ 小时（通常在人类睡眠时间） |
| 效率估算 | 手工编写的 ~1/10 时间 |

## 📂 仓库结构

```
harness-engineering/
├── README.md           ← 你在这里
├── AGENTS.md           ← 仓库导航入口（给智能体看的）
│
├── concepts/           # Phase 1：概念笔记
│   ├── AGENTS.md       #   目录说明 + 内容索引
│   ├── 00-overview.md  #   六大核心概念总览
│   ├── 01-...          #   仓库即记录系统
│   ├── 02-...          #   机械化执行
│   └── 03-...          #   熵管理与垃圾回收
│
├── thinking/           # Phase 2：独立思考与质疑
├── practice/           # Phase 3：小项目实验
├── feedback/           # Phase 4：踩坑与迭代心得
├── works/              # Phase 5：可展示的作品
├── prompts/            # 验证有效的提示词积累
└── references/         # 外部资源索引
```

每个子目录都有自己的 `AGENTS.md`，说明该目录的用途和写作约定。这本身就是原文「渐进式披露」的实践。

## 🚀 学习路线

- [ ] **Phase 1：理解核心概念** — 阅读 `concepts/`，拆解原文六大概念
- [ ] **Phase 2：形成自己的观点** — 在 `thinking/` 中写下质疑和延伸思考
- [ ] **Phase 3：选一个小项目实践** — 在 `practice/` 中用 AI 智能体从零构建
- [ ] **Phase 4：记录反馈迭代** — 在 `feedback/` 中记录踩坑和修正
- [ ] **Phase 5：输出可展示的作品** — 在 `works/` 中提炼成文章或工具

## 🔗 相关项目与资源

### 原始来源

| 资源 | 说明 |
|------|------|
| [OpenAI 原文（中文）](https://openai.com/zh-Hans-CN/index/harness-engineering/) | Harness Engineering 的完整阐述 |

### Ralph 系列 — Harness Engineering 的实战框架

「Ralph Wiggum 循环」是 Harness Engineering 的核心实现模式：让智能体在循环中自主工作直到任务完成。

| 项目 | Stars | 说明 |
|------|-------|------|
| [snarktank/ralph](https://github.com/snarktank/ralph) | 13.6k | 原版 Ralph：bash 脚本反复启动 AI，每次迭代清空上下文，直到 PRD 全部完成。6 条核心信条（Fresh Context、Backpressure、Plan Is Disposable 等） |
| [ralph-orchestrator](https://mikeyobrien.github.io/ralph-orchestrator/) | 2.3k | Rust 进化版：Hat 角色系统 + 事件驱动协调 + 多后端（Claude/Kiro/Gemini/Codex）+ 背压门控 + 持久化记忆 |
| [bmad-ralph](https://github.com/qianxiaofeng/bmad-ralph) | 2 | BMAD 方法论 + Ralph：并行 Claude Code worktree + 三层自愈（retry → restart → diagnose）+ SQLite 状态机 |

### Ralph 六条信条（与 Harness Engineering 的映射）

| Ralph 信条 | Harness Engineering 对应概念 |
|-----------|---------------------------|
| Fresh Context Is Reliability | 智能体可读性 — 每次迭代重新读取 |
| Backpressure Over Prescription | 机械化执行 — 不规定怎么做，但门控拒绝坏结果 |
| The Plan Is Disposable | 熵管理 — 重新生成的成本只是一次 planning loop |
| Disk Is State, Git Is Memory | 仓库即记录系统 — 文件是交接机制 |
| Steer With Signals, Not Scripts | 人类掌舵 — 加路标，不加脚本 |
| Let Ralph Ralph | 智能体执行 — 坐在循环上，不坐在循环里 |

### Anthropic 官方 — Harness 设计实战

| 资源 | 说明 |
|------|------|
| [Harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) | Anthropic Labs 实战：GAN 启发的三智能体架构（Planner→Generator→Evaluator），Sprint 合同机制，Context Anxiety 解法，Harness 随模型升级瘦身的方法论 |

### 效率悖论与能力进化

| 资源 | 说明 |
|------|------|
| [为什么 AI 写代码更快但交付没变](https://yousali.com/posts/20260303-ai-coding-efficiency-to-evolution/) | 16667 字深度长文：约束理论拆解效率悖论，Spec/Rule/Skill 三层区分，验证闭环，并发策略。"AI 就是今天的 NCX-10" |

### 社区资源

| 资源 | 说明 |
|------|------|
| [vibe-coding-cn](https://github.com/tukuaiai/vibe-coding-cn) | 中文 Vibe Coding 社区指南，仓库组织方式值得参考 |

## 🤝 参与贡献

欢迎通过 Issue 和 PR 参与：
- 补充概念笔记（`concepts/` 中还有待补充的概念）
- 分享你的独立思考（`thinking/`）
- 贡献实践案例（`practice/`）
- 推荐相关资源（`references/`）

## 📞 联系方式

| 渠道 | 链接 |
|------|------|
| GitHub | [@deusyu](https://github.com/deusyu) |
| X (Twitter) | [@0xdeusyu](https://x.com/0xdeusyu) |
| Telegram | [@DeusThink](https://t.me/DeusThink) |
| Telegram 交流群 | [@talkdeusyu](https://t.me/talkdeusyu) |
| Telegram 频道 | [@lovedesuyu](https://t.me/lovedesuyu) |
| Email | [rainman.deus@gmail.com](mailto:rainman.deus@gmail.com) |

## Star History

如果这个项目对您有帮助，请考虑为其点亮一颗 Star ⭐！

[![Star History Chart](https://api.star-history.com/svg?repos=deusyu/harness-engineering&type=Date)](https://star-history.com/#deusyu/harness-engineering&Date)

## 📄 License

MIT

---

> **来源文件：`harness-engineering-md/concepts/00-overview.md`**

# Harness Engineering 概念总览

> 来源：OpenAI 2026-02-11，作者 Ryan Lopopolo
> 背景：3人团队用 Codex 从空仓库到100万行代码，5个月，零手写代码

## 一句话定义

Harness Engineering = 工程师不再写代码，而是**设计环境、明确意图、构建反馈回路**，让 AI 智能体可靠地完成工作。

## 六大核心概念

### 1. 仓库即记录系统（Repo as System of Record）

- 不在仓库里的东西，对智能体来说不存在
- Slack 讨论、Google Docs、脑子里的知识 = 对智能体不可见
- 一切决策、规范、计划都必须以版本化工件提交到仓库

### 2. 地图而非手册（Map, Not Manual）

- AGENTS.md ≈ 目录页（~100行），不是百科全书
- 渐进式披露：从小入口点开始，指向更深层的文档
- 巨型指令文件的三个死因：挤占上下文、无法维护、无法机械验证

### 3. 机械化执行（Mechanical Enforcement）

- 文档会腐烂，lint 规则不会
- 自定义 linter + 结构测试 = 不变量的守护者
- lint 错误信息里内嵌修复指令，智能体可以自我纠正

### 4. 智能体可读性（Agent Readability）

- 优先选择"无聊"技术（API 稳定、训练集覆盖好）
- 有时重新实现子集比包装不透明的上游行为更划算
- 让应用可以按 git worktree 启动，智能体可以启动隔离实例

### 5. 熵管理 = 垃圾回收（Entropy & Garbage Collection）

- 智能体会复现仓库中已有的模式——包括坏模式
- "黄金规则"编码进仓库，定期后台任务扫描偏差
- 技术债 = 高息贷款，小额持续偿还

### 6. 人类掌舵，智能体执行（Humans Steer, Agents Execute）

- 人类时间是最稀缺的资源
- 出问题时，答案不是"更努力"，而是"缺什么上下文/工具/约束"
- 工程师的新角色：设计环境 → 拆解任务 → 提示智能体 → 验证结果

## 架构模型

```
每个业务域内的固定分层：
Types → Config → Repo → Service → Runtime → UI

横切关注点通过 Providers 进入（auth, telemetry, feature flags）
依赖只能向前流动，由 linter 强制执行
```

## 关键数据点

- 3人团队 → 5个月 → ~100万行代码 → ~1500个 PR
- 人均每天 3.5 个 PR，扩展到 7 人后吞吐量还在增长
- 单次 Codex 运行可持续 6+ 小时（通常在人类睡眠时间）
- 估算：约为手工编写的 1/10 时间

---

> **来源文件：`harness-engineering-md/concepts/01-repo-as-source-of-truth.md`**

# 概念 1：仓库即记录系统

## 原文要点

智能体在运行时无法访问的任何内容，对它来说都**不存在**。

知识的存放位置决定了它是否有效：

| 位置 | 对人类 | 对智能体 |
|------|--------|----------|
| Google Docs | ✅ | ❌ |
| Slack 讨论 | ✅ | ❌ |
| 团队成员脑中 | ✅ | ❌ |
| 仓库内 Markdown | ✅ | ✅ |
| 代码 + 注释 | ✅ | ✅ |
| Lint 规则 | 间接 ✅ | ✅（强制） |

## 文档结构（原文方案）

```
AGENTS.md              ← 入口目录 (~100行)
ARCHITECTURE.md        ← 域和包分层的顶层地图
docs/
├── design-docs/       ← 设计决策，带验证状态
├── exec-plans/        ← 执行计划，带进度和决策日志
│   ├── active/
│   └── completed/
├── product-specs/     ← 产品规格
├── references/        ← 外部参考（llms.txt）
├── generated/         ← 自动生成（DB schema 等）
├── QUALITY_SCORE.md   ← 每个领域的质量评分
├── RELIABILITY.md
├── SECURITY.md
└── ...
```

## 关键实践

1. **AGENTS.md 是目录，不是百科** — ~100行，只指路
2. **专职 linter + CI 验证** — 知识库是否更新、是否交叉链接、结构是否正确
3. **doc-gardening 智能体** — 定期扫描过时文档，自动发起修复 PR
4. **执行计划是一等工件** — 提交到仓库，版本控制，带进度日志

---

> **来源文件：`harness-engineering-md/concepts/02-mechanical-enforcement.md`**

# 概念 2：机械化执行

## 核心思想

> 通过强制执行不变量，而非对实施过程进行微观管理

文档会腐烂。人会忘记。但 lint 规则和 CI 检查每次都会执行。

## 两类约束

### 架构约束（结构测试）
- 域内分层顺序：Types → Config → Repo → Service → Runtime → UI
- 依赖方向只能向前
- 横切关注点必须通过 Providers 进入
- 违反 = CI 阻塞合并

### 品味不变式（自定义 linter）
- 结构化日志（禁止 console.log 裸输出）
- Schema/类型的命名约定
- 文件大小限制
- 平台特定的可靠性要求

## 关键设计：lint 错误信息 = 修复指令

```
❌ 普通做法：
Error: File exceeds 500 lines.

✅ Harness 做法：
Error: File exceeds 500 lines.
Fix: Split into domain-specific modules following docs/ARCHITECTURE.md#splitting-guide.
Consider extracting types to <domain>/types/ and service logic to <domain>/service/.
```

错误信息中注入智能体可执行的修复路径 → 自我纠正闭环。

## 哲学

> 在中央层面强制执行边界，在本地层面允许自主权。

类似大型工程平台组织的管理模式：
- **严格的**：边界、正确性、可重复性
- **自由的**：边界内的具体实现方式
- 生成的代码不符合人类风格偏好？没关系。正确 + 可维护 + 智能体可读 = 达标。

---

> **来源文件：`harness-engineering-md/concepts/03-entropy-and-garbage-collection.md`**

# 概念 3：熵管理与垃圾回收

## 问题

智能体会复现仓库中已存在的模式——**包括坏模式**。

随着时间推移，不可避免地产生漂移（drift）：
- 重复的辅助函数散落各处
- 不一致的错误处理风格
- 基于猜测的数据结构（YOLO 式探测）
- 过时的文档与实际代码不符

## 失败方案：人工清理

> 团队每周五花 20% 时间清理"AI 残渣"。不出所料，不具备可扩展性。

## 成功方案：编码 + 自动化

### "黄金规则"（Golden Rules）

带主观意见的机械规则，编码进仓库：

1. **共享实用程序包 > 手写辅助工具** — 不变式集中管理
2. **不做 YOLO 探测** — 在边界验证数据，或使用类型化 SDK
3. **偏好自有实现的关键子集** — 与自有遥测集成、100% 测试覆盖、行为完全可预测

### 垃圾回收流程

```
定期后台 Codex 任务
  → 扫描偏差
  → 更新质量评分
  → 发起重构 PR
  → 大多数 1 分钟内审查 + 自动合并
```

## 类比

技术债 = 高息贷款

- ✅ 每天小额偿还（持续垃圾回收）
- ❌ 累积到痛苦时一次性清偿（重写/大重构）

## 关键洞察

> 人类的品味一旦被捕捉（编码为规则），就会持续应用于每一行代码。

品味的传播路径：
```
人类审查评论 → 文档更新 → lint 规则 → 自动应用于所有代码
```

---

> **来源文件：`harness-engineering-md/concepts/04-agent-readability.md`**

# 概念 4：智能体可读性（Agent Readability）

## 原文要点

智能体在运行时无法在上下文中访问的任何内容，对它来说都**不存在**。优化目标从"人类可读"转向"智能体可推理"。

## 核心实践

### 选择"无聊"技术

- 优先选择 API 稳定、训练集覆盖好的技术
- "无聊"技术对智能体来说更容易建模：可组合性好、API 稳定、训练数据充分

### 有时重新实现比包装更划算

原文示例：没有引入通用的 `p-limit` 风格包，而是自研了带并发的 map 辅助函数：
- 与自有 OpenTelemetry 仪表紧密集成
- 100% 测试覆盖
- 行为完全符合运行时预期

判断标准：上游行为是否**不透明**？如果是，重新实现子集可能更便宜。

### 让应用对智能体可操作

- 应用可以根据 git worktree 启动 → 每次变更启动独立实例
- Chrome DevTools 协议接入智能体运行时 → DOM 快照、截图、导航
- 本地可观测性堆栈（LogQL 查日志、PromQL 查指标）→ 临时环境，任务完成即删除

这使得以下提示词变得可行：
- "确保服务启动在 800ms 内完成"
- "这四个关键用户旅程中的任何跨度都不得超过两秒"

## 来自其他文章的补充

### LangChain — Context Rot 问题

上下文窗口填满后，模型性能会退化（"dumb zone"）。应对策略：
1. **Compaction** — 智能压缩和卸载上下文
2. **工具输出卸载** — 保留大输出的头尾，完整内容存文件系统
3. **渐进式披露（Skills）** — 按需加载，不在启动时预装所有工具

### HumanLayer — 60 行规则

AGENTS.md 控制在 **60 行以内**。超过这个长度，效果反而下降。

### Martin Fowler — 约束越严，自主性越强

> 限制解空间反而让 AI 更可靠。

这是一个反直觉的洞察：给智能体的自由度越大，它犯错的概率越高。通过架构约束收窄解空间，智能体在约束内的表现会显著提升。

---

> **来源文件：`harness-engineering-md/concepts/05-throughput-changes-merge.md`**

# 概念 5：吞吐量改变合并理念

## 原文要点

当 Codex 的吞吐量远超人类注意力时，传统的工程规范变得不再有效。

核心转变：**纠错成本低，等待成本高。**

## 具体变化

### PR 生命周期缩短

- 1,500 个 PR / 5 个月 / 3 人 = 人均每天 3.5 个 PR
- PR 不再是需要精雕细琢的大作，而是快速流动的小变更
- 扩展到 7 人后吞吐量仍在增长（说明瓶颈不在人数）

### 合并门控最小化

- 尽量减少阻塞合并的门
- 测试偶发失败 → 后续重跑解决，不无限期阻塞
- 在低吞吐量环境中这是不负责任的；在高吞吐量环境中这通常是正确的

### 智能体审查智能体

- 人类可以审核 PR，但**不是必须的**
- 随着时间推移，几乎所有审核都调整为智能体对智能体
- Ralph Wiggum 循环：Codex 本地审核 → 请求额外智能体审查 → 对反馈做出响应 → 循环直到所有审核通过

## 来自其他文章的补充

### HumanLayer — 优化迭代速度而非首次成功率

实战结论：
- ❌ 每次改动跑全量测试
- ✅ 优化迭代速度，快速发现和修复问题
- ✅ 便宜模型（Sonnet/Haiku）做子任务，贵模型（Opus）做编排

### LangChain — Ralph Loop 机制

长时间自主执行需要：
1. 文件系统 + git 追踪持久化工作
2. **Ralph Loop** 拦截退出，在新上下文窗口中重注入原始提示词
3. 规划 + 自我验证分解目标为步骤

### Martin Fowler — 技术栈收敛假说

当编码从手写转向引导生成时，开发者偏好作为选型标准的重要性下降。组织可能基于 harness 的质量和"AI 友好度"来选择技术栈 → 技术栈趋向收敛。

## 关键洞察

这个概念的本质是一个**经济学问题**：

```
传统模式：人力贵 + 吞吐量低 → 每个 PR 都要精心审查 → 阻塞门多
Harness 模式：智能体便宜 + 吞吐量高 → 快速迭代修复 → 阻塞门少
```

前提条件：必须有足够的**背压机制**（测试、lint、结构检查）来保证基本质量，否则就不是"快速迭代"而是"快速腐烂"。

---

> **来源文件：`harness-engineering-md/concepts/06-harness-definition.md`**

# 概念 6：Harness 的精确定义与组件清单

> 本概念由 LangChain、HumanLayer、Martin Fowler 三篇文章综合提炼，是对 OpenAI 原文的扩展。

## 定义

> **Agent = Model + Harness**
>
> Harness = 模型之外的一切代码、配置和执行逻辑。

裸模型不是智能体——它接受文本/图片/音频/视频，输出文本。它不能原生维护状态、执行代码、访问实时知识、搭建环境。当 harness 给它状态、工具执行、反馈回路和可执行约束时，它才成为智能体。

## 完整组件清单

### 来自 LangChain

| 组件 | 说明 |
|------|------|
| System Prompts | AGENTS.md、CLAUDE.md |
| Tools & MCP | 扩展智能体能力的工具和协议 |
| Skills | 渐进式加载的知识包 |
| 沙箱基础设施 | 文件系统、浏览器、隔离执行环境 |
| 编排逻辑 | 子智能体生成、handoff、模型路由 |
| Hooks/中间件 | compaction、续接、lint 检查 |

### 来自 HumanLayer（六个配置杠杆）

| # | 杠杆 | 要点 |
|---|------|------|
| 1 | AGENTS.md | ≤60 行，禁止自动生成 |
| 2 | MCP Servers | 信任边界 + 工具数量控制 |
| 3 | Skills | 渐进式披露，按需加载 |
| 4 | Sub-Agents | 上下文防火墙，隔离防 context rot |
| 5 | Hooks | 生命周期脚本，成功静默/失败报错 |
| 6 | Back-Pressure | 测试/构建/类型检查 = 自我验证回路 |

### 来自 Martin Fowler（三层框架）

```
┌─────────────────────────────────────────┐
│        Context Engineering              │  知识库 + 动态上下文
├─────────────────────────────────────────┤
│     Architectural Constraints           │  LLM 审查 + linter + 结构测试
├─────────────────────────────────────────┤
│     Garbage Collection Agents           │  定期扫描 + 修复漂移
└─────────────────────────────────────────┘
```

## Harness 与模型训练的耦合

LangChain 文章的关键发现：

- 模型在 post-training 阶段与特定 harness 共同训练
- 模型可能 **overfit 到特定 harness**，换 harness 后表现暴跌
- Terminal Bench 2.0 数据：**纯 harness 优化**可以把排名从 Top 30 拉到 Top 5
- 推论：最适合你任务的 harness，不一定是模型 post-training 时用的那个

## 与 Harness.io（CI/CD 平台）的关系

两者不是同一个东西，但共享同一个工程哲学：

```
AI Harness Engineering          Harness.io (CI/CD)
约束 AI 智能体的行为              约束代码交付的过程
AGENTS.md + linter + 背压       Pipeline + Policy-as-Code + 门控
目标：可靠的代码生成              目标：可靠的代码部署

共同本质：用确定性约束驾驭不确定性系统
         Backpressure over Prescription
```

---

> **来源文件：`harness-engineering-md/concepts/AGENTS.md`**

# concepts/ — 概念笔记

原文六大核心概念的拆解与整理。每个概念一个文件，编号排序。

## 文件约定

- 文件名：`{编号}-{英文短名}.md`，如 `01-repo-as-source-of-truth.md`
- 结构：原文要点 → 关键实践 → 原文引用
- `00-overview.md` 是总览，先读这个

## 已有内容

| 文件 | 概念 | 来源 |
|------|------|------|
| [00-overview.md](00-overview.md) | 六大核心概念总览 | OpenAI 原文 |
| [01-repo-as-source-of-truth.md](01-repo-as-source-of-truth.md) | 仓库即记录系统 | OpenAI 原文 |
| [02-mechanical-enforcement.md](02-mechanical-enforcement.md) | 机械化执行 | OpenAI 原文 |
| [03-entropy-and-garbage-collection.md](03-entropy-and-garbage-collection.md) | 熵管理与垃圾回收 | OpenAI 原文 |
| [04-agent-readability.md](04-agent-readability.md) | 智能体可读性 | OpenAI + LangChain + HumanLayer + Fowler |
| [05-throughput-changes-merge.md](05-throughput-changes-merge.md) | 吞吐量改变合并理念 | OpenAI + HumanLayer + LangChain + Fowler |
| [06-harness-definition.md](06-harness-definition.md) | Harness 的精确定义与组件清单 | LangChain + HumanLayer + Fowler |

## 下一步

读完概念后，去 [thinking/](../thinking/) 写你自己的理解和质疑。

---

> **来源文件：`harness-engineering-md/references/articles.md`**

# 文章索引

## 脉络一：AI 时代的 Harness Engineering（大模型护栏与认知工程）

### 1. OpenAI 官方 — 原点与哲学

- **标题：** Harness engineering: leveraging Codex in an agent-first world
- **链接：** [openai.com](https://openai.com/zh-Hans-CN/index/harness-engineering/)
- **作者：** Ryan Lopopolo | **日期：** 2026-02-11
- **核心：** 3 人团队用 Codex 从空仓库到 100 万行代码，零手写代码。提出六大概念：仓库即记录系统、地图而非手册、机械化执行、智能体可读性、吞吐量改变合并理念、熵管理。
- **关联：** 本仓库的学习起点，所有概念笔记的来源

### 2. Martin Fowler / Birgitta Böckeler — 系统性认知

- **标题：** Harness Engineering
- **链接：** [martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)
- **作者：** Birgitta Böckeler (Thoughtworks) | **日期：** 2026-02-17
- **核心：** 将 OpenAI 原文提炼为三层框架（Context Engineering → Architectural Constraints → Garbage Collection Agents），提出四个前瞻假说
- **三层框架：**

| 层 | 内容 |
|---|------|
| Context Engineering | 知识库 + 动态上下文（可观测性数据、浏览器导航） |
| Architectural Constraints | LLM 审查 + 确定性 linter + 结构测试 |
| Garbage Collection Agents | 定期扫描文档不一致和架构违规 |

- **四个假说：**
  1. Harness 将成为未来的服务模板（类似今天的 service template）
  2. 约束越严，自主性越强（限制解空间反而让 AI 更可靠）
  3. 技术栈将趋向收敛（选择标准从"开发者偏好"变成"AI 友好度"）
  4. Pre-AI 和 Post-AI 应用将分裂（给遗留代码补 harness 可能不经济）
- **犀利批评：** OpenAI 原文缺少功能正确性验证——harness 管了结构和架构，但没讲怎么测行为
- **延伸阅读：**
  - [Mitchell Hashimoto: My AI Adoption Journey #Step 5: Engineer the Harness](https://mitchellh.com/writing/my-ai-adoption-journey#step-5-engineer-the-harness)
  - [Context Engineering for Coding Agents](https://martinfowler.com/articles/context-engineering-coding-agents.html)
  - [Humans and Agents in Software Engineering Loops](https://martinfowler.com/articles/humans-and-agents.html)

### 3. LangChain / Viv Trivedy — 解剖与机制

- **标题：** The Anatomy of an Agent Harness
- **链接：** [blog.langchain.com](https://blog.langchain.com/the-anatomy-of-an-agent-harness/)
- **作者：** Vivek Trivedy | **日期：** 2026-03
- **核心：** 给出 harness 的精确定义和完整组件清单

> **Agent = Model + Harness**。Harness = 模型之外的一切代码、配置和执行逻辑。

- **组件清单：**
  - System Prompts / Tools / Skills / MCP
  - 沙箱基础设施（文件系统、浏览器）
  - 编排逻辑（子智能体、handoff、模型路由）
  - Hooks/中间件（compaction、续接、lint 检查）
- **关键洞察：**
  - **Context Rot** — 上下文填满后性能退化，需要 compaction + 工具输出卸载 + 渐进式披露
  - **Ralph Loop** — 拦截退出、重注入提示词、强制在新上下文窗口中继续
  - **Harness 与模型训练耦合** — 模型会 overfit 到特定 harness，换 harness 表现可能暴跌（Terminal Bench 2.0：纯 harness 优化可把排名从 Top 30 拉到 Top 5）

### 4. Anthropic / Prithvi Rajasekaran — Harness 设计实战（长时自主编码）

- **标题：** Harness design for long-running application development
- **链接：** [anthropic.com](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- **作者：** Prithvi Rajasekaran (Anthropic Labs) | **日期：** 2026-03-24
- **核心：** Anthropic 官方工程博客，GAN 启发的三智能体架构实战，从前端设计到全栈自主编码

- **两个核心问题：**
  1. **Context Anxiety** — 模型接近上下文极限时提前收尾（Sonnet 4.5 尤为明显），compaction 不够，需要 context reset
  2. **Self-Evaluation 失败** — 智能体评估自己的工作时倾向于过度称赞，即使质量平庸

- **三智能体架构（GAN 启发）：**

| 智能体 | 职责 |
|--------|------|
| Planner | 1-4 句提示词 → 完整产品规格（刻意高层级，避免细节错误向下游级联） |
| Generator | 按 sprint 逐特性实现，React + Vite + FastAPI + SQLite/PostgreSQL |
| Evaluator | 用 Playwright MCP 实际操作运行中的应用，逐条验证 sprint 合同，打分 + 写详细 critique |

- **Sprint 合同机制：**
  - 每个 sprint 前，Generator 和 Evaluator **协商**"done 长什么样"
  - Generator 提议构建内容和验证标准，Evaluator 审核
  - 双方迭代达成一致后才开始编码
  - 解决了 spec 太高层级 → 实现不可验证的 gap

- **评估标准（前端设计 4 维度）：**
  1. Design Quality — 是否有连贯的视觉身份（权重高）
  2. Originality — 是否有原创设计决策，而非 AI 模板（权重高）
  3. Craft — 排版、间距、对比度等技术执行（默认就好）
  4. Functionality — 可用性独立于美学（默认就好）

- **迭代进化（模型升级后的 Harness 瘦身）：**

| 版本 | 模型 | 架构 | 时长 | 成本 |
|------|------|------|------|------|
| Solo baseline | Opus 4.5 | 单智能体 | 20 min | $9 |
| V1 Harness | Opus 4.5 | Planner + Generator(sprint) + Evaluator(per-sprint) | ~6 hr | $200 |
| V2 Harness | Opus 4.6 | Planner + Generator(无 sprint) + Evaluator(单次 pass) | ~4 hr | $125 |

- **关键经验：**
  - **每个 harness 组件都编码了一个假设**（"模型不能独立做 X"），这些假设需要定期重新压测
  - 新模型发布后应精简 harness：去掉不再承重的部分，添加新能力
  - Evaluator 的价值取决于任务是否处于模型能力边界：边界内 → 开销浪费；边界外 → 真正有帮助
  - "有趣的 harness 组合空间不会随模型改进而缩小——它会移动"

- **与其他文章的关联：**

| Anthropic 概念 | 对应文章 |
|---------------|---------|
| Context Anxiety + Reset | LangChain 的 Context Rot + Ralph Loop |
| Self-Evaluation 失败 → 分离 Evaluator | HumanLayer 的 Sub-Agent 上下文防火墙 |
| Sprint 合同 | OpenAI 的执行计划（exec-plans） |
| 4 维度评分标准 | OpenAI 的 QUALITY_SCORE.md |
| Harness 瘦身原则 | Fowler 的"约束越严，自主性越强" |
| "找最简方案，按需增加复杂度" | HumanLayer 的"简单开始，按需添加" |

### 5. HumanLayer / Kyle — 实践与避坑

- **标题：** Skill Issue: Harness Engineering for Coding Agents
- **链接：** [humanlayer.dev](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)
- **核心：** 最落地的一篇——六个配置杠杆 + 实战经验

- **六个杠杆：**

| # | 杠杆 | 要点 |
|---|------|------|
| 1 | AGENTS.md | 控制在 60 行以内，禁止自动生成 |
| 2 | MCP Servers | 别连不信任的，工具太多会填满上下文 |
| 3 | Skills | 渐进式加载，警惕恶意 skill |
| 4 | Sub-Agents | 上下文防火墙，隔离任务防 context rot |
| 5 | Hooks | 生命周期脚本，成功静默/失败报错 |
| 6 | Back-Pressure | 测试/构建/类型检查 = 自我验证回路 |

- **实战经验：**

| 无效 | 有效 |
|------|------|
| 预设理想配置 | 简单开始，按需添加 |
| 装一堆 skill/MCP "以防万一" | 团队间分发验证过的配置 |
| 每次改动跑全量测试 | 优化迭代速度而非首次成功率 |
| 微调子智能体的工具权限 | 便宜模型做子任务，贵模型做编排 |

- **金句：** "The model is probably fine. It's just a skill issue."

### 6. Anthropic / Lance Martin — 三大模式与性能数据

- **标题：** Harnessing Claude's intelligence
- **链接：** [claude.com](https://claude.com/blog/harnessing-claudes-intelligence)
- **作者：** Lance Martin (Claude Platform Team) | **日期：** 2026-04-02
- **核心：** 三个构建模式——利用 Claude 已知知识、追问"我可以停止做什么"、谨慎设定边界。配合 BrowseComp / Pokemon 等基准数据论证

- **三大模式：**

| 模式 | 核心主张 |
|------|---------|
| Use what Claude knows | 通用工具（bash + editor）优于定制工具，随模型升级自然增强 |
| Ask "what can I stop doing?" | 把编排、上下文管理、持久化三个决策权从 harness 交给模型 |
| Set boundaries carefully | 缓存优化（静态前置）+ 声明式工具提供安全门控与可观测性 |

- **"停止做什么"的三个层次：**

| 层次 | 旧假设 | 新做法 | 数据支撑 |
|------|--------|--------|---------|
| 编排 | 所有工具结果回流上下文 | 给 Claude 代码执行工具，让它自己过滤/管道 | BrowseComp: Opus 4.6 过滤能力 45.3% → 61.6% |
| 上下文管理 | 手工预加载任务指令 | Skills 渐进式披露 + context editing 移除过时内容 + 子 Agent 隔离 | BrowseComp: 子 Agent 提升 2.8% |
| 持久化 | 依赖外部检索基础设施 | Compaction（模型自主总结）+ Memory folder（模型自主写文件） | BrowseComp: Opus 4.6 compaction 达 84%；BrowseComp-Plus: memory folder +6.8% |

- **缓存优化五原则：**

| 原则 | 说明 |
|------|------|
| 静态在前，动态在后 | 稳定内容（系统提示词、工具）放前面 |
| 用消息传递更新 | 追加 `<system-reminder>` 而非编辑提示词 |
| 不切换模型 | 缓存是模型特定的，切换即失效；需要便宜模型用子 Agent |
| 谨慎管理工具 | 工具在缓存前缀中，增删会使缓存失效；用 tool search 追加 |
| 更新断点 | 多轮应用中将断点移至最新消息，使用自动缓存 |

- **声明式工具的四个价值：**
  1. 安全门控 — 不可逆操作（如外部 API）需用户确认
  2. 过时检查 — 写入工具检测文件自上次读取后是否被修改
  3. UX 渲染 — 模态窗口展示问题、提供选项、阻塞等待反馈
  4. 可观测性 — 结构化参数可记录、追踪、重放

- **Pokemon 记忆进化案例：**
  - Sonnet 3.5: 14,000 步后 31 个文件（含重复），仍在第二城镇，记忆 = NPC 对话转录
  - Opus 4.6: 同样步数 10 个文件（按目录组织），3 枚道馆徽章，记忆 = 战术笔记 + 失败经验

- **"上下文焦虑"案例：**
  - Sonnet 4.5 接近上下文极限时提前收尾 → 加了 context reset 补偿
  - Opus 4.5 天然消除了此行为 → context reset 变成死重
  - 启示：harness 中的补偿机制会随模型进化变成性能瓶颈

- **与其他文章的关联：**

| 本文概念 | 对应文章 |
|---------|---------|
| 通用工具 > 定制工具 | OpenAI 原文的 bash + editor 起源 |
| Skills 渐进式披露 | LangChain 的 Progressive Disclosure、HumanLayer 的 Skills 杠杆 |
| Compaction + Memory folder | LangChain 的 Context Rot 解法、Anthropic #4 的 Context Anxiety |
| 声明式工具 vs bash | HumanLayer 的 Back-Pressure 杠杆 |
| "停止做什么" | Anthropic #4 的 Harness 瘦身原则、Fowler 的假说 |
| 缓存优化 | 本仓库新增维度——此前文章未深入讨论 API 层成本优化 |

---

## 脉络二：云原生时代的 Harness.io（交付与平台工程）

### 6. Harness.io 官方 — 全局架构

- **标题：** Understanding CI/CD Platforms: The backbone of modern DevOps
- **链接：** [harness.io](https://www.harness.io/blog/understanding-ci-cd-platforms-the-backbone-of-modern-devops)
- **核心：** 标准 CI/CD 平台介绍。8 大组件：SCM → Build → Test → Code Quality → Security Scan → Artifact → Deploy → Monitor
- **Harness 差异化：** 统一管线、Test Intelligence 智能测试、最少脚本、Policy-as-Code 治理

### 7. Medium 实战专栏 — 未找到

- **标题：** Beyond Migration: How We Engineered a Secure & Intelligent Delivery Platform with Harness CICD
- **状态：** 文章可能已下架或标题有误，待补充

### 8. Google Cloud Architecture — 前沿场景结合

- **标题：** Harness CI/CD pipeline for RAG applications
- **链接：** [docs.cloud.google.com](https://docs.cloud.google.com/architecture/partners/harness-cicd-pipeline-for-rag-app)
- **作者：** Martin Ansong (Harness) | **日期：** 2025-04-11
- **核心：** 参考架构，Harness 全家桶（CI/CD/STO/SCS/CCM/FME）+ Google Cloud Run 部署 RAG 应用
- **9 步工作流：** Trigger → Compile & Test → Package → Dev Deploy → Staging → Approval → Production Canary → Feature Validation → Cost Tracking
- **附带 Terraform 模板：** [harness-community/harness-rag-ci-cd](https://github.com/harness-community/harness-rag-ci-cd)

---

## 脉络三：效率悖论与能力进化

### 9. YDD / Miss-you — 效率悖论的系统性拆解

- **标题：** 为什么 AI 写代码更快但交付没变，以及我怎么把它扳回来的
- **链接：** [yousali.com](https://yousali.com/posts/20260303-ai-coding-efficiency-to-evolution/)
- **作者：** Miss-you | **日期：** 2026-03-03 | **字数：** 16667
- **核心：** 从约束理论、Spec/Rule/Skill 架构、验证闭环、并发策略四个维度拆解效率悖论

- **关键数据：**
  - METR RCT 实验：AI 辅助编码客观慢 19%，主观觉得快 20%（偏差 39 个百分点）
  - Faros 万人遥测：个体 PR +98%，但 DORA 四大指标无一改善
  - PR 体积 +154%，评审时间 +91% → 上游加速被下游瓶颈吃掉
  - 90% 开发者在用 AI，仅 3.1% 高度信任

- **七章结构：**

| 章 | 主题 | 核心论点 |
|---|------|---------|
| 一 | 效率悖论 | AI = NCX-10（约束理论），加速非瓶颈 = 下游堆积 |
| 二 | 框架焦虑 | OpenSpec/Superpowers/BMAD/Spec Kit 做同一件事，别纠结 |
| 三 | Spec ≠ Rule ≠ Skill | **区别在加载机制**：Rule 头部常驻、Skill 尾部按需、Spec 被 Skill 消费 |
| 四 | 安灯绳 | 验证闭环（Lint→Review→UnitTest→E2E）= 瑞士奶酪模型 |
| 五 | 并发 | 单任务慢不是问题，不能并发才是；先建闭环再开并发 |
| 六 | 洗衣机悖论 | 省出的时间洗更多衣服 vs 去读书；真正红利是能力进化 |
| 七 | 保底秘籍 | 甜点区分三档 + 自动化日常（commit、日报） |

- **与 Harness Engineering 的深度关联：**

| YDD 概念 | Harness Engineering 对应 |
|----------|------------------------|
| AI = NCX-10（约束理论） | 吞吐量改变合并理念（概念 5） |
| Spec/Rule/Skill 三层区分 | 地图而非手册 + 渐进式披露（概念 2） |
| Rule ≤ 300-500 行 | HumanLayer 的 AGENTS.md ≤ 60 行 |
| Skill 按需加载到尾部 | LangChain 的 Progressive Disclosure |
| 安灯绳 = 验证闭环 | 机械化执行 + 背压（概念 3） |
| 并发 + WIP 限制 | 吞吐量管理（概念 5） |
| 洗衣机悖论 | 人类掌舵的本质：省出时间做更高层的事 |
| 瑞士奶酪模型 | 多层防御 = linter + 结构测试 + 智能体审查 |

- **金句：**
  - "AI 就是今天的 NCX-10"
  - "Rule 是全局变量，Skill 是模块化 import"
  - "洗衣机洗衣服，你去读书"
  - "AI Coding 的本质不是让你更快，而是让你重新定义做什么的边界"

---

## 两条脉络的关系

```
Harness Engineering（AI 护栏）     Harness.io（交付管线）
        │                                │
        │  约束 AI 智能体的行为              │  约束代码交付的过程
        │  AGENTS.md + linter + 背压       │  Pipeline + Policy-as-Code + 门控
        │  目标：可靠的代码生成              │  目标：可靠的代码部署
        │                                │
        └──────────┬─────────────────────┘
                   │
            共同本质：用确定性约束
            驾驭不确定性系统
```

不是同一个东西，但共享同一个工程哲学：与其规定怎么做（prescription），不如设置门控拒绝坏结果（backpressure）。

---

> **来源文件：`工程技术：在智能体优先的世界中利用 Codex.md`**

# 工程技术：在智能体优先的世界中利用 Codex

[openai.com](https://openai.com/zh-Hans-CN/index/harness-engineering/)

在过去五个月里，我们的团队一直在进行一项实验：构建并交付一款软件产品的内部 beta 版，**其中没有一行代码是人工编写的** 。

该产品有内部日常活跃用户和外部 Alpha 测试者。它经历了交付、部署、故障和修复的整个过程。与众不同的是，每一行代码 --- 从应用逻辑、测试、CI 配置、文档、可观察性到内部工具 --- 全都是由 Codex 编写的。据估计，我们只用了手工编写代码所需的大约 1/10 的时间就完成了这项工作。

**人类掌舵。智能体执行。**

我们有意选择这一限制，以便构建必要的内容，从而将工程速度提升数个数量级。我们用了几周的时间来交付最终达到一百万行代码的项目。为此，我们需要了解，当软件工程团队的主要工作不再是编写代码，而是设计环境、明确意图和构建反馈回路，从而使 Codex 智能体能够可靠地工作时，会发生哪些变化。

这个帖子要说的是，在我们与智能体团队一起从零开始打造一款全新产品的过程中，所能学到的经验教训 --- 哪些地方出了问题，哪些问题相互叠加，以及如何最大化利用我们唯一真正稀缺的资源：人类的时间和注意力。

<br />

## 我们从一个空的 Git 代码仓库开始

<br />

首次提交到一个空的代码仓库是在 2025 年 8 月下旬。

初始架构 --- 包括代码仓库结构、CI 配置、格式化规则、包管理器设置和应用框架 --- 是在一小套现有模板的指导下，由 Codex CLI 使用 GPT‑5 生成的。就连指导智能体如何在代码仓库中工作的初始 AGENTS.md 文件本身也是由 Codex 编写的。

该系统没有预存任何人工编写的代码。从一开始，代码仓库就由智能体塑造。

五个月后，该代码仓库已经拥有约一百万行代码，从应用逻辑、基础设施、工具、文档到内部开发者工具应有尽有。在那段时间内，大约有 1,500 个 Pull Request 被打开与合并，而推动 Codex 的仅仅是一个由三名工程师组成的小团队。这相当于平均每位工程师每天处理 3.5 个 PRs 的吞吐量，而且令人惊讶的是，随着团队规模扩大到现在的七名工程师，吞吐量甚至还*增加* 了。重要的是，这并非为了输出而输出：该产品已在数百名内测用户那里投入使用，其中包括每天都在使用的内测高级用户。

在整个开发过程中，人类从未直接直接贡献过任何代码。这成为团队的核心理念：**不手动编写代码** 。

<br />

## 重新定义工程师的角色

<br />

由于缺乏人工编码的实践，**工程师工作的重点转向了系统、架构和杠杆作用** 。

早期进展比我们所预期的要慢，而这并不是因为 Codex 不具备相应的能力，而是因为环境的规范不够明确。该智能体缺乏实现高级目标所需的工具、抽象层和内部结构，因而无法取得进展。我们工程团队的主要任务成了协助智能体完成有用的工作。

在实践中，这意味着采用深度优先的工作方式：将更大的目标拆解为更小的构建模块（设计、代码、评审、测试等），提示智能体去构建这些模块，并使用它们去解锁更复杂的任务。当事情进行不顺利时，解决方案基本上再也不会是"再努力一点"。因为取得进展的唯一方式是让 Codex 来完成工作，而人类工程师则总是介入这项任务并追问："究竟还需要什么样的能力，我们又该如何让这个能力对智能体来说既清晰可读又可强制执行？"

人类几乎完全通过提示与系统交互：工程师描述任务，运行智能体，并允许其打开一个 Pull Request。为了推动 PR 的完成，我们会指示 Codex 在本地审核其自身的更改，在本地和云端请求额外的特定智能体审查，对任何人工或智能体给出的反馈做出响应，并循环往复，直到所有智能体审核人员都满意为止（这实际上是一个 [++Ralph Wiggum 循环++ ⁠（在新窗口中打开）](https://ghuntley.com/loop/)）。Codex 直接使用我们的标准开发工具（gh、本地脚本和嵌入代码仓库的技能）来收集情境，而无需人工将内容复制粘贴到 CLI 中。

人类可以审核 Pull Request（合并请求），但并非必须这样做。随着时间的推移，我们已将几乎所有的审核工作调整为用智能体对智能体的方式来处理。

<br />

## 提高应用程序的可读性

<br />

随着代码吞吐量的增加，我们的瓶颈变成了人工 QA 能力。由于人类的时间和注意力是固定的限制因素，我们一直在努力通过令应用程序的 UI、日志和应用指标等内容对 Codex 直接可读，从而为智能体增加更多功能。

例如，我们令应用程序可以根据 git worktree 启动，因此 Codex 可以为每次更改启动并驱动一个实例。我们还将 Chrome DevTools 协议接入智能体运行时，并创建了用于处理 DOM 快照、屏幕截图和导航的技能。这使 Codex 能够复现错误、验证修复，并直接推理 UI 的行为。

![](https://image.cubox.pro/cardImg/18du531wpmjgvtn0dpugw54s6z7iqw9r685e9ggup1llheb9pg.png?imageMogr2/quality/90/format/gif/ignore-error/1)

我们对可观测性工具也做了同样的处理。日志、指标和追踪记录会通过一个本地可观测性堆栈展示给 Codex，对任何给定的工作树来说，该堆栈都是临时的。Codex 在该应用程序的一个完全独立的版本上运行，一旦任务完成，该版本的所有内容，包括日志和指标，都会被删除。智能体可以使用 LogQL 查询日志，使用 PromQL 查询指标。有了这些情境，像"确保服务启动在 800ms 内完成"或"这四个关键用户旅程中的任何跨度都不得超过两秒"这样的提示就变得可行了。

![](https://image.cubox.pro/cardImg/4jjd277vd1ghhlv9pruf97h1vz1mpnn5xkywr1g692ozpxp4k0.svg?imageMogr2/quality/90/ignore-error/1)

我们经常看到单次 Codex 运行在单个任务上持续工作超过六个小时（通常是在人类睡眠时间）。

<br />

## 我们将代码仓库设为记录系统

<br />

情境管理是使智能体在大型和复杂任务中有效发挥作用的最大挑战之一。我们学到的最早经验教训之一很简单：**要给 Codex 的是一张地图，而不是一本 1,000 页的说明书。**

我们尝试了"一个大型的 [AGENTS.md⁠（在新窗口中打开）](https://agents.md/)"方法。可想而知，这是一次失败的尝试：

* **情境是一种稀缺资源。** 一个巨大的指令文件会挤掉任务、代码和相关文档 --- 因此智能体要么会错过关键约束条件，要么开始针对错误的约束条件进行优化。
* **过多的指导反而变得** ***无效*** **。** 当一切都 "重要"时，一切都不重要了。智能体最终会在本地进行模式匹配，而不是有意识地进行导航。
* **它会立即腐烂。** 一本庞杂的手册会变成陈旧规则的坟场。智能体无法判断哪些信息仍然有效，一旦人类停止维护它，此文件就会悄然成为一个颇具吸引力的麻烦源头。
* **这很难核实。** 单个 blob 不适合进行机械检查（覆盖率、新鲜度、所有权、交叉链接），因此漂移是不可避免的。

因此，我们不再将 AGENTS.md 视为百科全书，而是将其视为**内容目录** 。

代码仓库的知识库位于一个结构化了的 docs/ 目录中，此目录被当作记录系统来使用。一份简短的 AGENTS.md（大约 100 行）被注入到情境中，主要用作地图，并指向其他地方更深层次的真实信息来源。

#### 纯文本

```
    
        
     
         1

     
         
`AGENTS.md`

    
        
    
        
     
         2

     
         
`ARCHITECTURE.md`

    
        
    
        
     
         3

     
         
`docs/`

    
        
    
        
     
         4

     
         
`├── design-docs/`

    
        
    
        
     
         5

     
         
`│   ├── index.md`

    
        
    
        
     
         6

     
         
`│   ├── core-beliefs.md`

    
        
    
        
     
         7

     
         
`│   └── ...`

    
        
    
        
     
         8

     
         
`├── exec-plans/`

    
        
    
        
     
         9

     
         
`│   ├── active/`

    
        
    
        
     
         10

     
         
`│   ├── completed/`

    
        
    
        
     
         11

     
         
`│   └── tech-debt-tracker.md`

    
        
    
        
     
         12

     
         
`├── generated/`

    
        
    
        
     
         13

     
         
`│   └── db-schema.md`

    
        
    
        
     
         14

     
         
`├── product-specs/`

    
        
    
        
     
         15

     
         
`│   ├── index.md`

    
        
    
        
     
         16

     
         
`│   ├── new-user-onboarding.md`

    
        
    
        
     
         17

     
         
`│   └── ...`

    
        
    
        
     
         18

     
         
`├── references/`

    
        
    
        
     
         19

     
         
`│   ├── design-system-reference-llms.txt`

    
        
    
        
     
         20

     
         
`│   ├── nixpacks-llms.txt`

    
        
    
        
     
         21

     
         
`│   ├── uv-llms.txt`

    
        
    
        
     
         22

     
         
`│   └── ...`

    
        
    
        
     
         23

     
         
`├── DESIGN.md`

    
        
    
        
     
         24

     
         
`├── FRONTEND.md`

    
        
    
        
     
         25

     
         
`├── PLANS.md`

    
        
    
        
     
         26

     
         
`├── PRODUCT_SENSE.md`

    
        
    
        
     
         27

     
         
`├── QUALITY_SCORE.md`

    
        
    
        
     
         28

     
         
`├── RELIABILITY.md`

    
        
    
        
     
         29

     
         
`└── SECURITY.md`

    
        
```

<br />

代码仓库内知识存储布局。

设计文档已被编目和索引，其中包括验证状态和一套核心理念，定义了智能体优先的操作原则。[++架构文档++ ⁠（在新窗口中打开）](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)提供域和包分层的顶层地图。一份高质量的文档会对每个产品领域和架构层进行评分，并随着时间的推移追踪差距。

计划被视为一流的工件。临时轻量计划用于小幅变更，而复杂工作则记录在[++执行计划++ ⁠（在新窗口中打开）](https://cookbook.openai.com/articles/codex_exec_plans)中，并附带进度和决策日志，这些日志会被提交到代码仓库。活跃计划、已完成计划和已知的技术债务都已进行版本控制并集中存放，使智能体能够在不依赖外部情境的情况下运行。

这实现了**渐进式披露** ：智能体从一个小而稳定的切入点开始，并被指导下一步该去哪里查看，而不是一开始就被淹没。

我们严格执行这一点。专职的 linter 和 CI 作业会验证知识库的更新状况、是否已交叉链接且结构正确。一个定期运行的"doc-gardening"智能体会扫描那些不再反映真实代码行为的过时或废弃文档，并发起修复用的 Pull Request。

<br />

## 目标是智能体的可读性

<br />

随着代码库的发展，Codex 的设计决策框架也需要随之演变。

由于该代码仓库完全由智能体生成，因此我们首先针对 *Codex* 的*可读性* 进行了优化。就像团队会努力提升代码对新入职工程师的可导航性一样，我们的人类工程师的目标也是让智能体能够**直接从代码仓库** 推理出完整的业务领域。

从智能体的角度来看，它在运行时无法在情境中访问的任何内容都是不存在的。存储在 Google Docs、聊天记录或人们头脑中的知识都无法被系统访问。代码仓库本地的、已版本化的工件（例如，代码、Markdown、模式、可执行计划）就是它所能看到的全部。

![](https://image.cubox.pro/cardImg/28y5kf5fb91hw1iekmely4yzzx9zapfnklq1cxy8xtirmtfqsv.png?imageMogr2/quality/90/ignore-error/1)

我们了解到，随着时间的推移，我们需要将越来越多的情境推送到仓库中。那次让团队在架构模式上达成一致的 Slack 讨论？如果智能体无法发现它，那么它就会像迟了三个月入职的新员工一样，对其一无所知。

为 Codex 提供更多情境意味着要组织和展示正确的信息，好令智能体能够基于这些信息进行推理，而不是用临时指令使其不堪重负。就像你会在产品原则、工程规范和团队文化（包括表情符号偏好）方面为新队友提供引导一样，将这些信息提供给智能体会带来更一致的输出。

这一框架明确了许多取舍。我们倾向于选择那些可以完全内化于在仓库中进行推理的依赖项和抽象。对智能体来说，通常被称为"枯燥"的技术，由于其可组合性、API 稳定性和在训练集里的表现，往往更容易建立模型。在某些情况下，让智能体重新实现部分功能子集比绕过公共库中不透明的上游行为更便宜。例如，我们没有引入通用的 p-limit 风格包，而是投入使用了我们自己的带并发的 map 辅助函数：它与我们的 OpenTelemetry 仪表紧密集成，具备 100% 的测试覆盖率，并且其行为完全符合我们的运行时预期。

将系统的更多部分转化为智能体可以检查、验证并直接修改的形式，可以直接提高杠杆效应 --- 这不仅适用于 Codex，也适用于其他智能体（例如[++Aardvark++](https://openai.com/zh-Hans-CN/index/introducing-aardvark/)) 也在参与代码库的开发。

<br />

## 规范架构与品味

<br />

仅靠文档本身，是没法保持完全由智能体生成的代码库的连贯性的。**通过强制执行不变量，而非对实施过程进行微观管理，我们令智能体能够快速交付，而且不会削弱基础。** 例如，我们要求 Codex [++在边界处解析数据形状++ ⁠（在新窗口中打开）](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)，但不规定具体实现方式（模型似乎偏好 Zod，但我们没有指定特定库）。

智能体在具有[++严格边界和可预测结构++ ⁠（在新窗口中打开）](https://bits.logic.inc/p/ai-is-forcing-us-to-write-good-code)的环境中最为高效，因此我们围绕一个严格的架构模型构建了该应用。每个业务域都划分为一组固定的层，依赖方向经过严格验证，并且仅允许有限的一组边。这些约束是通过自定义的 linter（当然是由 Codex 生成的！）和结构测试机械地强制执行的。

下图展示了规则：在每个业务领域内（例如应用设置），代码只能"向前"依赖于一组固定的层（Types → Config → Repo → Service → Runtime → UI）。横切关注点（认证、连接器、遥测、功能标志）通过一个单一的显式接口进入：Providers。其他任何内容都不被允许，并将通过自动化方式强制执行。

![](https://image.cubox.pro/cardImg/1cb576y3zxcddfztvooal38es7r94orcbbyw8nsye064zqlr1n.png?imageMogr2/quality/90/ignore-error/1)

这种架构通常要等到你拥有数百名工程师时才会推迟。对于编码智能体来说，这是一个早期的先决条件：有了约束，速度才不会下降，架构才不会漂移。

在实践中，我们通过自定义的代码检查器和结构测试来强制执行这些规则，并辅以一小组"品味不变式"。例如，我们通过自定义 lint 静态地强制执行结构化日志记录、模式和类型的命名约定、文件大小限制，以及特定平台的可靠性要求。由于这些 lint 是自定义的，我们编写错误信息时会在智能体情境中注入修复指令。

在以人为本的工作流程中，这些规则可能会让人感到迂腐或束缚。有了智能体，它们就成了倍增器：一旦编码，它们就能立即应用于所有地方。

同时，我们还明确指出了哪些地方需要限制，哪些地方不需要限制。这类似于领导一个大型工程平台组织：在中央层面强制执行边界，在本地层面允许自主权。你非常重视界限、正确性和可重复性。在这些边界内，你允许团队或智能体在解决方案的表达方式上拥有很大的自由。

生成的代码不总是符合人类的风格偏好，这也没关系。只要输出是正确的、可维护的，并且对未来的智能体运行而言清晰易读，就可以算作达标。

人类的品味会不断反馈到系统中。审查评论、重构的 Pull Request 和面向用户的 Bug 会被记录为文档更新，或直接编码到工具中。当文档不够完善时，我们会将规则转化为代码

<br />

## 吞吐量改变了合并的理念

<br />

随着 Codex 的吞吐量增加，许多传统的工程规范变得不再有效。

该代码仓库在运行过程中尽量减少阻塞合并门。Pull Request 的生命周期很短。测试偶发失败通常通过后续重跑来解决，而不是无限期地阻碍进展。在一个智能体吞吐量远超人类注意力的系统中，纠错成本低，而等待成本高。

在低吞吐量环境中，这样做是不负责任的。而在这里，这通常是正确的选择。

<br />

## "智能体生成"实际上意味着什么

<br />

当我们说代码库是由 Codex 智能体生成的，我们指的是整个代码库。

智能体的产出包括：

* 产品代码与测试
* CI 配置和发布工具
* 内部开发者工具
* 文档和设计历史
* 评估框架
* 审阅评论和回复
* 管理代码仓库本身的脚本
* 生产仪表板定义文件

人类始终参与其中，但工作的抽象层次与过去不同。我们优先处理工作，将用户反馈转化为验收标准，并对结果进行验证。当智能体遇到困难时，我们将其视为一个信号：识别缺失的内容 --- 工具、指导与约束、文档 --- 并将其反馈到代码仓库中，始终由 Codex 自己编写修复。

智能体可以直接使用我们的标准开发工具。他们会拉取审查反馈、在行内回复、推送更新，并且经常压缩并合并他们自己的 Pull Request（合并请求）。

<br />

## 不断提高的自主水平

<br />

随着越来越多的开发环节被直接编码到系统中 --- 包括测试、验证、审查、反馈处理和恢复 --- 该代码仓库最近跨过了一个重要门槛，使 Codex 能够端到端地驱动一个新功能。

给定一个提示，智能体现在可以：

* 验证代码库的当前状态
* 重现已报告的漏洞
* 录制一个演示故障的视频
* 实施修复措施
* 通过运行应用程序来验证修复
* 录制第二个视频，演示解决方案
* 打开 Pull Request
* 回应智能体和人类反馈
* 检测并修复构建故障
* 仅在需要判断时才交由人工处理
* 合并更改

此行为在很大程度上取决于此代码仓库的具体结构和工具，不应在没有类似投入的情况下假定它可以泛化 --- 至少目前还不行。

<br />

## 熵与垃圾收集

<br />

**完全自主的智能体也引入了新的问题。** Codex 会复现代码仓库中已存在的模式 --- 甚至包括那些不均衡或不够理想的模式。随着时间的推移，这不可避免地导致漂移。

最初，人类是手动处理这个问题的。我们的团队过去每周五（占一周的20%）都要花时间清理"AI 残渣"。不出所料，那并不具备可扩展性。

相反，我们开始将我们称为"黄金原则"的内容直接编码到代码仓库中，并建立了一个循环清理流程。这些原则是带有主观意见的机械规则，旨在保持代码库的可读性和一致性，以便将来运行智能体。例如：(1) 我们更倾向于使用共享的实用程序包，而不是手工编写的辅助工具，以便将不变式集中管理；(2) 我们不会使用"YOLO 式"探测数据 --- 我们会验证边界，或依赖类型化的 SDK，这样智能体就不会意外地基于猜测的结构进行构建。我们会定期运行一组后台 Codex 任务，扫描偏差、更新质量等级，并发起有针对性的重构 Pull Request。其中大多数都可以在一分钟内完成审查并自动合并。

其功能类似于垃圾回收。技术债务就像一笔高息贷款：不断地以小额贷款的方式偿还债务，总比让债务不断累积，再痛苦地一次解决要好得多。人类的品味一旦被捕捉，就会持续应用于每一行代码。这也使我们能够每天发现并解决不良模式，而不是让它们在代码库中传播数天或数周。

<br />

## 我们仍在学习的内容

<br />

到目前为止，这一策略在 OpenAI 的内部发布和采纳过程中表现良好。为真实用户打造真实产品，帮助我们将投资锚定在现实中，并引导我们实现长期的可维护性。

我们尚不清楚的是，在一个完全由智能体生成的系统中，架构连贯性会如何随着时间的推移而演变。我们仍在学习人类的判断力在哪些方面能发挥最大作用，以及如何对这种判断力进行编码，使其发挥更大作用。我们也不知道，随着时间的推移，模型的功能不断增强，这一系统将如何演变。

显而易见的是：构建软件仍然需要纪律，但纪律更多地体现在支撑结构上，而不是代码上。保持代码库一致性的工具、抽象和反馈回路变得越发重要。

**我们当前最棘手的挑战集中在设计环境、反馈回路和控制系统方面** ，帮助智能体实现我们的目标：大规模构建和维护复杂、可靠的软件。

随着像 Codex 这样的智能体在软件生命周期中占据越来越大的比重，这些问题将变得更加重要。我们希望通过分享一些早期的经验教训，帮助你理清投入精力的方向，以便[++你可以直接开始构建++](https://openai.com/zh-Hans-CN/codex/)。

[Read in Cubox](https://cubox.pro/web/card/7437365631520866436)

---

> **来源文件：`Effective harnesses for long-running age....md`**

# Get the developer newsletter

[www.anthropic.com](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

As AI agents become more capable, developers are increasingly asking them to take on complex tasks requiring work that spans hours, or even days. However, getting agents to make consistent progress across multiple context windows remains an open problem.

The core challenge of long-running agents is that they must work in discrete sessions, and each new session begins with no memory of what came before. Imagine a software project staffed by engineers working in shifts, where each new engineer arrives with no memory of what happened on the previous shift. Because context windows are limited, and because most complex projects cannot be completed within a single window, agents need a way to bridge the gap between coding sessions.

We developed a two-fold solution to enable the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) to work effectively across many context windows: an **initializer agent** that sets up the environment on the first run, and a **coding agent** that is tasked with making incremental progress in every session, while leaving clear artifacts for the next session. You can find code examples in the accompanying [quickstart.](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)

## The long-running agent problem

The Claude Agent SDK is a powerful, general-purpose agent harness adept at coding, as well as other tasks that require the model to use tools to gather context, plan, and execute. It has context management capabilities such as compaction, which enables an agent to work on a task without exhausting the context window. Theoretically, given this setup, it should be possible for an agent to continue to do useful work for an arbitrarily long time.

However, compaction isn't sufficient. Out of the box, even a frontier coding model like Opus 4.5 running on the Claude Agent SDK in a loop across multiple context windows will fall short of building a production-quality web app if it's only given a high-level prompt, such as "build a clone of [claude.ai](http://claude.ai/redirect/website.v1.52cdad0c-ca7a-43d0-8297-e3f64b8a4f36)."

Claude's failures manifested in two patterns. First, the agent tended to try to do too much at once---essentially to attempt to one-shot the app. Often, this led to the model running out of context in the middle of its implementation, leaving the next session to start with a feature half-implemented and undocumented. The agent would then have to guess at what had happened, and spend substantial time trying to get the basic app working again. This happens even with compaction, which doesn't always pass perfectly clear instructions to the next agent.

A second failure mode would often occur later in a project. After some features had already been built, a later agent instance would look around, see that progress had been made, and declare the job done.

This decomposes the problem into two parts. First, we need to set up an initial environment that lays the foundation for *all* the features that a given prompt requires, which sets up the agent to work step-by-step and feature-by-feature. Second, we should prompt each agent to make incremental progress towards its goal while also leaving the environment in a clean state at the end of a session. By "clean state" we mean the kind of code that would be appropriate for merging to a main branch: there are no major bugs, the code is orderly and well-documented, and in general, a developer could easily begin work on a new feature without first having to clean up an unrelated mess.

When experimenting internally, we addressed these problems using a two-part solution:

1. Initializer agent: The very first agent session uses a specialized prompt that asks the model to set up the initial environment: an `init.sh` script, a claude-progress.txt file that keeps a log of what agents have done, and an initial git commit that shows what files were added.
2. Coding agent: Every subsequent session asks the model to make incremental progress, then leave structured updates.^1^

The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window, which is accomplished with the claude-progress.txt file alongside the git history. Inspiration for these practices came from knowing what effective software engineers do every day.

## Environment management

In the updated [Claude 4 prompting guide](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices#multi-context-window-workflows), we shared some best practices for multi-context window workflows, including a harness structure that uses "a different prompt for the very first context window." This "different prompt" requests that the initializer agent set up the environment with all the necessary context that future coding agents will need to work effectively. Here, we provide a deeper dive on some of the key components of such an environment.

### Feature list

To address the problem of the agent one-shotting an app or prematurely considering the project complete, we prompted the initializer agent to write a comprehensive file of feature requirements expanding on the user's initial prompt. In the [claude.ai](http://claude.ai/redirect/website.v1.52cdad0c-ca7a-43d0-8297-e3f64b8a4f36) clone example, this meant over 200 features, such as "a user can open a new chat, type in a query, press enter, and see an AI response." These features were all initially marked as "failing" so that later coding agents would have a clear outline of what full functionality looked like.

    {
        "category": "functional",
        "description": "New chat button creates a fresh conversation",
        "steps": [
          "Navigate to main interface",
          "Click the 'New Chat' button",
          "Verify a new conversation is created",
          "Check that chat area shows welcome state",
          "Verify conversation appears in sidebar"
        ],
        "passes": false
      }

We prompt coding agents to edit this file only by changing the status of a passes field, and we use strongly-worded instructions like "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality." After some experimentation, we landed on using JSON for this, as the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files.

### Incremental progress

Given this initial environment scaffolding, the next iteration of the coding agent was then asked to work on only one feature at a time. This incremental approach turned out to be critical to addressing the agent's tendency to do too much at once.

Once working incrementally, it's still essential that the model leaves the environment in a clean state after making a code change. In our experiments, we found that the best way to elicit this behavior was to ask the model to commit its progress to git with descriptive commit messages and to write summaries of its progress in a progress file. This allowed the model to use git to revert bad code changes and recover working states of the code base.

These approaches also increased efficiency, as they eliminated the need for an agent to have to guess at what had happened and spend its time trying to get the basic app working again.

### Testing

One final major failure mode that we observed was Claude's tendency to mark a feature as complete without proper testing. Absent explicit prompting, Claude tended to make code changes, and even do testing with unit tests or `curl` commands against a development server, but would fail recognize that the feature didn't work end-to-end.

In the case of building a web app, Claude mostly did well at verifying features end-to-end once explicitly prompted to use browser automation tools and do all testing as a human user would.

![](https://image.cubox.pro/cardImg/1fr8fmv28dgxyragd7lbt4leb3lzz5r9gtzxya4sunyfsydw9d?imageMogr2/quality/90/ignore-error/1) Screenshots taken by Claude through the Puppeteer MCP server as it tested the claude.ai clone.   

Providing Claude with these kinds of testing tools dramatically improved performance, as the agent was able to identify and fix bugs that weren't obvious from the code alone.

Some issues remain, like limitations to Claude's vision and to browser automation tools making it difficult to identify every kind of bug. For example, Claude can't see browser-native alert modals through the Puppeteer MCP, and features relying on these modals tended to be buggier as a result.

## Getting up to speed

With all of the above in place, every coding agent is prompted to run through a series of steps to get its bearings, some quite basic but still helpful:

1. *Run `pwd` to see the directory you're working in. You'll only be able to edit files in this directory.*
2. *Read the git logs and progress files to get up to speed on what was recently worked on.*
3. *Read the features list file and choose the highest-priority feature that's not yet done to work on.*

This approach saves Claude some tokens in every session since it doesn't have to figure out how to test the code. It also helps to ask the initializer agent to write an init.sh script that can run the development server, and then run through a basic end-to-end test before implementing a new feature.

In the case of the claude.ai clone, this meant that the agent always started the local development server and used the Puppeteer MCP to start a new chat, send a message, and receive a response. This ensured that Claude could quickly identify if the app had been left in a broken state, and immediately fix any existing bugs. If the agent had instead started implementing a new feature, it would likely make the problem worse.

Given all this, a typical session starts off with the following assistant messages:

    [Assistant] I'll start by getting my bearings and understanding the current state of the project.
    [Tool Use] <bash - pwd>
    [Tool Use] <read - claude-progress.txt>
    [Tool Use] <read - feature_list.json>
    [Assistant] Let me check the git log to see recent work.
    [Tool Use] <bash - git log --oneline -20>
    [Assistant] Now let me check if there's an init.sh script to restart the servers.
    <Starts the development server>
    [Assistant] Excellent! Now let me navigate to the application and verify that some fundamental features are still working.
    <Tests basic functionality>
    [Assistant] Based on my verification testing, I can see that the fundamental functionality is working well. The core chat features, theme switching, conversation loading, and error handling are all functioning correctly. Now let me review the tests.json file more comprehensively to understand what needs to be implemented next.
    <Starts work on a new feature>

Agent failure modes and solutions

|                                 **Problem**                                  |                                                   **Initializer Agent Behavior**                                                   |                                                                                               **Coding Agent Behavior**                                                                                               |
|------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Claude declares victory on the entire project too early.                     | Set up a feature list file: based on the input spec, set up a structured JSON file with a list of end-to-end feature descriptions. | Read the feature list file at the beginning of a session. Choose a single feature to start working on.                                                                                                                |
| Claude leaves the environment in a state with bugs or undocumented progress. | An initial git repo and progress notes file is written.                                                                            | Start the session by reading the progress notes file and git commit logs, and run a basic test on the development server to catch any undocumented bugs. End the session by writing a git commit and progress update. |
| Claude marks features as done prematurely.                                   | Set up a feature list file.                                                                                                        | Self-verify all features. Only mark features as "passing" after careful testing.                                                                                                                                      |
| Claude has to spend time figuring out how to run the app.                    | Write an `init.sh` script that can run the development server.                                                                     | Start the session by reading `init.sh`.                                                                                                                                                                               |

Summarizing four common failure modes and solutions in long-running AI agents.

## Future work

This research demonstrates one possible set of solutions in a long-running agent harness to enable the model to make incremental progress across many context windows. However, there remain open questions.

Most notably, it's still unclear whether a single, general-purpose coding agent performs best across contexts, or if better performance can be achieved through a multi-agent architecture. It seems reasonable that specialized agents like a testing agent, a quality assurance agent, or a code cleanup agent, could do an even better job at sub-tasks across the software development lifecycle.

Additionally, this demo is optimized for full-stack web app development. A future direction is to generalize these findings to other fields. It's likely that some or all of these lessons can be applied to the types of long-running agentic tasks required in, for example, scientific research or financial modeling.

### Acknowledgements

Written by Justin Young. Special thanks to David Hershey, Prithvi Rajasakeran, Jeremy Hadfield, Naia Bouscal, Michael Tingley, Jesse Mu, Jake Eaton, Marius Buleandara, Maggie Vo, Pedram Navid, Nadine Yasser, and Alex Notov for their contributions.

This work reflects the collective efforts of several teams across Anthropic who made it possible for Claude to safely do long-horizon autonomous software engineering, especially the code RL \& Claude Code teams. Interested candidates who would like to contribute are welcome to apply at [anthropic.com/careers](http://anthropic.com/careers).

### Footnotes

1. We refer to these as separate agents in this context only because they have different initial user prompts. The system prompt, set of tools, and overall agent harness was otherwise identical.

[Read in Cubox](https://cubox.pro/web/card/7437365883229440115)

---

> **来源文件：`Harness design for long-running applicat....md`**

# Get the developer newsletter

[www.anthropic.com](https://www.anthropic.com/engineering/harness-design-long-running-apps)

*Written by Prithvi Rajasekaran, a member of our[Labs](https://www.anthropic.com/news/introducing-anthropic-labs) team.*

Over the past several months I've been working on two interconnected problems: getting Claude to produce high-quality frontend designs, and getting it to build complete applications without human intervention. This work originated with earlier efforts on our [frontend design skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md) and [long-running coding agent harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), where my colleagues and I were able to improve Claude's performance well above baseline through prompt engineering and harness design---but both eventually hit ceilings.

To break through, I sought out novel AI engineering approaches that held across two quite different domains, one defined by subjective taste, the other by verifiable correctness and usability. Taking inspiration from [Generative Adversarial Networks](https://en.wikipedia.org/wiki/Generative_adversarial_network) (GANs), I designed a multi-agent structure with a **generator** and **evaluator** agent. Building an evaluator that graded outputs reliably---and with taste---meant first developing a set of criteria that could turn subjective judgments like "is this design good?" into concrete, gradable terms.

I then applied these techniques to long-running autonomous coding, carrying over two lessons from our earlier harness work: decomposing the build into tractable chunks, and using structured artifacts to hand off context between sessions. The final result was a three-agent architecture---planner, generator, and evaluator---that produced rich full-stack applications over multi-hour autonomous coding sessions.

## Why naive implementations fall short

We've previously shown that harness design has a substantial impact on the effectiveness of long running agentic coding. In an earlier[experiment](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), we used an initializer agent to decompose a product spec into a task list, and a coding agent that implemented the tasks one feature at a time before handing off artifacts to carry context across sessions. The broader developer community has converged on similar insights, with approaches like the "[Ralph Wiggum](https://ghuntley.com/ralph/)" method using hooks or scripts to keep agents in continuous iteration cycles.

But some problems remained persistent. For more complex tasks, the agent still tends to go off the rails over time. While decomposing this issue, we observed two common failure modes with agents executing these sorts of tasks.

First is that models tend to lose coherence on lengthy tasks as the context window fills (see our post on [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)). Some models also exhibit "context anxiety," in which they begin wrapping up work prematurely as they approach what they believe is their context limit. Context resets---clearing the context window entirely and starting a fresh agent, combined with a structured handoff that carries the previous agent's state and the next steps---addresses both these issues.

This differs from compaction, where earlier parts of the conversation are summarized in place so the same agent can keep going on a shortened history. While compaction preserves continuity, it doesn't give the agent a clean slate, which means context anxiety can still persist. A reset provides a clean slate, at the cost of the handoff artifact having enough state for the next agent to pick up the work cleanly. In our earlier testing, we found Claude Sonnet 4.5 exhibited context anxiety strongly enough that compaction alone wasn't sufficient to enable strong long task performance, so context resets became essential to the harness design. This solves the core issue, but adds orchestration complexity, token overhead, and latency to each harness run.

A second issue, which we haven't previously addressed, is self-evaluation. When asked to evaluate work they've produced, agents tend to respond by confidently praising the work---even when, to a human observer, the quality is obviously mediocre. This problem is particularly pronounced for subjective tasks like design, where there is no binary check equivalent to a verifiable software test. Whether a layout feels polished or generic is a judgment call, and agents reliably skew positive when grading their own work.

However, even on tasks that do have verifiable outcomes, agents still sometimes exhibit poor judgment that impedes their performance while completing the task. Separating the agent doing the work from the agent judging it proves to be a strong lever to address this issue. The separation doesn't immediately eliminate that leniency on its own; the evaluator is still an LLM that is inclined to be generous towards LLM-generated outputs. But tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work, and once that external feedback exists, the generator has something concrete to iterate against.

## Frontend design: making subjective quality gradable

I started by experimenting on frontend design, where the self-evaluation issue was most visible. Absent any intervention, Claude normally gravitates toward safe, predictable layouts that are technically functional but visually unremarkable.

Two insights shaped the harness I built for frontend design. First, while aesthetics can't be fully reduced to a score---and individual tastes will always vary---they can be improved with grading criteria that encode design principles and preferences. "Is this design beautiful?" is hard to answer consistently, but "does this follow our principles for good design?" gives Claude something concrete to grade against. Second, by separating frontend generation from frontend grading, we can create a feedback loop that drives the generator toward stronger outputs.

With this in mind, I wrote four grading criteria that I gave to both the generator and evaluator agents in their prompts:

* **Design quality:** Does the design feel like a coherent whole rather than a collection of parts? Strong work here means the colors, typography, layout, imagery, and other details combine to create a distinct mood and identity.
* **Originality:** Is there evidence of custom decisions, or is this template layouts, library defaults, and AI-generated patterns? A human designer should recognize deliberate creative choices. Unmodified stock components---or telltale signs of AI generation like purple gradients over white cards---fail here.
* **Craft:** Technical execution: typography hierarchy, spacing consistency, color harmony, contrast ratios. This is a competence check rather than a creativity check. Most reasonable implementations do fine here by default; failing means broken fundamentals.
* **Functionality:** Usability independent of aesthetics. Can users understand what the interface does, find primary actions, and complete tasks without guessing?

I emphasized design quality and originality over craft and functionality. Claude already scored well on craft and functionality by default, as the required technical competence tended to come naturally to the model. But on design and originality, Claude often produced outputs that were bland at best. The criteria explicitly penalized highly generic "AI slop" patterns, and by weighting design and originality more heavily it pushed the model toward more aesthetic risk-taking.

I calibrated the evaluator using few-shot examples with detailed score breakdowns. This ensured the evaluator's judgment aligned with my preferences, and reduced score drift across iterations.

I built the loop on the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview), which kept the orchestration straightforward. A generator agent first created an HTML/CSS/JS frontend based on a user prompt. I gave the evaluator the Playwright MCP, which let it interact with the live page directly before scoring each criterion and writing a detailed critique. In practice, the evaluator would navigate the page on its own, screenshotting and carefully studying the implementation before producing its assessment. That feedback flowed back to the generator as input for the next iteration. I ran 5 to 15 iterations per generation, with each iteration typically pushing the generator in a more distinctive direction as it responded to the evaluator's critique. Because the evaluator was actively navigating the page rather than scoring a static screenshot, each cycle took real wall-clock time. Full runs stretched up to four hours. I also instructed the generator to make a strategic decision after each evaluation: refine the current direction if scores were trending well, or pivot to an entirely different aesthetic if the approach wasn't working.

Across runs, the evaluator's assessments improved over iterations before plateauing, with headroom still remaining. Some generations refined incrementally. Others took sharp aesthetic turns between iterations.

The wording of the criteria steered the generator in ways I didn't fully anticipate. Including phrases like "the best designs are museum quality" pushed designs toward a particular visual convergence, suggesting that the prompting associated with the criteria directly shaped the character of the output.

While scores generally improved over iterations, the pattern was not always cleanly linear. Later implementations tended to be better as a whole, but I regularly saw cases where I preferred a middle iteration over the last one. Implementation complexity also tended to increase across rounds, with the generator reaching for more ambitious solutions in response to the evaluator's feedback. Even on the first iteration, outputs were noticeably better than a baseline with no prompting at all, suggesting the criteria and associated language themselves steered the model away from generic defaults before any evaluator feedback led to further refinement.

In one notable example, I prompted the model to create a website for a Dutch art museum. By the ninth iteration, it had produced a clean, dark-themed landing page for a fictional museum. The page was visually polished but largely in line with my expectations. Then, on the tenth cycle, it scrapped the approach entirely and reimagined the site as a spatial experience: a 3D room with a checkered floor rendered in CSS perspective, artwork hung on the walls in free-form positions, and doorway-based navigation between gallery rooms instead of scroll or click. It was the kind of creative leap that I hadn't seen before from a single-pass generation.

## Scaling to full-stack coding

With these findings in hand, I applied this GAN-inspired pattern to full-stack development. The generator-evaluator loop maps naturally onto the software development lifecycle, where code review and QA serve the same structural role as the design evaluator.

### The architecture

In our earlier [long-running harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), we had solved for coherent multi-session coding with an initializer agent, a coding agent that worked one feature at a time, and context resets between sessions. Context resets were a key unlock: the harness used Sonnet 4.5, which exhibited the "context anxiety" tendency mentioned earlier. Creating a harness that worked well across context resets was key to keeping the model on task. Opus 4.5 largely removed that behavior on its own, so I was able to drop context resets from this harness entirely. The agents were run as one continuous session across the whole build, with the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)'s automatic compaction handling context growth along the way.

For this work I built on the foundation from the original harness with a three-agent system, with each agent addressing a specific gap I'd observed in prior runs. The system contained the following agent personas:

**Planner:** Our previous long-running harness required the user to provide a detailed spec upfront. I wanted to automate that step, so I created a planner agent that took a simple 1-4 sentence prompt and expanded it into a full product spec. I prompted it to be ambitious about scope and to stay focused on product context and high level technical design rather than detailed technical implementation. This emphasis was due to the concern that if the planner tried to specify granular technical details upfront and got something wrong, the errors in the spec would cascade into the downstream implementation. It seemed smarter to constrain the agents on the deliverables to be produced and let them figure out the path as they worked. I also asked the planner to find opportunities to weave AI features into the product specs. (See example in the Appendix at the bottom.)

**Generator:** The one-feature-at-a-time approach from the earlier harness worked well for scope management. I applied a similar model here, instructing the generator to work in sprints, picking up one feature at a time from the spec. Each sprint implemented the app with a React, Vite, FastAPI, and SQLite (later PostgreSQL) stack, and the generator was instructed to self-evaluate its work at the end of each sprint before handing off to QA. It also had git for version control.

**Evaluator:** Applications from earlier harnesses often looked impressive but still had real bugs when you actually tried to use them. To catch these, the evaluator used the Playwright MCP to click through the running application the way a user would, testing UI features, API endpoints, and database states. It then graded each sprint against both the bugs it had found and a set of criteria modeled on the frontend experiment, adapted here to cover product depth, functionality, visual design, and code quality. Each criterion had a hard threshold, and if any one fell below it, the sprint failed and the generator got detailed feedback on what went wrong.

Before each sprint, the generator and evaluator negotiated a sprint contract: agreeing on what "done" looked like for that chunk of work before any code was written. This existed because the product spec was intentionally high-level, and I wanted a step to bridge the gap between user stories and testable implementation. The generator proposed what it would build and how success would be verified, and the evaluator reviewed that proposal to make sure the generator was building the right thing. The two iterated until they agreed.

Communication was handled via files: one agent would write a file, another agent would read it and respond either within that file or with a new file that the previous agent would read in turn. The generator then built against the agreed-upon contract before handing the work off to QA. This kept the work faithful to the spec without over-specifying implementation too early.

### Running the harness

For the first version of this harness, I used Claude Opus 4.5, running user prompts against both the full harness and a single-agent system for comparison. I used Opus 4.5 since this was our best coding model when I began these experiments.

I wrote the following prompt to generate a retro video game maker:
> *Create a 2D retro game maker with features including a level editor, sprite editor, entity behaviors, and a playable test mode.*

The table below shows the harness type, length it ran for, and the total cost.

| **Harness**  | **Duration** | **Cost** |
|--------------|--------------|----------|
| Solo         | 20 min       | $9       |
| Full harness | 6 hr         | $200     |

The harness was over 20x more expensive, but the difference in output quality was immediately apparent.

I was expecting an interface where I could construct a level and its component parts (sprites, entities, tile layout) then hit play to actually play the level. I started by opening the solo run's output, and the initial application seemed in line with those expectations.

As I clicked through, however, issues started to emerge. The layout wasted space, with fixed-height panels leaving most of the viewport empty. The workflow was rigid. Trying to populate a level prompted me to create sprites and entities first, but nothing in the UI guided me toward that sequence. More to the point, the actual game was broken. My entities appeared on screen but nothing responded to input. Digging into the code revealed that the wiring between entity definitions and the game runtime was broken, with no surface indication of where.

![](https://image.cubox.pro/cardImg/m4r4hyb2807933itm4oatolj9qjbljxrkjq9s7fc69j33x22v?imageMogr2/quality/90/format/gif/ignore-error/1) Initial screen when opening the app created by the solo harness.  

After evaluating the solo run, I turned my attention to the harness run. This run started from the same one-sentence prompt, but the planner step expanded that prompt into a 16-feature spec spread across ten sprints. It went well beyond what the solo run attempted. In addition to the core editors and play mode, the spec called for a sprite animation system, behavior templates, sound effects and music, an AI-assisted sprite generator and level designer, and game export with shareable links. I gave the planner access to our [frontend design skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md), which it read and used to create a visual design language for the app as part of the spec. For each sprint, the generator and evaluator negotiated a contract defining the specific implementation details for the sprint, and the testable behaviors that would be tested to verify completion.

The app immediately showed more polish and smoothness than the solo run. The canvas used the full viewport, the panels were sized sensibly, and the interface had a consistent visual identity that tracked the design direction from the spec. Some of the clunkiness I'd seen in the solo run did remain---the workflow still didn't make it clear that you should build sprites and entities before trying to populate a level, and I had to figure that out by poking around. This read as a gap in the base model's product intuition rather than something the harness was designed to address, though it did suggest a place where targeted iteration inside the harness could help to further improve output quality.

Working through the editors, the new run's advantages over solo became more apparent. The sprite editor was richer and more fully featured, with cleaner tool palettes, a better color picker, and more usable zoom controls.

Because I'd asked the planner to weave AI features into its specs, the app also came with a built-in Claude integration that let me generate different parts of the game through prompting. This significantly sped up the workflow.

![](https://image.cubox.pro/cardImg/3eobe0raxrmk33a7d64pj2cbu1dzz7axtdwxxuytbo6ofgj1ix?imageMogr2/quality/90/format/gif/ignore-error/1) Initial screen: Creating a new game, in the app built with the full harness

The biggest difference was in play mode. I was actually able to move my entity and play the game. The physics had some rough edges---my character jumped onto a platform but ended up overlapping with it, which felt intuitively wrong---but the core thing worked, which the solo run did not manage. After moving around a bit, I did hit some limitations with the AI's game level construction. There was a large wall that I wasn't able to jump past, so I was stuck. This suggested there were some common sense improvements and edge cases that the harness could handle to further refine the app.

Reading through the logs, it was clear that the evaluator kept the implementation in line with the spec. Each sprint, it walked through the sprint contract's test criteria and exercised the running application through Playwright, filing bugs against anything that diverged from expected behavior. The contracts were granular---Sprint 3 alone had 27 criteria covering the level editor---and the evaluator's findings were specific enough to act on without extra investigation. The table below shows several examples of issues our evaluator identified:

|                               **Contract criterion**                                |                                                                                                                    **Evaluator finding**                                                                                                                     |
|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Rectangle fill tool allows click-drag to fill a rectangular area with selected tile | **FAIL** --- Tool only places tiles at drag start/end points instead of filling the region. `fillRectangle` function exists but isn't triggered properly on mouseUp.                                                                                         |
| User can select and delete placed entity spawn points                               | **FAIL** --- Delete key handler at `LevelEditor.tsx:892` requires both `selection` and `selectedEntityId `to be set, but clicking an entity only sets `selectedEntityId`. Condition should be `selection || (selectedEntityId && activeLayer === 'entity')`. |
| User can reorder animation frames via API                                           | **FAIL** --- `PUT /frames/reorder` route defined after `/{frame_id}` routes. FastAPI matches 'r`eorder`' as a frame_id integer and returns 422: "unable to parse string as an integer."                                                                      |

Getting the evaluator to perform at this level took work. Out of the box, Claude is a poor QA agent. In early runs, I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway. It also tended to test superficially, rather than probing edge cases, so more subtle bugs often slipped through. The tuning loop was to read the evaluator's logs, find examples where its judgment diverged from mine, and update the QAs prompt to solve for those issues. It took several rounds of this development loop before the evaluator was grading in a way that I found reasonable. Even then, the harness output showed the limits of the model's QAing capabilities: small layout issues, interactions that felt unintuitive in places, and undiscovered bugs in more deeply nested features that the evaluator hadn't exercised thoroughly. There was clearly more verification headroom to capture with further tuning. But compared to the solo run, where the central feature of the application simply didn't work, the lift was obvious.

### Iterating on the harness

The first set of harness results was encouraging, but it was also bulky, slow, and expensive. The logical next step was to find ways to simplify the harness without degrading its performance. This was partly common sense and partly a function of a more general principle: every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing, both because they may be incorrect, and because they can quickly go stale as models improve. Our blog post [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) frames the underlying idea as "find the simplest solution possible, and only increase complexity when needed," and it's a pattern that shows up consistently for anyone maintaining an agent harness.

In my first attempt to simplify, I cut the harness back radically and tried a few creative new ideas, but I wasn't able to replicate the performance of the original. It also became difficult to tell which pieces of the harness design were actually load-bearing, and in what ways. Based on that experience, I moved to a more methodical approach, removing one component at a time and reviewing what impact it had on the final result.

As I was going through these iteration cycles, we also released Opus 4.6, which provided further motivation to reduce harness complexity. There was good reason to expect 4.6 would need less scaffolding than 4.5 did. From our [launch blog:](https://www.anthropic.com/news/claude-opus-4-6) "\[Opus 4.6\] plans more carefully, sustains agentic tasks for longer, can operate more reliably in larger codebases, and has better code review and debugging skills to catch its own mistakes." It also improved substantially on long-context retrieval. These were all capabilities the harness had been built to supplement.

### Removing the sprint construct

I started by removing the sprint construct entirely. The sprint structure had helped to decompose work into chunks for the model to work coherently. Given the improvements in Opus 4.6, there was good reason to believe that the model could natively handle the job without this sort of decomposition.

I kept both the planner and evaluator, as each continued to add obvious value. Without the planner, the generator under-scoped: given the raw prompt, it would start building without first speccing its work, and end up creating a less feature-rich application than the planner did.

With the sprint construct removed, I moved the evaluator to a single pass at the end of the run rather than grading per sprint. Since the model was much more capable, it changed how load-bearing the evaluator was for certain runs, with its usefulness depending on where the task sat relative to what the model could do reliably on its own. On 4.5, that boundary was close: our builds were at the edge of what the generator could do well solo, and the evaluator caught meaningful issues across the build. On 4.6, the model's raw capability increased, so the boundary moved outward. Tasks that used to need the evaluator's check to be implemented coherently were now often within what the generator handled well on its own, and for tasks within that boundary, the evaluator became unnecessary overhead. But for the parts of the build that were still at the edge of the generator's capabilities, the evaluator continued to give real lift.

The practical implication is that the evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the current model does reliably solo.

Alongside the structural simplification, I also added prompting to improve how the harness built AI features into each app, specifically getting the generator to build a proper agent that could drive the app's own functionality through tools. That took real iteration, since the relevant knowledge is recent enough that Claude's training data covers it thinly. But with enough tuning, the generator was building agents correctly.

### Results from the updated harness

To put the updated harness to the test, I used the following prompt to generate a Digital Audio Workstation (DAW), a music production program for composing, recording, and mixing songs:
> *Build a fully featured DAW in the browser using the Web Audio API.*

The run was still lengthy and expensive, at about 4 hours and $124 in token costs.

Most of the time went to the builder, which ran coherently for over two hours without the sprint decomposition that Opus 4.5 had needed.

|----------------------|-----------------|-------------|
| **Agent \& Phase**   | **Duration**    | **Cost**    |
| Planner              | 4.7 min         | $0.46       |
| Build (Round 1)      | 2 hr 7 min      | $71.08      |
| QA (Round 1)         | 8.8 min         | $3.24       |
| Build (Round 2)      | 1 hr 2 min      | $36.89      |
| QA (Round 2)         | 6.8 min         | $3.09       |
| Build (Round 3)      | 10.9 min        | $5.88       |
| QA (Round 3)         | 9.6 min         | $4.06       |
| **Total V2 Harness** | **3 hr 50 min** | **$124.70** |

As with the previous harness, the planner expanded the one-line prompt into a full spec. From the logs, I could see the generator model did a good job planning the app and the agent design, wiring the agent up, and testing it before handing off to QA.

That being said, the QA agent still caught real gaps. In its first-round feedback, it noted:
> This is a strong app with excellent design fidelity, solid AI agent, and good backend. The main failure point is Feature Completeness --- while the app looks impressive and the AI integration works well, several core DAW features are display-only without interactive depth: clips can't be dragged/moved on the timeline, there are no instrument UI panels (synth knobs, drum pads), and no visual effect editors (EQ curves, compressor meters). These aren't edge cases --- they're the core interactions that make a DAW usable, and the spec explicitly calls for them.

In its second round feedback, it again caught several functionality gaps:
> Remaining gaps:  
> - Audio recording is still stub-only (button toggles but no mic capture)  
> - Clip resize by edge drag and clip split not implemented  
> - Effect visualizations are numeric sliders, not graphical (no EQ curve)

The generator was still liable to miss details or stub features when left to its own devices, and the QA still added value in catching those last mile issues for the generator to fix.

Based on the prompt, I was expecting a program where I could create melodies, harmonies, and drum patterns, arrange them into a song, and get help from an integrated agent along the way. The video below shows the result.

The app is far from a professional music production program, and the agent's song composition skills could clearly use a lot of work. Additionally, Claude can't actually hear, which made the QA feedback loop less effective with respect to musical taste.

But the final app had all the core pieces of a functional music production program: a working arrangement view, mixer, and transport running in the browser. Beyond that, I was able to put together a short song snippet entirely through prompting: the agent set the tempo and key, laid down a melody, built a drum track, adjusted mixer levels, and added reverb. The core primitives for song composition were present, and the agent could drive them autonomously, using tools to create a simple production from end to end. You might say it's not pitch-perfect yet---but it's getting there.

## What comes next

As models continue to improve, we can roughly expect them to be capable of working for longer, and on more complex tasks. In some cases, that will mean the scaffold surrounding the model matters less over time, and developers can wait for the next model and see certain problems solve themselves. On the other hand, the better the models get, the more space there is to develop harnesses that can achieve complex tasks beyond what the model can do at baseline.

With this in mind, there are a few lessons from this work worth carrying forward. It is always good practice to experiment with the model you're building against, read its traces on realistic problems, and tune its performance to achieve your desired outcomes. When working on more complex tasks, there is sometimes headroom from decomposing the task and applying specialized agents to each aspect of the problem. And when a new model lands, it is generally good practice to re-examine a harness, stripping away pieces that are no longer load-bearing to performance and adding new pieces to achieve greater capability that may not have been possible before.

From this work, my conviction is that the space of interesting harness combinations doesn't shrink as models improve. Instead, it moves, and the interesting work for AI engineers is to keep finding the next novel combination.

## Acknowledgements

Special thanks to Mike Krieger, Michael Agaby, Justin Young, Jeremy Hadfield, David Hershey, Julius Tarng, Xiaoyi Zhang, Barry Zhang, Orowa Sidker, Michael Tingley, Ibrahim Madha, Martina Long, and Canyon Robbins for their contributions to this work.

Thanks also to Jake Eaton, Alyssa Leonard, and Stef Sequeira for their help shaping the post.

## Appendix

Example plan generated by planner agent.

    RetroForge - 2D Retro Game Maker

    Overview
    RetroForge is a web-based creative studio for designing and building 2D retro-style video games. It combines the nostalgic charm of classic 8-bit and 16-bit game aesthetics with modern, intuitive editing tools---enabling anyone from hobbyist creators to indie developers to bring their game ideas to life without writing traditional code.

    The platform provides four integrated creative modules: a tile-based Level Editor for designing game worlds, a pixel-art Sprite Editor for crafting visual assets, a visual Entity Behavior system for defining game logic, and an instant Playable Test Mode for real-time gameplay testing. By weaving AI assistance throughout (powered by Claude), RetroForge accelerates the creative process---helping users generate sprites, design levels, and configure behaviors through natural language interaction.

    RetroForge targets creators who love retro gaming aesthetics but want modern conveniences. Whether recreating the platformers, RPGs, or action games of their childhood, or inventing entirely new experiences within retro constraints, users can prototype rapidly, iterate visually, and share their creations with others.

    Features
    1. Project Dashboard & Management
    The Project Dashboard is the home base for all creative work in RetroForge. Users need a clear, organized way to manage their game projects---creating new ones, returning to works-in-progress, and understanding what each project contains at a glance.

    User Stories: As a user, I want to:

    - Create a new game project with a name and description, so that I can begin designing my game
    - See all my existing projects displayed as visual cards showing the project name, last modified date, and a thumbnail preview, so that I can quickly find and continue my work
    - Open any project to enter the full game editor workspace, so that I can work on my game
    - Delete projects I no longer need, with a confirmation dialog to prevent accidents, so that I can keep my workspace organized
    - Duplicate an existing project as a starting point for a new game, so that I can reuse my previous work

    Project Data Model: Each project contains:

    Project metadata (name, description, created/modified timestamps)
    Canvas settings (resolution: e.g., 256x224, 320x240, or 160x144)
    Tile size configuration (8x8, 16x16, or 32x32 pixels)
    Color palette selection 
    All associated sprites, tilesets, levels, and entity definitions

    ...

[Read in Cubox](https://cubox.pro/web/card/7437365058440529007)

---

> **来源文件：`book2/full.md`**

<table><tr><td>Claude Code $ RUNTIME DISCIPLINE</td><td>Codex $ POLICY AND LOCAL RULES</td></tr><tr><td></td><td></td></tr></table>

# Claude Code 和 Codex的 Harness 设计哲学

殊途同归，还是各表一枝

做系统的人，  
不过是把必然会来的摧残，  
提前写进控制流，  
省得它反过来支配你。 O

CONTROL / LOOP / POLICY / STATE / LOCAL GOVERNANCE / VERIFICATION

# 从会用 Agent，到做出 Agent PoC

https://agentway.dev

# 目录

# 导读

阅读地图 2

先看第一本书：Claude Code 给出的九个结构判断 . . . . 2  
再看这本比较书：同一个问题，Claude Code 和 Codex 从哪里起笔 3  
合起来以后，真正清楚的是什么 . . 4  
推荐阅读顺序 5  
一句话总结 5

# 序言两套 Harness

# 6

# 第 1 章为什么要把 Claude Code 和 Codex 放在一起看 8

1.1 因为它们比较的是对模型的不信任 . . . 8  
1.2 Claude Code 代表一种运行时优先的驯化路线 . . . . 8  
1.3 Codex 代表一种显式控制面优先的驯化路线 . . . 9  
1.4 两者都在回答同一个问题，但起笔位置不同 . . . 10  
1.5 为什么这种差异值得团队认真看 10  
1.6 本文的基本判断 11

# 第 2 章两种控制面 12

2.1 控制面这件事，首先不是文风问题 . . . 12  
2.2 Claude Code 的控制面是动态装配线 13  
2.3 Codex 的控制面是带编号的公文系统 13  
2.4 AGENTS.md 与 CLAUDE.md：同样是本地规则，气质却不同 14  
2.5 两种控制面的代价 15  
2.6 这章的比较结论 15

# 第 3 章心跳放在哪 16

3.1 代理系统的核心是连续性 16  
3.2 Claude Code：把连续性压进主循环 . . 17  
3.3 Codex：把连续性拆成线程、rollout 与状态桥 . . . 17  
3.4 差别在于状态安放的位置 18  
3.5 对恢复与可审计性的影响 . . . . 20  
3.6 对产品和团队接口的影响 . . . 20  
3.7 本章结论 . . 21

# 第 4 章工具、沙箱与策略语言 22

4.1 真正危险的是开始执行 22

4.2 Claude Code：重点在运行时编排和危险动作约束 23

4.3 Codex：重点在工具 schema、审批参数和策略引擎 23

4.4 运行时审批对照策略语言 24

4.5 沙箱与审批，不只是安全问题，也是产品定义问题 25

4.6 MCP、扩展工具与边界外移 25

4.7 本章结论 . . . 26

# 5 章技能、Hook 与本地规则 27

5.1 真正能落地的 agent，一定会地方化 . . . 27

5.2 Claude Code：把局部制度做成现场记忆 28

5.3 Codex：把局部制度做成结构化注入和事件系统 28

5.4 Claude Code 偏经验收编，Codex 偏制度挂载 . . 29

5.5 对组织可复制性的影响 29

5.6 本章结论 . 30

第 6 章委派、验证与持久状态 31

6.1 多代理的真正问题是责任 . . 31

6.2 Claude Code：多代理服务于运行时职责分区 31

6.3 Codex：多代理服务于显式工具化协作 . 32

6.4 持久状态让验证不只是礼仪 . . 32

6.5 对恢复与收尾的不同态度 33

6.6 本章结论 . . 33

# 第 7 章殊途同归 34

7.1 先说“同归”的部分 34

7.2 再说“各表一枝”的部分 34

7.3 如果非要给它们起一个更难听但更准确的名字 35

7.4 对后来者的启发 35

7.5 最终判断 36

# 第 8 章如果你要自己做 37

8.1 比较的最终用途是少走弯路 . . . . 37  
8.2 三种常见团队，三种起手方向 . . . 37  
8.3 什么该学 Claude Code，什么该学 Codex . . . 39  
8.4 一个危险误区：把“显式”与“灵活”误认为天然对立 40  
8.5 给后来者的一组顺序建议 . . . 40  
8.6 本章结论 . . . . 41

# 附录 A 源码地图

# 42

A.1 Claude Code 侧主要依据 . 42

A.2 Codex 侧主要依据 43

A.3 各章对照 . . 44附录 B 检查清单 46

B.1 控制面清单 . . . . 46  
B.2 连续性清单 . . 46  
B.3 工具与审批清单 47  
B.4 本地治理清单 47  
B.5 多代理与验证清单 47  
B.6 你更像哪一类系统 48  
B.7 最后六问 . . 48

# 导读

“人活在世上，就是为了忍受摧残。”  
做 harness 也是。区别只在于，有人把摧残写进控制流，有人把摧残写进制度层。

这不是一份功能表，也不是一篇产品评测。它要比较的是两套系统如何承认模型不可靠，并把这种不可靠驯化成可持续工作的工程秩序，而不只是看“谁支持更多工具”。

本书有三个判断前提：

‧ Claude Code 和 Codex 比较的重点不在模型，而在 harness‧ harness 是一种权力分配方式，而不是若干功能的拼盘‧ 工程系统的差别，常常不在名词，而在秩序住在哪一层

如果你第一次进入这套比较，建议这样读：

1. 先读序言，确认比较对象不是模型，而是 harness 的秩序设计。  
2. 再读第 1 到第 6 章，顺着控制面、连续性、工具治理、本地制度和多代理验证五条比较轴往下走。  
3. 然后读第 7 章殊途同归，还是各表一枝，把前面的比较收束成总判断。  
4. 最后读第 8 章如果你要自己做：该向谁学，先学什么，把比较转成可执行的路径选择。

如果只想先看总判断，可以直接跳到第 7 章。

# 阅读地图：如何理解第一本书与这本比较书

如果把这两个目录都看成在写 AI coding agent，那么最容易误读的地方，是把它们当成两份重复文档。它们并不重复，分工其实很清楚。

第一本书更像单体解剖。它以 Claude Code 为样本，讨论一套可控 agent 为什么必须具备控制面、query loop、工具权限、上下文治理、恢复路径、多代理验证和团队制度这些器官。它要回答的问题是：一套能在真实工程环境里持续工作的 harness，内部骨架应该是什么样。

这本比较书更像比较解剖。它把 Claude Code 和 Codex 放在一起，比较两者如何承认模型不可靠，以及如何把秩序安放在不同层级。它要回答的问题是：同样是做 harness，哪些设计更接近共识，哪些体现了不同工程路线的取舍。

现在还可以再多补一层用途：当你把前面这些判断带去看第三方 harness 时，也更容易识别一种常见误区。很多系统表面上也有 memory、skills、compact 和多代理，但上下文治理的主轴仍然是先把大量文本塞进 prompt，超了再截断和补救。这种路线看上去像“信息更全”，实际往往更费 token，也更容易把工作语义冲淡。

换句话说，可以把两者理解成同一研究计划的前后两步：

‧ 第一步，在第一本书里先抽出 Harness Engineering 的一般原则。  
‧ 第二步，在这本比较书里再看这些原则如何在两套系统里分别落地。

# 先看第一本书：Claude Code 给出的九个结构判断

第一本书的主线很稳定，基本可以压缩成九个判断。

1. harness 的第一职责，是先约束模型别把工程环境弄坏；放大模型能力通常建立在这个前提之上。

2. prompt 在 agent 里更接近控制平面的一部分，也承载了一部分过去常被当成人设文案的内容。  
3. query loop 才是 agent 的心跳，真正的系统重点在“一轮怎样接下一轮”。  
4. 工具不只是能力列表，它们更是受审批、调度和中断语义约束的执行接口。  
5. 上下文并不是越多越好，memory、CLAUDE.md 和 compact 本质上是在做预算治理。  
6. 错误不能只当边角料处理，恢复路径最好按主路径来设计。  
7. 多代理的价值主要落在职责分区和独立验证上，表面上的“分身感”反而只是次要现象。  
8. 团队落地不能靠个人技巧，必须把规则沉淀成可复用制度。  
9. 最终可以落成一套较稳定的 Harness Engineering 原则清单。

如果只读第一本书，你会得到一个很强的总体印象：Claude Code 的系统气质偏运行时治理。它首先关心的是—

‧ 会话如何连续运行，  
‧ 工具如何别闯祸，  
‧ 恢复如何别把系统拖进死循环，‧ 验证如何别沦为形式。

# 再看这本比较书：同一个问题，Claude Code 和 Codex 从哪里起笔

这本比较书在这个基础上，把比较轴明确拆成了几层。

# 控制面

Claude Code 更像动态 prompt 装配线。它把很多秩序压进运行前后的 prompt 拼装、会话状态和上下文治理里。

Codex 更像显式控制层。它把 instruction fragments、审批策略、工具 schema、thread、rollout、hook 等结构尽量模块化、类型化、可组合化。

# 连续性

Claude Code 把连续性压进主循环，强调 query loop 的心跳纪律。

Codex 把连续性拆进 thread、rollout 和 state bridge，强调状态如何被结构化持有和恢复。

# 工具与权限

Claude Code 偏运行时约束，重点在调用时如何审批、如何中断、如何避免危险动作直接落地。

Codex 偏策略语言和工具契约，重点在 schema、approval policy、sandbox 和 execpolicy 这些显式器官。

# 本地治理

Claude Code 倾向把地方经验收编成现场记忆，例如 CLAUDE.md、memory、skills 和工作流约束。

Codex 倾向把地方制度挂到结构化注入和事件系统上，例如 instructions、skills、hooks和明确的工具边界。

# 多代理与验证

Claude Code 强调多代理是运行时职责分区，验证必须独立于实现阶段。

Codex 则更强调通过显式委派、持久状态和工具化协作，把验证从“礼仪动作”变成可跟踪的系统能力。

# 合起来以后，真正清楚的是什么

把第一本书和这本比较书放在一起看，能得到三个更完整的结论。

# 第一，比较的重点主要落在 harness

这两套文档反复指向同一个事实：AI coding system 的核心挑战，首先是如何让模型在终端、文件系统、权限和团队制度中不失控；模型能力的提升要放在这个前提里理解。

阅读地图

# 第二，Claude Code 和 Codex 的差别，主要是秩序安放的位置不同

Claude Code 更像从运行时事故经验里塑出来的系统，优先解决连续性、恢复和现场治理。

Codex 更像从显式结构设计里塑出来的系统，优先解决控制层命名、策略表达、边界清晰和可组合性。

# 第三，后来者不该照抄产品，而该识别自己的主要不确定性

如果你的问题是长会话容易失控、恢复路径很脆、验证总被跳过，那么更该先学第一本书强调的运行时纪律。

如果你的问题是规则来源太散、权限边界不清、工具契约不稳定、团队很难复制同一套行为，那么更该先学这本比较书里总结出的 Codex 式显式控制层。

如果你看到某套系统主要靠堆叠 bootstrap 文本、身份设定、技能目录和工作区说明来维持连续性，那也不必急着被“上下文很多”这件事打动。很多时候，这更像一种尚未把上下文真正治理起来的过渡状态，离成熟的第三条路线还有一段距离。

# 推荐阅读顺序

如果你是第一次进入这套材料，推荐按下面的顺序读。

1. 先读序言，先确认这套比较关注的是秩序放在哪一层，不只是罗列功能表。  
2. 再读第 1 章为什么要把 Claude Code 和 Codex 放在一起看，建立问题意识。  
3. 然后顺着第 2 到第 6 章读完控制面、连续性、工具治理、本地制度和多代理验证这五条比较轴。  
4. 如果只想快速看总结，直接读第 7 章殊途同归，还是各表一枝。  
5. 如果你的目标是自己动手搭系统，最后读第 8 章如果你要自己做：该向谁学，先学什么。这一章现在也补了一张三路对照图，用来说明为什么有些 harness 明明“上下文很满”，却依然又贵又乱。

# 一句话总结

第一本书解释的是：为什么一个可控的 agent 必须采用这种结构。

这本比较书解释的是：当两套系统都认真做 harness 时，它们为什么会长得不一样。

# 序言两套 Harness，不必假装是同一匹马的附件

比较两套 AI coding harness，最容易犯的错误，是拿一张功能对照表当作思想史。左边写“有技能”，右边也写“有技能”；左边写“有沙箱”，右边也写“有沙箱”；左边写“能开子代理”，右边也写“能开子代理”。这样写的好处是省事，坏处是几乎什么也没说。因为工具栏上的名词相同，不代表系统的骨架相同。就像两个城市都修了桥，不能说明它们是按同一条河设计的。

这份内容想比较的是骨头，而不只是名字。

Claude Code 和 Codex 都属于那一类已经不满足于“让模型多说两句”的系统。它们都把模型放进了更麻烦的环境里：终端、文件系统、权限、工具调用、团队规范、长会话、恢复路径。到了这一步，真正决定系统成败的，往往就不再是模型本身，而在于它外面那套不怎么讨喜的约束装置。也就是 harness。

我在前一套内容里，已经把 Claude Code 当作一个样本，讨论过 Harness Engineering的一般原则。那时重点是单体解剖。现在再看，会觉得还缺一个动作：把它和另一个同样认真、但长法不同的系统摆在一起。只有比较以后，很多原来看似自然的设计，才会暴露出它其实只是某一条工程路径的选择。

Codex 值得比较，恰恰因为它不是 Claude Code 的复制版。从 core/src/lib.rs 一眼看过去，就能看到一种很明确的系统意志：把线程、rollout、state bridge、instructions、skills、hooks、sandboxing、exec policy、tools 这些东西拆成模块。目标是让控制层显式地变成可组合、可导入、可序列化、可策略化的器官，而不只是藏在一团运行时直觉里。

Claude Code 则不同。它更接近在主循环的压力下被塑出来的系统。你去看src/query.ts，再看它周围包裹的 compact、tool orchestration、permission、中断与恢复，很容易意识到，它的很多精华都发生在“这轮怎么接下一轮”这个问题上。也就是说，它的 harness 首先得连续运转，然后才谈如何把规则拆得更漂亮。

两者都承认模型不可靠。这一点很重要。因为只要这一点成立，许多浪漫的说法就都得后退。你不能把模型当作一个天然可信的执行体，不能让它在无边界条件下操作 shell、文件和网络，也不能指望它凭一时聪明维持长会话的秩序。一个系统要是愿意承认这一点，它就早晚会补齐 prompt 分层、状态持久化、权限控制、上下文治理、失败恢复、验证机制和本地制度这些器官。只是器官的位置，不一定一样。

这份内容还有一个边界，需要先说清楚。它不会提供 Claude Code 或 Codex 的源代码副本，也不会大段转录实现文本。原因并不玄妙，无非是版权和边界感。我们能做的，是在合理引用和工程分析范围内，基于文件结构、模块接口和可观察的设计意图，提炼出比较结论。换句话说，这里讨论的是系统怎样思考自己，而不是把受保护的实现挪到别处摆出来。

如果一定要先给出一句总判断，我现在比较愿意这样说：

Claude Code 与 Codex 的共同点，不在于它们都很会调用工具，而在于它们都不肯把模型当作一个可以放任自流的部件。

至于不同点，则更耐看一些。

Claude Code 更接近从运行时纪律出发。它担心会话怎么断，工具怎么串，compact怎么救，用户怎么插话，子代理怎么收尸。它有一种做过很多脏活以后的现实感，像个知道现场会出乱子的人，因此把很多本该由“聪明”解决的问题，提前交给控制流和恢复流去解决。

Codex 更接近从结构化控制层出发。它把 instruction fragment、thread、approvalpolicy、tool schema、hook event、exec policy 这些东西尽量明说出来，不羞于把系统做成一套带强命名、强边界和强配置感的装置。它不相信默契，宁可多定义几个类型，也不愿靠一团含混的约定去维持系统秩序。

两种路数都合理。只是合理的地方，不一样。

所以这不是一篇谁输谁赢的文章。工程上真正有价值的比较，通常是识别路径依赖，而不是排座次。你用什么结构去承认模型的不可靠，就会形成什么样的 harness。你把控制权放在哪一层，系统以后就会围着哪一层长肉。很多团队做 agent 总爱问“有没有最佳实践”，这问题问得太像买厨具。更好的问题应该是：你的主要不确定性在哪，你准备把秩序安放在哪。

下面七章，就从这个问题开始。

@wquguru   
2026.04.01   
Claude Code 源码泄漏的愚人节

btw. 您可以在 harness‑books.agentway.dev/book2‑comparing 访问在线版，获取更好的阅读体验

# 第 1 章为什么要把 Claude Code 和Codex 放在一起看

# 1.1 因为它们比较的是对模型的不信任

如果把 Claude Code 和 Codex 当作两个“会写代码的助手”，那比较就会很无聊。无非是谁支持更多工具、谁的终端体验更顺手、谁的配置项更细。这些东西当然有用，但它们不解释为什么系统会呈现出今天这种形态。

真正值得比较的地方，是它们都承认了一件对产品宣传不太友好的事实：模型不能直接拿来当执行体。它会误判，会忘记上下文，会把语气里的自信和结论里的正确性混为一谈。一旦这种东西接上 shell、文件系统和多轮状态，问题就不再是“答得对不对”，而是“它做过的事以后谁来收拾”。

Claude Code 在这一点上表现得很像一个做过事故复盘的系统。你看 query.ts、toolOrchestration.ts、compact.ts 以及 Bash 相关 prompt，就会发现它对失败、膨胀、中断和误操作的想象力很丰富。一个系统如果老是预设好几种失败路径，通常是因为它见过太多乐观主义留下的烂摊子，而不只是因为悲观。

Codex 则是另一种诚实。它把“不信任模型”落实为显式模块边界。core/src/lib.rs 里把 instructions、skills、sandboxing、exec_policy、rollout、state_db_bridge、thread_manager等器官明明白白列出来，等于是在说：秩序不能靠模型自己领会，得靠系统把职责拆出来。

所以比较这两者，是为了看两种不同的驯化路线，而不是为了看谁更会调用命令。

# 1.2 Claude Code 代表一种运行时优先的驯化路线

Claude Code 的很多精华，发生在主循环附近。这不是偶然。因为它的问题意识本来就很强烈地围绕“会话如何连续”展开。系统不只是要回答，还要在回答之后继续存在；不只是要执行，还要在执行之后保留秩序。这种压力会让架构自然向运行时编排倾斜。

因此它的关键词是：

‧ query loop   
compact   
‧ tool orchestration   
‧ interrupt permission ask/allow/deny   
‧ forked agent lifecycle

这些词看上去都不像品牌文案，更接近值班表。可一个系统到了真的要干活的时候，值班表往往比愿景更重要。

Claude Code 的长处也因此很鲜明。它对“连续工作中的脏活”特别敏感：消息膨胀、输出截断、工具结果回灌、上下文裁剪、子代理状态隔离、验证阶段独立、hook 生命周期收口。这些东西不是光靠一套漂亮接口定义就能解决的，必须经过运行时一轮轮摔打。

# 1.3 Codex 代表一种显式控制面优先的驯化路线

Codex 的气质不太一样。它当然也有运行时，但更引人注目的，是它把控制层尽量做成显式结构。

在 instructions/src/fragment.rs 和 user_instructions.rs 里，用户指令和skill 指令会以带有清楚 marker 的 contextual fragment 进入 prompt，而不是随便拼接。AGENTS.md的内容会被包装成明确边界的用户消息，skill 也会以<skill>片段注入。这说明 Codex 对控制面有一种近乎文书工作的偏爱：它并不拒绝灵活，但不愿让灵活失去边界。

同样，tools/src/lib.rs 和 local_tool.rs 也很说明问题。工具是一组 schema化的构造结果，而不只是一堆运行时对象。exec_command、shell、write_stdin、request_permissions、spawn_agent、wait_agent 等工具，在系统里首先是接口定义，其次才是执行动作。

再看 execpolicy/src/lib.rs，审批和执行限制甚至被做成单独 crate，包含 Policy、Rule、Evaluation、Decision、parser 等概念。这种做法其实很少见。很多系统也有权限策略，但往往散落在运行时各处；Codex 则把它往“可解析的政策语言”那一边推了一步。

# 1.4 两者都在回答同一个问题，但起笔位置不同

从更高处看，这两套系统都在回答同一个问题：

如何让一个会说话、会调工具、但本质不可靠的模型，在工程环境里做出可接受的事？

Claude Code 的起笔位置更接近：

“模型已经在循环里了。我们怎样保证它这一轮不会把下一轮弄坏？”

Codex 的起笔位置更接近：

“模型会接触很多控制信息。我们怎样把这些信息做成显式、可组合、可策略化的结构？”

前者强调流转，后者强调分层。前者把秩序安在 runtime heartbeat 上，后者把秩序安在 typed substrate 上。两者都不轻信模型，但它们把“不信任”安放在不同地方。

# 1.5 为什么这种差异值得团队认真看

因为一个团队以后会形成什么样的工作方式，常常取决于它最先把秩序放在哪。

如果你先强调运行时连续性，团队自然会更关注：

‧ 错误恢复‧ 中断响应‧ 状态污染‧ 工具编排‧ 长会话可靠性

如果你先强调显式控制面，团队自然会更关注：

‧ 指令边界  
‧ 配置层级  
‧ tool schemapolicy 语言  
‧ thread state 与持久化

两种方向都没有错。错的是混着用，最后既没有运行时纪律，也没有清楚的控制层，只剩一堆可以演示、但不好维护的聪明把戏。

# 1.6 本文的基本判断

这一章先把全文立场摆明：

Claude Code 和 Codex 代表的是两种 harness 设计哲学，而不只是两个“谁功能更全”的产品。

它们殊途同归，是因为都知道模型不可信，真正可信的只能是约束结构。

它们各表一枝，是因为一个更接近从现场经验里塑出来的运行时系统，另一个更接近由类型、策略和线程模型塑出来的控制系统。

下面的章节，就沿着这条判断往下拆。

# 第 2 章两种控制面：Prompt 拼装与Instruction Fragment

![](images/3c723b7b7d2935bfdfd60892f89d2f500514ad104eb7539108c6d5360435ef51.jpg)  
图 1: 控制面对比图

# 2.1 控制面这件事，首先不是文风问题

很多人谈 prompt，谈着谈着就会落到文风上。仿佛系统控制的核心，是把一段文字写得更像老工程师，或者更像耐心导师。这样理解 prompt，多少有点把警察制度理解成说话语气。

Claude Code 和 Codex 的共同点在于，它们都不这么看。它们都把面向模型的指令，当成行为控制的一部分。只是实现方式不同。

Claude Code 采用层层拼装。constants/prompts.ts、utils/systemPrompt.ts、claudemd.ts、memory 与 output style 等内容，会按运行时条件注入到 systemprompt 里。这里最重要的不是文案本身，而是分层拼装逻辑——多个来源在同一控制面里如何排优先级、如何避免互相打架。

Codex 更接近结构化片段。instructions/src/fragment.rs 里定义了 AGENTS.md和 skill 的 fragment 标记；user_instructions.rs 则把用户指令序列化成带目录和边界标记的消息。换句话说，Codex 并不把 instruction 当成一块随意串接的自然语言，而是当成”有开始、有结束、有来源类型”的上下文单元。

这两种做法都有效，但透露出不同的系统性格。

# 2.2 Claude Code 的控制面是动态装配线

Claude Code 的 system prompt 设计，有一个相当朴素的前提：控制面会随着当前任务、memory、工具能力和团队注入发生变化，而不是固定文本。

所以它的 system prompt 可以被理解为一条装配线。默认 prompt 是底板，appendprompt 是外加要求，agent prompt 是特定角色的补充，CLAUDE.md 和 memory 又带来现场条件。这样做的好处，是它能让同一个主循环适配很多不同场景。代价则是，你必须非常在乎装配顺序，否则一层层拼上去以后，系统很容易出现相互覆盖和语义稀释。

也正因为如此，Claude Code 非常依赖运行时对 prompt 的治理。控制面是任务现场不断被注入、覆盖、折叠和压缩的动态组合物，而不是静止的法规文本。这种结构与它的 query loop 性格很配。因为 loop 天然要求每一轮都重新计算“现在什么最重要”。

说到底，Claude Code 对 prompt 的态度是：你得能跟着现场走。它不太追求把一切instruction 预先格式化成稳定的对象，而更关心这些 instruction 在长会话里怎么被活用。

# 2.3 Codex 的控制面是带编号的公文系统

Codex 的写法则相反。它似乎很不愿意让 instruction 只作为一堆“模型自己体会”的自由文本存在。

ContextualUserFragmentDefinition 这种命名已经相当直白。它强调的是：

‧ 片段类型‧ 起止边界‧ 包裹规则‧ 如何转换为消息

这说明 Codex 的设计者更在乎 instruction 的“可识别性”。一段本地规则，不只是“有内容”，还必须能在系统内部被识别为某一类内容。AGENTS.md 不只是读进来，还是一个明确的 fragment；skill 也不只是附录文本，而是一个明确包裹过的上下文单元。

而且这不是停留在概念层面的命名好看。fragment.rs 里真的把 AGENTS_MD_START_MARAGENTS_MD_END_MARKER、SKILL_OPEN_TAG、SKILL_CLOSE_TAG 定成常量，再由ContextualUserFragmentDefinition::wrap() 和 into_message() 把内容包装成 ResponseItem::Message。到了 user_instructions.rs，UserInstruc-tions 还会把目录名序列化进 # AGENTS.md instructions for ... 这一行；SkillInstructions 则额外带上 <name> 和 <path>。也就是说，Codex 连“这段规则来自哪个目录、哪个 skill 文件”都尽量不让模型自己猜。

这种做法有两个直接后果。

第一，控制面的可调试性更强。你知道某段信息为什么会出现在消息历史里，也更容易说明它从哪里来。

第二，控制面更适合继续程序化。今天是 marker，明天就可能细化为 precedence、merge rule 或 visibility rule。系统一旦先把 instruction 类型定义清楚，以后很多治理动作就有明确落点。

# 2.4 AGENTS.md 与 CLAUDE.md：同样是本地规则，气质却不同

这两套系统最耐人寻味的一个对照，是本地规则文件。

Claude Code 强调CLAUDE.md。它更接近团队或目录范围内的长期工作约束，和 mem‑ory、skill 一起构成“做事时该记住什么”。它的优势是贴近任务现场。你在某个目录里干活，就把这地方的规矩读进来。它有一种工程现场公告板的气质，适合告诉系统：这里有哪些常识、禁忌和局部制度。

Codex 强调 AGENTS.md，而且还进一步讨论 hierarchy。docs/agents_md.md 甚至明确说，在 child_agents_md 功能开启时，系统会追加关于作用域与优先级的说明，即便当前并没有 AGENTS.md。这件事很有意思。它说明 Codex 不仅在乎“有没有规则”，还在乎“规则的适用范围和继承关系如何被系统明说”。

这背后的区别可以概括成一句不太客气但挺准确的话：

# 第 2 章两种控制面

Claude Code 更接近让现场规则进入会话。

Codex 更接近让现场规则进入制度。

# 2.5 两种控制面的代价

运行时装配线的代价，是难以彻底形式化。它灵活，但也更依赖主循环和工程经验。规则多了以后，要防止互相覆盖和语义稀释。

结构化片段的代价，是系统会显得更重。你得定义 marker、类型、序列化和注入方式，还得考虑哪些东西应当成为一等对象，哪些不必。系统因此更清楚，也更啰嗦。

说得更直接些：

‧ Claude Code 容易形成经验型控制力‧ Codex 容易形成制度型控制力

经验型的长处是灵活，坏处是有时不够显式。  
制度型的长处是清楚，坏处是需要持续维护结构成本。

# 2.6 这章的比较结论

这一章可以先下一个不太保守的判断：

Claude Code 把 prompt 视为运行时控制面的动态拼装结果，Codex 把instruction 视为可识别、可包裹、可序列化的结构化片段。

前者更接近现场编导，后者更接近制度秘书。

你不能简单说谁更先进。真正要看的是，你的系统更怕哪一种失控：

‧ 怕长会话里指令失真、现场变化太快，就更容易欣赏 Claude Code 的动态装配‧ 怕规则来源不清、作用域模糊、无法系统化治理，就更容易欣赏 Codex 的 fragment化写法

下一章要谈的，是两者更深的分野：会话连续性究竟主要寄托在 query loop，还是寄托在 thread、rollout 和 state 这些更显式的结构上。

# 第 3 章心跳放在哪：Query Loop 对照Thread、Rollout 与 State

![](images/053d1b95a787e8a111bef0b2d11b170fbf336e1732a0d9da355969cac9967cdb.jpg)  
  
图 2: 连续性对比图

# 3.1 代理系统的核心是连续性

把代理系统理解成“多轮聊天”，就像把数据库理解成“一个比较耐心的记事本”。不能说全错，但这种说法掩盖了真正的架构问题。

代理系统真正的难题，是连续性：

‧ 上一轮做了什么，这一轮怎么接‧ 工具结果怎么回填

‧ 中断之后怎么收口  
‧ 上下文太长以后怎么整理  
‧ 失败时要重试、压缩、还是忠实汇报这些问题决定系统是不是 agent，而不只是某个”支持工具调用的问答接口”。  
Claude Code 与 Codex 在这里的差异，比任何功能对照都更有含金量。

# 3.2 Claude Code：把连续性压进主循环

Claude Code 的主轴很明显，就在 query() 和 queryLoop() 一带。它把很多关键问题都压进循环状态里处理：

‧ 当前消息序列   
‧ tool use context compact 跟踪 output token 恢复计数 pending summary   
turn count   
‧ transition

这意味着 Claude Code 对“代理如何活着”这个问题的回答，是运行时性的。连续性主要由 loop 维护。系统的骨架因此更接近一个不断自我校正的会话发动机，而非一个先有强外部状态模型、再由状态模型驱动执行的体系。

它的优势非常现实。因为很多会话里的真实麻烦，恰好都发生在 loop 里：工具返回的顺序、模型输出突然截断、prompt too long、history snip、microcompact、用户插话。Claude Code 不试图回避这些问题，而是把它们作为 loop 内部的合法状态来处理。

这种设计有一种很工程的粗粝感。它不优雅，但通常更稳。

# 3.3 Codex：把连续性拆成线程、rollout 与状态桥

Codex 则显得更“账本化”。从 core/src/lib.rs 就可以看到，连续性并不只存在于一个巨大的循环里，它被分摊到：

‧ codex_thread

thread_manager rollout   
state_db_bridge state   
message_history

再看 sdk/typescript/src/thread.ts，thread 是外部开发者可以直接理解和操作的一级概念。Thread 持有 id，可以 runStreamed()，也可以 run()；thread.started会回填线程 ID；approval policy、working directory、sandbox mode、networkaccess、additional directories 等 turn 级执行条件，都是和线程运行紧密耦合的显式参数。

这里甚至能看到一种很具体的“线程主权”。runStreamedInternal() 不是随便把输入丢给后端，它会先做 normalizeInput()，把文本和本地图像分开，再调用 cre-ateOutputSchemaFile() 为本轮准备输出 schema 文件；真正执行时，把 threadId、approvalPolicy、sandboxMode、workingDirectory、networkAccessEnabled、additionalDirectories 一并送进 _exec.run()。流里一旦收到 thread.started事件，线程对象本身就更新_id。这说明 thread 不是外围包装，而是 turn 级执行语义真正经过的一层。

这里最有意思的地方，是连续性已经不只是“循环还在继续”，而是“一个线程正在被一套更显式的状态结构持续记录和约束”。rollout 的存在尤其说明 Codex 很在乎回放、索引、持久化和会话外可见性。

这会让系统更接近一个真正的执行记录器，而不只是一个现场对话管理器。

# 3.4 差别在于状态安放的位置

需要说明一点：Claude Code 当然也有状态，Codex 当然也有循环。真正不同的，不在有没有，而在主权在哪。

Claude Code 把状态主权更多交给 query loop。换句话说，系统认为“会话怎么继续”是 runtime 核心问题，许多事情要在 loop 里直接解决。

Codex 则把状态主权更明确地交给 thread 和 rollout 结构。它认为连续性不该只是一段内部控制流的副产物，还应当是一套被线程和状态基础设施承接的显式事实。

这就是为什么看 Thread 那个 TypeScript SDK 文件，会觉得 Codex 的 thread 已经是产品概念，而不只是内部实现细节。开发者被允许直接围绕 thread 来思考 agent turn。

![](images/ba69d5982d9e4929caca6a5dc77f3c4ffb8e6ccd3949c8e38a9c9cde3e4480fa.jpg)  
图 3: Codex 线程、turn 与状态细节图

Claude Code 的 query loop 则更接近发动机室。你知道它重要，但用户不一定直接围着它组织所有心智模型。

# 3.5 对恢复与可审计性的影响

这种状态安放差异，会直接影响恢复和审计。

Claude Code 的恢复强项，在于它离现场近。因为很多问题就在 loop 内部被发现和修复，例如 reactive compact、token 上限恢复、工具中断处理。它不需要先把麻烦搬运到更高一层状态模型里，再考虑怎么回滚。

Codex 的恢复强项，则更可能体现在状态可追踪性。线程有 ID，rollout 有记录，statebridge 和 message history 提供了更清楚的外部结构。这使得系统更容易回答“上一轮到底发生了什么”，而不只是停留在一团运行时逻辑里的回想。

如果把 core/src/lib.rs 一起看，这种“档案意识”就更明显。它不只是暴露 Codex-Thread，还显式导出 ThreadManager、RolloutRecorder、state_db_bridge 以及message_history 相关模块。一个系统如果把这些器官放到根模块出口附近，基本等于承认：连续性不是 query loop 顺便维持出来的副产品，而是基础设施本身。

简单说：

‧ Claude Code 更接近现场救火队‧ Codex 更接近带档案系统的调度中心

二者都重要。只是前者更擅长维持运行，后者更擅长说清楚运行是如何被维持的。

# 3.6 对产品和团队接口的影响

这种差异还会影响团队怎么接入系统。

如果系统主权在 loop，团队更容易沿着运行时问题组织工作：

‧ 哪些错误需要恢复‧ 哪些动作应当中断compact 何时触发‧ 工具结果如何串回主对话

如果系统主权在线程和状态结构，团队更容易沿着接口与治理组织工作：

# 第 3 章心跳放在哪

‧ thread 的生命周期是什么  
‧ rollout 要保留哪些事件状态库放在哪  
approval policy 如何成为 turn 级选项

因此 Claude Code 更接近先把 agent 做会，再把制度嵌进去；Codex 更接近先把制度接口立起来，再让 agent 在里面工作。

# 3.7 本章结论

这一章的结论可以写得明确一点：

Claude Code 的连续性更多由 query loop 承担，Codex 的连续性更多由thread、rollout 与 state 基础设施承担。

前者强调 runtime heartbeat。

后者强调 persisted session substrate。

这不是审美差异，这是系统权力分配。谁来拥有连续性，谁就定义了 harness 的中心。

下一章进入最硬的一层：工具、沙箱、审批和执行策略。到了这里，浪漫叙事一般都会自动退场，因为 shell 不大关心文风。

# 第 4 章工具、沙箱与策略语言：谁来阻止模型动手太快

# Claude Code vs Codex: Tool Governance and Execution Boundaries

![](images/6eb349f8905198bba64055f587c230da33991b0ed21844da27be6b43daa92116.jpg)  
图 4: 工具治理对比图

# 4.1 真正危险的是开始执行

一个模型说错话，通常只是浪费时间。一个模型跑错命令，就可能顺手把目录、仓库、进程和工作流一起带坏。所以真正把 AI coding system 区分开来的，是它调工具之前谁拥有最后解释权。

第 4 章工具、沙箱与策略语言

Claude Code 和 Codex 在这件事上都很认真，但认真得不一样。

Claude Code 更接近在运行时把工具纳入调度纪律。它有 toolOrchestration.ts、toolExecution.ts、StreamingToolExecutor.ts、useCanUseTool.tsx、Bash专门 prompt 以及 allow/deny/ask 语义。它关心的是：这次工具调用能不能跑，怎么跑，能不能并发，用户有没有拒绝，跑到一半如何中断，结果怎么回到上下文。

Codex 则把工具本身先做成类型化接口。tools/src/lib.rs 导出一整套工具构造 器，local_tool.rs 则 定 义 exec_command、shell、shell_command、re-quest_permissions 等 schema 结构。工具在 Codex 里首先是规范化的 API 面，其次才是执行单元。

# 4.2 Claude Code：重点在运行时编排和危险动作约束

Claude Code 的工具系统有一种很强的现场调度感。并发要看 schema 和 isConcur-rencySafe()；上下文修改要保证回放顺序稳定；流式工具执行还要考虑中断、syn‑thetic result 和 UI 反馈。

这套系统最像工程现实的地方，是它承认工具调用是“一个带后果的过程”，而非单个点动作。从这一点看，Claude Code 的 harness 很像给模型装了一个工地监工。工人当然可以干活，但监工得盯着：

‧ 先做哪一个  
‧ 哪些能并行  
‧ 哪些必须串行  
‧ 做完以后怎么记账  
‧ 干到一半被叫停怎么办

尤其是 Bash 这类高风险工具，Claude Code 的态度简直可以说是唠叨。可工程里真正成熟的系统，通常都会对最危险的接口变得唠叨。谁还在 shell 面前保持一种青年式的洒脱，多半还没有足够多的事故记忆。

# 4.3 Codex：重点在工具 schema、审批参数和策略引擎

Codex 则更接近把“风险动作”的控制做成正式接口约束。

以 local_tool.rs 为例，exec_command 这类工具会显式拥有这些字段，而不是简单接收一个字符串命令：

cmd workdir   
‧ shell   
tty yield_time_ms max_output_tokens   
‧ login approval 相关参数

而 shell / shell_command 还会在描述层面直接要求设置 workdir，提醒不要滥用cd。这说明 Codex 不满足于“后台自己做对”，它还希望把正确使用方式嵌进工具定义本身。

更进一步，Codex 把审批和权限提升抽成显式参数，把 request_permissions 做成单独工具，又把 execpolicy 单独做成 crate。这里的关键词已经超出简单的 permission，进入了更完整的策略层：

‧ Policy ‧ Rule Evaluation Decision parser

这套命名几乎等于在说：执行边界已经形成一门小型政策语言，而不只是几个 if/else。

而且这种“语言化”不是虚张声势。local_tool.rs里各个工具的 schema 都会明确 re‑quired 字段，并把 additional_properties 关掉，减少模型乱塞参数的空间；shell和 shell_command 的描述里甚至直接写着“尽量不要用 cd，应当设置 workdir”。execpolicy/src/lib.rs 则不只导出 parser 和 PolicyParser，还导出 block-ing_append_allow_prefix_rule、blocking_append_network_rule 这种修正规则的 helper。换句话说，Codex 不是只会检查政策，还准备了修改和补丁政策的正式入口。

# 4.4 运行时审批对照策略语言

Claude Code 和 Codex 在工具风险控制上的分歧，可以概括为：

‧ Claude Code 偏运行时审批链

‧ Codex 偏显式策略语言与参数化审批

Claude Code 的 ask/allow/deny 逻辑，很适合与具体工具调用现场紧密耦合。系统可以根据当前上下文、工具类型、用户动作和会话状态来决定是否继续。它的长处是灵敏，缺点是规则更容易藏在 runtime 逻辑里。

Codex 的 exec policy 思路，则是尽量把规则抽离出来，让它成为可以单独解析、单独评估的实体。这种写法的长处，是规则可读性和可迁移性更强，也更适合团队级治理。缺点是系统会显得更重，而且你得认真维护 policy 设计，而不是把它当注释。

说得粗一点：

Claude Code 更接近“值班经理现场拍板”。

Codex 更接近“公司先写好制度，再看这单是否合规”。

# 4.5 沙箱与审批，不只是安全问题，也是产品定义问题

很多团队把沙箱、审批、权限看成安全附属件。这个看法有点轻慢。对于 coding agent来说，这些东西其实定义了产品是什么。

假如系统允许模型直接在用户目录里跑任意命令，那它就成了一个把风险转嫁给用户的agent，而不只是“更强”。反过来，如果系统能明确表达 sandbox mode、network access、approval policy、additional directories、state DB 位置和 MCP tool approvals，那它给用户提供的就不只是能力，还有行为边界。

Codex 在 thread.ts 里把这些 turn 级条件显式暴露出来，说明它把这些东西视为线程运行语义的一部分，而不是隐藏实现细节。Claude Code 则在工具执行、中断、permission hook 与 Bash 限制里，把边界压到运行时现场去执行。

这意味着二者在产品哲学上也不一样：

‧ Claude Code 更接近“边做边看守”‧ Codex 更接近“先给出执行契约，再开始做”

# 4.6 MCP、扩展工具与边界外移

两套系统都支持把更多能力接进来，但方式仍然保留差异。

Claude Code 更接近把 skill、hook、permission 和工具 prompt 拼接成一套场景化治理链。它擅长让本地规则跟着任务现场进入主循环。

# 第 4 章工具、沙箱与策略语言

Codex 则更愿意把外部能力纳入统一工具系统。tools/src/lib.rs 中 MCP re‑source、dynamic tool、tool discovery 等接口，说明外部扩展最好也成为 schema化、公理化的工具对象，而不是运行时临时约定。

这是很关键的分歧。因为一旦生态变大，系统会越来越依赖“扩展能力如何服从总规则”。  
谁先把边界外移问题想清楚，谁的扩展体系以后就更不容易变成杂物间。

# 4.7 本章结论

这一章可以压缩成一句比较硬的判断：

Claude Code 的工具治理更强地依赖运行时编排与现场审批，Codex 的工具治理更强地依赖 schema、参数化权限和独立策略系统。

前者像经验丰富的工头。

后者像有制度处和法务部的施工单位。

你要是只看“都能跑命令”，就会错过真正重要的差异。重要的是，谁在工具动手之前拥有最终秩序。

下一章看更接地气的一层：skills、hooks、本地规则文件和团队制度。技术系统一旦要进团队，最后都得学会写村规民约。

# 第 5 章技能、Hook 与本地规则：系统如何学会守乡约

Claude Code vs Codex: Local Governance, Skills, and Multi-Agent Work

![](images/0c595beb4907fe8f24fb2aab93484c162a761ce27af63a796fce5f598f625bca.jpg)  
图 5: 本地治理对比图

# 5.1 真正能落地的 agent，一定会地方化

任何一个通用 coding agent，只要真的开始给团队干活，就会遇到同一个问题：公司有公司的规矩，仓库有仓库的规矩，目录有目录的规矩，人还有人的怪脾气。系统要是不能吸收这些局部制度，就只能永远停留在演示环境里。

Claude Code 和 Codex 都给出了答案，只是方向不同。

# 5.2 Claude Code：把局部制度做成现场记忆

Claude Code 的地方化能力，很大一部分落在：

‧ CLAUDE.md   
‧ skill   
‧ hook session memory

这几样东西组合起来，有一种很强的”现场经验沉淀”味道：

‧ CLAUDE.md 告诉系统在这个仓库、这个目录、这个团队里什么算常识；  
‧ skill 把某类工作流程打包；  
‧ hook 把团队治理挂到生命周期节点上；  
‧ session memory 则让当前工作不至于每轮都从头做人。

它们的共同特点，是都非常贴近任务现场。这里的重点在于让规则进入当前会话，参与当前执行，而不是先定义一套万古不变的组织制度。Claude Code 很像一个愿意随身带笔记本的工程师，走到哪就把当地规矩抄下来。

这种做法的好处，是非常实用。它适合多项目、多目录、多种局部约束并存的环境。坏处是，如果没有额外整理，知识容易以“现场补丁”的形式扩张。

# 5.3 Codex：把局部制度做成结构化注入和事件系统

Codex 也有 skill，也有本地规则，也有 hook，但气质明显更制度化。

先 看 skill。skills/src/lib.rs 显 示 系 统 会 把 内 置 system skills 安 装 到CODEX_HOME/skills/.system， 还 会 对 skill 资 产 做 hash/fingerprint。 这 个细节很说明问题，因为它表明 skill 在 Codex 里不只是临时读入的文本，而是“被安装、被管理、可追踪版本形态”的资产。

更关键的是，它连“什么时候需要重装 skill”都想好了。install_system_skills()会先算 embedded skills 的 fingerprint，只有 marker 不匹配时才删掉旧目录并重新写入；匹配时直接跳过。这个细节看着小，实际上说明 Codex 把 skill 当成可部署资产，而不是每次启动都顺手读一堆模板文本。

再看 AGENTS.md。这套机制在 Codex 中不只表示“读一份本地说明”，还伴随着作用域和 hierarchy 的讨论。也就是说，局部规则不只是内容，还带着位置关系。

最后看 hook。hooks/src/engine/mod.rs 里把 hook 事件明确拆成：

session_start pre_tool_use post_tool_use user_prompt_submit ‧ stop

而且每个 handler 都有 event_name、matcher、timeout、status message、sourcepath、display order 等结构。这说明 Codex 的 hook 更接近显式生命周期事件系统，而不是“哪里方便就塞一个回调”。

再往下看还会发现，hook engine 区分了 preview_\* 和 run_\* 两套路径，先预览哪些 handler 会命中，再决定真正执行；在 Windows 上还会因为能力不完整而明确关闭 codex_hooks 并返回 warning。也就是说，Codex 连 hook 能不能开、为什么不开，都希望成为系统可解释的一部分。

# 5.4 Claude Code 偏经验收编，Codex 偏制度挂载

把两者放在一起看，差异就非常清楚了。

Claude Code 的本地治理，更接近把现场经验不断收编进主循环附近。它擅长让 agent在当前上下文里迅速学会“这里怎么办事”。

Codex 的本地治理，则更接近把地方规则挂载到明确控制面与生命周期机制上。它擅长让规则不仅被读懂，还被分类、排序、安装和触发。

这就导致两者的团队感不同。

Claude Code 的团队感，像一个熟悉现场、懂得看气氛的老员工。

Codex 的团队感，像一个新来但制度意识极强的项目经理，先把规则贴出来，再开始协调人做事。

# 5.5 对组织可复制性的影响

这种差异最影响组织复制能力。

如果一个系统主要靠现场经验注入，它会更快地适应新仓库，也更容易在复杂局部语境里保持有效。但复制到更多团队时，往往需要额外整理，避免大家各写各的CLAUDE.md、各做各的 skill，最后像各省自行印教材。

如果一个系统主要靠结构化注入和事件挂载，它在组织扩展上更有潜力。因为规则更容易被统一分发、版本化和审计。代价是学习成本更高，团队要先接受更多显式制度。

这是一种经典工程取舍：

‧ 越贴近现场，越有弹性‧ 越制度化，越易复制

两者都不会自动给你幸福。真正决定结果的，是团队究竟需要哪一种稳定性。

# 5.6 本章结论

这一章的归纳可以写成：

Claude Code 更倾向于把局部治理做成现场记忆与运行时注入，Codex 更倾向于把局部治理做成结构化资产与生命周期事件系统。

这不是“都支持 skills 和 hooks”的同义反复。

差别在于，Claude Code 问的是“怎样让 agent 在这里干活更像本地人”，Codex 问的是“怎样让本地规则进入一套可管理的制度框架”。

下一章要看这两种系统在更高风险处如何分工：多代理、验证、持久状态和恢复。系统一旦开始让多个代理干活，光讲规矩还不够，还得讲责任分离。

# 第 6 章委派、验证与持久状态：谁来防止系统自己给自己打高分

# 6.1 多代理的真正问题是责任

很多人一听多代理，就像听到公司要扩编，立刻想到效率提升。其实真正棘手的，从来都是多出来的责任怎么切，而不只是多几个代理。

如果同一个系统既负责执行，又负责总结，又负责验证，还顺手负责给自己写评语，那 最后通常会得出一个令人宽慰但不太可靠的结论：干得不错。

Claude Code 在这方面相当清醒。前一套内容里已经分析过，它会把 explore、execute、synthesis、verification 拆开，并且把 verify 做成一种独立纪律，而非礼貌性的结尾动作。这件事很重要，因为它说明系统不愿让“完成”只由执行代理自己宣布。

Codex 也明显走在这条路上。tools/src/lib.rs 中大量 agent 相关工具，比如 create_spawn_agent_tool_v\*、create_wait_agent_tool_v\*、cre-ate_send_message_tool、create_close_agent_tool_v\*， 说 明 代 理 委 派 在Codex 里是正式工具能力，而不是什么黑魔法。

# 6.2 Claude Code：多代理服务于运行时职责分区

Claude Code 的多代理机制，整体上还是围绕主循环和任务推进展开。它更接近在说：主代理不该什么都自己干，尤其不该既干活又验收。

因此它把多代理主要用来处理：

‧ 探索型任务外包 ‧ 执行型任务分流 synthesis 汇总 verification 独立复核

这种架构非常符合它的整体气质。因为 Claude Code 的强项本来就在运行时编排，所以多代理也自然被纳入“当前这轮任务怎么往前推进”的治理框架里。换句话说，它并不是先有一个宏大的 agent platform，再往里塞任务；它是先有现场调度问题，再发展出代理分工。

# 6.3 Codex：多代理服务于显式工具化协作

Codex 的代理委派则更明显地被定义成工具接口。这种写法会让多代理更接近一个正式子系统。

这带来两个影响。

第一，委派动作更容易被记录、审计和组合。因为它是显式工具调用，而不是某段内部runtime 魔法。

第二，代理协作更容易与线程、状态和审批体系对齐。既然 Codex 本来就很重视 thread、rollout 和 policy，那么多代理也自然更适合进入这套基础设施，而不只是临时现场技巧。

这里的“正式”不是泛泛而谈。agent_tool.rs 里，spawn_agent、send_input、wait_agent、close_agent 都有单独 schema；send_input 明确区分 inter-rupt $\underline { { \underline { { \mathbf { \Pi } } } } } =$ true 的立即打断和默认排队；wait_agent 甚至有 default/min/max timeout选项；close_agent 还明确写着会连同 open descendants 一起关闭。也就是说，Codex 不是只提供“找个子代理帮忙”这件事，而是把协作中的抢占、等待和收尾都定义成了协议字段。

这种设计很适合把多代理做成平台能力。它不见得更灵巧，但更容易长期维护。

# 6.4 持久状态让验证不只是礼仪

验证之所以常常流于形式，一个重要原因是系统没有足够好的状态承接。上一步刚干完什么、为什么这么干、哪些工具动过、哪些文件变过——要是这些信息都只在执行代理脑子里，那验证阶段就很容易沦为一场貌似认真、实则缺材料的表演。

Claude Code 的做法，是尽量让会话状态、工具结果和恢复分支在 runtime 里连续可见，再配合独立验证纪律来降低自我美化。

Codex 的做法，则更可能通过 thread、rollout、message history、state DB bridge这些结构，为验证提供更清楚的材料基础。一个有会话档案意识的系统，更容易把“刚才到底做了什么”说清楚。

# 第 6 章委派、验证与持久状态

因此二者在验证问题上并非冲突，它们补的是不同缺口：

‧ Claude Code 补的是执行者过于沉浸现场的问题‧ Codex 补的是系统协作必须留下结构化证据的问题

# 6.5 对恢复与收尾的不同态度

多代理系统还有一个现实问题：怎么收尾。

Claude Code 的很多设计细节都说明，它很在乎 task cleanup、父子 abort 传播、sub‑agent lifecycle hook 之类的事情。在它的世界里，多代理首先是运行时现场的一部分，现场出了问题，必须能及时收口。

Codex 这边，从工具化代理和线程状态结构来看，更偏向于把代理生命周期纳入显式状态管理和调用协议。它不只关心”子代理死没死”，还关心”这个委派行为作为一条系统事件该如何留存”。

这种区别同样是气质问题：

‧ Claude Code 更接近项目现场的总工，担心人散场以后地上还留着坑‧ Codex 更接近带项目管理系统的组织者，担心每个协作动作有没有进入记录体系

# 6.6 本章结论

这一章的结论不难写：

Claude Code 的多代理设计更强调运行时职责分离与现场收尾，Codex 的多代理设计更强调工具化委派、状态承接与可审计协作。

二者都试图避免系统自己给自己打高分。

只是 Claude Code 更靠角色分离和验证纪律。

Codex 更靠显式接口、线程状态和协作记录。

最后一章，我们把前面六章压成总判断，回答书名里的问题：究竟是殊途同归，还是根本不同种。

# 第 7 章殊途同归， 还是各表一枝

# 7.1 先说“同归”的部分

要是只问结论，我会先说：它们确实殊途同归。

原因很简单。Claude Code 和 Codex 都不把模型当作值得直接托付的执行体。它们都承认：

‧ prompt 不等于控制全部‧ 工具必须受约束‧ 长会话一定需要状态治理‧ 本地规则必须进入系统‧ 多代理必须有分工和验证

换句话说，它们都已经越过了那种“只要模型更强，系统问题就会自动消失”的幼稚阶段。谁能走到这一步，谁就已经不再把 agent 当成聊天机器人带几把工具那么简单。

所以从总体方向看，它们确实在同一个目的地上会合：把 harness 当成真正的控制层，把模型当成这层控制之下最不稳定、但也最有生产力的部件。

# 7.2 再说“各表一枝”的部分

但要是因此说它们本质一样，那就太粗糙了。

Claude Code 的主轴更像这样：

‧ 从 query loop 出发  
‧ 在运行时处理连续性  
‧ 用 compact、工具编排、中断和恢复维持秩序  
‧ 用技能、hook、验证把现场规则和团队制度接进来

# 第 7 章殊途同归

Codex 的主轴更像这样：

‧ 从模块边界和控制层显式化出发  
‧ 把 instruction 做成 fragment  
‧ 把工具做成 schema  
‧ 把执行边界做成 policy  
‧ 把会话做成 thread / rollout / state  
‧ 把本地规则与 hook 做成结构化资产和事件系统前者像从机械经验里塑出来的系统。  
后者像从制度设计里塑出来的系统。  
这就是“各表一枝”的地方。差别不在目的，而在骨架。

# 7.3 如果非要给它们起一个更难听但更准确的名字

我甚至愿意把它们叫作两种不同的 harness 政体。

Claude Code 比较接近运行时共和制。很多权力集中在主循环和现场调度上，秩序通过不断的现实协商来维持。它并不是不讲制度，只是制度往往服务于会话现场。

Codex 比较像控制面立宪制。很多权力首先被写进类型、片段、策略、线程和事件系统里，运行时当然还要做判断，但那套判断更倾向于在明确框架下展开。

这么说当然有点夸张，不过有助于看清一件事：harness 从来不只是技术组件堆积，它也是一种权力分配方式。谁定义边界，谁解释状态，谁拥有最后的执行解释权——这些事情最后都会体现在架构里。

# 7.4 对后来者的启发

如果团队准备做自己的 coding agent，这份比较真正有用的地方，是帮你少犯两类错误，而不是让你选边站。

第一类错误，是误以为只要学一套功能表就够了。其实不够。你得先决定自己的主要矛盾是什么。是长会话里容易失控，还是规则来源太散、权限边界不清？不同矛盾，会把你推向不同 harness 形态。

第二类错误，是试图把两者最顺眼的特性不加判断地拼在一起。工程上最危险的往往不是取舍，而在没有取舍。你既想要完全动态的运行时灵活性，又想要彻底显式的结构化控制面，最后多半会得到两头都不彻底的系统。

更合理的做法是：

‧ 如果你更怕现场失控，就先把 runtime heartbeat 做扎实‧ 如果你更怕制度失真，就先把 instruction、tool、policy、state 显式化‧ 等主矛盾稳住，再逐步补另一边

这里还可以多加一个提醒。现实里很多后起系统既没有把运行时纪律做扎实，也没有把控制层显式化到位，而是走向第三种更容易上手、也更容易失控的路线：把越来越多的bootstrap 文件、角色设定、技能说明和工作区文本堆进 prompt，试图靠“信息更全”弥补骨架不足。这类系统短期里常常显得能跑，长期里却容易同时暴露两类问题：token烧得快，工作语义又不够稳。

# 7.5 最终判断

书名里的问题，现在可以正式回答。

它们是殊途同归。

也是各表一枝。

“同归”说的是最终承认的现实一致：模型不可靠，harness 才是秩序来源。

“各表一枝”说的是实现这个现实的政治经济学不同：Claude Code 更信运行时纪律，Codex 更信显式控制层。

而那些主要靠 prompt 堆叠来维持上下文的系统，则更像还停在中间地带。它们已经意识到模型会忘、会漂移，所以开始加 memory、加 skills、加 compact；但如果上下文治理仍然主要依赖“先注入，再抢救”，那就还没有真正决定把秩序放在哪一层。

这两种路径没有谁天然更高明。真正的问题是，你的系统准备把不确定性关进哪一层笼子里。

笼子的位置，决定了系统以后会演化成什么样。

# 第 8 章如果你要自己做：该向谁学，先学什么

# 8.1 比较的最终用途是少走弯路

写比较文最没意思的结尾，就是把读者推回一种消费主义姿态：请在 A 和 B 之间二选一。工程系统不是耳机，不靠横评下单。真正有用的问题是，如果你准备自己做一套harness，或者准备重构现有 agent，应该先学谁的哪一部分。

Claude Code 和 Codex 给出的，是两种起手式，而不是两份答案。

Claude Code 适合提醒你：别把运行时问题想得太文雅。真正把系统拖垮的，往往是query loop 里的脏活，例如工具结果收口、上下文膨胀、中断恢复、子代理清理、验证独立、失败熔断。谁轻视这些问题，谁最后就会得到一个看着聪明、用着费命的系统。

Codex 则适合提醒你：别把控制层做成一团心照不宣。instruction 来源、tool schema、approval policy、thread state、hook event、skills 资产，这些东西越早显式化，后面越容易治理。谁总指望运行时临场发挥去替代制度，谁最后就会发现系统越来越像一座口头约定搭起来的棚子。

# 8.2 三种常见团队，三种起手方向

# 第一种：已经有 agent 原型，但长会话经常失控

这种团队通常最需要先学 Claude Code。

因为他们的问题多半不在“控制面定义不清”，而在系统活不长。常见症状包括：

‧ 上下文越来越乱‧ 工具调用链断裂‧ 中断后状态说不清

# 第 8 章如果你要自己做

‧ 子代理跑完以后没人收口‧ 验证变成随口一说

这时候最该补的是主循环纪律，而不是更多配置项。先把 runtime heartbeat 做稳，再谈制度美学。

# 第二种：已经有不少规则，但规则来源过散、权限边界不清

这种团队通常更该先学 Codex。

因为他们的问题不在现场活不过去，而在系统越来越难治理。常见症状包括：

‧ 本地规则四处散落  
‧ 哪些约束进了 prompt，哪些进了工具，没人说得清  
‧ 审批逻辑混在代码里，难以解释  
‧ 多种扩展能力接进来以后，边界越来越模糊

这时候最需要的，是把控制层显式化。先把 instruction、tool、policy、thread 这些概念定义清楚，再让 runtime 在里面工作。

# 第三种：还没有成型系统，准备从零开始

这种团队最危险，因为最容易同时羡慕两边的优点，然后把自己搞成折中失败品。

更稳妥的路线通常是：

‧ 先选一个主矛盾  
‧ 先围绕主矛盾设计主骨架  
‧ 另一边只补最低限度，不要一口气学全

要是你的第一阶段主要风险是“模型会乱来”，那就先做 Claude Code 式的 runtimediscipline。

要是你的第一阶段主要风险是“团队会失去秩序”，那就先做 Codex 式的显式控制层。  
最怕的是两边都想一次学全，结果既没有扎实主循环，也没有清楚控制面。

# 8.3 什么该学 Claude Code，什么该学 Codex

这部分不妨说得更硬一些。

优先学 Claude Code 的地方：

‧ query loop 的状态心智compact 与上下文治理‧ 工具编排与中断处理‧ 子代理生命周期和验证独立‧ 把失败路径当主路径设计优先学 Codex 的地方：

‧ instruction fragment 化  
‧ tool schema 化approval/policy 的显式表达  
‧ thread / rollout / state 的基础设施化  
‧ hook 事件和 skills 资产管理

这张表看上去像折衷，其实不是。它隐含着一个前提：你得先知道自己在学什么。学习的理由应该是那一块正好补你的短板，而不是因为别人已经做了。

如果把上一册里关于上下文治理的判断带进来，再看一些第三方 harness，就会更容易识别一种常见但代价很高的路线：它不是先把上下文拆成不同寿命、不同职责、不同入口成本的单元，而是先把大量 bootstrap 文件、技能说明、身份设定和工作区文本尽量塞进 prompt，再在快要溢出时靠截断、compact 和恢复链补锅。

这类系统表面上也有 memory、skills、compact，甚至也会做上限控制，但治理主轴仍然是“先注入，再抢救”。问题就在这里。上下文一旦主要靠堆叠文本来组织，token浪费只是第一层代价，更麻烦的是语义信号会被稀释：模型确实看到了很多东西，却不一定更清楚下一步该抓住哪一类工作语义。

如果拿一句话概括三条路线的差异，大概可以这样说：

Claude Code 更像把上下文当工作内存来经营，先想什么该保住，什么该压缩。

Codex 更像把上下文当结构化单元来治理，先想来源类型、作用域和状态承接。

OpenClaw 这一类系统则更像把上下文当 prompt 容器来扩容，先想还能再塞什么，超了再说。

这也是为什么很多团队一开始会觉得这种路线“信息更全”，但真到长会话、多代理和复杂任务时，往往会同时抱怨两件事：一是 token 烧得快，二是效果并没有随着上下文变胖而稳定提升。因为它解决的是装进去多少，不是继续工作时真正需要保住什么。

# 8.4 一个危险误区：把“显式”与“灵活”误认为天然对立

做系统的人经常有一种偷懒的对立法。

一说显式控制层，就觉得系统会太重、太慢、不灵活。

一说运行时灵活，就觉得可以先靠经验把事做起来，结构以后再说。

这两种想法都不高明。显式并不必然僵硬，灵活也不必然混乱。真正的问题在于，你有没有清楚地定义“哪些东西必须显式，哪些东西可以留给现场判断”。

Claude Code 的长处，不在于它排斥结构，而在于它知道哪些麻烦必须在运行时正面处理。

Codex 的长处，不在于它排斥灵活，而在于它知道哪些边界如果不先讲清楚，后面任何灵活都会变成争议。

真正好的第三种 harness，不该把两者折中平均，而应明确区分：

‧ 哪些规则必须先写死  
‧ 哪些判断可以留给运行时  
‧ 哪些状态必须持久化  
‧ 哪些经验只需要在会话内暂时保留

# 8.5 给后来者的一组顺序建议

如果要从零开始做一套 harness，我更倾向于推荐下面这个顺序：

1. 先定义高风险动作和最小权限模型  
2. 再定义主循环或线程生命周期  
3. 再定义上下文治理与恢复路径  
4. 再定义技能、本地规则与 hook  
5. 最后再扩多代理、平台化和复杂生态

这个顺序看起来不性感，但大致符合事故发生顺序。工程里很多设计顺序，应该按事故出现的先后排，而不是按演示时的好看程度排。

# 8.6 本章结论

这一章只想留下一句朴素的话：

学 Claude Code，主要是学如何让系统在现场稳定运行；学 Codex，主要是学如何让系统在组织里长久维持秩序。

谁只学前者，容易变成经验过强、制度不足。  
谁只学后者，容易变成制度漂亮、现场发虚。  
真正值得做的，是根据自己的主矛盾决定先长哪根骨头，而不是选边站。

# 附录 A 源码地图：这套比较主要依据哪些文件

这份附录只做一件事：说明各章判断主要基于哪些文件。它不是源码转载目录，也不意味着内容会提供相关源代码副本。

这里仍然保留同样的边界：

‧ 仅做必要的工程性引用和模块定位‧ 不附带 Claude Code 或 Codex 的实现正文‧ 不做大段源码转录

# A.1 Claude Code 侧主要依据

总体控制面与 prompt：

src/constants/prompts.ts src/utils/systemPrompt.ts src/utils/claudemd.ts src/memdir/memdir.ts

运行时循环与恢复：

src/query.ts   
src/QueryEngine.ts   
src/services/compact/autoCompact.ts   
src/services/compact/compact.ts

工具与权限：

# 附录 A 源码地图

‧ src/services/tools/toolOrchestration.ts src/services/tools/toolExecution.ts src/services/tools/StreamingToolExecutor.ts src/hooks/useCanUseTool.tsx src/tools/BashTool/prompt.ts src/tools/BashTool/bashPermissions.ts

多代理、skills、hooks：

‧ src/utils/forkedAgent.ts src/coordinator/coordinatorMode.ts src/tasks/LocalAgentTask/LocalAgentTask.tsx src/tools/SkillTool/SkillTool.ts src/tools/SkillTool/prompt.ts src/utils/hooks/hooksConfigManager.ts

# A.2 Codex 侧主要依据

# 核心模块骨架：

core/src/lib.rs‧ tools/src/lib.rsskills/src/lib.rs‧ hooks/src/lib.rsinstruction fragment 与用户注入：

‧ instructions/src/lib.rs instructions/src/fragment.rs instructions/src/user_instructions.rs ‧ docs/agents_md.md

工具、审批与执行策略：

‧ tools/src/local_tool.rs ‧ tools/src/agent_tool.rs

# 附录 A 源码地图

‧ execpolicy/src/lib.rs ‧ docs/execpolicy.md ‧ docs/sandbox.md

# 线程与状态：

sdk/typescript/src/thread.ts ‧ core/src/lib.rs core/src/thread_manager.rs core/src/rollout.rs core/src/state_db_bridge.rs core/src/message_history.rs

hook 事件引擎：

‧ hooks/src/engine/mod.rs

# A.3 各章对照

# 第 1 章：

‧ Claude Code 的 query.ts、toolOrchestration.ts‧ Codex 的 core/src/lib.rs

# 第 2 章：

‧ Claude Code 的 prompt assembly 与 CLAUDE.md‧ Codex 的 fragment.rs、user_instructions.rs

# 第 3 章：

‧ Claude Code 的 query loop / QueryEngine  
‧ Codex 的 thread.ts、thread_manager、rollout、state_db_bridge 暴露模块

# 第 4 章：

# 附录 A 源码地图

‧ Claude Code 的工具编排、Bash 限制、权限语义‧ Codex 的 tools/src/lib.rs、local_tool.rs、execpolicy/src/lib.rs

# 第 5 章：

‧ Claude Code 的 skill / hook / memory 体系‧ Codex 的 skills 体系、hooks engine

# 第 6 章：

‧ Claude Code 的 forked agent / verification 纪律‧ Codex 的 agent tool 集合、thread / rollout / state

# 第 7 章：

‧ 综合前述所有文件形成总判断

# 附录 B 检查清单：如何判断你的Harness 更像 Claude Code、Codex，还是半成品

比较如果不能落成检查清单，最后很容易只剩一些表述完整却难落地的判断。下面这份附录，就是把前面几章压成团队可直接讨论的清单。

# B.1 控制面清单

检查这些问题：

‧ 本地规则是作为自由文本拼装，还是作为带类型边界的 fragment 注入instruction 的来源、作用域和优先级能否说清楚prompt 中哪些部分是真控制面，哪些只是输出风格团队规则更像 CLAUDE.md 这类现场说明，还是更像 AGENTS.md 这类结构化制度入口

如果这些问题答不清，说明你的控制面还停留在“能用就行”的阶段。

# B.2 连续性清单

检查这些问题：

‧ 系统的连续性主要由主循环维持，还是由 thread / rollout / state 维持‧ 中断以后，谁来保证工具账本、消息序列和状态收口‧ 长会话膨胀时，是否存在明确 compact / truncation / recovery 机制‧ 线程 ID、会话索引和状态落地是否是系统一等概念

附录 B 检查清单

如果长会话主要靠模型自己“记得住”，那基本不用再往下看了。

# B.3 工具与审批清单

# 检查这些问题：

‧ 工具是运行时对象，还是 schema 化接口‧ 审批主要靠现场判断，还是有显式 policy / rule 体系‧ 危险工具是否有专门治理，而不是与普通读操作一视同仁‧ workdir、network、sandbox、approval 等执行边界能否被显式表达如果系统只能回答“我们也有权限控制”，那通常等于还没有真正设计权限控制。

# B.4 本地治理清单

# 检查这些问题：

‧ 本地规则能否按目录、团队、任务类型分层  
‧ skills 是不是可以被视为可复用制度切片，而不只是长 prompt  
‧ hooks 是否挂在明确生命周期事件上  
‧ skill / rule / hook 是否有版本、来源和触发边界

团队治理如果主要依赖口头说明，系统迟早会学会装懂。

# B.5 多代理与验证清单

# 检查这些问题：

‧ 多代理是为了并行，还是为了职责分离‧ 是否存在独立 verification 机制‧ 代理委派是否是显式工具或显式状态事件‧ 子代理失败、超时、取消以后，谁负责清理一个不能独立验证、不能明确收尾的多代理系统，通常只是把混乱并行化。

# B.6 你更像哪一类系统

更像 Claude Code 的信号：

‧ 你最重视 query loop、工具编排、中断、compact 与恢复‧ 你擅长让规则快速进入现场会话‧ 你更关心 agent 如何在复杂任务里持续运行

更像 Codex 的信号：

‧ 你最重视 instruction fragment、tool schema、approval policy、thread / roll‑out / state  
‧ 你擅长把本地规则做成结构化资产  
‧ 你更关心 agent 如何在组织里被长期治理

# 更像半成品的信号：

‧ 两边的名词都说得出来，但谁负责秩序说不清‧ 有很多能力入口，但没有清楚的恢复路径‧ 有很多规则文本，但没有作用域和优先级‧ 有多代理，但没有责任分离和收尾机制

# B.7 最后六问

要是时间不够，只问这六句：

‧ 谁拥有最终控制权，模型还是 harness  
‧ 连续性主要住在 loop 里，还是住在线程和状态里  
‧ 工具动手前，谁来拦最后一道  
‧ 本地规则怎么进入系统，怎么分层  
‧ 验证由谁负责，如何独立  
‧ 出事以后，团队靠什么追溯

这六句问下来，系统大概属于哪一派，通常也就露出来了。
---

> **来源文件：`book1/full.md`**

<table><tr><td></td><td>ET</td><td>tx</td><td>#</td></tr><tr><td>AXP</td><td>#</td><td>E</td><td>SYSTEM FIRST MODEL SECOND</td></tr><tr><td></td><td></td><td></td><td></td></tr></table>

# Harness Engineering

Claude Code 设计指南一个系统是否可靠，不在它会不会说，而在它出了岔子以后，谁来收拾残局。 O

CONTROL PLANE / QUERY LOOP / RECOVERY / VERIFICATION

# 从会用 Agent，到做出 Agent PoC

https://agentway.dev

# 目录

导读 1

序言 Harness 2

第 1 章为什么需要 Harness Engineering 5

1.1 问题在于让模型别乱来 5

1.2 Claude Code 的第一层 Harness：受约束的会话系统 5

1.3 第二层 Harness：代理依赖持续循环 6

1.4 第三层 Harness：工具调用必须服从调度 7

1.5 第四层 Harness：最危险的工具，必须配最细的规矩 7

1.6 第五层 Harness：错误属于主路径的一部分 8

1.7 从源码里可以提炼出的第一个原则 8

# 第 2 章 Prompt 不是人格 10

2.1 把 prompt 当成人设，是一种常见误会 10

2.2 从源码看，Claude Code 的 prompt 从一开始就是分层的 10

2.3 Prompt 的真正价值，不在文字本身，而在优先级 11

2.4 Prompt 不是静态文案，它还连接着记忆系统 . . 12

2.5 真正的控制平面，还要考虑缓存与计算成本 13

2.6 用户可以覆盖 prompt，但不能跳过这套结构 . . 13

2.7 为什么说 prompt 在这里更像宪法，而不是台词 14

2.8 从源码里可以提炼出的第二个原则 14

3 章 Query Loop 16

3.1 一个代理系统是否成熟，先看它有没有循环 16

3.2 状态属于主业务 16

3.3 Query loop 的第一职责是治理输入 . . . . 18  
3.4 调用模型只是循环的一段，不是循环本身 . . . . . . 19  
3.5 心跳必须处理中断，否则它就只是惯性 . . . . . . 19  
3.6 心跳还必须处理恢复，否则它只是脆弱的重复劳动 20  
3.7 停止条件不能只有一个，否则系统会把失败和完成混为一谈 . . . . 21  
3.8 QueryEngine 说明它属于会话生命周期 . . 21  
3.9 从源码里可以提炼出的第三个原则 . . 24

# 第 4 章工具、权限与中断 25

4.1 一旦模型开始调用工具，问题的性质就变了 25  
4.2 工具调度属于行为宪法的一部分 25  
4.3 运行一个工具，真正执行前已经发生了很多事 26  
4.4 权限先于能力：Claude Code 没把模型当有天然授权的人 . . . . 26  
4.5 权限结果本身也是一种运行时语义 . 27  
4.6 StreamingToolExecutor 说明中断是一等语义 . . . . . . . . 27  
4.7 Bash 为什么永远比别的工具更可疑 . . . 29  
4.8 工具系统真正保护的，不只是用户，还包括系统自己 . . . . 31  
4.9 从源码里可以提炼出的第四个原则 . . 31

# 第 5 章上下文治理

# 33

5.1 上下文一多，系统就容易产生一种低级幻觉 33  
5.2 CLAUDE.md 体系说明，长期指令不能和临场对话混在一起 . . . . . . . 33  
5.3 MEMORY.md 是索引，不是日记本 34  
5.4 Session memory 说明，短期连续性也不能靠聊天记录硬扛 . 35  
5.5 自动 compact 说明，上下文治理首先是预算治理 . . 36

5.6 compactConversation() 说明，摘要要重建可继续工作的上下文 36

5.7 上下文治理的关键是保留工作语义

5.8 从源码里可以提炼出的第五个原则

# 6 章错误与恢复 39

6.1 工程世界最不值得相信的话，就是“正常情况下” 39  
6.2 prompt too long 是一种必然周期 . 39  
6.3 响应式 compact 说明，恢复的关键在于别把自己逼进死循环 40  
6.4 max_output_tokens 的处理说明，恢复要以续写为主 41  
6.5 auto compact 的失败熔断，说明恢复系统自己也要受治理 . . . 41  
6.6 compact 自己也会爆，所以连“修复动作”都需要修复策略 . . . 42  
6.7 abort 语义说明，中断也属于错误恢复的一部分 42  
6.8 错误处理真正保护的，是执行叙事的一致性 . . 45  
6.9 从源码里可以提炼出的第六个原则 . . 45

# 第 7 章多代理与验证

# 47

7.1 单代理走到一定程度，问题就不再是“会不会做”，而是“怎么分工” 47  
7.2 forked agent 的第一原则是 cache‑safe . . . . . 47  
7.3 状态隔离说明，子代理首先要减少污染 . . . . . . . . . 48  
7.4 协调者模式说明，synthesis 才是稀缺能力 . . 49  
7.5 验证必须独立成阶段，否则“实现完成”很快就会冒充“问题解决” 49  
7.6 hooks 和任务生命周期说明，子代理不是扔出去就算了 . 50  
7.7 验证不仅针对代码，也针对记忆和建议 . . 52  
7.8 多代理真正解决的是不确定性的分区 . . . . . . . 52  
7.9 从源码里可以提炼出的第七个原则 . . . . . . . 53

# 第 8 章团队落地 54

8.1 个人顺手，不代表团队就能稳定复用 . . . 54  
8.2 团队第一步，是先把最低边界做清楚 . . 54  
8.3 CLAUDE.md 的价值，在于稳定、分层、少争议 . . . 55  
8.4 复用的重点，先是验证定义，再是 skill 数量 . . . . . 56  
8.5 skill 更适合作为工作流模块来理解 . . . 57  
8.6 approval 的重点，是按风险分层 . . . . . . . 57  
8.7 hook 是高级能力，通常不必作为第一步 . . . 58  
8.8 可复盘轨迹很重要，但要分清基线层和高阶层 . . . 59  
8.9 从源码里可以提炼出的第八个原则 . 60

# 第 9 章 Harness Engineering 十条原则 61

9.1 把模型当不稳定部件，不要当同事 . . . . 61  
9.2 Prompt 是控制面的一部分 . . 61  
9.3 Query loop 才是代理系统的心跳 . . . . 61  
9.4 工具是受管执行接口 62  
9.5 上下文是工作内存 62  
9.6 错误路径就是主路径 . . . 62  
9.7 恢复的目标是继续工作 62  
9.8 多代理的意义，是把不确定性分区 . . . 62  
9.9 验证必须独立，不能让系统自己给自己打分 62  
9.10 团队制度比个人技巧重要 . . 63  
9.11 最后一句话 . . . 63

# 附录 A 检查清单 64

A.1 Agent Runtime 设计清单 . 64  
A.2 Prompt 设计清单 64  
A.3 Tool 与 Permission 设计清单 65  
A.4 Context 治理清单 65  
A.5 Error Recovery 设计清单 66  
A.6 Multi‑Agent 设计清单 66  
A.7 Team 落地清单 66  
A.8 Review 问题单 . 67  
A.9 最后一个清单 67

# 附录 B 图示 68

B.1 图一：Claude Code 总体控制面 . 68  
B.2 图二：Query Loop 主循环与恢复分支 . . 69  
B.3 图三：Tool Batch Ordering 与 StreamingToolExecutor . . 70  
B.4 图四：Context Sources 与 Compact Rebuild 70  
B.5 图五：Coordinator‑Worker Flow 与 Verification Separation . . . 70  
B.6 图六：团队治理图 . . . 70

# 附录 C 源码地图

# 76

C.1 第 1 章为什么需要 Harness Engineering 76  
C.2 第 2 章 Prompt 是控制面，不是人格装修 77  
C.3 第 3 章 Query Loop：代理系统的心跳 77  
C.4 第 4 章工具、权限与中断 . 77  
C.5 第 5 章上下文治理：Memory、CLAUDE.md 与 Compact . . . . . . 78  
C.6 第 6 章错误与恢复 . . . 79  
C.7 第 7 章多代理与验证 . . . 79  
C.8 第 8 章团队落地 80  
C.9 第 9 章十条原则 80

# 导读

这本书关心的不是“模型会不会写代码”，而是“一个会写代码的模型被放进终端、仓库和团队流程以后，怎样才不会把系统带偏”。

这不是源码注释汇编，也不是产品功能介绍。它关注的是 Claude Code 如何把不稳定模型收束进可持续运行的工程秩序，让控制面、主循环、工具权限、上下文治理、恢复路径、多代理验证与团队制度组织成一套完整骨架。

本书有三个阅读前提：

‧ 重点不在模型能力，而在 harness 如何组织约束与执行‧ 重点不在函数逐条解释，而在运行时结构为什么必须呈现为这种形态‧ 重点不在个人技巧，而在这些结构怎样变成团队可以复用的制度

# 建议阅读顺序：

1. 序言 Harness、终端与工程约束2. 第 1 章为什么需要 Harness Engineering3. 第 2 章 Prompt 不是人格，Prompt 是控制平面4. 第 3 章 Query Loop：代理系统的心跳5. 第 4 章工具、权限与中断：为什么代理不能直接碰世界6. 第 5 章上下文治理：Memory、CLAUDE.md 与 Compact 是预算制度7. 第 6 章错误与恢复：出错后仍能继续工作的代理系统8. 第 7 章多代理与验证：用分工和验证管理不稳定性9. 第 8 章团队落地：把一个聪明工具变成可复用制度10. 第 9 章 Harness Engineering 十条原则11. 附录 A 检查清单：把原则落成能执行的约束12. 附录 B 图示：把运行时骨架画出来13. 附录 C 源码地图：本书各章主要依据哪些文件

如果只想先看总判断，可以直接跳到第 9 章。

# 序言 Harness、终端与工程约束

这些年，人们喜欢把会写代码的模型叫作智能体。这个词带着明显的乐观色彩，仿佛只要模型能读仓库、调工具、写出像样的 patch，它就可以在工程环境里独立行动。可工程环境有明确后果。终端、文件系统和 Git 历史都不是抽象空间，任何改动都会留下痕迹。

一个只会输出文本的模型，出错时主要带来理解成本。一个能运行命令、写文件、访问网络、修改仓库的模型，出错后留下的是执行结果。目录会变化，进程会中断，配置会损坏，历史会变得难以追踪。到了这一步，核心问题不再是模型是否足够聪明，而是系统是否提供了足够约束。

这本书讨论的，正是这种约束。

我把它叫作 Harness Engineering。这里的 harness 可以理解为一组持续生效的控制结构，用来约束模型在工程环境中的行为边界。对 AI coding agent 来说，没有约束的能力只会扩大事故半径。

这本书也不是一份 Claude Code 源码讲解。源码当然重要，但如果只沿着目录逐个解释，很容易写成注释汇编。那样的内容能说明函数做了什么，却未必能回答系统为什么必须呈现为现在这种结构。要理解 Claude Code 这类系统，光知道有 queryLoop()、compactConversation()、runTools() 还不够。更重要的问题是：为什么一个”会写代码”的系统，最终需要 prompt 分层、权限判定、状态机、compact、恢复分支、subagent 生命周期、verification 阶段和团队制度这些结构？

答案并不复杂，因为模型本身并不稳定。

这个判断未必讨喜，但工程系统不能依赖乐观叙事维持。一个部件如果本质上不稳定，系统就必须围绕这个事实设计；否则，问题只会在事故复盘里集中出现。

Claude Code 值得研究，因为它在实现上保持了明确的工程克制：

‧ 没有假定模型会持续正确，因此用 query loop 管理状态；  
‧ 没有假定工具调用天然安全，因此用权限和调度约束工具；  
‧ 没有假定上下文越多越好，因此引入 memory、CLAUDE.md、compact 和 sessionmemory；  
‧ 没有把错误视为偶发事件，因此为 prompt too long、max output tokens、中断和 hook 回环设计恢复路径；  
‧ 没有把多代理直接等同于更强能力，因此把 synthesis 和 verification 单独拆开，避免系统自我背书。

这一整套东西，合起来才是 agent。模型只是 agent 里最会说话、也最不稳定的那个部件。

所以这本书有一个始终不变的基本立场：

Prompt 决定它怎么说话，Harness 决定它怎么做事。

这里说的 harness，不是一层附属工具，也不是对模型能力的情绪化防御。它是模型进入工程环境的前提。缺少这层约束，风险最终会转移给用户、团队和未来的维护者。

这里也先说明一个边界：本书不会附带 Claude Code 源代码，也不会长篇逐段转录源码。原因很简单，就是版权边界。我们能做的，是在合理引用和工程分析的范围内，基于源码结构提炼设计原则、运行机制与方法论判断，而不是把受版权保护的实现文本重新发布一遍。

本书试图做两件事。

第一件，是基于 Claude Code 源码，把真正决定系统可靠性的结构讲清楚。重点在于解释为什么上下文治理必须成为主路径，为什么多代理解决的是职责分区，为什么团队制度必须纳入生命周期节点，而不是简单罗列“这里有 compact”“这里有 subagent”“这里有 hook”。

第二件，是把这些实现背后的判断提炼成更一般的工程原则。具体代码版本会变化，函数名会变化，产品形态也会变化。但只要大家还在尝试把不稳定模型接入真实工作流，某些原则就仍然有效。比如：

‧ 错误路径要按主路径设计  
‧ 验证必须进入完成定义  
‧ 权限是系统器官，而不是附属功能  
‧ 上下文是资源，不是垃圾桶  
‧ 多代理要靠角色分离，不靠人海战术  
‧ 团队制度比个人技巧重要

如果这些判断成立，那么 Claude Code 更适合作为一份样本。它的价值不在于教人复制一套一模一样的 CLI，而在于展示一个面向真实工程环境的 AI 代理，最终会如何走向更严格的约束结构。

更直接地说，这本书不讨论如何用模型包装出一个”像工程师”的幻觉，而讨论如何在模型并不具备工程师稳定性的前提下，仍然构造出一个可运行的工程系统。

这类工作通常不显眼。回滚、审批、权限、验证、compact、清理孤儿进程都不显眼，但系统能否长期稳定运行，往往取决于这些部分。过度追求”像人一样自然”的代理体验，其常见结果是系统具备了类似人的失误模式，却没有承担后果的能力。

既然如此，就从约束谈起。

接下来九章，讨论的都是这套 Harness 结构如何形成，为什么必须采用这种安排，以及一个团队如何把个人经验沉淀成可以复用的工程制度。

@wquguru   
2026.04.01   
Claude Code 源码泄漏的愚人节

btw. 您可以在 harness‑books.agentway.dev/book1‑claude‑code 访问在线版，获取更好的阅读体验

# 第 1 章为什么需要 HarnessEngineering

# 1.1 问题在于让模型别乱来

这些年，人们很喜欢谈智能体。这个词常常带着轻快的预期，仿佛只要模型会写几段代码、会调几个工具，就可以像见习工程师一样在终端里独立工作。可终端和文件系统都带有明确后果。一个会说话的概率分布，一旦能接触 shell、Git、网络和本地文件，问题就从”回答得不够好”变成”执行造成实际破坏”。

所以问题的重点，一直是怎样把它约束成一个可管理的系统。所谓 Harness Engineer‑ing，讨论的就是这件事。Harness 是一整套制度化的控制平面，用来处理一个很现实的问题：模型并不天然值得信任。

这个判断未必轻松，但通常有用。一个代理系统要进入真实工程环境，首先要承认自己的核心部件是不稳定的。忽视这一点，问题最后通常会在日志和事故记录里出现。

# 1.2 Claude Code 的第一层 Harness：受约束的会话系统

如果只看表面，Claude Code 像一个能和用户对话、还能顺手改代码的 CLI。可从实现上看，它一开始就没有把自己当成“裸模型接口”来设计，而是当成一个带有上下文边界、运行时状态和行为规约的会话系统。

这一点从 system prompt 的组织方式就能看出来。

‧ 在 src/constants/prompts.ts:175 开始，系统先定义身份和总任务。‧ 在 src/constants/prompts.ts:186 开始，补上关于工具、权限、系统提醒和上下文压缩的系统级说明。‧ 在 src/constants/prompts.ts:199 开始，再补上做任务时的工程约束，比如不要越权改动、不要把验证说成已经完成、不要为了省事发明抽象。

这里值得停一下。很多人谈 prompt，还停留在“你是一个什么样的助手”这种修辞层面。Claude Code 在实现上把 prompt 放进了运行时控制结构里，这些文字用来规定执行边界、失败行为和报告责任。

更重要的是，这个 prompt 采用分段拼装方式。在 src/constants/prompts.ts:444的 getSystemPrompt() 里， 静 态 部 分 和 动 态 部 分 被 明 确 拆 开，memory、lan‑guage、output style、MCP instructions、scratchpad 等内容按段注入。到了src/utils/systemPrompt.ts:28，系统又把默认 prompt、自定义 prompt、agentprompt 和 append prompt 组织成一套优先级规则。

这说明了一个朴素的工程事实：一个真正可用的代理系统，不能依赖一段“万能提示词”解决所有问题。它必须把控制拆成层，把层次拆成职责。否则，新增提醒和禁令很快就会互相冲突，系统行为也会变得难以预测。

# 1.3 第二层 Harness：代理依赖持续循环

如果说 prompt 规定了它应该成为什么样的东西，那么 query loop 规定了它实际上如何运行。

Claude Code 的核心不在某个单独的 API 调用，而在 src/query.ts:219 开始的query()，以及 src/query.ts:241 开始的 queryLoop()。这段实现里最重要的一点，是它明确承认代理系统依赖带状态的多轮执行。

在 src/query.ts:268，系统把 messages、toolUseContext、autoCompactTrack-ing、maxOutputTokensRecoveryCount、hasAttemptedReactiveCompact、pend-ingToolUseSummary、turnCount、transition 等内容放进同一个跨迭代状态里。一个会话系统一旦这样设计，就等于正式承认：上一轮留下的问题会进入下一轮，系统必须有能力继续处理。

这是 Harness 思维的核心。真正的问题在于系统能不能在连续多轮里保持行为一致：

‧ 有没有预算概念  
‧ 有没有恢复概念  
‧ 有没有上下文膨胀后的自救机制  
‧ 有没有在工具调用失败后继续推进任务的能力

缺少这些结构，所谓智能体就只是一个不稳定的执行者。

在 src/query.ts:365 往后，这个循环还会在每轮调用前处理消息裁剪、tool resultbudget、history snip、microcompact、context collapse、autocompact 等内容。

实现细节虽然很多，但共同指向一点：Claude Code 在调用发生前就尽量把控制权收回到运行时一侧。

这也是为什么 Harness Engineering 不能被看作 prompt engineering 的附属品。前者关心状态机，后者关心措辞。措辞当然重要，但状态机决定系统行为最终由谁负责。

# 1.4 第三层 Harness：工具调用必须服从调度

一个模型如果只能输出文本，顶多让人觉得它有时说得太满。可一旦它能调用工具，系统风险就立刻从修辞风险变成执行风险。这时候最重要的问题是：谁决定工具怎么跑。

Claude Code 给出的答案很直接。运行时会根据工具属性决定并发还是串行。

在 src/services/tools/toolOrchestration.ts:19 的 runTools() 里，工具调用先经过 partitionToolCalls() 分组。到了 src/services/tools/toolOrchestration.ts:9系统会读取工具 schema，并调用 isConcurrencySafe() 判断一个工具是否适合并发执行。能并发的归成一批，不能并发的按顺序一个个来。并发路径里，context modifier 会先缓存，再按原始 block 顺序回放，见 src/services/tools/toolOrchestration.ts:31到 :63。

这件事很有代表性。它说明 Claude Code 没有把工具当成模型能力的自然延伸，而是当成需要调度纪律的受管执行单元。缺少调度纪律的工具系统，只会把模型的不稳定性放大到外部世界。

并发如果不受约束，就会扩大事故半径。Claude Code 在这里采取了偏保守的策略。在会碰到文件、终端和权限的场景里，这种保守通常更可靠。

# 1.5 第四层 Harness：最危险的工具，必须配最细的规矩

在所有工具里，Bash 最值得警惕。因为它几乎不受领域边界约束，可以直接接触文件、进程、网络和 Git 仓库，还会带上重定向、管道等复杂 shell 语义。一个系统如果对 Bash过度信任，后果通常会很具体。

Claude Code 对 Bash 的态度，可以在 src/tools/BashTool/prompt.ts:42 往后看得很清楚。这里写了一整段操作规约，尤其是围绕 git 和 PR 的那部分：不要乱改git config，不要跳过 hooks，不要随手 git add .，不要在 pre‑commit 失败后用--amend 把上一条提交也搭进去，不要在没有明确要求时提交，更不要默认 push。

写到这个地步，有人会觉得它过于细碎。但高风险接口通常就需要高密度约束。Bash 一旦进入真实工作流，很多规则都必须明确写出来。

Harness Engineering 的一个重要原则，就是把高风险能力包装成高约束能力。能力越强，控制越细。原因很简单：外部世界不会因为模型语气坚定，就自动原谅一次错误执行。

# 1.6 第五层 Harness：错误属于主路径的一部分

很多软件把失败路径看成例外，把成功路径看成正文。代理系统不能这样做。因为代理系统的失败不是偶发性的，它是一种稳定存在。模型会超 token，会触发 prompt toolong，会撞上 max_output_tokens，还会遇到工具拒绝、用户打断、hook 阻塞、API重试等各种中断。要是这些情况都只在最后用几个 catch 打发一下，那系统表面上在运行，实际上只是不断把麻烦往后滚。

Claude Code 在 query loop 里没有这样处理。光看 src/query.ts:453 往后关于autocompact 的处理，以及 src/query.ts:592 往后对上下文上限和阻断逻辑的注释，就能看出它把失败当作会持续发生的结构性条件来处理。

这也是 Harness 和普通助手的重要差别之一。普通助手常见的设计逻辑是先回答，错了再道歉。Harness 更强调先约束，再执行；即使出错，也要按恢复路径处理，而不是靠临场发挥补救。

一个会道歉的系统，不一定成熟。一个知道何时不该开始、何时该重试、何时该中止、何时该准确汇报失败的系统，才更接近成熟。

# 1.7 从源码里可以提炼出的第一个原则

到这里，第一章其实只想说一件事：

代理系统的关键能力是约束执行。

Claude Code 的源码在几个关键位置都指向同一个结论：

constants/prompts.ts 说明 prompt 是控制平面的一部分，而不是人格装饰utils/systemPrompt.ts 说明系统行为必须有清楚的分层优先级query.ts 说明代理运行依赖持续的循环状态，而不是单次问答services/tools/toolOrchestration.ts 说明工具调用必须服从调度纪律‧ tools/BashTool/prompt.ts 说明高风险工具必须伴随高密度约束

把这些放在一起看，就会发现 Harness Engineering 并不神秘。它只是坚持几条常被忽视的工程常识：

‧ 模型会犯错  
‧ 工具会扩大错误后果  
上下文会膨胀  
‧ 状态会污染下一轮  
‧ 用户会打断你  
‧ 失败会反复出现

既然如此，系统就不能靠“聪明”维持秩序，只能靠结构维持秩序。结构不像聪明那样显眼，但通常更可靠。

下一章要谈的，是这套结构里最容易被误解的一层：system prompt。很多人把它看成人设文本，本书会说明它更接近操作系统里的规章制度。人设可以改善观感，规章才能约束机器。

# 第 2 章 Prompt 不是人格，Prompt 是控制平面

# 2.1 把 prompt 当成人设，是一种常见误会

很多人一说起 system prompt，首先想到的是一段熟悉的话术：你是谁，你擅长什么，你应该温柔、专业、简洁，最好再有一点稳定的人格。对于只负责聊天的系统，这种理解倒也够用；但对一个要读文件、调工具、动 shell、处理权限、跨轮执行的代理系统来说，这种理解明显不够。

原因很简单。人设描述解决的是“它像什么”，控制平面解决的是“它能做什么、什么时候做、做错了怎么办、谁来兜底”。两者不在同一层。一个系统可以有讨人喜欢的人设，同时在执行层面缺少规矩。那种系统出事时往往会显得很真诚，因为它很会道歉。但道歉并不能替代运行时设计。

Claude Code 的实现恰好说明了这一点。它的 system prompt 是一组分层拼装的行为区块。换句话说，这里的 prompt 更接近一套运行时协议，而不是一篇人物小传。

# 2.2 从源码看，Claude Code 的 prompt 从一开始就是分层的

在 src/constants/prompts.ts:444 的 getSystemPrompt() 里，Claude Code 返回的是一个由多个 section 组成的数组，而不是一段完整字符串。这个细节很重要。因为一旦 prompt 变成多个块，系统就正式承认它内部包含一组职责不同的约束。

这些 section 至少包含几类东西。

首先是身份和总任务说明。在 src/constants/prompts.ts:175，系统说明自己是一个交互式代理，要用可用工具帮助用户完成软件工程任务。这里同时嵌入了一些安全约束，比如不要乱猜 URL。

然后是系统级规则。在 src/constants/prompts.ts:186 开始，系统明确规定：

‧ 用户能看见的是哪些文本  
‧ 工具调用可能触发权限审批  
‧ 用户拒绝后不能机械重试  
‧ tool result 和 user message 里可能混入 system‑reminder  
‧ 上下文会被自动压缩

这些内容有一个显著特征：它们并不关心模型“像不像一个聪明助手”，而是关心它是否是一个守规矩的执行体。这就是控制平面的语气，它的核心任务是定义边界。

再往下，在 src/constants/prompts.ts:199 开始，是做任务时的工程性指令：不要随意增加需求，不要越权优化，不要为了让结果显得完整而隐瞒验证失败，不要在没有必要时制造抽象。这些内容看起来像写作风格要求，其实它们和工程约束绑得很紧。一个会自动“顺手优化一切”的模型，从产品角度看也许很热情，从工程角度看则相当危险。

所以，从源码结构上就能看出来：Claude Code 的 prompt 要解决的是如何让模型在复杂运行时里遵守边界。

# 2.3 Prompt 的真正价值，不在文字本身，而在优先级

如果 prompt 只是写在那里，还不够说明问题。真正决定它是否属于控制平面的，是系统是否给它定义了严格优先级。

这一点可以看 src/utils/systemPrompt.ts:28 开始的 buildEffectiveSystem-Prompt()。这段代码把 prompt 的来源明确排成一条链：

1. override system prompt   
2. coordinator system prompt   
3. agent system prompt   
4. custom system prompt   
5. default system prompt

最后还会统一拼接 appendSystemPrompt。

这个设计很说明问题。它表明 Claude Code 并不相信“默认 prompt 一劳永逸”。相反，它承认系统里存在多种语境：

‧ 协调者模式需要自己的系统行为‧ agent 模式需要自己的职责说明‧ 用户可以通过 CLI 覆盖或追加 prompt‧ 默认 prompt 只是没有更高优先级时的基线更朴素地说，成熟系统不会迷信唯一版本的 prompt。它会把 prompt 看成一个有层级的配置系统，让不同职责在不同上下文里生效。

这里还有一个很值得注意的细节。在 src/utils/systemPrompt.ts:99 往后，系统对 proactive mode 做了特殊处理：如果 agent prompt 和 proactive mode 同时存在，agent prompt 不再替换默认 prompt，而是附加在默认 prompt 之后。这个决定本身就很说明问题。它意味着系统知道，有时候默认约束不能丢，新增 agent 只能在默认约束之上叠加领域行为，而不能把整套纪律换掉。

可以把它理解为一套通用制度外加岗位说明书。岗位说明书可以补充职责，但不能直接冲掉底层制度，否则系统很快就会各自为政。

# 2.4 Prompt 不是静态文案，它还连接着记忆系统

如果说前面这些内容已经像一套运行时说明书，那么看到 Claude Code 如何处理 mem‑ory 和 CLAUDE.md 后，就会更清楚地意识到：这里的 prompt 已经是整个上下文治理入口，而不只是“写给模型看的一段话”。

在 src/utils/claudemd.ts:1153 的 getClaudeMds() 里，系统会把 project in‑structions、local instructions、team memory、auto memory 等不同来源的内容整理成统一格式，再拼接进 prompt 相关上下文中。这里连每种内容的来源说明都写得很细，比如这是项目级指令、用户私有项目指令、共享 team memory，还是跨会话持久化的 auto memory。

而在 src/memdir/memdir.ts:187 开始的 buildMemoryLines() 里，系统连“如何保存记忆”这件事都变成了 prompt 的一部分。它会明确告诉模型：

‧ memory 是文件化持久系统  
‧ MEMORY.md 是索引，不是正文要如何写 frontmatter  
‧ 哪些信息不该保存  
‧ plan 和 task 不该被误用成 memory

这件事非常关键。它把 prompt 的职责从“约束当前行为”扩展到了“约束未来知识的沉淀方式”。这已经超出了通常意义上的提示词，更接近一份写给运行时参与者的知识治理协议。

换句话说，Claude Code 不只是用 prompt 规定“这一轮怎么说话”，还用 prompt 规定“长期记忆如何形成”。一个系统只要走到这一步，它的 prompt 就不可能再只是语气问题，而必然进入制度问题。

# 2.5 真正的控制平面，还要考虑缓存与计算成本

多数人理解 prompt 时，很少会想到性能。常见想法是 prompt 只是喂给模型的文本，写好即可。Claude Code 的实现更务实：prompt 同时也是计算成本。它越复杂、变化越频繁，缓存命中就越差，系统运行就越贵、越慢。

在 src/constants/systemPromptSections.ts:16 往后，系统把 prompt section区分成两类：

‧ 可缓存的 systemPromptSection‧ 会打破缓存的 DANGEROUS_uncachedSystemPromptSection而 resolveSystemPromptSections() 会优先从缓存里拿已经计算过的内容，只在必要时重算。到了 clearSystemPromptSections()，系统又会在 /clear 或 /compact之后清空这些状态。

这件事看起来像优化，实际上同样属于控制平面。一个真正可运行的 prompt 系统，不可能只考虑表达能力，而不考虑它对吞吐、延迟和缓存的影响。Claude Code在 getSystemPrompt() 里甚至把静态部分和动态部分用 boundary 显式分开，见src/constants/prompts.ts:560 往后。这说明它在设计时已经承认：有些内容在会话中相对稳定，有些内容会逐轮变化，二者不能混在一起消耗缓存。

一个工程系统只要开始关心“哪部分 prompt 会导致缓存失效”，它就已经不再把prompt 当作文案创作。文案追求完整表达，控制平面追求可治理、可复用、可预测的行为成本。两者关注的问题不同。

# 2.6 用户可以覆盖 prompt，但不能跳过这套结构

Claude Code 并没有把用户锁死在默认 prompt 上。相反，CLI 明确支持覆盖和追加。

在 src/main.tsx:1342 往后，系统处理 --system-prompt、--system-prompt-file、--append-system-prompt、--append-system-prompt-file 这些选项。也就是说，用户当然可以带着自己的规约来。

但这里有个关键点。系统虽然允许覆盖和追加，却仍然坚持用统一的 buildEffec-tiveSystemPrompt() 做最终装配。这说明它允许自定义，但不放弃秩序。用户可以改内容，系统仍然保留结构。

没有结构的可定制，最后往往会退化成另一种随意。今天加一段，明天减一段，后天某个 agent 又替换掉基线约束，系统行为就会越来越像临时口头通知。Claude Code 的选择是让用户修改，但修改必须发生在既定优先级和分层机制里。

# 2.7 为什么说 prompt 在这里更像宪法，而不是台词

如果把前面各节放在一起看，可以得到一个相当明确的结论：

Claude Code 的 prompt 更像宪法。

所谓台词，是给角色在场上说的；所谓宪法，是规定权力边界、责任关系和例外情况如何处理。Claude Code 的 prompt 更接近后者，因为它满足了几个结构条件：

‧ 它分层，而不是一块写到底  
‧ 它有优先级，而不是谁后写谁说了算  
它与 memory、CLAUDE.md、agent instructions、MCP instructions 一起组成完整控制平面  
‧ 它有缓存和动态 section 机制，不是随手拼一段文本  
‧ 它和 runtime 紧密耦合，而不是游离于系统之外的装饰物

这也是为什么“写一个好 prompt”单独拿出来时价值有限。更重要的问题是：prompt在系统里处于什么位置，它和哪些模块配合，它是否参与权限、状态、上下文和长期记忆的治理。如果不回答这些问题，所谓好 prompt 往往只是在某个顺利场景里暂时成立。

# 2.8 从源码里可以提炼出的第二个原则

这一章最后可以归纳成一句话：

Prompt 的价值，在于它是否被纳入一套清楚的控制结构。

Claude Code 的源码在几个地方共同证明了这一点：

constants/prompts.ts 把 prompt 写成分段控制结构，而不是一段统一宣言utils/systemPrompt.ts 明确规定了 prompt 来源的优先级utils/claudemd.ts 把项目级和长期记忆内容纳入上下文装配memdir/memdir.ts 用 prompt 规定了长期记忆的保存规则constants/systemPromptSections.ts 则把 prompt 进一步变成可缓存、可失效、可按段重算的运行时对象

所以，一个成熟代理系统里的 prompt，不该被理解成“让模型入戏的开场白”。它更像一套运行中的制度文本。制度文本当然也可以写得清楚，但最重要的部分始终是约束力。

下一章要讨论的，是另一根更硬的骨头：query loop。因为再好的控制平面，最后都要落到执行循环里。prompt 规定边界，循环决定命运。一个系统最终会成为什么样子，往往体现在它每一轮如何继续、如何中断、如何恢复的那套状态机里。

# 第 3 章 Query Loop：代理系统的心跳

# 3.1 一个代理系统是否成熟，先看它有没有循环

如果把一个会写代码的模型看成代理系统，最容易犯的错误，就是把它想象成一个加强版问答接口。用户发来一句话，模型输出一个结果，事情就算办完。这种想法并非毫无来由，因为很多大模型产品确实这样工作。但只要系统开始调用工具、跨轮执行、处理中断、保存状态、重试失败、压缩上下文，这种“一问一答”的理解就会迅速失效。

Claude Code 的实现没有犯这个错误。它从结构上明确承认：代理依赖一段持续的、有状态的执行过程。

这一点在 src/query.ts:219 的 query() 和 src/query.ts:241 的 queryLoop()里表现得很明显。前者只是壳，真正重要的是后者。queryLoop() 不是把模型调用包在一个 try/catch 里就结束。它维护了一套跨迭代状态，先处理一系列前置治理动作，然后进入模型流式阶段；等模型返回后，再决定是进入工具执行、恢复、压缩、继续下一轮，还是直接终止。

这意味着 Claude Code 的核心是维持一个会话内的执行秩序。这里的关键名词是 life‑cycle。一个系统是否能被称为 agent，往往不取决于它会不会说，而取决于它能不能在几轮之后仍然知道自己在做什么。

# 3.2 状态属于主业务

很多系统在设计之初，都倾向于把状态看成包袱，仿佛无状态才更优雅。对代理系统来说，这种偏好作用有限。只要它进入真实工作流，状态就会自然出现。忽视状态，并不能消除状态，只会让它以更难管理的方式返回。

Claude Code 在这里的态度很直接。在 src/query.ts:203 到 :217，系统把 queryloop 的可变状态定义得很清楚：

![](images/260eb1d501cdf6c0c3bb0d255f0fcc0c93e3a3dc06d6f42fadaac77cdd545fac.jpg)  
图 1: Claude Code Query Loop Core

‧ toolUseContext   
‧ autoCompactTracking maxOutputTokensRecoveryCount hasAttemptedReactiveCompact pendingToolUseSummary stopHookActive turnCount   
transition

到了 src/query.ts:268，这些状态在每次 query loop 启动时被整体装配成一个State 对象，并在后续各个 continue 分支里整体更新。

这一点很重要。Claude Code 没有把恢复、压缩、预算、hook、turn 计数散落在局部变量和布尔开关里，而是承认它们共同构成了“本轮结束后下一轮如何继续”的基础。它把状态当作心跳的一部分。

这就是成熟代理系统和一次性脚本的区别。脚本只关心这一步有没有跑完，代理系统还要关心：这一步失败之后，下一步能不能继续承接前面留下的状态。

# 3.3 Query loop 的第一职责是治理输入

从外部看代理系统，很多人会以为它的核心动作是“调用模型”。但在工程上，真正重要的常常是模型调用之前那一长串整理工作。Claude Code 在 queryLoop() 里把这件事写得很清楚。

在正式进入模型流之前，系统会先做这些事：

‧ 启动相关 memory 的预取，见 src/query.ts:297  
‧ 预取 skill discovery，见 src/query.ts:323  
‧ 截取 compact boundary 之后的有效消息，见 src/query.ts:365  
应用 tool result budget，见 src/query.ts:369  
‧ 进行 history snip，见 src/query.ts:396  
‧ 进行 microcompact，见 src/query.ts:412  
‧ 进行 context collapse，见 src/query.ts:428  
‧ 最后才尝试 autocompact，见 src/query.ts:453

这串顺序本身就是一种架构声明。它告诉读者，Claude Code 把“上下文治理”放在“模型推理”之前。也就是说，它不把从混乱中整理秩序的责任交给模型，而是先由运行时完成治理，再把更干净的输入交给模型。

这件事很重要，因为很多系统恰恰相反：先把大量上下文塞进去，再寄希望于模型自己判断什么重要，什么不重要。那种做法看似省事，实际上是在把运行时应承担的责任转嫁给概率分布。

Claude Code 的做法更接近传统工程流程：先整理现场，再开始执行。它不追求潇洒，但通常更稳妥。

# 3.4 调用模型只是循环的一段，不是循环本身

等前面的治理工作都做完，Claude Code 才进入模型调用阶段。这个阶段出现在src/query.ts:652 往后。这里有个值得专门指出的细节：系统会进入 for await 流式消费模型输出，而不是同步拿一个完整结果回来。

这意味着模型输出在 Claude Code 里是一串事件流，而不只是“最终答案”。事件里可能包含：

‧ assistant 文本 ‧ tool_use block usage 更新 stop reason ‧ API 错误

这一点在 src/query.ts:826 往后尤其明显。系统会把 assistant message 存起来，提取其中的 tool_use block，决定是否需要 follow‑up，还可能边流边把工具送给StreamingToolExecutor。

从工程角度看，这是一种根本性的变化。一旦把模型输出当成事件流，系统架构就不再只是“请求‑响应”，而更像“驱动‑调度‑反馈”的过程。流式输出的意义，也不只是更早看到几个字，而是允许运行时在模型尚未完全结束之前，就开始安排下一步执行。

这也是为什么前面说 query loop 才是代理系统的心跳，而不是模型调用本身。模型调用只是心跳中的一次收缩，真正维持系统运行的是整套循环：输入如何收进来，流如何消费，工具如何调度，失败如何恢复，何时继续下一轮。

# 3.5 心跳必须处理中断，否则它就只是惯性

一个真正的心跳，不只是能持续跳动，还必须能在必要时停下来。停不下来，系统就只剩惯性。

Claude Code 对中断的处理写得很实在。在 src/query.ts:1011 往后，系统会优先处理 streaming abort。如果启用了 streamingToolExecutor，就必须先消费剩余结果，生成 synthetic tool_result，避免已经发出的 tool_use 没有配套结果；否则，就用 yieldMissingToolResultBlocks() 主动补全中断说明。

这背后有一个很基础的工程原则：只要系统向外承诺了一段执行，就要在中断时把账补平。不能因为用户打断了，就假装前面的几个 tool_use 从未发生。外部系统、UI 和transcript 都需要一致的因果链，哪怕结果是“中断了”，也必须中断得完整。

这件事之所以重要，是因为代理系统一旦进入多工具、多轮次状态，外部世界对它的要求就不只是“有没有最终答案”，而是“它留下的轨迹能不能被解释”。不能解释的执行轨迹，迟早会变成运维问题、审计问题，或者变成团队里谁也说不清楚的长期隐患。

所以，处理中断是 runtime 的基本责任。已经开始的动作需要有交代，哪怕交代的是“没做完”。

# 3.6 心跳还必须处理恢复，否则它只是脆弱的重复劳动

如果说中断是外部世界打进来的意外，那么恢复就是系统内部预留的余量。没有恢复能力的循环，不管表面多整洁，最后都会暴露出同一个问题：它把幸运当成了设计。

Claude Code 对恢复的处理是层层递进的，而不是简单重试。最典型的是 prompt‑too‑long 和 max‑output‑tokens。

在 src/query.ts:1065 往后，系统会先判断最后一条 assistant message 是否是被withheld 的 prompt too long。如果是，先试图让 context collapse 把积压的 collapse提交出去（见 :1086 到 :1116）；如果还不够，再进入 reactive compact（见 :1119到 :1166）。换句话说，系统会按成本和破坏性从低到高，逐层尝试恢复。

对 max_output_tokens 的处理也一样。在 src/query.ts:1185 往后，系统先尝试提升 token cap；如果还不行，再生成一条 meta message，让模型从被截断处继续往下做，而不是先道歉、先总结、先写一段漂亮的空话。

这很能说明 Claude Code 的设计态度。它把恢复看成运行时主路径的一部分，而不是模型失败后的礼貌动作。恢复的意义，在于给系统一个继续工作的机会。在真实工程里，继续工作通常比维持表面上的礼貌更重要。

# 3.7 停止条件不能只有一个，否则系统会把失败和完成混为一谈

普通问答系统的停止条件比较简单：有回答就结束。代理系统不能这么偷懒。因为一个会话里，出现“当前轮结束”并不等于“任务完成”，更不等于“系统成功”。

Claude Code 的 query loop 至少区分了这些情况：

‧ streaming 正常完成但有 tool_use，需要 follow‑up  
‧ 没有 tool_use，进入 stop hooks 和可能的后续判定  
‧ 被用户中断  
‧ 触发 prompt‑too‑long 恢复  
‧ 触发 max‑output‑tokens 恢复  
‧ stop hook 阻塞导致重进循环  
‧ API 错误直接返回

这可以从 src/query.ts:1062 往后一直看到 :1305。尤其是 stop hooks 那段，在:1267 到 :1305，系统不仅处理 hook，还专门防止“compact 后仍然太长，再被 hook阻塞，再继续 compact”的死循环。

这个地方很值得注意。许多系统只有一种朴素想法：失败了就重试。Claude Code 则承认，重试本身也是一种需要被管理的行为。系统必须知道为什么重试、已经试过什么、哪些保护状态不能被重置、哪些情况会导致无限循环。正是这些判断，把一个“会继续试”的系统和一个“知道什么时候不该再试”的系统区分开了。

# 3.8 QueryEngine 说明它属于会话生命周期

如果 queryLoop() 还不足以说明问题，那么 QueryEngine 的存在就更直接了。

在 src/QueryEngine.ts:176 开始，源码明确写着：

QueryEngine owns the query lifecycle and session state for a conver‑ sation.

这句话已经把整章的重点说得很明确。QueryEngine 管理的是一个 conversation 的query lifecycle，而不是某一次调用。src/QueryEngine.ts:180 还专门说明：一个QueryEngine 对应一个 conversation，每次 submitMessage() 都是在同一个 con‑versation 里开启新一轮 turn，状态会持续保存。

# Chapter 3 · QueryEngine Turn Flow

![](images/04a1d5fb63a1631a7ddab41e14e9efd30bc5acf05dd167c52af25fe332e08984.jpg)  
图 2: Claude Code QueryEngine Turn Flow

# Chapter 3 $\bullet$ QueryEngine State Carry-Over

![](images/9dac7eda351b306aceab44a4aaeaaef3805dfbeef5b9169ef7060fe2579fe8ca.jpg)  
图 3: Claude Code QueryEngine State Carry‑Over

到了 src/QueryEngine.ts:675 往后，QueryEngine 把准备好的 messages、sys-temPrompt、userContext、systemContext、toolUseContext 一起交给 query()，再把 assistant、user、compact boundary 等消息写回 transcript。

这说明 query loop 是会话系统真正的执行中心。外层的 UI、SDK、session persistence都围着它转。要理解 Claude Code 的设计，不能只看它有哪些工具，也不能只看它prompt 写了什么，最终还是得看这个循环如何把前面的约束落实成连续行为。

# 3.9 从源码里可以提炼出的第三个原则

这一章最后可以收敛成一句话：

代理系统的核心能力，是维持可恢复的执行循环。

Claude Code 的源码在几个关键点共同支持这个判断：

query.ts 用显式 State 管理跨轮执行状态，而不是把一切寄托在局部变量上  
‧ 模型调用前有大段输入治理逻辑，说明运行时先于推理  
流式消费把模型输出当事件流，而不是当最终文案中断路径会补齐 synthetic tool_result，说明系统关心因果闭环prompt‑too‑long、max‑output‑tokens、stop hooks 都走明确恢复分支，说明失败是主路径的一部分  
‧ QueryEngine.ts 明确把 query lifecycle 当作 conversation 的所有权对象

这意味着一个成熟 agent 的“心跳”至少要满足几个条件：

‧ 它有明确的跨轮状态  
‧ 它能治理输入，而不只是被动消费输入  
‧ 它能流式地承接模型输出  
‧ 它能补齐中断后的执行账本  
‧ 它能区分完成、失败、恢复和继续

缺少这些结构的系统，也许仍然能做出漂亮 demo，但它们更接近一次性表演，而不是运行时。表演当然有价值，只是不能替代秩序。

下一章要讨论的，是这套心跳最直接碰到外部世界的地方：工具、权限与中断。前面这一章解释了循环为什么存在，下一章要继续说明，循环一旦拥有工具，为什么必须学会克制。

# 第 4 章工具、权限与中断：为什么代理不能直接碰世界

# 4.1 一旦模型开始调用工具，问题的性质就变了

只会输出文本的模型，出错时主要增加沟通成本。它说错了，可以不信；它总结得糟，可以重问。可一旦模型开始调用工具，问题的性质就变了。因为工具不是意见，工具是动作。动作会留下结果，结果会接触真实世界。

这件事在 shell 上最容易看清。一个模型如果把一段解释写错了，影响通常还停留在理解层面；可要是它运行了一条不该运行的命令，文件会被删掉，进程会被中止，Git 历史也会变得难以收拾。能力增强往往伴随后果增强。

所以，工具系统最重要的问题是：谁来约束这些工具。Claude Code 对这个问题的回答，是把工具变成受管执行接口，避免让模型直接伸手去碰世界。

# 4.2 工具调度属于行为宪法的一部分

Claude Code 在 src/services/tools/toolOrchestration.ts:19 的 run-Tools() 里，先做了一件很有代表性的事情：不直接执行一串 tool_use，而是先按并发安全性分批。

在 src/services/tools/toolOrchestration.ts:91 的 partitionTool-Calls() 里，系统会先读取工具的 inputSchema，再调用 isConcurrencySafe() 判断这类调用是否适合并发。如果适合，就把它们归入并发批次；如果不适合，就拆成串行单元。

这看上去像性能优化，实际更接近一致性设计。一个工具系统一旦允许并发，就必须回答一个老问题：上下文变化由谁决定、按什么顺序生效。Claude Code 在并发路径里没有让最先完成的工具抢先改上下文，而是在 toolOrchestration.ts:31 到 :63 先缓

# 第 4 章工具、权限与中断

存 contextModifier，再按原始 block 顺序回放。也就是说，即便执行是并发的，语义上的上下文演化仍然保持确定顺序。

这是一种典型的工程保守。它的前提是：并发可以提高吞吐，但不能破坏因果秩序。工具如果只会跑得更快，却不能保证上下文一致性，就会替系统制造另一种随机性。

成熟代理系统不会迷信并发。它会把并发当成需要证明自身无害的例外，而不是默认自由。Claude Code 在这里显然把问题扩散速度考虑得很充分。

# 4.3 运行一个工具，真正执行前已经发生了很多事

很多人以为tool_use一旦出现，下一步自然就是执行。Claude Code 的实现说明，真正靠谱的系统不会这么草率。

在 src/services/tools/toolExecution.ts:30 之后，runToolUse() 所依赖的执行逻辑，已经把 permission、hooks、telemetry、synthetic error materialization 等能力接进来了。即使不追每个细节，只看整体结构也能发现：工具执行在 Claude Code里是一段完整的流程，包含：

‧ 前置校验‧ 执行中事件执行后修正‧ 失败补偿

这说明工具在这里的地位，和普通库函数并不一样。库函数默认属于程序内部，调用者自己承担后果；工具则属于模型与外部世界之间的接口，所以系统不能假设调用者具备稳定判断。换句话说，工具执行周围之所以需要这么多包裹层，是因为调用者本身就是最不稳定的变量。

从设计哲学上说，这一点很重要：工具不应该被建模为“模型能力的延长线”，而应该被建模为“需要运行时代为管理风险的外部能力”。一旦接受这一点，permission、hooks、interrupt、synthetic result 这些结构就更像常识，而不是负担。

# 4.4 权限先于能力：Claude Code 没把模型当有天然授权的人

Claude Code 的权限入口，在 src/hooks/useCanUseTool.tsx:27 往后。CanUse-ToolFn 的存在本身已经说明一件事：工具是否允许执行，并不由模型自己说了算，而

要交给权限判定链。

在 useCanUseTool() 里，系统不会因为模型提出了一个工具请求，就默认执行。相反，它会先调用 hasPermissionsToUseTool(...) 做权限判定，见 useCanUse-Tool.tsx:37。返回结果会分成 allow、deny 或 ask。这一点看上去平常，其实很关键。因为真正成熟的权限系统，除了“能”和“不能”，还要承认第三种状态：系统自己也不该替用户做决定。

到了 useCanUseTool.tsx:64 往后，这条链继续分出不同路径：

‧ deny：直接拒绝  
‧ ask：进入协调器、swarm worker、classifier 或交互式审批路径  
‧ allow：才真正放行

这意味着 Claude Code 从结构上否认了一种常见且危险的想法：模型懂了用户意图，就等于它有权代替用户执行。事实并非如此。理解意图不等于拥有授权，更不等于拥有持续授权。系统必须把“会做”和“可以做”分开。

从这个角度看，权限系统是在澄清代理角色。Claude Code 允许模型提出动作建议，但是否放行，由运行时、规则和用户决定。系统刻意把能力判断和授权判断分开。

# 4.5 权限结果本身也是一种运行时语义

在 src/utils/permissions/PermissionResult.ts:23 往后，系统甚至给权限行为准备了专门的描述函数：allow、deny、ask。这个细节很重要。它说明权限在 ClaudeCode 里不只是内部布尔值，而是有独立语义的运行时对象。

这件事之所以重要，是因为权限系统要让系统能够明确地表达“为什么这一步没有继续”。当一个代理说“我需要确认”时，系统是在声明责任边界。责任边界一旦说清楚，后续的拒绝、放行、缓存规则、临时授权、永久授权，才有地方安放。

更直接地说，一个代理系统如果连“这一步是我能做、不能做，还是需要问”的区别都说不清，就不该碰终端。因为终端不会替系统补完语义，终端只会执行。

# 4.6 StreamingToolExecutor 说明中断是一等语义

工具一旦开始并发和流式执行，中断问题就会立刻变得复杂。此时系统面对的是一个包含 queued、executing、completed、yielded 等多状态的队列，而不再只是单一动作。

# Chapter 4 · Permission Decision Layers

![](images/e7afc0d834135b256e7e97b5af5462aa089833ca0d3397b66504d3146c4e66be.jpg)  
图 4: Claude Code Permission Decision Layers

第 4 章工具、权限与中断

Claude Code 在 src/services/tools/StreamingToolExecutor.ts:34 往后，明确把这套东西做成了一个独立的流式工具执行器。这里面最值得注意的是它如何处理中断和丢弃。

在 StreamingToolExecutor.ts:64 到 :70，系统允许在 streaming fallback 时整体 discard 当前工具集合；在 :153 到 :205，它会根据不同原因生成 synthetic errormessage，包括：

‧ sibling error ‧ user interrupted ‧ streaming fallback

到了 :210 往后，系统还会专门判断中断原因，区分：

‧ 因为别的并行工具出错而取消‧ 因为用户 interrupt 而取消因为 fallback 而放弃当前批次

更细一点，在 :233 往后，工具还有 interruptBehavior，决定它在用户插话时究竟该 cancel 还是 block。

这套设计的意义很大。它说明 Claude Code 并不把中断理解成“执行失败的一种特殊情况”，而是把中断当成和执行本身同样重要的语义。系统不仅要知道工具能不能开始，还要知道它被打断时如何收场、如何补齐结果、是否允许新消息插入。

这正是 Harness Engineering 的一个基本特点：不仅设计开始，也设计停下。没有停下语义的执行系统，最终只能依赖用户外部打断来补完设计。

# 4.7 Bash 为什么永远比别的工具更可疑

在 Claude Code 的工具世界里，Bash 不是普通工具，它更像风险放大器。原因很简单：它过于通用。越通用的接口，越难靠领域知识限制它。一个 file read tool 至少不会顺手杀进程，一个 grep tool 至少不会偷偷 push 代码，而 Bash 几乎什么都能做。

Claude Code 对 Bash 的不信任，写得相当实在。

一层是在 prompt 上，见 src/tools/BashTool/prompt.ts:42 往后。这里对 git、PR、危险命令、hook、force push、interactive flags 这些事情写了大量明确规则。那段 prompt 看上去啰嗦，实际上很有分寸：凡是后果大的地方，系统就不怕啰嗦。

![](images/7b39abf9e430b445ff18f0bb9b0ea2982c0ac4572bcb9b902ec0f6869ea3e972.jpg)  
图 5: Claude Code Tool Execution Lifecycle

# 第 4 章工具、权限与中断

另一层是在权限和安全判定上。src/tools/BashTool/bashPermissions.ts:1 往后整整一大段，都在处理 shell 语义、命令前缀、重定向、wrapper、安全环境变量、classifier 与规则匹配。你从 bashPermissions.ts:95 往后甚至能看到系统为了防止复合命令导致检查失控，还专门给 subcommand 数量设了上限。

这说明，Bash 在 Claude Code 里一直被视为需要特殊审查的危险通道，不是普通的命令入口。工程师在这里承认了一件简单的事实：Bash 很强，所以必须被当成特例。

这是一个值得借鉴的判断。高风险能力不应该享受通用能力的待遇。能力越通用，越要特殊看管。把 Bash 当成普通工具，往往只是设计上的偷懒。

# 4.8 工具系统真正保护的，不只是用户，还包括系统自己

权限、调度和中断看起来像是在保护用户，其实它们同时也在保护系统自身。因为一个代理系统如果允许自己留下这些问题——不完整的 tool_result、失序的上下文修改、无边界的并发副作用、说不清楚的中断语义——最终最先崩掉的往往是系统的一致性。

这一点在 query.ts 里和工具执行层是互相咬合的。前一章提到，query loop 在中断时会补齐 synthetic tool_result；这一章看到，StreamingToolExecutor 也在内部预留了 discarded、hasErrored、siblingAbortController、interruptBehavior 等机制。两边一起作用，目的是让系统在“执行过什么、没执行完什么、为什么停了”这些问题上还能保持一条可追溯的因果链。

这也是 Harness 的核心含义之一：替系统保住秩序。很多约束表面上是在防止误操作，更深一层是在防止系统自己变成一堆无法解释的状态残片。

# 4.9 从源码里可以提炼出的第四个原则

这一章最后可以压成一句话：

工具是受管执行接口；权限是代理系统的基本器官。

Claude Code 的源码在几个地方共同支持这个判断：

‧ toolOrchestration.ts 把工具先分批，再执行，说明调度先于冲动‧ toolExecution.ts 把 hooks、permission、telemetry 和 synthetic error 包在工具执行周围，说明执行不是裸调用

# 第 4 章工具、权限与中断

useCanUseTool.tsx 把权限结果分成 allow / deny / ask，说明系统把授权当成独立语义  
StreamingToolExecutor.ts 为中断、fallback、并发出错预留专门语义，说明停止和开始同样重要  
BashTool/prompt.ts 与 bashPermissions.ts 对 Bash 采取特殊高压治理，说明高风险能力必须接受更密约束

如果要把这些提炼成可迁移的工程原则，大概可以写成这样几条：

‧ 让模型提出动作，不等于让模型拥有授权‧ 工具调度必须保持因果秩序，哪怕执行并发‧ 中断要有一等语义，不能靠异常兜底‧ 高风险工具必须区别对待，不能图省事走通道化设计‧ 一个工具系统真正保护的，既是用户，也是运行时本身下一章要讨论的是这套系统里另一种常见错觉：上下文越多越好。Claude Code 的实现恰好说明，真正有经验的系统不会把上下文当仓库，而会把它当资源。接下来要讲的，是 memory、CLAUDE.md 与 compact 如何共同组成上下文治理。

# 第 5 章上下文治理：Memory、CLAUDE.md 与 Compact 是预算制度

# 5.1 上下文一多，系统就容易产生一种低级幻觉

人一旦可以往上下文里不停塞东西，就很容易相信一个朴素的神话：信息越多，系统越聪明。这个神话听起来甚至有点合情合理。毕竟知道得多，总比知道得少强。可惜代理系统不是图书馆，模型也不是藏书管理员。上下文不是一个“存进去就算拥有”的仓库，它首先是一笔昂贵、易膨胀、还会自我污染的预算。

Claude Code 的源码在这件事上很不浪漫。它并没有把上下文设计成一个可以无限堆叠的记忆池，反而在很多地方反复提醒自己：该加载什么、该截断什么、什么东西要长期保留、什么东西只能短期摘要，都是运行时必须严肃治理的事。

所以这一章要讨论的是：Claude Code 怎样防止自己被记住的东西拖死。这件事和“记住更多”看起来相近，工程上却是两种制度。前者偏向收藏癖，后者才接近治理术。

# 5.2 CLAUDE.md 体系说明，长期指令不能和临场对话混在一起

Claude Code 在 src/utils/claudemd.ts 开头就把记忆层次说得很清楚。它把 in‑struction source 分成几层：

managed memory，例如 /etc/claude-code/CLAUDE.md user memory，例如 \~/.claude/CLAUDE.md   
project memory，例如项目根目录里的 CLAUDE.md、.claude/CLAUDE.md、 .claude/rules/\*.md   
‧ local memory，例如 CLAUDE.local.md

而且这些文件会按优先级和目录距离加载。离当前工作目录越近的 project 规则，优先级越高；越偏向私有、越偏向本地的规则，越晚加载，因而越靠近模型的注意力前沿。

这件事特别要紧。因为它说明 Claude Code 从一开始就拒绝把“长期协作规则”和“本轮临时对话”混成一锅粥。团队规范、个人偏好、仓库约束，这些东西的寿命远长于某一轮用户消息；如果把它们全都塞进聊天记录里，系统就会在两个极端之间摇摆：要么每轮都重复注入，浪费上下文；要么靠模型自己回忆，迟早失手。

claudemd.ts 给出的答案，是把这些稳定规则做成可发现、可分层、可组合的持久指令系统。还有个细节很有意思：它支持 @include，并且只允许一大批明确列出的文本扩展名。这说明工程师除了追求 include 的便利，也在提防另一种常见事故：有人把二进制、巨型文档、甚至不该进 prompt 的东西糊里糊涂带进来了。

这是正经工程师才有的克制。系统会先问：”什么东西值得进入系统记忆，什么东西一旦进入就是污染。”

# 5.3 MEMORY.md 是索引，不是日记本

如果 CLAUDE.md 管的是规则层，那么 memdir 处理的就是另一类更细的长期记忆。src/memdir/memdir.ts 里有一段设计很值得反复看：ENTRYPOINT_NAME 被定义成MEMORY.md，但这个文件并不被鼓励用来直接堆内容，它被定义为 index。

源码里写得很实在。buildMemoryLines() 明确告诉模型，保存 memory 是两步：

1. 把具体 memory 写进独立文件  
2. 再在 MEMORY.md 里加一个一行指针

为什么这么麻烦？因为系统知道入口文件天然会被频繁加载，而频繁加载的东西一旦变胖，整套上下文就会被它慢慢拖成一个不好收拾的胖子。

这也是为什么 memdir.ts 里专门有 MAX_ENTRYPOINT_LINES = 200 和 MAX_ENTRYPOINT_BYTES$= 2 5 \_ 0 0 0 ,$ 。超过了，系统会直接 truncateEntrypointContent()，并在结尾追加明确警告：只加载了一部分，请把细节移到 topic files。

这套做法特别像一个见过太多失控索引的人。它不相信大家会天然克制，所以把“入口必须短”做成硬约束。因为入口文件一旦既当目录又当正文，最后就既不是目录，也不是正文，只是一个谁都不愿再读第二遍的烂尾摘要。

从 Harness Engineering 的角度看，这里抽出来的原则非常清楚：长期记忆必须分成“入口”和“正文”。入口负责低成本寻址，正文负责高密度承载。把两者混为一谈，最终一定是入口失效，随后整套记忆系统退化成摆设。

# 5.4 Session memory 说明，短期连续性也不能靠聊天记录硬扛

只有长期 memory 还不够。代理系统真正难受的地方，常常在于“这轮之前我们到底做到哪一步了”。这是一次会话内部的连续性问题。

Claude Code 在 src/services/SessionMemory/prompts.ts 里专门给这件事建了一套模板。默认模板里有这些栏目：

‧ Current State   
‧ Task specification Files and Functions Workflow Errors & Corrections Codebase and System Documentation Learnings   
‧ Key results   
‧ Worklog

你一看就知道，这不是给人抒情的。它关心的是：现在做到哪了，踩过什么坑，改过哪些文件，后面该接什么。更有意思的是更新 prompt 的语气。源码里明确要求：

‧ 只能用 Edit tool 更新 notes file‧ 不要提 note‑taking 这件事本身‧ 不要改模板结构‧ Current State 必须始终反映最近工作‧ 每节都要信息密集，但要控制预算

这说明 session memory 在 Claude Code 里并非“另存一份聊天记录”，它会把当前会话萃取成一种可继续工作的操作说明书。它不求完整复刻对话，而求压缩出未来继续干活所必需的骨架。

这里有个极其工程化的细节。prompts.ts 里定义了 MAX_SECTION_LENGTH $=$ 2000和 MAX_TOTAL_SESSION_MEMORY_TOKENS = 12000。超过预算，系统不会夸你记得细，而是要求你 aggressively condense，尤其优先保留 Current State 和 Errors& Corrections。

这很能说明问题。真正成熟的系统，会把“为继续工作保留最有用的部分”当成美德。  
因为上下文预算是工作内存。工作内存的第一职责是可操作。

# 5.5 自动 compact 说明，上下文治理首先是预算治理

到这里，长期规则、持久 memory、session memory 都有了，但上下文还是会膨胀。于是 Claude Code 在 src/services/compact/autoCompact.ts 里进一步承认一个现实：不管你多会整理，只要对话够长，总会逼近窗口边缘。

getEffectiveContextWindowSize() 先把模型 context window 减去一笔保留给summary 输出的预算。MAX_OUTPUT_TOKENS_FOR_SUMMARY 直接预留了 20,000 to‑kens。也就是说，系统先假定 compact 本身要花钱，绝不把窗口吃到只剩一口气时才想起求生。

接着 getAutoCompactThreshold() 又在有效窗口上再扣掉 AUTOCOMPACT_BUFFER_TOKENS$= ~ 1 3 \_ 0 0 0 $ 。警告阈值、错误阈值、手动 compact 预留空间，也都各自分出 buffer。

这套数字背后有个很朴素的道理：上下文治理需要提前为失败和恢复留出余地。不留余地的系统，平时看着像节俭，出事时才暴露真相——不过是把风险账单留给了下一轮。

更有意思的是 AutoCompactTrackingState。它不仅记 compacted，还记 turn-Counter、turnId 和 consecutiveFailures。这说明 autocompact 是一段会被追踪、会失败、会被限流的运行时行为。

源码甚至写了一个很直白的注释：全球每天曾经浪费大量 API calls 在连续失败的 au‑tocompact 上，所以 MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES $= 3$ ，再失败就触发 circuit breaker。这里的气质非常好，像一个终于受不了浪费的人：你可以失败，但不能无限次、无记忆地失败。

# 5.6 compactConversation() 说明，摘要要重建可继续工作的上下文

很多人一听 compact，会以为就是“把前面聊天摘要一下”。Claude Code 的实现要复杂得多。src/services/compact/compact.ts 里的 compactConversation() 真正做的，是把原有上下文拆开、摘要、再注入必要附件，重新搭出一个还能工作的后compact 世界。

先看压缩前的清洗。stripImagesFromMessages() 会把图片、文档替成 [image]、[document] 之类的标记；stripReinjectedAttachments() 会把反正之后还要重新注入的 attachment 先剥掉，免得浪费 token。仅这两个动作就说明，compact 会有选择地丢掉那些”对摘要没用、但 token 开销极大”的部分。

再看摘要失败时的处理。源码里有 truncateHeadForPTLRetry()，专门应对“compact请求自己都 prompt too long”的尴尬场面。也就是说，系统不仅承认主流程会爆，还承认“救火工具本身也会爆”。这很像真实世界，而不是 demo。

而在 compact 成功之后，Claude Code 做的不是简单保留一条 summary。它还会：

‧ 清空旧的 readFileState  
‧ 重新生成 post‑compact file attachments  
‧ 把 plan attachment 补回来  
把 plan mode attachment 补回来  
‧ 把 invoked skills attachment 补回来  
‧ 把 deferred tools、agent listing、MCP instructions 的 delta attachment 重新补回来  
‧ 执行 session start hooks 和 post‑compact hooks  
‧ 写 compact boundary message，记录 pre‑compact token 数与边界信息

这些动作合在一起，意思很明确：compact 的目标是把“继续干活所需的运行时环境”重新铺平。摘要只是中间产物，不是最终目的。

所以 compact 在 Claude Code 里更像一次受控重启，而不是一次聊天总结。旧上下文会被转译成新的工作底座。这种设计很值得记住，因为很多系统只做前半截，结果compact 之后虽然“还记得大概”，却已经失去了工具状态、计划状态、附件状态，接下来还得再花几轮找回自己。

# 5.7 上下文治理的关键是保留工作语义

如果只看 compact.ts 的后半段，会发现一个贯穿始终的倾向：Claude Code 真正在意的是把工作语义保住。

例如它会恢复最近访问文件的 attachment，因为这些文件往往构成当前工作面的局部现实；它会恢复 plan mode，因为否则模型压缩完以后可能忘了自己还处在 plandiscipline 里；它会保留 invoked skills 的内容，但又给每个 skill 设置 token cap，避免 skill 本身在 post‑compact 阶段反客为主。

源码里这句话很有味道：per‑skill truncation beats dropping。意思是，即使要裁，也优先保住开头那一段最关键指令，而不是整个扔掉。这就是治理，不是纯粹节流。纯节流是砍，治理是知道该砍哪里、该保什么。

从这里可以抽出一个相当稳妥的经验：上下文系统应该优先保留能维持行动语义的东西，而不是优先保留看起来信息量最大的东西。文件细节、当前计划、错误修正、技能约束，这些都直接决定下一步能不能做对。反过来，冗长的历史对话、重复出现的附件、运行时随时可以重新拿到的东西，就没必要再占着座位。

# 5.8 从源码里可以提炼出的第五个原则

这一章最后可以压成一句话：

上下文是工作内存。治理它的目标是支持系统继续工作。

Claude Code 的源码在几个层面共同支持这个判断：

claudemd.ts 把长期指令分层加载，说明稳定规则要和临时对话分开治理  
memdir.ts 把 MEMORY.md 定义成索引并强行截断，说明入口文件必须短而可寻  
址  
SessionMemory/prompts.ts 用固定模板提炼会话连续性，并对 section 和总量设预算，说明短期记忆也必须结构化  
autoCompact.ts 为 compact 预留输出预算、缓冲区和失败熔断，说明上下文窗口要按风险来经营  
compact.ts 在摘要后恢复计划、文件、技能、工具附件和 hook 状态，说明 compact的目标是重建工作语义，而不是写一段好看的总结

如果把这些抽象成可迁移的工程原则，大概有这样几条：

‧ 长期规则、长期记忆、会话连续性，应该分层，不该混写  
‧ 入口型记忆必须短小，否则整个系统会被入口拖垮session summary 应该服务于“继续工作”，而不是服务于“回忆完整”compact 是上下文治理主路径  
‧ 压缩后的上下文必须保住运行语义，而不是只保住语言表面

下一章要讲的是这套治理系统碰到极限时怎么办。因为一个真系统终究会出错：prompttoo long，max output tokens，hook 死循环，恢复分支相互打架。到那时你才看得出来，一个代理系统到底是在“赌不出事”，还是在认真设计出事之后如何继续运行。

# 第 6 章错误与恢复：出错后仍能继续工作的代理系统

# 6.1 工程世界最不值得相信的话，就是“正常情况下”

很多系统设计文档里，最常见的偷懒方式，就是先讲一遍“正常情况下”的流程，仿佛只要主路径足够漂亮，错误就会自动显得次要。可代理系统一旦进入真实运行环境，这种写法通常很快就会露馅。因为现实中什么都会出问题：

‧ 模型会被截断  
‧ 请求会超长hook 会制造回环  
‧ 工具会中断  
‧ fallback 会发生  
‧ 恢复逻辑本身也会失手

所以，判断一个代理系统成熟不成熟，不能只看它回答顺畅的时候有多像个人，而要看它出故障的时候像不像系统。前者容易靠一点 prompt 工程粉饰，后者只能靠运行时纪律。

Claude Code 在这一点上的可取之处，是它没有假装自己不会出错。相反，源码里反复体现出一种冷静判断：错误属于主路径，恢复则是必须提前设计好的运行机制。

# 6.2 prompt too long 是一种必然周期

对长会话代理来说，prompt too long 是一种迟早会来的季节变化。你如果把它当偶发异常，系统迟早会被它教育。

Claude Code 的 query.ts 就没有把它当偶发异常处理。在 src/query.ts 里，系统甚至会“暂时扣下”这类错误，不立刻把它原样抛给用户。流式阶段里，withheld 逻辑会识别 recoverable errors，包括：

prompt too long media size error max output tokens

这件事的意思很明确：有些错误要先交给恢复系统试着处理，再决定是否展示给用户。  
这个顺序很关键，因为用户真正关心的通常是系统还能不能继续干活。

在 prompt too long 的分支上，Claude Code 先尝试更便宜、更保守的恢复路径。若启用了 context collapse，就先 recoverFromOverflow()，把已经 staged 的 collapse提交掉；如果还不行，再进入 reactiveCompact.tryReactiveCompact()。也就是说，恢复是分层的：先排空已知积压，再做更重的全文压缩，不会一上来就重建世界。

这种次序特别有工程味。因为真正好的恢复系统，不会把所有错误都交给“最重的一把锤子”。它会先试图保住最细粒度的上下文，再在必要时接受更粗糙的摘要替代。

# 6.3 响应式 compact 说明，恢复的关键在于别把自己逼进死循环

很多系统做恢复时容易犯一个愚蠢但常见的错误：一旦发现错误可恢复，就不停重试，直到把错误从偶发事件升级成资源灾难。

Claude Code 对这件事非常警惕。query.ts 里有两个地方都能看出这种警惕。

第一处，是 hasAttemptedReactiveCompact。一旦 reactive compact 已经试过，再次遇到同类问题时，系统不会装傻重来。因为工程师很明白：如果 compact 之后还是不行，那么继续 compact 大概率只是在把同一种失败换个姿势再演一次。

第二处，是 stop hooks 的防死循环处理。源码里有非常直白的注释：如果 prompt toolong 之后还让 stop hooks 介入，就可能出现 death spiral，路径大致是：

错误 $_ - >$ hook blocking $_ - >$ retry $_ - >$ 错误 $_ - >$ hook blocking

这话写得一点也不文学，却比许多文学都诚实。因为它承认系统里最危险的错误，是失败分支和恢复分支彼此咬住，开始无限自我复制。

所以 Claude Code 在 prompt too long 无法恢复时，会直接 surface 错误并跳过 stophooks。原因很简单：这时候继续走形式流程，只会让坏事更有仪式感。

# 6.4 max_output_tokens 的处理说明，恢复要以续写为主

大模型产品有个很坏的习惯，一旦输出截断，就先来一段很客气的废话：抱歉，刚才被截断了，我来总结一下。听上去态度不错，实际上对工作几乎没帮助。

Claude Code 在 src/query.ts:1185 往后的处理，明显更接近工程系统。它先试一种成本较低的恢复：如果当前使用的是较保守 cap，就把 maxOutputTokensOverride提升到更高值，直接重跑同一请求。注意，这一步没有插入 meta message，也没有让模型先寒暄，系统先给它一次把原任务做完的机会。

如果更高 cap 也不够，再进入第二层恢复：给模型追加一条 meta user message，内容非常实在，大意是：

直接继续，不要道歉，不要 recap，若中断发生在半句，就从半句接着写；剩余工作拆小一点。

这是一条很有启发意义的系统指令。它说明 Claude Code 对恢复的理解，是尽量保持任务连续性，不要把额外 token 花在礼貌性收尾上。在长任务里，这种区别非常大。因为每一次截断后的 recap，都会进一步消耗预算，并且增加语义漂移。最后系统做的就不再是任务本身，而是一轮轮地回顾自己做任务。

所以对 max_output_tokens 来说，较好的恢复通常是续写。Claude Code 在这里优先保证任务连续性，而不是补充礼貌性说明。

# 6.5 auto compact 的失败熔断，说明恢复系统自己也要受治理

如果说前面讲的是“单次错误怎么救”，那 src/services/compact/autoCompact.ts处理的就是另一个层面的问题：当恢复机制本身不断失败时，怎么办。

源码的回答很简单，也很正确：别一直试。

AutoCompactTrackingState 里专门有 consecutiveFailures。一旦失败次数超过阈值，shouldAutoCompact 即便判断“按理说该 compact 了”，系统也会直接跳过。源码注释甚至给出过往数据：曾有大量 session 在连续 autocompact failure 上白白烧掉海量 API calls，所以必须加 circuit breaker。

失败熔断的本质，是承认当前恢复手段在这个局面里已经失效。一个真正成熟的系统，不能只会在成功时记录指标，也得在失败时懂得收手。不会收手的恢复系统，和不会刹车的汽车差不多，理论上都叫系统，实际上都不该上路。

从 Harness Engineering 角度看，这里可以抽出一条很硬的原则：任何自动恢复机制都必须可计数、可限次、可熔断。否则恢复会从保险丝变成新的起火点。

# 6.6 compact 自己也会爆，所以连“修复动作”都需要修复策略

compactConversation() 这段代码还有一个很动人的现实主义时刻：它承认 com‑pact 请求自己也可能 prompt too long。

这件事看上去带一点黑色幽默。系统为了缩短上下文去发摘要请求，结果摘要请求也因为上下文太长而失败。很多人不喜欢这种情形，因为它暴露得过于直接。但工程系统首先要解决的是继续运行，而不是保持表面完整。

Claude Code 的处理方式，是在 compact.ts 里引入 truncateHeadForPTLRetry()。当 compact 自己太长时，系统会先把更早的 API round 成组地从头部剥掉，再重试compact，避免让用户卡在“连压缩都压不动”的状态里。

这里的取舍很清楚：这种修复有损，也会丢历史，但它优先保证用户不被完全锁死。源码注释写得很实在，这是一种 last‑resort escape hatch。

这种处理方式的价值，在于它没有回避现实约束。系统快要窒息时，优先级是先恢复呼吸，再讨论信息保真度。这个判断不追求漂亮，但很实用。

# 6.7 abort 语义说明，中断也属于错误恢复的一部分

很多人把 abort 单独归到交互体验，不愿意把它放进错误恢复讨论里。从运行时角度看，中断就是一种必须被正确回收的失败态。

Claude Code 在两个层面都认真处理了这件事。

一层在 query.ts。如果 streaming 时用户打断，系统会先消费 StreamingToolEx-ecutor.getRemainingResults()，为已经发出但尚未完成的工具生成 synthetictool_result，确保前面承诺过的 tool_use 不会变成悬空债务。

另一层在 compact.ts。源码里专门把 compact 的 abort controller 传给 forkedagent，并处理 APIUserAbortError，防止“被用户按了 Esc 的 compact”误算成一次成功摘要。

这两处连在一起看，意思很明确：中断不只是“用户不想看了”，而是一次需要正确收尾的状态转移。错误恢复如果只管异常、不管中断，最终会留下大量语义半残的执行轨

![](images/0830748e47d586d640bd2f4a064444b054f22f502d15ae27b9ed3a213baf9c82.jpg)  
图 6: Claude Code Recovery Decision Paths

# Chapter 6 $\bullet$ Compact Fallbacks

![](images/2e1b288f10e3e7c7f0c7753416a63f220d8a56827b1c48afef44c6cb29461e2d.jpg)  
图 7: Claude Code Compact Fallbacks

迹。那种轨迹通常短期内没人查，长期看全是祸根。

# 6.8 错误处理真正保护的，是执行叙事的一致性

把这些源码放在一起看，会发现 Claude Code 对错误与恢复的理解，有一个很核心但常被忽略的目标：保护执行叙事的一致性。

什么叫执行叙事？很简单，就是系统还能不能说清楚：

‧ 我刚才试图做什么  
‧ 为什么没做成我用了什么恢复路径  
‧ 现在是继续、停止，还是换轨

query.ts 里的 transition.reason，maxOutputTokensRecoveryCount，hasAt-temptedReactiveCompact，以及 compact boundary、synthetic error message这些东西，都是为了让这条叙事线不断裂。它们是为了让系统自己别失忆。

一个没有叙事一致性的代理系统，表面也许还能继续输出，但它的内部已经开始散了：

‧ 今天，用户看到的是多说几句废话‧ 明天，运维看到的是一会儿 hook retry、一会儿 compact retry，理不清因果‧ 后天，团队看到的是系统出了问题，谁都说不清它到底经历了什么

所以错误恢复真正修补的，不只是错误本身，还有系统对自己行为的解释能力。解释能力一断，系统就会从工程对象退化成玄学对象。

# 6.9 从源码里可以提炼出的第六个原则

这一章最后可以收成一句话：

代理系统是否可靠，体现在错误发生后仍能维持可解释、可限界、可继续的执行秩序。

Claude Code 的源码在几个点上共同支持这个判断：

query.ts 会暂时扣下可恢复错误，先交给恢复分支处理，说明错误要先尝试转化

# 第 6 章错误与恢复

prompt‑too‑long 恢复先走 collapse drain，再走 reactive compact，说明恢复路径按成本和破坏性分层  
hasAttemptedReactiveCompact 与 stop hook guard 明确防止死循环，说明恢复本身也要受治理  
max_output_tokens 先提 cap，再要求模型直接续写，说明恢复的目标是延续任务，不是补充礼貌动作  
autoCompact.ts 的 consecutive failure 与 circuit breaker，说明自动恢复必须可熔断  
compact.ts 对 compaction 自身的 prompt‑too‑long 也有降级修复，说明连修复动作本身都要有恢复策略

如果把这些抽成可迁移的工程原则，大概是这样：

‧ 错误恢复要分层，不要所有问题都打一把重锤  
‧ 恢复逻辑必须防止自我回环自动恢复需要计数和熔断  
‧ 截断后的最佳恢复通常是续写，不是总结  
‧ 中断也是一种需要语义收尾的失败态  
‧ 一个系统是否可靠，最终要看它出错后还能不能把自己的行为讲明白

下一章要进入另一类更棘手的问题：多代理与验证。因为当一个系统不再只是“自己出错自己救”，而开始把任务分给别的 agent，再把结果收回来复核，错误与恢复的问题就从单线程秩序升级成了组织问题。那时你面对的不只是一个模型会不会失手，而是一群不稳定执行体如何彼此约束。

# 第 7 章多代理与验证：用分工和验证管理不稳定性

# 7.1 单代理走到一定程度，问题就不再是“会不会做”，而是“怎么分工”

一个代理如果只在单线程里回答问题，很多矛盾都还能靠耐心遮过去。它慢一点，用户多等会儿；它想得乱一点，多追问几轮；它偶尔把上下文拖成一团，也还可以靠 compact补救。可一旦任务变大，单代理模型就会碰到一个更难缠的问题：研究、实现、验证都挤在同一条上下文链上，彼此抢预算、抢注意力、抢叙事中心。

这时候，多代理看上去像一种自然答案。再开几个 worker，不就行了？但事情没这么便宜。多代理并不天然带来秩序，很多时候它只会把单代理的混乱并行复制几份。真正困难的是隔离这些 agent 的不稳定性，同时把结果组织回来。

Claude Code 的源码在这点上很清醒。它没有把 subagent 当成“另一个会说话的窗口”，而是把它当成一段需要明确缓存边界、状态边界、验证职责和清理责任的受管执行流程。

# 7.2 forked agent 的第一原则是 cache‑safe

src/utils/forkedAgent.ts 开头有一段注释，非常能说明 Claude Code 对 sub‑agent 的真实理解。它说 forked agent utility 的职责包括：

1. 与父代理共享 cache‑critical params，确保 prompt cache hit  
2. 跟踪整个 query loop 的 usage  
3. 记录指标  
4. 隔离可变状态，防止干扰主循环

这四条里，最先出现的是“共享 cache‑critical params”。这并非偶然。它说明在 ClaudeCode 眼里，fork 是运行时层面的受控分叉。既然是分叉，就必须非常在意哪些参数必须和父请求保持一致，否则 prompt cache 共享就失效，成本和延迟会立刻变坏。

CacheSafeParams 里明明白白列了这些要素：

systemPrompt userContext systemContext toolUseContext ‧ forkContextMessages

还专门提醒：别随便改 maxOutputTokens，因为 thinking config 也会受影响，而thinking config 又是 cache key 的一部分。

这段设计说明，多代理首先是运行时经济学问题。一个子代理如果每次都把父上下文重新烧一遍 token，看上去像在并行提效，实际只是把浪费并行化。Claude Code 在这个环节先处理的是：怎么 fork 才不把缓存打烂。

# 7.3 状态隔离说明，子代理首先要减少污染

forked agent 的第二个关键，在 createSubagentContext()。源码里对它的默认行为写得很直白：默认情况下，所有 mutable state 都隔离，避免干扰 parent。

它默认会做这些事：

‧ readFileState 先 clone  
abortController 生成 child controller，而不是直接共享  
getAppState 做包装，让子代理避免 permission promptsetAppState 默认 no‑op  
nestedMemoryAttachmentTriggers、loadedNestedMemoryPaths 等集合都重新建

只有在明确 opt‑in 的情况下，才会共享某些 callback，例如 shareSetAppState、shareSetResponseLength、shareAbortController。

这套设计特别重要，因为它揭示了一个很多人做多代理时都会忽略的事实：子代理最宝贵的地方，在于它可以避免把自己的局部混乱污染主线程。研究中的误判、临时读到的文件状态、一次性的推理枝杈、正在进行的工具决策，如果全都直接写回主上下文，你得到的只会是更快的脏化。

Claude Code 在这里的态度是：共享要靠明确同意，隔离才是默认伦理。这种伦理很像数据库事务设计，不像聊天玩具。它不假定“大家都是自己人，状态可以随便串”，而是假定“只要是可变状态，就必须先隔离，再决定共享哪些部分”。

# 7.4 协调者模式说明，synthesis 才是稀缺能力

如果只看 src/coordinator/coordinatorMode.ts，你会发现 Claude Code 对 co‑ordinator 的要求很有分寸。它明确说 coordinator 的工作包括：

‧ 帮用户达成目标  
‧ 指挥 worker 做 research、implementation、verification综合结果并和用户沟通  
‧ 能直接回答的问题就直接回答，不要滥委派

最关键的一句，在第 5 节 prompt 里：Always synthesize。当 worker 回报研究结果后，协调者必须先读懂，再写出具体 prompt；不要说“based on your findings”，不要把理解继续外包给 worker。

这句话几乎就是多代理系统的命门。因为真正稀缺的是有人把 worker 带回来的局部知识重新压成清晰、可执行、可验证的下一步。缺少这一层，多代理很快就会退化成一种带着礼貌措辞的任务转发机。每个 agent 都在忙，系统整体却并没有更懂。

Claude Code 至少在 prompt 设计上很明白这个道理。它要求 research 和 synthesis分开，要求协调者对研究结果负责。后续 prompt 里必须出现具体文件、具体位置、具体变更，而不是抽象地”根据前面的结论”。这是非常正统的工程分工：研究可以分布式，但理解必须重新收束。

# 7.5 验证必须独立成阶段，否则“实现完成”很快就会冒充“问题解决”

coordinatorMode.ts 还有一段特别值得抄下来。它把常见任务分成：

‧ Research ‧ Synthesis

# 第 7 章多代理与验证

‧ Implementation ‧ Verification

并且专门强调：verification 的目标是证明代码有效，而不只是确认代码存在。源码里甚至写得近乎不留情面：

‧ run tests with the feature enabled ‧ investigate errors, don’t dismiss as unrelated ‧ be skeptical ‧ test independently, don’t rubber‑stamp

这段话说明 Claude Code 没把验证当成实现 worker 顺手带一下的附属环节，而是当成第二层质量关。你甚至能在 prompt 里看到“implementation worker 自证一遍，verification worker 再作为第二层 QA”这种明确分层。

为什么这点这么重要？因为在代理系统里，“我改了代码”和“代码因此正确”之间，隔着一条很宽的河。模型尤其擅长在这条河上搭纸桥。它会给你改动、解释、甚至给你一段像样的测试输出，但这些都不等于功能真的在系统里站住了。

所以，把 verification 单列出来，是为了防止“会改代码”冒充“能交付结果”。HarnessEngineering 在多代理阶段真正需要的，正是这种角色分化。实现的人要尽量专注于改；验证的人要专门怀疑这些改动配不配活着。

# 7.6 hooks 和任务生命周期说明，子代理不是扔出去就算了

多代理系统还有一个很容易被忽略的地方：spawn 只是开头，收尾同样重要。

src/utils/hooks/hooksConfigManager.ts 里 定 义 了 SubagentStart 和SubagentStop 两类 hook。前者在 subagent 启动时触发，输入里有 agent_id 和agent_type；后者在 subagent 即将结束时触发，输入里还带 agent_transcript_path，并允许 exit code 2 把 stderr 反馈给 subagent，继续让它跑。

这说明子代理在 Claude Code 里是显式暴露生命周期节点的系统对象。启动时可以观测，停止前可以介入，转录路径可追踪。这里的重点在于，“子代理结束”也是需要被管理的事件。

与 此 同 时，src/tasks/LocalAgentTask/LocalAgentTask.tsx 的 regis-terAsyncAgent() 又展示了另一个层面：每个 async agent 都会注册 cleanuphandler，父 abort 可以自动传播给子 abort controller。任务结束后还要 evictoutput、更新状态、解除 cleanup 注册。

# 第 7 章多代理与验证

这套机制非常像操作系统，不像聊天面板。它关心的核心问题是：

‧ 这个 agent 是否仍在运行‧ 父任务死了它是否该跟着死‧ 它的输出文件是否还要保留‧ 它的 cleanup callback 有没有泄漏

# Chapter 7 $\bullet$ Multi-Agent Runtime Lifecycle

![](images/579845918b1f7f9b2febe74748754f8c16a9fcf509bbe2d6488372cad42691e1.jpg)  
图 8: Claude Code Multi‑Agent Runtime Lifecycle

很多多代理 demo 都只做到“我能再起一个 agent”，Claude Code 至少多做了一步：

它把 agent 当作会泄漏资源、会残留状态、会在父进程结束后变成孤儿的运行实体来看待。这才像是在把代理当系统组件处理。

# 7.7 验证不仅针对代码，也针对记忆和建议

多代理与验证并不只发生在 code change 之后。Claude Code 在 memory 体系里也埋了一条很值得注意的原则。

src/memdir/memoryTypes.ts 里专门提醒：memory records can become stale； 在基于 memory 给用户建议之前，要先 verify current state；如果记忆与现状冲突， 要相信眼下读到的真实状态，并更新或删除 stale memory。

这句话放在多代理章节里，恰好能说明一个更一般的事实：验证是整个系统用来抵抗时间漂移和上下文漂移的基本习惯。一个系统如果只验证新写下去的代码，却不验证旧记忆、旧假设、旧索引，那它仍然会被历史信息带偏。

从这个角度看，verify 既是一项 skill，也是一种组织纪律。你可以把工作分出去，可以把信息存起来，可以让其他 agent 先跑在前面，但在用户准备据此行动之前，总要有人回到当前现实，重新确认这些东西还是真的。

# 7.8 多代理真正解决的是不确定性的分区

把这些源码拼起来看，会发现 Claude Code 的多代理设计其实围绕一个朴素目标展开：给不确定性分区。

研究 worker 可以在局部上下文里探索，不必把所有试探都写回主线程。实现 worker可以专注修改，不必同时扛着全局沟通负担。验证 worker 可以专门怀疑，不必替自己的实现辩护。coordinator 则留在中间做收束、综合和用户界面。

这套分区带来的最大好处是职责清晰。职责一清晰，错误就更容易定位：

‧ 是 research 没找到关键线索‧ 还是 synthesis 没吃透研究‧ 还是 implementation 写错了‧ 还是 verification 放水了

反过来，如果所有事情都交给一个代理顺手完成，你最后得到的只是一锅浓汤。味道也许不错，出了问题却没法分层修。

所以，多代理真正有价值的地方，在于把不同种类的不确定性关进不同容器里，再用coordinator 把它们组织回来。这种做法比单纯追求并发更稳，也更符合工程要求。

# 7.9 从源码里可以提炼出的第七个原则

这一章最后可以压成一句话：

多代理依赖清晰分工：研究、实现、验证和综合各自处在不同约束容器里，最后由协调者把结果重新缝合成可交付结果。

Claude Code 的源码在几个地方共同支持这个判断：

‧ forkedAgent.ts 把 cache‑safe 参数、usage tracking 与状态隔离放在第一位，说明 fork 首先是运行时控制问题createSubagentContext() 默认隔离 mutable state，只允许显式 opt‑in 共享，说明多代理先防污染再谈协作coordinatorMode.ts 强调 coordinator 必须 synthesize，而不是转发研究结果，说明综合理解不能外包  
同一个文件把 verification 独立成阶段，并要求独立证明变更有效，说明实现与验证必须角色分离hooksConfigManager.ts 提供 SubagentStart / SubagentStop 生命周期hook，说明子代理是可观测对象，不是黑箱线程  
‧ LocalAgentTask.tsx 处理 parent abort、cleanup、output eviction，说明agent 生命周期需要回收机制

如果把这些提炼成可迁移的工程原则，大概是这样：

‧ fork 时先考虑 cache 和状态边界，再考虑“人格分工”  
‧ 子代理默认应隔离，可共享必须显式声明  
‧ 研究可以委派，综合理解不能委派  
‧ 验证必须与实现解耦，否则系统会奖励自证正确  
‧ agent 生命周期必须可观测、可中止、可清理  
‧ 真正的并行价值在于职责更清楚

下一章要讨论的，是当这一整套机制落到团队里时，如何从个人技巧变成组织制度。也就是说，CLAUDE.md、skills、approval、hook、memory 这些东西，怎样从“某个高手自己会用”变成“一个团队可以稳定复用”的工程实践。

# 第 8 章团队落地：把一个聪明工具变成可承受的工作流

# 8.1 个人顺手，不代表团队就能稳定复用

很多 AI coding 工具在个人手里看着很灵。熟练用户知道什么时候该补上下文，什么时候该盯着它别乱动，什么时候一句“不要碰这个目录”就能把风险压住。于是团队很容易产生一个错觉：既然高手已经能把它用顺，那推广不过是多写几篇经验文档。

问题在于，个人技巧之所以有效，恰恰因为它依赖个人持续盯防、背景知识和临场判断。团队一旦接手，问题就变了。你不能再假定每个人都知道哪些命令危险，哪些 memory已经过期，哪些 skill 会 fork 子代理，哪些步骤必须 ask，哪些步骤只是“看起来没事”。

所以，团队落地真正要解决的，是把原来靠高手脑内维持的秩序，压成多数人都能重复执行的工作流。

Claude Code 的源码之所以值得参考，在于它把很多高手经验显式化了：指令如何分层加载，权限如何决策，子代理如何隔离，生命周期上有哪些可插点。这些实现细节提醒我们，团队采用一个 coding agent，既是在引入一个更聪明的补全工具，也是在重新安排“谁在什么边界内做什么事”。

# 8.2 团队第一步，是先把最低边界做清楚

这一章最容易被误读的一点，是把团队落地想成“大规模制度化工程”。现实里，多数团队一开始不会先上 hooks、审计链和复杂 skill 目录，他们更常见的起点其实只有四件事：

‧ 哪些任务允许 agent 直接参与‧ 哪些改动必须经过人工 review‧ 改完至少要跑什么验证

‧ 哪些资源一律不能碰

这四件事看起来朴素，却比一堆宏大口号更重要。团队起步阶段更需要的，是先把最低可控边界画清楚。

如果把这个边界画错，后面所有自动化都会失真：

‧ 允许范围没定义，大家会拿 agent 去做本不该自动化的事review 责任没定义，出问题时没人知道最后一层把关是谁‧ 验证标准没定义，系统会自动学会迎合最低标准‧ 禁区没定义，所谓效率提升最后只是扩大事故半径

因此，更现实的团队落地顺序通常会是：

1. 先把可接受使用范围讲清楚

2. 再把 review 和验证口径讲清楚

3. 然后才考虑如何把高频流程复用起来

很多团队最后失败，往往不是因为 agent 不够强，而是因为起步时跳过了这一步。

# 8.3 CLAUDE.md 的价值，在于稳定、分层、少争议

前面已经讲过 claudemd.ts 的分层加载。到了团队采用阶段，这件事仍然重要，但它的意义应该理解得更克制一些。

团队级 CLAUDE.md 更适合承载稳定规则，不必把所有流程细节都堆进去。比如：

‧ 代码库级硬约束，例如禁止写某类目录、禁止危险命令  
‧ 统一验证口径，例如改完至少跑哪些检查  
‧ 协作纪律，例如不要覆盖用户未要求改动，不要在脏工作区擅自 reset  
‧ 输出风格，例如 review 先报 findings，再报总结

不适合堆进去的，通常是这些：

‧ 会频繁波动的临时流程‧ 只有少量任务才用到的操作细节‧ 本来更适合沉淀成 command、skill 或脚本的步骤原因很简单。CLAUDE.md一旦被写成百科全书，它就会迅速失去两个最重要的属性：稳定性和可信度。团队成员不再确定它写的到底是现行规则，还是半年前遗留的讨论；系统也会学会一种很糟糕的行为模式：把过期规范当现行法律。

所以，团队 CLAUDE.md 的理想状态不是信息越多越好，而是内容稳定、几乎不需要争论。它更像地基，而不是公告栏。

# 8.4 复用的重点，先是验证定义，再是 skill 数量

落地 AI coding agent，最常见的失败不在 prompt，不在 model，也不在 skill 数量，而在团队对“完成”根本没有统一定义。

有人觉得能跑就行。有人觉得测试过一半就行。有人觉得模型解释得挺像样也行。这样一来，再聪明的系统也只能学会迎合最低标准。

Claude Code 源码里反复出现的一个倾向，是把 verification 从“顺手看看”提升成独立动作。前面提过 coordinator mode 会把 verification 单独抽出来；verify 相关约束也不只是在检查文件存在，更强调要证明改动确实起作用。

这对团队尤其关键，因为 skill 可以复制流程，但只有验证定义才能复制质量。

更现实的团队做法通常是先把下面三件事写清楚：

‧ 哪些任务必须有独立验证‧ 验证至少包含哪些动作，例如测试、运行、日志检查或人工验收‧ 验证失败时能不能标记为“已完成但带已知问题”

这三件事如果不清楚，后面任何自动化都只是在加速模糊。相反，只要这三件事先统一了，即使一开始 skill 很少，团队也能先把质量底线稳住。

所以，从落地优先级看，正确顺序通常是：

‧ 先统一验证定义‧ 再把高频流程沉淀成 skill 或命令‧ 最后才考虑更复杂的自动化编排

# 8.5 skill 更适合作为工作流模块来理解

很多团队第一次做 skill，最容易走偏的一点，就是把它当成“长一点的 prompt 模板”，或者反过来，把它神圣化成“组织制度切片”。

这两种理解都不够准确。

从 Claude Code 的实现看，SkillTool 显然不是一个随口参考的提示词仓库。匹配到 skill时必须实际调用；skill 已经加载过就不应重复加载；必要时它还会在 forked sub‑agentcontext 中执行，有自己的上下文边界和工具集合。

这说明 skill 至少是带执行语义的工作流模块，而不只是文本说明。

但落到团队实践时，更稳妥的理解仍然是：skill 先解决“高频任务如何稳定复用”。至于更重的制度职责，通常没必要一开始就全压在它身上。多数团队真正需要 skill 的场景，通常是这些：

‧ 某类改动每次都要重复同一组检查‧ 某类问题总要查同几份上下文某类任务需要固定输出物‧ 某类流程适合分给子代理独立完成

这时 skill 的价值在于把知识、顺序、边界和输出物打包成可重复调用的模块。

所以，团队做 skill 时，更值得先问的是：

‧ 这个 skill 到底服务哪类任务  
‧ 它默认能动哪些工具  
‧ 它是直接执行，还是应该 fork 给子代理‧ 调完以后应该留下什么结果，怎样验证

如果这些问题答不出来，skill 很快就会退化成名字好听、内容冗长、但谁也说不准实际会发生什么的“半自动口号”。

# 8.6 approval 的重点，是按风险分层

Claude Code 从权限判断到局部 allow rule 注入，始终在强调一件事：会做，不等于应该被允许做。

这一点在个人使用时容易被低估，因为个人往往愿意临场放权。可团队里不一样。一旦代理开始写文件、改 Git 状态、调网络、访问外部系统，它做的每一步都不只是技术动作，也是在移动责任边界。

但多数团队在这里也常犯另一个错误：一上来就想设计非常复杂的审批体系，结果落地成本极高，最后没人执行。

更现实的做法通常是先按风险分层，不必按工具名字一刀切。比如：

‧ 读文件、列目录、纯分析，通常风险较低‧ 改工作区、改配置、执行写操作，风险明显更高‧ 推 Git、打外网、访问敏感环境，风险再上一个等级

这种分层方式比“这个工具一律允许、那个工具一律禁止”更接近后果本身。因为团队真正要控制的，是不可逆性和环境敏感度，而不是按钮名称。

所以 approval 在团队落地中的价值，主要是把风险边界说清楚。边界一旦清楚，自动化才不会在错误的地方放大伤害。

# 8.7 hook 是高级能力，通常不必作为第一步

hooksConfigManager.ts 暴露了很多生命周期事件：SessionStart、SessionEnd、SubagentStart、SubagentStop、PreCompact、PostCompact、FileChanged、Di-rectoryChange 等。把这些事件放在一起看，会明白 hook 的真正价值：它让制度有机会在正确时机发生。

比如：

‧ instruction file 加载时补充组织级上下文  
‧ subagent 停止前补一轮验证compact 前后记录摘要session 结束时做归档或清理

这些都很有用。但更重要的是看清楚一件事：有用，不等于应该优先引入。

对多数普通研发团队来说，更常见的第一步会是：

‧ 仓库级说明文件code review 规则CI 和测试要求

‧ 少量高频命令或 skill

只有当使用规模、风险等级或合规要求继续上升时，hook 才开始真正体现价值。否则它很容易引入新的复杂度：脚本没人维护、触发时机没人说清、调试成本反而比人工操作更高。

因此，更成熟的判断是：hook 属于高级自动化接口，适合挂“时点动作”，也更适合放在基础治理已经稳定之后再引入。

# 8.8 可复盘轨迹很重要，但要分清基线层和高阶层

这一章最容易被说重的地方，就是“观测与审计”。

事情出错以后，团队当然需要知道为什么发生、从哪一步开始偏离、谁批准了关键动作。这一点没有问题。Claude Code 的实现里，日志、telemetry、task output、transcriptpath、hook event、agent notification 这些东西拼起来，确实构成了更强的复盘能力。

但现实里必须区分两层：

第一层是多数团队都会有、也已经足够支撑日常复盘的基线轨迹：

‧ Git diff 和 commit 记录 ‧ PR 评论与 reviewer 意见 ‧ CI 结果与测试日志 ‧ issue、任务单和验收结论 第二层才是更高阶的 agent 过程轨迹：

‧ transcript path  
‧ tool 调用记录  
‧ hook 事件compact 前后摘要  
‧ 子代理 usage 与状态变化

对大多数团队来说，真正的关键通常是先确认第一层没有缺口。因为很多团队连基本的验证和 review 都没统一，过早追求全链路 agent 审计，最后很容易把治理做成高成本摆设。

更合理的说法是：

# 第 8 章团队落地

‧ 基线层复盘能力，是团队采用 agent 的必需品‧ 高阶层审计轨迹，是高风险、高规模、强合规团队的增强项

把这两层分开，才不会把少数平台团队的治理要求误写成所有团队的通用起点。

# 8.9 从源码里可以提炼出的第八个原则

这一章最后更准确的压缩句，应该是：

团队落地的关键，是先把可接受边界、验证标准和高频工作流稳稳固定下来。

Claude Code 的源码给出的启发，真正可迁移的大概是这些：

‧ 指令要先分层，稳定规则和临时流程不要混在一起‧ skill 适合沉淀高频工作流，但前提是适用边界、工具范围和输出物清楚approval 应按风险和环境分层，不必按工具名字粗暴切割‧ hook 很强，但属于高阶能力，应该在基础治理稳住以后再引入‧ 复盘轨迹要分层建设，先保证基线层清楚，再决定是否上高阶审计

如果把它翻成团队可执行原则，大概会更接近下面这几条：

‧ 先定义可接受使用范围，再谈大规模推广  
‧ 先统一验证定义，再扩 skill 数量  
‧ 先用 review、CI 和最少说明文件把底线稳住，再引入 hooks 和复杂编排‧ 任何自动化流程都要能解释它做了什么，但不必一开始就追求全链路重审计‧ 团队更值得追求的，不是制度越堆越多，而是边界越清楚、系统越可承受

下一章是全书收束。前面几章一路讲下来，其实是在不断逼近同一个判断：模型是最不稳定的部件，所以真正要设计的，是如何让系统在它不可靠的前提下，仍然输出可承受、可验证、可纠偏的行为。

# 第 9 章 Harness Engineering 十条原则

写技术书有个坏习惯，讲完一堆细节以后，生怕下判断，仿佛只要把复杂性展示够了，就可以免除结论责任。其实不行。复杂归复杂，判断还是要下。因为团队真正带得走的，往往是若干能反复使用的原则，而不是某个版本的函数名。

前面八章绕来绕去，无非是在逼近这样一个事实：模型不可靠，但系统仍然可以可靠；  
前提是你别把可靠性寄托在模型身上，而要把它做进 harness。

这一章不再展开细讲，只把前面的论点压成十条原则。它们不是格言，也不是口号，它们来自 Claude Code 源码与工程结构里的工作判断。

# 9.1 把模型当不稳定部件，不要当同事

同事可以被信任地承担职责，模型不能。模型也许能像同事一样说话，但它不会自动获得同事那种稳定性、责任感和持续判断力。你越早承认这一点，系统就越早开始补上权限、恢复、验证和回滚。

# 9.2 Prompt 是控制面的一部分

system prompt 用来定义行为协议。它和 runtime、tool schema、memory、hook一起组成控制平面。把 prompt 当人格设定，最后你会得到一个很会表演、但不受约束的系统。

# 9.3 Query loop 才是代理系统的心跳

真正的 agent 依赖一段持续的执行循环。输入治理、流式消费、工具调度、恢复分支、停止条件，都是这个心跳的一部分。没有 query loop 的系统，也许能做 demo，但还谈不上运行时。

# 9.4 工具是受管执行接口

一旦模型开始碰 shell、文件系统、Git 和网络，问题就从“它会不会说”变成“它会不会留下后果”。所以工具必须被调度、被授权、被中断、被补账。越危险的工具，越不能按普通能力对待。

# 9.5 上下文是工作内存

能塞进上下文，不等于应该塞进去。长期规则、持久记忆、会话连续性和临时对话，应该分层治理。compact 的目标是保住继续工作的语义底座。好的上下文管理，标准不是”够多”，而是”可治理”。

# 9.6 错误路径就是主路径

prompt too long、max output tokens、中断、hook 回环、compact 自身失败，这些都是长会话代理迟早要面对的日常天气。恢复、熔断、限次、防死循环，必须在设计时就存在，而不是出问题以后再补。

# 9.7 恢复的目标是继续工作

截断之后最好的动作，通常是续写；压缩失败时最重要的是先让系统恢复呼吸。工程系统真正的礼貌，在于别把用户困在失败态里。

# 9.8 多代理的意义，是把不确定性分区

多代理会把研究、实现、验证、综合放进不同职责容器里。隔离状态，分离角色，最后由 coordinator 收束理解。并行真正带来的价值，不是更快，而是让职责边界更清楚。

# 9.9 验证必须独立，不能让系统自己给自己打分

实现者天然倾向于相信自己的改动“差不多行了”。模型更是如此。凡是重要任务，验证都应该成为独立阶段，最好还有独立角色。否则所谓“完成”，很快就会退化成“已经写

完并且我觉得没问题”。

# 9.10 团队制度比个人技巧重要

一个高手可以靠经验把代理驯服，一个团队不行。团队需要的是：

‧ 分层 CLAUDE.md‧ 明确 approval可执行 skill‧ 生命周期 hook‧ 可追踪 transcript‧ 统一验证定义

只有把个人经验制度化，代理系统才可能成为组织能力，而不是个人把戏。

# 9.11 最后一句话

如果一定要把全书再缩成一句话，那大概就是：

Harness Engineering 关心的是：在模型并不可靠的前提下，系统仍然能表现出工程系统应有的行为。

Claude Code 的源码真正教人的，是这种克制：它始终把不稳定性当已知前提，再围着这个前提设计 prompt、loop、tools、memory、compact、recovery、verification和 team workflow。也正因为如此，它值得被当作设计样本。

书写到这里，结论其实已经比过程简单。难的从来不在把原则说出来，而在愿不愿意承认：Harness 比激情重要，制度比聪明重要，验证比自信重要。谁把这三句话听进去了，大概就已经站在 Harness Engineering 的门口了。

# 附录 A 检查清单：把原则落成能执行的约束

前面几章一直在谈原则。原则如果不能落成检查清单，最后很容易只剩一些听起来都对、却落不了地的判断。附录的任务，就是把那些容易说、难坚持的判断，压成几组可以直接拿去用的清单。

这些清单并不保证系统自动变好，它们只是防止一些最常见、也最无聊的错误反复出现。  
工程里很多进步，本来就靠少犯重复错误，而不只是靠灵感。

# A.1 Agent Runtime 设计清单

一个 AI coding agent 如果要进入真实工程工作流，至少该回答清楚这些问题：

‧ 是否存在明确的 query loop，而非把每轮调用都当作独立问答‧ 是否有跨轮状态对象，明确记录恢复、预算、压缩、hook、turn 计数等信息‧ 是否把模型输出当事件流处理，而不只是当最终文案处理是否能在中断时补齐未完成的 tool result，保持执行账本闭环‧ 是否区分完成、失败、恢复、继续这些不同终止语义‧ 是否为长会话设计了 context budget，而非只在超长时临场补锅

如果这些问题里有两三个答不上来，那么这个系统大概率还停留在“会做 demo”的阶段，离“会跑工程流程”还有距离。

# A.2 Prompt 设计清单

system prompt 不该只是长，也该有分层和职责。

检查时至少看这些：

# 附录 A 检查清单

‧ 是否把身份描述、行为规则、工具约束、输出纪律分开组织  
‧ 是否明确 prompt 的优先级来源，例如默认、项目、自定义、追加、agent 专属prompt  
是否把危险动作、越权动作、验证纪律写成明确规则，而非隐约暗示  
‧ 是否避免让 prompt 承担本该由 runtime 处理的职责  
‧ 是否允许团队稳定维护，而非每次修 bug 都往 prompt 里再塞一段话一个很实用的判断标准是：删掉某段 prompt 以后，系统行为会不会出现结构性变化。  
如果会，说明它真是控制面；如果不会，可能只是装饰。

# A.3 Tool 与 Permission 设计清单

凡是让模型碰世界的系统，都该先问这些：

‧ 工具调用是否经过统一调度，而非让模型直接裸调‧ 并发是否需要显式证明安全，而非默认允许是否存在 allow / deny / ask 这样的权限语义分叉高风险工具是否被当成特例治理，而非与普通工具一视同仁是否能对中断、fallback、sibling failure 生成明确收尾语义是否能记录工具执行因果链，避免出现悬空 tool_use

如果你的 Bash 和 ReadTool 在治理上几乎一样，那通常说明风险理解得还不够。

# A.4 Context 治理清单

任何长会话代理，迟早都会被上下文教育。早点治理，代价比较低。

检查时至少看这些：

‧ 长期规则、长期记忆、会话连续性、临时对话是否分层  
‧ 是否有明确入口文件和正文文件的区分，避免索引型文件不断膨胀  
‧ 是否对 memory、session memory、skill 附件设 token 预算是否预留 compact 输出空间，而非把窗口吃满再抢救compact 之后是否恢复工作语义，例如计划、技能、关键文件、工具状态  
‧ 是否对 compact 自己失败也准备了恢复策略

上下文治理做得好的系统，往往看起来有点吝啬。那种吝啬通常是优点，不是缺点。

# A.5 Error Recovery 设计清单

错误恢复最怕两件事：没有设计，和设计成死循环。

至少要检查：

‧ 可恢复错误是否先进入恢复分支，而非第一时间只展示给用户  
‧ 恢复路径是否分层，先低破坏性，再高破坏性  
‧ 是否有防止 reactive compact、stop hooks、retry 相互咬住的保护max_output_tokens 后是否优先续写，而非优先 recap  
自动恢复是否有计数、限次和熔断  
‧ 中断是否也被当作需要语义收尾的失败态

一个不会收手的恢复系统，和一个不会恢复的系统一样危险，只是它危险得更勤奋一点。

# A.6 Multi‑Agent 设计清单

多代理的重点在于组织不确定性。检查时要看：

‧ fork 时是否考虑 prompt cache 共享和 cache‑safe 参数一致性  
‧ 子代理默认是否隔离 mutable state  
‧ 是否区分 research、implementation、verification、synthesis 角色  
coordinator 是否真正承担综合理解，而非只转发 worker 结果  
‧ verification 是否独立于 implementation  
‧ agent 生命周期是否可观测、可中止、可清理  
‧ 父 abort 是否能传播到子代理，防止孤儿任务残留

如果一个系统号称 multi‑agent，但所有 agent 都在做差不多的事，而且没人真正负责synthesis 和 verification，那它通常只是在把混乱扩成并行。

# A.7 Team 落地清单

团队推广时，最容易误判的一点，是把个人熟练度误当成制度成熟度。

落地前最好先核对：

‧ 是否已有分层 CLAUDE.md，且团队知道什么该写进去、什么不该写

‧ 是否先统一验证定义，再批量造 skill  
‧ 是否按后果和环境敏感度划 approval 边界是否把关键制度挂在合适 hook 时点，而非全塞进静态文档  
‧ 是否保留 transcript、task output、hook event 等复盘证据  
‧ 是否有对 stale memory、过期规则、失效 skill 的维护机制

一个团队真正能承受代理系统，往往是因为普通成员也能在制度内把它用对，而不只是依赖几个高手。

# A.8 Review 问题单

如果你要 review 一个 AI coding agent 方案，可以直接追问下面这些问题：

‧ 哪些行为由 prompt 约束，哪些由 runtime 强制？  
‧ 模型误用工具时，谁来拦？在哪里拦？  
‧ 上下文何时压缩，压缩后如何恢复工作语义？  
‧ prompt too long 和 max output tokens 分别怎么恢复？  
‧ 中断后怎样保证 transcript 和工具结果一致？  
‧ 多代理里谁负责 synthesis，谁负责 verification？  
‧ 失败恢复有没有熔断和防死循环机制？  
‧ 团队如何审计代理做过什么、为什么这么做？

一个方案如果在这些问题上总回答“到时候可以再加”，通常说明它现在还没有真正设计运行时，只是设计了一个乐观场景。

# A.9 最后一个清单

如果嫌前面都太长，那至少记住这六条：

‧ 先设计权限，再设计能力  
‧ 先设计回滚，再设计自治  
‧ 先设计验证，再设计交付  
‧ 先设计上下文预算，再设计长期对话  
‧ 先设计生命周期，再设计多代理  
‧ 先设计制度，再指望团队熟练

做到这六条，系统未必立刻优秀；做不到这六条，系统大概率只是暂时没出事。

# 附录 B 图示：把运行时骨架画出来

前面的章节一直在用文字解释运行时结构。文字当然能说清楚，但有些东西画成图以后，读者会更快意识到：Claude Code 是一套相当明确的状态机，不只是“一团 prompt 加几个工具”。

![](images/2505e5543997b60cafb6b12f6bda0f4e5c8d71d2362d28289e919ff4a90d585d.jpg)  
B.1 图一：Claude Code 总体控制面  
图 9: Claude Code 总体控制面

这张图不该画成“用户 $_ - >$ 模型 $_ - >$ 工具 $_ - >$ 输出”那种幼儿读物，因为那种画法会把真正重要的器官都藏起来。更合理的理解方式，是把 Claude Code 分成五层：

1. 用户交互层  
2. 控制面层  
3. 执行循环层  
4. 外部能力层  
5. 持久化与观测层

图的重点是强调以下几点，而不是把模块都列全：

‧ 模型不在最上层，也不在最底层‧ 模型只是 query loop 中的一环‧ 真正把系统绑在一起的，是控制面和恢复面

![](images/73e7c3380bcea21dc1a35a4d220b2cb5eaa38849d11884f739d4d84cc63592bf.jpg)  
B.2 图二：Query Loop 主循环与恢复分支  
图 10: Query Loop 主循环

![](images/aa7187a1e5129756101dbd2f87255c2e2c535ae171c8724a369f432a90cb1cf6.jpg)  
图 11: Query Loop 恢复分支

![](images/503e4f0cedd26bffafd9373c331b73360f708a8b169857d69e24ee91d1bcc3e5.jpg)  
图 12: Tool Batch Ordering

# B.3 图三：Tool Batch Ordering 与 StreamingToolExecutor

B.4 图四：Context Sources 与 Compact Rebuild

B.5 图五：Coordinator‑Worker Flow 与 Verification Separation

B.6 图六：团队治理图

![](images/013eedc4b09cbf4114b0e9640bc3c69cb71782289603111af3547629977c715a.jpg)  
图 13: StreamingToolExecutor Lifecycle

![](images/147ad6933dcb1c6983fc3862bf126a8d6bc1b862d2c7b9a75bd53173848db7c6.jpg)  
图 14: Context Sources And Budget

#

![](images/bc632dc1d7cdd4d4cf6a452df7a2815122fa7ba70dd65ebfcebc0ec5fa10d195.jpg)  
图 15: Compact Rebuild Pipeline

![](images/8240ffb7554391ca2a72ac0c895f26f3ec3e86a111a92272b2c4a49704de96d6.jpg)  
图 16: Coordinator And Worker Flow

![](images/b414d361f7a9a27d1dfa52c5fe88e8dec2187221162724acdcb4e2e894bc112f.jpg)  
图 17: Verification Separation

![](images/ec7d149a5ee016ba99dea45097374902c7f753b16563e5dd1fcc06fb9d7074b3.jpg)  
图 18: 团队治理图

# 附录 C 源码地图：本书各章主要依据哪些文件

这本书虽然不是源码导读，但终究是基于源码写的。这里把每一章最主要的依据文件整理成一份地图。

这份地图不是完整索引，只列与本书论点直接相关的主文件。

这里也补一句版权边界：这份源码地图的作用，是说明分析依据来自哪些文件，而不是承诺随内容提供这些文件的正文内容。这里仅保留必要的工程性引用、模块定位和结构分析，不附源码副本，不做大段实现转载。

# C.1 第 1 章为什么需要 Harness Engineering

# 核心文件：

src/constants/prompts.ts   
src/utils/systemPrompt.ts   
src/query.ts   
src/services/tools/toolOrchestration.ts   
src/tools/BashTool/prompt.ts

# 本章主要论点来源：

‧ prompt 属于控制面组成部分，而不是人格包装‧ query loop 才是代理系统骨架‧ 工具和 Bash 风险说明 harness 的必要性

# C.2 第 2 章 Prompt 是控制面，不是人格装修

# 核心文件：

src/constants/prompts.ts   
src/utils/systemPrompt.ts   
src/utils/claudemd.ts   
src/memdir/memdir.ts   
src/constants/systemPromptSections.ts   
src/main.tsx

# 本章主要论点来源：

‧ system prompt 的分层拼装  
‧ CLAUDE.md 与 memory 作为控制面输入  
‧ 动态系统提醒与上下文注入

# C.3 第 3 章 Query Loop：代理系统的心跳

# 核心文件：

src/query.tssrc/QueryEngine.ts本章主要论点来源：

‧ query loop 的状态机性质  
‧ 输入治理先于模型调用  
‧ 流式事件消费与恢复分支  
‧ QueryEngine 对 conversation lifecycle 的所有权

# C.4 第 4 章工具、权限与中断

# 核心文件：

# 附录 C 源码地图

‧ src/services/tools/toolOrchestration.ts src/services/tools/toolExecution.ts src/services/tools/StreamingToolExecutor.ts src/hooks/useCanUseTool.tsx src/utils/permissions/PermissionResult.ts src/tools/BashTool/prompt.ts src/tools/BashTool/bashPermissions.ts

# 本章主要论点来源：

‧ 并发安全与上下文顺序回放  
‧ 工具执行包裹层allow / deny / ask 权限语义  
‧ streaming 工具中断与 synthetic result  
‧ Bash 的特殊高压治理

# C.5 第 5 章上下文治理：Memory、CLAUDE.md 与Compact

# 核心文件：

src/utils/claudemd.ts   
src/memdir/memdir.ts   
src/services/SessionMemory/prompts.ts   
src/services/compact/autoCompact.ts   
src/services/compact/compact.ts   
src/query.ts

# 本章主要论点来源：

‧ CLAUDE.md 的分层发现和加载  
‧ MEMORY.md 作为入口索引而非正文仓库session memory 的结构化连续性  
‧ autocompact 阈值、buffer 与 circuit breaker  
‧ compact 后的工作语义重建

# C.6 第 6 章错误与恢复

# 核心文件：

src/query.ts src/services/compact/autoCompact.ts src/services/compact/compact.ts src/services/api/withRetry.ts

# 本章主要论点来源：

withheld recoverable errors  
prompt‑too‑long 的 collapse drain 与 reactive compact  
max_output_tokens 的 escalate 与 resume  
autocompact failure 熔断  
compaction 自身 PTL 重试

# C.7 第 7 章多代理与验证

# 核心文件：

‧ src/utils/forkedAgent.ts src/coordinator/coordinatorMode.ts src/tasks/LocalAgentTask/LocalAgentTask.tsx src/utils/hooks/hooksConfigManager.ts src/skills/bundled/verify.ts src/memdir/memoryTypes.ts

# 本章主要论点来源：

‧ forked agent 的 cache‑safe 参数与状态隔离  
‧ coordinator 的 synthesis 责任verification 独立成阶段subagent lifecycle hook  
‧ task cleanup 与父子 abort 传播  
‧ 对 stale memory 的 verify discipline

# C.8 第 8 章团队落地

# 核心文件：

src/utils/claudemd.ts   
src/tools/SkillTool/prompt.ts   
src/tools/SkillTool/SkillTool.ts   
src/utils/forkedAgent.ts   
src/utils/hooks/hooksConfigManager.ts   
src/main.tsx

# 本章主要论点来源：

‧ 团队 CLAUDE.md 的分层稳定性  
‧ skill 作为制度切片而非 prompt 收藏夹  
‧ approval 边界与 allow rules  
‧ hook 生命周期治理  
‧ session startup 与 instructions / skill loading

# C.9 第 9 章十条原则

第 9 章并非直接从单一文件推出，它是对前面所有章节的压缩。它的依据，就是全书已经使用过的这些核心模块共同呈现出的系统结构：

prompt assembly query loop tool orchestration permission model context governance recovery system multi‑agent orchestration ‧ team governance hooks
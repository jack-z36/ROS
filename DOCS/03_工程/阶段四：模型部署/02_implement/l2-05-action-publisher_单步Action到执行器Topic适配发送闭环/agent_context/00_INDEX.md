# L2-05 Agent 上下文索引

> [!info] 产物归属
> - 消费对象：L3 生成 Agent、实现 Agent、验收 Agent、L2 Gate 与 Git 合入流程。
> - 权威性：本目录 Markdown 是 L2-05 的 Agent 权威上下文；根目录 HTML 仅是人类低密度投影。
> - `l2_id`：`l2-05-action-publisher`
> - L2 名称：单步 Action 到执行器 Topic 适配发送闭环。
> - `l2_design_dir`：`l2-05-action-publisher_单步Action到执行器Topic适配发送闭环`
> - 人类入口：`../L2架构交互可视化.html`
> - 上游来源：当前 L1 任务/架构 Markdown，以及用户在 2026-07-10 指定的 L2-05 详细功能边界约束。
> - 不负责范围：本目录不生成 L3 卡片、不实现源码、不授权真机动作。
> - 读取时机：设计 L3、实现 action publisher、验收 shadow/safe-run 或判断 L2 Gate 前必须读取。
> - 冲突处理：HTML 与 Markdown 冲突时以 Markdown 为准；当前 checkout 的旧 L1 L2-05 段落与用户详细约束冲突时，以本包记录的用户确认边界为准，并在上游同步前阻止合入。

## 权威关系

```text
用户指定的 2026-07-10 L2-05 详细边界
  -> 本目录 Agent Markdown
  -> 根目录 L2架构交互可视化.html
```

- HTML 不用于生成 L3。
- 语义修改顺序固定为：先改本目录 Markdown，再同步 HTML。
- 本包只完成 L2 设计；不创建 `03_tasks/`、dispatch、验收卡片或 `src/model_deploy/act/` 实现。
- `Pi0.5` 只提供结构证据。它的 14D joint、bridge/mux 订阅与 shadow command 行为不能覆盖本 L2 的 16D TCP 输出边界。

## 路由表

| 读取目的 | 必读文件 |
|---|---|
| 确认最终输入、输出、模式、负责/不负责、状态、上下游与完成判据 | `01_L2功能边界.md` |
| 查 Pi0.5 对应源码、3.5 层微元、class 封装、差异和复用判断 | `02_pi05源码3.5层微元拆解.md` |
| 查 ACT 微元、class/function 决策、创建顺序、状态所有权和失败传播 | `03_ACT微元设计与协作.md` |
| 查 AI 侧 Gate、required L3 草案、验证层级、命令和阻断项 | `04_L2验收机制.md` |
| 查人类可执行清单、观察点、风险、真机限制和签字格式 | `05_人类验收机制.md` |
| 查 `types/` 公共 RAM 契约设计 | `06_types层设计.md` |
| 查 `config/` 输出映射配置的窄扩展设计 | `07_config层设计.md` |
| 确认 `repo/` 不新增产物及验证方式 | `08_repo层设计.md` |
| 查 `service/` 的纯 RAM 拆分、映射和发布计划构造 | `09_service层设计.md` |
| 确认 `runtime/` 不新增产物及 L2-06 所有权 | `10_runtime层设计.md` |
| 查 `ui/` ROS publisher、模式门控、deadband 和 status 设计 | `11_ui层设计.md` |

## HTML-MD 语义对齐表

| HTML view id | HTML view label | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `boundary`（radio `v1`） | 维度1 · 功能边界 | 唯一 ROS 出口、四项 RAM 输入、两条并行输出通道、模式门控和边界墙 | `agent_context/01_L2功能边界.md` | `## 1. 一句话运行时职责`、`## 2. 输入`、`## 3. 输出`、`## 4. 模式矩阵`、`## 5. 负责内容`、`## 6. 不负责内容` | 完整字段、四路本地原子性边界、最小状态、上游漂移审计和完成判据 |
| `pi05map`（radio `v2`） | 维度2 · Pi0.5 如何运作 | 旧实现如何经 deploy node、bridge、mux 发出 14D joint 命令，以及为什么不能照搬 | `agent_context/02_pi05源码3.5层微元拆解.md` | `## 1. 白话运行机制`、`## 2. 源码范围与差异`、`## 3. Pi0.5 源码 3.5 层微元拆解`、`## 4. class 封装盘点` | 精确路径/对象/行号、状态与并发、复用等级和逐项风险 |
| `blueprint`（radio `v3`） | 维度3 · 开发蓝图 | types/config/service/ui 四层产物、repo/runtime 无产物、微元与 class/function 协作 | `agent_context/03_ACT微元设计与协作.md`、`agent_context/06_types层设计.md`、`agent_context/07_config层设计.md`、`agent_context/08_repo层设计.md`、`agent_context/09_service层设计.md`、`agent_context/10_runtime层设计.md`、`agent_context/11_ui层设计.md` | `## 2. ACT 微元设计`、`## 3. 内部协作`、六层设计文件全文 | 函数签名、消息类型决策、依赖方向、错误行为、测试落点和上游兼容风险 |
| `acceptance`（radio `v4`） | 维度4 · 人类验收标准 | 如何证明 dry/shadow/safe 三模式、四路门控、映射、deadband、status 和无硬件越界 | `agent_context/04_L2验收机制.md`、`agent_context/05_人类验收机制.md` | `## 2. Required L3 草案`、`## 3. Gate 验收矩阵`、`## 4. 验证命令`、`## 2. 人类验收清单` | BLOCKED_ENV/HARDWARE 处理、签字格式、下游放行和 Git 合入条件 |

## 已锁定设计决策

| 决策 | 结论 |
|---|---|
| `/act/policy_action` 方向 | 纯输出；不订阅，不是 command bridge 中间输入。 |
| 输出拓扑 | 观测通道与四路 command 从同一 safe action 并行派生，独立门控。 |
| action 语义 | 输入始终是 16D TCP action；夹爪输入为 `[0,1]`，仅在 L2-05 映射为 `0..100`。 |
| ROS transport | policy=`Float32MultiArray`，arm=`PoseStamped`，gripper=`Float64`，status=`String(JSON)`；内部仍使用类型化结果对象。 |
| class 选择 | 一个长生命周期 `ActionPublisher` 持有 publisher 与夹爪防刷最小状态；纯映射保持函数。 |
| 运行模式 | dry-run 不要求 ROS；shadow-run 只发 policy/status；safe-run 仅在最终授权允许时发四路 command。 |
| 真机 | 默认不执行；real-robot 必须另行授权、急停就绪并先有 shadow 证据。 |

## 污染与漂移检查

- 旧 layer-based ID `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware` 仅允许出现在本行的旧资料污染检查中。
- 旧 `ACT Contract Delta` 与旧 `AS-IS Contract -> TO-BE Contract -> Contract Delta` 仅允许作为禁止继承的历史语义出现。
- 旧阶段二开发范式与旧 `L2能力模块说明文件模板` 禁止作为本包模板来源。
- 当前 checkout 的 L1 L2-05 段仍含“订阅/串行 bridge/workspace/IK”漂移；后续 Agent 不得据此覆盖本包已确认边界。
- 当前 L2-04 设计若把 safe action 的夹爪段解释为 `0..100`，属于跨 L2 契约漂移；L2-05 Gate 必须要求上游保持 `[0,1]`。

## 开放决定

无待询问用户的设计决定。用户已要求后续采用最佳判断一口气完成。ROS 环境与真实硬件是否存在属于验收阻断状态，不属于设计歧义。

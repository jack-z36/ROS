# L2-05 Agent 上下文索引

> [!info] 产物归属
> - 消费对象：L3 生成 Agent、实现 Agent、验收 Agent、L2 Gate 与 Git 合入流程。
> - 权威性：本目录 Markdown 是 L2-05 的 Agent 权威上下文；根目录 HTML 仅是人类低密度投影。
> - `l2_id`：`l2-05-action-publisher`
> - L2 名称：单步 Action 到执行器 Topic 适配发送闭环。
> - `l2_design_dir`：`l2-05-action-publisher_单步Action到执行器Topic适配发送闭环`
> - 人类入口：`../L2架构交互可视化.html`
> - 上游来源：当前 L1 任务/边界/协作 Markdown，以及用户在 2026-07-13 确认的“三编排函数 + CLI 总开关 + 动态许可 + 单一 pose frame”设计。
> - 不负责范围：本目录不生成 L3 卡片、不实现源码、不授权真机动作。
> - 读取时机：设计 L3、实现 action publisher、验收观察链路或判断 L2 Gate 前必须读取。

## 权威关系与 HTML 状态

```text
用户 2026-07-13 确认的 L2-05 新设计
  -> 本目录 Agent Markdown
  -> 根目录 L2架构交互可视化.html（待同步投影）
```

- HTML 不用于生成 L3。
- 语义修改顺序固定为：先改本目录 Markdown，再同步 HTML。
- **当前 HTML 状态：`STALE_PENDING_SYNC`。** 本次用户只指定更新 `agent_context/`；HTML 仍含旧 `dry-run / shadow-run / safe-run` 和旧 A/B/C 微元，不得作为当前设计依据。
- 在 HTML 同步并通过验证前，本 L2 **不具备 L3 生成就绪状态**。
- 本包不创建 `03_tasks/`、dispatch、验收卡片或 `src/model_deploy/act/` 实现。
- Pi0.5 只提供结构证据；其 14D joint、bridge/mux 订阅和 mode 状态机不能覆盖当前 16D TCP 输出边界。

## 路由表

| 读取目的 | 必读文件 |
|---|---|
| 确认输入、输出、CLI 总开关、动态许可、负责/不负责、状态和完成判据 | `01_L2功能边界.md` |
| 查 Pi0.5 对应源码、3.5 层微元、class 封装、差异和复用判断 | `02_pi05源码3.5层微元拆解.md` |
| 查 ACT 微元、三编排函数、class/function 决策、状态所有权和失败传播 | `03_ACT微元设计与协作.md` |
| 查 A/B/C 编号权威、总量、父子关系、调用树和上游复用对象（L3 切片前必读） | `03a_功能微元总览与组织结构.md` |
| 查 AI 侧 Gate、required L3 草案、验证层级、命令和阻断项 | `04_L2验收机制.md` |
| 查人类可执行清单、观察点、风险、真机限制和签字格式 | `05_人类验收机制.md` |
| 查 `types/` 公共 RAM 契约设计 | `06_types层设计.md` |
| 查 `config/` CLI 总开关与输出映射配置 | `07_config层设计.md` |
| 确认 `repo/` 不新增产物及验证方式 | `08_repo层设计.md` |
| 查 `service/` 的 B1 纯 RAM Topic 载荷生成 | `09_service层设计.md` |
| 确认 `runtime/` 不新增产物及 L2-06 所有权 | `10_runtime层设计.md` |
| 查 `ui/` 的 B2 ROS message 打包与 B3 选择/发布 | `11_ui层设计.md` |

## HTML-MD 语义对齐表

| HTML view id | HTML view label | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `boundary`（radio `v1`） | 维度1 · 功能边界 | 消费四类 RAM 输入，经三编排函数输出 policy、可选四路 command、status 和 RAM result | `agent_context/01_L2功能边界.md` | `## 1. 一句话运行时职责`、`## 2. 输入`、`## 3. 输出`、`## 4. 发布决策`、`## 5. 负责内容`、`## 6. 不负责内容` | CLI 总开关与动态许可双条件、最小状态、失败/部分发布语义 |
| `pi05map`（radio `v2`） | 维度2 · Pi0.5 如何运作 | 旧实现如何经 deploy node、bridge、mux 发出 14D joint 命令，以及为什么只能结构参考 | `agent_context/02_pi05源码3.5层微元拆解.md` | `## 1. 白话运行机制`、`## 2. 源码范围与差异`、`## 3. Pi0.5 源码 3.5 层微元拆解`、`## 4. class 封装盘点` | 精确路径/对象/行号、状态与并发、复用等级和逐项风险 |
| `blueprint`（radio `v3`） | 维度3 · 开发蓝图 | A1 class、B1-B3 三编排函数、C1-C21 原子微元和 types/config/service/ui 落点 | `agent_context/03a_功能微元总览与组织结构.md`、`agent_context/03_ACT微元设计与协作.md`、`agent_context/06_types层设计.md`、`agent_context/07_config层设计.md`、`agent_context/08_repo层设计.md`、`agent_context/09_service层设计.md`、`agent_context/10_runtime层设计.md`、`agent_context/11_ui层设计.md` | `03a` 的 `## 2. 总量与分层` / `## 3. 调用树`；`03` 的 `## 2. ACT 微元设计` / `## 4. 三编排函数`；六层文件全文 | A/B/C 编号权威、字段级数据结构、函数签名、错误行为、依赖方向和测试落点 |
| `acceptance`（radio `v4`） | 维度4 · 人类验收标准 | 如何证明 CLI 默认关闭、动态许可门控、三编排函数、status 和无硬件越界 | `agent_context/04_L2验收机制.md`、`agent_context/05_人类验收机制.md` | `04` 的 `## 2. Required L3 草案` / `## 3. Gate 验收矩阵` / `## 4. 验证脚本设计`；`05` 的 `## 2. 人类验收清单` | BLOCKED_ENV/HARDWARE、签字格式、下游放行和 Git 合入条件 |

> [!warning] HTML 漂移
> 上表描述的是 HTML 应同步到的目标语义，不代表当前 HTML 已对齐。HTML 同步前只能读取本目录 Markdown。

## 已锁定设计决策

| 决策 | 结论 |
|---|---|
| 运行模式 | L2-05 不再使用 `dry-run / shadow-run / safe-run` 运行模式枚举。 |
| 人工总开关 | 启动 CLI `--enable-command-output`；未显式传入时 `command_output_enabled=False`。 |
| 动态许可 | L2-06 每 tick 提供 `CommandPermit(allowed, reason_code)`；不重复携带 mode。 |
| command 发布条件 | `command_output_enabled AND CommandPermit.allowed`；任一为假时只发布 policy/status。 |
| 三编排函数 | B1 `build_topic_payloads` → B2 `build_ros_messages` → B3 `ActionPublisher.publish` 选择并写出。 |
| status 时机 | `/act/command/status` 必须在真实发布事实形成后构造，不能进入 B2 的候选消息 bundle。 |
| action 语义 | 16D TCP action；夹爪输入 `[0,1]`，仅在 B1 映射为 `0..100`。 |
| frame | 第一版使用单一 `pose_frame_id`；无 TF 转换时禁止把相同数值分别贴成不同左右 base frame。 |
| ROS transport | policy=`Float32MultiArray`，arm=`PoseStamped`，gripper=`Float64`，status=`String(JSON)`。 |
| class 选择 | 一个长生命周期 `ActionPublisher` 持有六 publisher、夹爪防刷最小状态和最近结果；B1/B2 为无状态函数。 |
| 真机 | 默认不执行；真实命令还必须有 L2-06 动态许可、急停就绪和人工授权证据。 |

## 污染与漂移检查

- 旧 layer-based ID 只允许出现在本行污染检查中，不得定义当前边界。
- 旧 `ACT Contract Delta` 和阶段二模板不得作为当前任务来源。
- Pi0.5 的 14D、JointState、bridge/mux subscription、raw deadman 和 mode 状态机不得进入当前实现。
- 当前 L1 L2-05 段仍含 latest state、workspace/IK 和旧 mode 语义；上游未同步前不得覆盖本包边界。
- 当前源码 `SafetyResult` 使用 `status/action/findings`；任何 `result.accepted` 设计均为过期语义。
- 当前源码 `RuntimeConfig.mode` 及 `publishes_command_topics` 属待迁移旧配置；L2-05 实现不得消费它们。
- `command_output_enabled` 只能由显式 CLI 启动参数置真，不能因持久化 YAML 默认值意外开启。

## 开放项与阻断项

- 用户设计决定：已全部确认。
- 阻断项 1：根目录 HTML 尚未同步本轮 Agent Markdown。
- 阻断项 2：当前 L1 边界/协作文档尚未同步新的 CLI 总开关和 frame 语义。
- 阻断项 3：源码尚无 `types/action_publish.py`、`service/action_output_adapter.py`、`ui/action_publisher.py` 等 L2-05 实现；这是后续 L3 范围。

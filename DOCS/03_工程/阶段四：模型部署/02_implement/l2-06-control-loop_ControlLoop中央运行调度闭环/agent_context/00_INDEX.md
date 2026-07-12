# L2-06 ControlLoop 中央运行调度闭环：Agent 入口

- `l2_id`：`l2-06-control-loop`
- 人类入口：`../L2架构交互可视化.html`。
- Agent 权威：本目录 Markdown；HTML 只做可视化投影，不能用于生成 L3。

## 阅读路由

| 目的 | 读取文件 |
|---|---|
| 先确认职责、上下游与禁区 | `01_L2功能边界.md` |
| 回看 Pi0.5 结构证据 | `02_pi05源码3.5层微元拆解.md` |
| 实现前获得状态机、协作与拟议产物 | `03_ACT微元设计与协作.md` |
| 实现前确认 A/B/C 编号、调用树与复用对象 | `03a_功能微元总览与组织结构.md` |
| 写 Gate 或验证脚本 | `04_L2验收机制.md` |
| 人工 / 真机前验收 | `05_人类验收机制.md` |
| types 无新增的理由 | `06_types层设计.md` |
| config 无新增的理由 | `07_config层设计.md` |
| repo 无新增的理由 | `08_repo层设计.md` |
| service 无新增的理由 | `09_service层设计.md` |
| runtime 状态机实施 | `10_runtime层设计.md` |
| UI timer/装配实施 | `11_ui层设计.md` |

## HTML-MD 语义对齐表

| HTML view id | HTML view label | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `boundary` | 功能边界 | 中央 tick 负责什么、何时 fallback | `agent_context/01_L2功能边界.md` | `## 运行责任与边界` | 完整输入输出、开放决策 |
| `pi05map` | Pi0.5 如何运作 | 旧程序的 timer、queue、worker 如何协作 | `agent_context/02_pi05源码3.5层微元拆解.md` | `## 源码证据与复用结论` | 精确路径、行范围、风险 |
| `blueprint` | 开发蓝图 | 新 ACT 的真实 tick 调用方向、A/B/C 微元与六层落点 | `agent_context/03a_功能微元总览与组织结构.md`、`agent_context/03_ACT微元设计与协作.md`、`agent_context/06_types层设计.md` 至 `agent_context/11_ui层设计.md` | `## 运行时调用树`、`## tick 状态机`、`## 六层落点` | 函数签名、状态所有权、依赖方向 |
| `acceptance` | 人类验收标准 | 后续如何跑验证脚本并理解输出 | `agent_context/04_L2验收机制.md`、`agent_context/05_人类验收机制.md` | `## 4. 验证脚本合同`、`## 人类验收清单` | Gate 分层、阻断与签字记录 |

## 污染检查

本包以 L1 任务、模块边界和协作架构为权威；Pi0.5 仅为只读结构参考。禁止把旧 layer-based L2、阶段二模板、归档任务或 Contract Delta 当作本包输入。第一版不包含 action smoothing、跨 chunk 融合或 RTC 对齐。

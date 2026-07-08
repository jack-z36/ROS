# L2-01 Agent 上下文索引

> [!info] 产物归属
> - 类型：L2 设计包内 Agent 消费入口。
> - `l2_id`：`l2-01-external-contract`
> - 人类入口：`../L2架构交互可视化.html`
> - 本目录职责：集中收纳 L2-01 的高密度、结构化、可检索 Markdown 上下文。
> - 本目录不负责：提供低密度人类浏览体验；人类优先打开根目录 HTML。

## 权威关系

- L3 生成、实现、验收和 Gate 判断必须以本目录 Markdown 为权威。
- `../L2架构交互可视化.html` 只服务人类快速理解；与本目录冲突时，以本目录 Markdown 为准。
- 本目录文件的 L2 边界继承自当前 L1 任务文档和 L1 Agent 架构文档，不继承旧 layer-based L2、旧 Contract Delta 或阶段二模板。
- 本 L2-01 第一版明确不定义 action smoothing、smoothstep blend、跨 chunk 融合、RTC 类平滑或复杂时间对齐配置；这些是后续优化，不进入当前 Gate。

## 路由表

| 读取目的 | 必读文件 |
|---|---|
| 确认 L2 身份、输入输出、负责/不负责、上下游和完成判据 | `01_L2功能边界.md` |
| 查 Pi0.5 源码对应对象、3.5 层微元、class 封装和复用判断 | `02_pi05源码3.5层微元拆解.md` |
| 查 ACT 微元、class/function 决策、协作关系、状态归属和失败传播 | `03_ACT微元设计与协作.md` |
| 查 AI 侧 L2 Gate、required L3 草案、自动化验收命令和通过/失败现象 | `04_L2验收机制.md` |
| 查人类验收清单、运行命令、观察点、风险和签字入口 | `05_人类验收机制.md` |
| 查 `types/` 层目标源码路径、职责、数据结构、函数和验收覆盖 | `06_types层设计.md` |
| 查 `config/` 层目标源码路径、配置 schema、校验器和验收覆盖 | `07_config层设计.md` |
| 查 `repo/` 层目标源码路径、外部文件读取和验收覆盖 | `08_repo层设计.md` |
| 确认本 L2 是否新增 `service/` 产物及原因 | `09_service层设计.md` |
| 确认本 L2 是否新增 `runtime/` 产物及原因 | `10_runtime层设计.md` |
| 确认本 L2 是否新增 `ui/` 产物及原因 | `11_ui层设计.md` |

## HTML-MD 语义对齐表

HTML `L2架构交互可视化.html` 由 4 个维度 view 组成，每个 view 与本目录 Markdown 一一语义对齐，view 根节点带 `data-agent-source` 指向权威 MD。HTML 与 MD 冲突时以 MD 为准。

| HTML view id | HTML view label | 维度 · Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `boundary` (radio `v1`) | 维度1 · 功能边界 | l2-01 功能边界：地基定位 / 启动期三步加工 / 负责·不负责边界墙 / 16D 数据契约段序 | `agent_context/01_L2功能边界.md` | `## 1. 一句话运行时职责`、`## 2. 输入`、`## 3. 输出`、`## 4. 负责内容`、`## 5. 不负责内容`、`## 8. 上下游`、`## 7. 代码层落点` | 完整输入/输出字段、污染检查表（完成判据与六层落点细节移至维度4/维度3） |
| `pi05map` (radio `v2`) | 维度2 · Pi0.5 如何运作 | 讲清 Pi0.5 部署代码中与 L2-01 对应的功能模块（部署配置装载 + bundle 装载）是如何运作的：入口调用链 / 七段装配 / bundle 读盘 / 持有状态与跨边界 | `agent_context/02_pi05源码3.5层微元拆解.md` | `## 0. L2-01 对应 Pi0.5 的哪一部分`、`## 1. 运行机制`、`## 2. 源码范围匹配摘要`、`## 3. 3.5 层微元表`、`## 4. class 封装盘点`、`## 5. 禁止继承的 Pi0.5 行为` | 真实源码路径（src-layout）、完整 3.5 层微元表、class 封装内部状态与并发特征、维度差异（26D/14D vs 16D/16D） |
| `blueprint` (radio `v3`) | 维度3 · 开发蓝图 | 开发建议与蓝图：启动期装配时序、六层落点矩阵、ACT 微元落点表、去平滑影响 | `agent_context/03_ACT微元设计与协作.md`、`agent_context/06_types层设计.md`、`07_config层设计.md`、`08_repo层设计.md`、`09_service层设计.md`、`10_runtime层设计.md`、`11_ui层设计.md` | `## 2. ACT 微元设计`、`## 3. 内部协作关系`、`## 4. 去除平滑处理后的协作影响`、各层设计文件全文、config/runtime 层设计的去平滑段落 | 每个微元 3.5 层类型、函数/class 判断、各层目标源码路径与依赖方向、禁止字段清单 |
| `acceptance` (radio `v4`) | 维度4 · 人类验收标准 | 验收口径：完成判据合法/非法路径图、AI Gate 矩阵、人类清单、通过/失败现象、签字入口、真机风险 | `agent_context/01_L2功能边界.md`、`agent_context/04_L2验收机制.md`、`agent_context/05_人类验收机制.md` | `## 6. 完成判据`、`## 2. Gate 验收项`、`## 3. 建议命令`、`## 4. 下游放行`、`## 5. 不允许合入条件`、`## 2. 人类验收清单`、`## 3. 签字位置`、`## 4. 真机风险` | 完整 Gate 5 项字段、人类 4 项命令、签字 Markdown 格式、真机风险声明 |

## 污染检查入口

本 L2 当前设计不得把以下内容作为权威来源：

- 旧 layer-based L2 ID：`l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware`
- 旧 `ACT Contract Delta` 或旧 `AS-IS Contract -> TO-BE Contract -> Contract Delta`
- 旧阶段二开发范式或旧阶段二 L2 模板
- `_legacy_layer_based_act/`、`_archived_pi05/` 或 `02_implement/归档/` 下的旧产物

如果上述词汇出现在本目录，只能位于明确的污染检查、废弃说明或只读参考语境中。

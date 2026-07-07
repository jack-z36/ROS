# L2-01 Agent 上下文索引

> [!info] 产物归属
> - 类型：L2 设计包内 Agent 消费入口。
> - `l2_id`：`l2-01-external-contract`
> - 人类入口：`../L2架构交互可视化.html`
> - 本目录职责：集中收纳 L2-01 的全部高密度、结构化、可检索 Markdown 上下文，供 Agent 设计 L3、验收 Gate 或排查边界问题时按需读取。
> - 本目录不负责：提供低密度人类浏览体验；人类优先打开根目录 HTML。

## 权威关系

- L3 生成、实现、验收和 Gate 判断必须以本目录 Markdown 为权威。
- `../L2架构交互可视化.html` 只服务人类快速理解；与本目录冲突时，以本目录 Markdown 为准。
- 本目录文件的 L2 边界继承自当前 L1 任务文档和 L1 Agent 架构文档，不继承旧 layer-based L2、Contract Delta 或阶段二模板。

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

## 污染检查入口

本 L2 当前设计不得把以下内容作为权威来源：

- 旧 layer-based L2 ID：`l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware`
- 旧 `ACT Contract Delta` 或旧 `AS-IS Contract -> TO-BE Contract -> Contract Delta`
- 旧阶段二开发范式或旧阶段二 L2 模板
- `_legacy_layer_based_act/`、`_archived_pi05/` 或 `02_implement/归档/` 下的旧产物

如果上述词汇出现在本目录，只能位于明确的污染检查、废弃说明或只读参考语境中。

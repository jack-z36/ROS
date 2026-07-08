# L2-02 ObservationSnapshot 组装闭环 Agent 上下文索引

## 1. L2 身份

| 字段 | 内容 |
|---|---|
| l2_id | `l2-02-observation-snapshot` |
| L2 名称 | 传感器订阅与 ObservationSnapshot 组装闭环 |
| L2 设计目录 | `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/` |
| 人类 HTML 入口 | `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/L2架构交互可视化.html` |
| Agent 权威上下文 | 本目录 `agent_context/*.md` |

本文是 L2-02 设计包的 Agent 路由入口。HTML 只服务人类快速理解；后续 Agent 生成 L3 或执行验收时必须以本目录 Markdown 为权威。

本轮只生成 L2 设计内容，不生成 L3 任务文件、dispatch、验收卡片或 acceptance 执行文件，不修改 `src/model_deploy/act/` 源码。

## 2. 必读路由

| 读取目的 | 必读文件 |
|---|---|
| 确认 L2 输入、输出、负责 / 不负责和上下游 | `01_L2功能边界.md` |
| 理解 Pi0.5 源码如何完成 observation 组装 | `02_pi05源码3.5层微元拆解.md` |
| 理解 ACT 版微元、class / function 判断和协作关系 | `03_ACT微元设计与协作.md` |
| 设计 AI 侧 L2 Gate、验证层级和 blocked 项 | `04_L2验收机制.md` |
| 设计人类可执行验收清单和签字入口 | `05_人类验收机制.md` |
| 查看公共数据结构落点 | `06_types层设计.md` |
| 查看配置层是否新增产物 | `07_config层设计.md` |
| 查看外部资源读取层是否新增产物 | `08_repo层设计.md` |
| 查看 RAM 内 observation 组装服务设计 | `09_service层设计.md` |
| 查看 latest-only observation buffer 设计 | `10_runtime层设计.md` |
| 查看 ROS callback / message adapter 设计 | `11_ui层设计.md` |

## HTML-MD 语义对齐表

HTML 用 4 个维度（维度1 功能边界 / 维度2 Pi0.5 如何运作 / 维度3 开发蓝图 / 维度4 人类验收标准）呈现，每个维度 `<section>` 带 `data-agent-source` 指向权威 Markdown。

| HTML 维度 | 维度名 | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| 维度1 | 功能边界 | L2-02 地位定位、负责 vs 不负责边界墙、输入输出契约（topic → snapshot → latest buffer 数据流） | `agent_context/01_L2功能边界.md`, `agent_context/03_ACT微元设计与协作.md` | `## 2. L2 功能边界`, `## 3. 输入输出契约`, `## 4. 负责内容`, `## 5. 不负责内容`, `## 4. 内部协作关系` | 完整上下游、责任边界、字段、输出对象、状态所有权和副作用 |
| 维度2 | Pi0.5 如何运作 | callback → 缓存 → snapshot → buffer 的白话讲解、术语词典、跟一个字段走全流程、Pi0.5→ACT 差异 | `agent_context/02_pi05源码3.5层微元拆解.md`, `agent_context/03_ACT微元设计与协作.md` | `## 1. 源码范围`, `## 2. 3.5 层微元表`, `## 3. class 封装盘点`, `## 4. 不可照搬项`, `## 4. 内部协作关系`, `## 5. 失败传播` | collector / buffer / node 运行机制、blocked / fallback 关系和 Gate 判失败条件 |
| 维度3 | 开发蓝图 | 装配时序、六层代码落点（types/service/runtime/ui 有产物，config/repo 无产物）、每层 class 微元拆解 | `agent_context/03_ACT微元设计与协作.md`, `agent_context/06_types层设计.md`, `agent_context/07_config层设计.md`, `agent_context/08_repo层设计.md`, `agent_context/09_service层设计.md`, `agent_context/10_runtime层设计.md`, `agent_context/11_ui层设计.md` | `## 2. ACT 微元设计`, `## 3. 六层产物设计表`, `## 3. 文件设计` | 六层落点、依赖方向、线程锁、latest-only 语义、ROS 可选 import 边界和无产物层说明 |
| 维度4 | 人类验收标准 | ① 跑 `bash src/model_deploy/act/scripts/l2_02_verify.sh`（分层分组终端输出 + FAIL 定位 + 汇总行）；② 终端输出翻译表（每标签→层→维度3图②微元→PASS/FAIL含义）；文档审查项；blocked 项和签字入口 | `agent_context/04_L2验收机制.md`, `agent_context/05_人类验收机制.md` | `## 3. 验证标签表`, `## 4. 统一验收脚本设计需求`, `## 5. Blocked 项`, `## 6. 失败现象`, `## 2. 人类验收清单`, `## 3. 签字格式` | 验证标签、脚本输出格式规约、退出码、标签→微元映射、签字格式和 ROS env-blocked 说明 |

## 3. 污染检查

以下内容只允许作为污染检查、旧流程隔离或只读参考说明出现，不得作为当前 L2 边界、任务来源或验收来源：

- 旧 layer-based L2：`l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware`。
- 禁止以 `ACT Contract Delta` 或 `AS-IS Contract -> TO-BE Contract -> Contract Delta` 作为当前任务边界来源。
- 禁止套用 `阶段二开发范式` 或 `L2能力模块说明文件模板`。

当前 L2 边界只来自新版 L1 任务文档、L1 功能模块边界文档和 L1 协作架构文档。Pi0.5 源码只作为结构参考。

## 4. 当前开放决策

- `ObservationSnapshot` 作为跨 L2 公共 RAM 契约，设计落点补充为 `src/model_deploy/act/types/observation.py`。这会让 L2-03 和 L2-06 只依赖 `types/`，避免依赖 L2-02 的 `service/` 或 `runtime/` 实现。
- 本轮不生成 L3；`04_L2验收机制.md` 中的后续实现切片仅用于说明 Gate 覆盖，不创建任务文件。


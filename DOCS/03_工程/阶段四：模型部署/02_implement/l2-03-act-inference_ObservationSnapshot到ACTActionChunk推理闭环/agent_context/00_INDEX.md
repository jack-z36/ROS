# L2-03 Agent 上下文索引

> [!info] 产物归属
> - 类型：L2 设计包内 Agent 消费入口。
> - `l2_id`：`l2-03-act-inference`
> - 人类入口：`../L2架构交互可视化.html`
> - 本目录职责：集中收纳 L2-03 的高密度、结构化、可检索 Markdown 上下文。
> - 本目录不负责：提供低密度人类浏览体验；人类优先打开根目录 HTML。

## 权威关系

- L3 生成、实现、验收和 Gate 判断必须以本目录 Markdown 为权威。
- `../L2架构交互可视化.html` 只服务人类快速理解；与本目录冲突时，以本目录 Markdown 为准。
- 本目录文件的 L2 边界继承自当前 L1 任务文档和 L1 Agent 架构文档，不继承旧 layer-based L2、旧 Contract Delta 或阶段二模板。
- 本 L2-03 第一版明确不实现 action smoothing、smoothstep blend、跨 chunk 融合、RTC 类平滑或复杂时间对齐；这些是后续优化，不进入当前 Gate。
- 本 L2-03 只消费 `InferenceRequest` 产出 `ActionChunk`，不决定 action 何时执行（单步选择归 L2-06）。

## 路由表

| 读取目的 | 必读文件 |
|---|---|
| 确认 L2 身份、输入输出、负责/不负责、上下游和完成判据 | `01_L2功能边界.md` |
| 查 Pi0.5 推理源码对应对象、3.5 层微元、class 封装和复用判断 | `02_pi05源码3.5层微元拆解.md` |
| 查 ACT 推理微元、class/function 决策、协作关系、状态归属和失败传播 | `03_ACT微元设计与协作.md` |
| 查 AI 侧 L2 Gate、required L3 草案、自动化验收命令、.sh 脚本设计需求、通过/失败现象和下游放行条件 | `04_L2验收机制.md` |
| 查人类验收清单、运行命令、观察点、风险和签字入口 | `05_人类验收机制.md` |
| 确认本 L2 是否新增 `types/` 产物及原因 | `06_types层设计.md` |
| 确认本 L2 是否新增 `config/` 产物及原因 | `07_config层设计.md` |
| 查 `repo/` 层目标源码路径、policy loader、bundle 装载和验收覆盖 | `08_repo层设计.md` |
| 查 `service/` 层目标源码路径、batch adapter、normalizer 使用和验收覆盖 | `09_service层设计.md` |
| 查 `runtime/` 层目标源码路径、InferenceWorker 和验收覆盖 | `10_runtime层设计.md` |
| 确认本 L2 是否新增 `ui/` 产物及原因 | `11_ui层设计.md` |

## HTML-MD 语义对齐表

HTML `L2架构交互可视化.html` 由 4 个维度 view 组成，每个 view 与本目录 Markdown 一一语义对齐，view 根节点带 `data-agent-source` 指向权威 MD。HTML 与 MD 冲突时以 MD 为准。

| HTML view id | HTML view label | 维度 · Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `boundary` (radio `v1`) | 维度1 · 功能边界 | L2-03 功能边界：后台推理角色定位 / snapshot→chunk 加工链 / 负责·不负责边界墙 / 输入输出契约 | `agent_context/01_L2功能边界.md` | `## 1. 一句话运行时职责`、`## 2. 输入`、`## 3. 输出`、`## 4. 负责内容`、`## 5. 不负责内容`、`## 8. 上下游`、`## 7. 代码层落点` | 完整输入/输出字段、污染检查表、统一推理接口契约 |
| `pi05map` (radio `v2`) | 维度2 · Pi0.5 如何运作 | 讲清 Pi0.5 推理链路（policy_loader + inference_worker + normalization + bundle）是如何运作的：后台推理轴 / predict 链路 / batch 构造 / normalizer / class 封装 | `agent_context/02_pi05源码3.5层微元拆解.md` | `## 0. L2-03 对应 Pi0.5 的哪一部分`、`## 0.5 白话开场`、`## 1. 运行机制`、`## 2. 范围匹配摘要`、`## 3. 3.5 层微元表`、`## 4. class 封装盘点`、`## 5. 禁止继承` | 真实源码路径、完整微元表、class 内部状态与并发特征、维度差异（26D/14D vs 16D/16D）、模型框架差异（Pi0.5 vs ACT） |
| `blueprint` (radio `v3`) | 维度3 · 开发蓝图 | 开发建议与蓝图：三轴推理装配、六层落点矩阵、ACT 推理微元落点表、fake-policy、去平滑影响 | `agent_context/03_ACT微元设计与协作.md`、`agent_context/06_types层设计.md`、`agent_context/07_config层设计.md`、`agent_context/08_repo层设计.md`、`agent_context/09_service层设计.md`、`agent_context/10_runtime层设计.md`、`agent_context/11_ui层设计.md` | `## 2. ACT 微元设计`、`## 3. 内部协作关系`、`## 4. 去除平滑处理后的协作影响`、各层设计文件全文 | 每个微元 3.5 层类型、函数/class 判断、各层目标源码路径与依赖方向、fake-policy 接口契约 |
| `acceptance` (radio `v4`) | 维度4 · 人类验收标准 | 人类验收标准：Part A 单脚本 `l2_03_verify.sh` 自动跑所有模块测试并分层分组打印（`.term` 终端范例块含 FAIL 定位）；Part B 终端输出翻译表（`.trtab`）逐行对照标签→层→完整定位链→PASS/FAIL含义 | `agent_context/01_L2功能边界.md`、`agent_context/04_L2验收机制.md`、`agent_context/05_人类验收机制.md` | `## 6. 完成判据`、`## 2. Gate 验收项`、`## 4. .sh 验收脚本设计需求`、`## 6. 不允许合入条件`、`## 2. 人类验收清单`、`## 3. 签字位置`、`## 4. 真机风险` | 脚本 16 个验证标签与微元的完整映射、终端输出格式规范、FAIL 定位块格式、退出码规则、BLOCKED 判定规则、签字格式 |

## 污染检查入口

本 L2 当前设计不得把以下内容作为权威来源：

- 旧 layer-based L2 ID：`l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware`
- 旧 `ACT Contract Delta` 或旧 `AS-IS Contract -> TO-BE Contract -> Contract Delta`
- 旧阶段二开发范式或旧阶段二 L2 模板
- `_legacy_layer_based_act/`、`_archived_pi05/` 或 `02_implement/归档/` 下的旧产物
- Pi0.5 的 26D state / 14D action 旧维度作为 ACT 当前 16D/16D 维度
- Pi0.5 的 `blend_steps`、`smoothstep_alpha`、`_blend_next_action` 平滑逻辑作为第一版能力

如果上述词汇出现在本目录，只能位于明确的污染检查、废弃说明或只读参考语境中。

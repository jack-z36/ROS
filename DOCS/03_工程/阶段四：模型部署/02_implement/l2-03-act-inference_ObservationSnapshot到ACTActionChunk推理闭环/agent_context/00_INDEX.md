# L2-03 Agent 上下文索引

> [!info] 产物状态
> - `l2_id`：`l2-03-act-inference`
> - 设计对象：把一个 `ObservationSnapshot` 同步转换为一个 `ActionChunk`。
> - 本目录：Agent/L3 设计、实现和验收的 Markdown 权威入口。
> - 最近一次边界确认：2026-07-10。
> - 最近一次 HTML-MD 对齐：2026-07-10。`../L2架构交互可视化.html` 已与本目录 Markdown 语义对齐，可作为人类快速浏览入口。

## 1. 权威顺序

发生冲突时按以下顺序解释：

1. `../../agent_context/02_L1_ACT功能模块边界.md` 中的 L2-03 边界。
2. `../../agent_context/03_L1_ACT功能模块协作架构.md` 中的对象所有权与 L2 协作关系。
3. 本目录 `01`、`03`、`06`～`11` 的 L2-03 设计结论。
4. 本目录 `02` 的 Pi0.5/LeRobot ACT 源码证据。
5. Pi0.5 源码本身，只用于理解，不得覆盖当前 L1/L2 边界。

旧 layer-based L2、归档任务、旧 Contract Delta 和旧 HTML 投影不在当前权威链中。

## 2. 已确认结论速查

| 维度 | 当前结论 |
|---|---|
| 启动期依赖 | `DeployConfig`、`state_normalizer`、`action_normalizer`、已加载并完成启动配置的 ACT policy |
| 单次输入 | `ObservationSnapshot` |
| 唯一成功输出 | `ActionChunk`，只包含 `(chunk_size, 16)`、`float32`、物理语义 actions |
| 对外调用语义 | 同步 `ObservationSnapshot -> ActionChunk`；何时、在哪个线程调用由 L2-06 决定 |
| 一级阶段一 | Observation 批次准备：snapshot 到 policy device 上的 ACT batch |
| 一级阶段二 | ACT 前向：只调用 `policy.predict_action_chunk(batch)` |
| 一级阶段三 | ActionChunk 后处理：raw normalized tensor 到物理 `ActionChunk` |
| 总入口 | 极薄编排入口依次调用三个一级阶段；batch/raw tensor 不泄漏给 L2-06 |
| class 聚合 | 一个无调度状态的 inference service 对象持有四项只读依赖 |
| 新增代码层 | `types/`、`service/` 和对应测试 |
| 明确无产物层 | `config/`、`repo/`、`runtime/`、`ui/` |
| 禁止 API | `policy.select_action()`；它带 action queue/temporal ensemble 单步消费语义 |
| 禁止修补 | 不 clamp、不裁剪、不补齐、不重排模型输出 |
| 运行职责 | 不加载文件，不建 worker/queue/timer，不记录 metrics，不做 fallback/cursor/safety/ROS |

## 3. 建议读取顺序

| 顺序 | 文件 | 解决的问题 |
|---|---|---|
| 1 | `01_L2功能边界.md` | L2-03 能消费什么、产出什么、负责什么、禁止什么 |
| 2 | `02_pi05源码3.5层微元拆解.md` | Pi0.5 与 LeRobot ACT 实际源码做了什么，哪些可借鉴、哪些必须剥离 |
| 3 | `03_ACT微元设计与协作.md` | 三个一级阶段、全部 3.5 层微元、只读状态、失败传播和协作顺序 |
| 4 | `06_types层设计.md` | `ActionChunk` 的唯一字段和构造约束 |
| 5 | `09_service层设计.md` | service class、三个一级函数、子功能和文件聚合 |
| 6 | `07_config层设计.md` | L2-03 实际读取哪些配置语义，哪些配置不得参与 |
| 7 | `08_repo层设计.md` | 为什么本 L2 不加载 policy/normalizer，不新增 repo 文件 |
| 8 | `10_runtime层设计.md` | L2-06 与 L2-03 的线程、queue、结果记录和 cursor 边界 |
| 9 | `11_ui层设计.md` | ROS 输入输出为什么都不属于本 L2 |
| 10 | `04_L2验收机制.md`、`05_人类验收机制.md` | 如何证明功能闭环与边界闭环 |

## 4. 核心术语

| 术语 | 本设计中的精确定义 |
|---|---|
| 模型就绪图像 | L2-02 已按训练/部署契约完成像素级预处理的单视图图像；L2-03 不再 resize、换色、缩放或视觉归一化 |
| ACT batch | 仅在 L2-03 service 内部存在的 `dict[str, Tensor]`；含 batch 维并位于 policy device |
| raw action chunk | policy 直接返回的模型尺度 tensor，预期 `(1, chunk_size, 16)`；不是跨 L2 类型 |
| physical actions | 经 `action_normalizer.unnormalize()` 恢复后的部署侧 16D 物理语义数组 |
| `ActionChunk` | L2-03 创建、L2-06 消费的跨 L2 值对象；只含 physical actions |
| 一级阶段函数 | 对一段完整业务阶段的第一次封装；内部再编排多个 3.5 层计算微元 |
| 总编排入口 | 对 L2-06 暴露的唯一业务入口；不决定调用时间、线程或失败策略 |

## 5. HTML-MD 语义对齐表

`../L2架构交互可视化.html` 已与本目录 Markdown 语义对齐。每个 HTML 视图根元素携带 `data-agent-source`，下表提供双向映射。

| HTML view id | HTML view label | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `boundary` | 维度1 功能边界 | 消费什么配置/依赖/snapshot、产出什么 ActionChunk、内部三个一级阶段的宏观流程 | `agent_context/01_L2功能边界.md` | §1 一句话职责 / §2 输入边界 / §3 输出边界 / §4 宏观流程 / §5 负责 / §6 不负责 / §7 状态与副作用 / §8 失败边界 / §9 层落点 / §10 上下游 | 完整失败边界表（§8 每类失败的行为与禁止项）、状态/副作用/并发表（§7）、完成判据清单（§11）、已确认事项（§12） |
| `boundary` | 维度1 · DeployConfig 消费卡 | 5 项 L2-03 实际消费的配置语义及所有不消费字段的归属 | `agent_context/07_config层设计.md` | §2 消费语义 / §3 不消费语义 / §4 不允许新增配置 | 所有 17 项不消费字段的完整归属表（§3）、禁止新增配置项的完整列表（§4）、验收确认（§5） |
| `boundary` | 维度1 · ActionStateNormalizer 消费卡 | 两个独立 normalizer 实例的调用方向与次数约束 | `agent_context/01_L2功能边界.md` + `agent_context/08_repo层设计.md` | §2.1 启动期依赖 + §2 L2-01 提供资源 | normalizer 字段完整表（min_vals/max_vals/vector_dim）、调用方向与次数精确约束、两个实例不得交换的硬性规则 |
| `boundary` | 维度1 · ObservationSnapshot 消费卡 | 16D encoded_state 段序 + 图像前置契约 | `agent_context/01_L2功能边界.md` | §2.2 单次输入 / §2.3 图像前置契约 | 完整 16D 物理语义段序表（坐标系/单位/值域）、图像前置契约的完整约束、构造时自动校验的详细说明 |
| `boundary` | 维度1 · ActionChunk 产出卡 | 只含 actions 的 frozen dataclass，不含任何运行元数据 | `agent_context/01_L2功能边界.md` + `agent_context/06_types层设计.md` | §3 输出边界 + §2~§5 ActionChunk 定义 | 固定 16D 语义完整段序表（§4）、构造约束的 5 项完整检查、明确不存在的 7 项字段及其归属原因（§5）、依赖关系（§6） |
| `pi05map` | 维度2 Pi0.5 如何运作 | Pi0.5 源码推理链的白话讲解、ACT 归属对比 | `agent_context/02_pi05源码3.5层微元拆解.md` | §1 源码范围 / §2 纯推理链 / §3 边界归属 / §4 LeRobot ACT API 差异 / §5 微元映射 / §6 3.5 层判断 / §7 class 封装比较 / §8 禁止继承 | 完整 3.5 层微元判断表（§6 每行的当前判断）、class 封装比较表（§7 每项的处理方式）、LeRobot ACT API 决定性差异的完整源码证据（§4） |
| `blueprint` | 维度3 开发蓝图 | 运行时协作链 SVG + 六层代码落点 radio panes | `agent_context/03_ACT微元设计与协作.md` + `agent_context/09_service层设计.md` | §1 总体结构 / §2 3.25 层聚合 / §3 启动期上下文 / §4~§7 三个阶段+总入口 / §8 3.5 层总账 / §10 失败传播 + §2~§3 class 设计 | 变量所有权与生命周期完整表（§9）、3.5 层总账精确数量（§8 计算函数 12 个等）、L2 协作边界表（§11 每对协作的提供/接收与禁止反向承担） |
| `blueprint` | 图② types 层 | ActionChunk 唯一字段 + 构造校验 | `agent_context/06_types层设计.md` | §1 新增产物 / §2 类型职责 / §3 数据与构造约束 / §4 固定 16D 语义 / §5 不存在字段 / §8 边界声明 | 固定 16D 语义完整段序表（§4）、明确不存在的字段与方法完整列表（§5）、依赖关系（§6） |
| `blueprint` | 图② config 层 | 复用 L2-01 DeployConfig，不新增产物 | `agent_context/07_config层设计.md` | §1 无产物声明 / §2 消费语义 / §3 不消费语义 / §4 不允许新增 | 所有 17 项不消费字段的完整归属表（§3）、禁止新增配置的完整列表（§4） |
| `blueprint` | 图② repo 层 | 不新增产物——四项稳定依赖由 L2-01 注入 | `agent_context/08_repo层设计.md` | §1 无产物声明 / §2 L2-01 提供资源 / §3 禁止产物 / §4 不复用 Pi0.5 runtime / §6 验收 | L2-01 提供的完整资源表（§2）、禁止 repo 产物的完整文件/函数列表（§3）、为什么不复用 Pi0.5 Pi05PolicyRuntime（§4） |
| `blueprint` | 图② service 层 | ActInferenceService class + 3 个文件 + 全部微元 | `agent_context/09_service层设计.md` | §1 目标源码树 / §2 聚合总览 / §3 act_inference.py / §4 observation_batch.py / §5 action_chunk_postprocess.py / §6 依赖方向 / §7 异常语义 | ActInferenceService 数据字段完整表（§3.1）、每阶段所有计算微元的精确输入/输出/异常（§4~§5 每个微元的精确边界）、完整依赖方向（§6）、异常语义规则（§7） |
| `blueprint` | 图② runtime 层 | 不落点——所有运行对象归 L2-06 | `agent_context/10_runtime层设计.md` | §1 无产物声明 / §2 调用边界 / §3 归 L2-06 对象 / §4 并发约束 | L2-06 完整运行对象列表（§3 每项归属说明）、精确的调用边界（§2 双方各 5 项职责）、并发约束（§4） |
| `blueprint` | 图② ui 层 | 不落点——无 ROS/硬件 I/O | `agent_context/11_ui层设计.md` | §1 无产物声明 / §2 外部接口分工 / §3 间接关系 / §4 禁止内容 | 完整外部接口分工表（§2 每项交互的所有者与 L2-03 关系）、禁止内容的完整列表（§4） |
| `acceptance` | 维度4 人类验收标准 | .sh 脚本终端输出 + 翻译表 + 文档审查项 | `agent_context/04_L2验收机制.md` + `agent_context/05_人类验收机制.md` | §2 测试目录 / §3 Gate 场景 / §4 .sh 设计需求 + §2 自动验收 / §3 人工审查清单 / §4 可视化追踪 / §6 签字 / §7 风险边界 | 完整 Gate 场景表（§3.1~§3.5 每个场景的输入/通过现象/失败现象）、完整标签→微元映射（§4.3 每行的 PASS 含义）、BLOCKED 判定规则（§4.4）、人工审查 8 项清单（§3）、sentinel 追踪协议（§4）、签字模板（§6） |

### 对齐规则

- MD 是权威设计源；HTML 是其压缩视觉投影。
- 每项 HTML 展示的关系、箭头、状态所有者、失败路径、Gate 信号或边界声明均须能在上表中追溯到 MD 节。
- 若修改 MD 语义，必须同步更新 HTML 投影并在本表确认映射仍有效。
- L3 生成和实现以本目录 Markdown 为准，HTML 不作为补充设计依据。

## 6. 污染检查入口

以下内容只能出现在“禁止继承”或源码对比语境中，不能成为 L2-03 产物：

- `load_act_policy_runtime`、`policy_loader.py`、bundle/checkpoint/adapter 读取。
- 生产代码中的 fake-policy 选择分支。
- `InferenceWorker`、`InferenceRequest`、`LatestQueue`、`SharedBuffer`、`RuntimeMetrics`。
- `request_id`、observation/inference/ready time、latency、`action_dt`、cursor、error state。
- `select_action()`、action queue、temporal ensemble、action smoothing、cross-chunk fusion、RTC。
- normalized action clamp、chunk crop、padding 或静默维度修补。
- ROS subscriber/publisher、机械臂或夹爪硬件命令。

如果实现需要其中任一能力，先回到 L1 边界重新设计，不得在 L2-03 内局部增加。

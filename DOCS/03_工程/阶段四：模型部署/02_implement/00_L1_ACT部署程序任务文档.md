# L1 ACT 部署程序任务文档

> [!info] 产物归属
> - 类型：L1 架构协作包中的 Agent 任务管理上下文（阶段四：模型部署）。
> - 目标路径：`DOCS/03_工程/阶段四：模型部署/02_implement/00_L1_ACT部署程序任务文档.md`。
> - 适用对象：基于同事 `pi05_old/pi05_test/pi05/` 部署代码进行核心参考与改造，编写第一版 ACT 部署程序。
> - 代码根目录：`src/model_deploy/act/`。
> - 本文职责：定义 L1 总目标、L2 功能模块清单、稳定 L2 ID、线性开发顺序、L2 依赖关系和 L1 验收口径。
> - 关联产物：
>   - 模块边界：`01_L1_ACT功能模块边界.md`（每个 L2 的输入/输出/负责/不负责/完成判据）。
>   - 模块协作：`02_L1_ACT功能模块协作架构.md`（模块间数据流、调用关系、对象所有权）。
>   - 人类可视化：`ACT架构交互可视化.html`。
> - 本文不展开：单模块边界（指向 01）、模块间协作（指向 02）。

## 0. 消费者分工与本文定位

L1 架构协作包按消费对象拆分为 4 个产物：

| 消费者 | 消费产物 | 消费目的 | 信息密度 |
|---|---|---|---|
| Agent | 本文档（任务文档） | 获取 L1 总目标、L2 清单与开发顺序、L1 验收口径。 | 中。任务管理属性。 |
| Agent | `01_L1_ACT功能模块边界.md` | 完整理解每个 L2 的功能边界。 | 高。逐模块边界契约。 |
| Agent | `02_L1_ACT功能模块协作架构.md` | 完整理解模块间协作关系。 | 高。协作关系契约。 |
| 人类 | `ACT架构交互可视化.html` | 快速理解整体架构、模块协作和模块边界。 | 低。可视化为主。 |

## 1. L1 总目标

本 L1 的目标是实现一个可运行、可验证、可逐步接入真机的 ACT 部署程序。

程序运行时的主链路是：

```text
外部参数
-> 传感器 observation topics
-> ObservationSnapshot
-> ACT batch
-> ACT action_chunk
-> chunk 时间对齐与平滑
-> 单步 action 安全检查
-> 执行器可消费 topic
-> ControlLoop 持续调度
```

本任务不是直接照搬同事 Pi0.5 程序，也不是按 `types / config / repo / service / runtime / ui` 六个目录拆任务。六层目录只定义代码落点；L2 任务按运行时功能闭环拆分。

## 2. L2 功能模块清单

本 L1 拆成 7 个 L2，按运行时功能闭环组织：

| L2 ID | 中文名称 |
|---|---|
| `l2-01-external-contract` | 外部参数加载与契约校验闭环 |
| `l2-02-observation-snapshot` | 传感器订阅与 ObservationSnapshot 组装闭环 |
| `l2-03-act-inference` | ObservationSnapshot 到 ACT ActionChunk 推理闭环 |
| `l2-04-action-smoothing` | ActionChunk 时间对齐与平滑融合闭环 |
| `l2-05-safety-guard` | 单步 Action 安全检查闭环 |
| `l2-06-action-publisher` | 单步 Action 到执行器 Topic 适配发送闭环 |
| `l2-07-control-loop` | ControlLoop 中央运行调度闭环 |

后续 dispatch、状态摘要、三级分支和 acceptance 目录必须使用上述稳定 L2 ID。

旧 `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware` 是 layer-based 历史 ID，不得作为新版 L2 / L3 执行入口。

每个 L2 的功能定义、输入、输出、负责/不负责内容、完成判据和代码层落点见 `01_L1_ACT功能模块边界.md`。

## 3. L2 线性开发顺序

建议按以下顺序线性开发：

```text
L2-01 外部参数加载与契约校验闭环
L2-02 传感器订阅与 ObservationSnapshot 组装闭环
L2-03 ObservationSnapshot 到 ACT ActionChunk 推理闭环
L2-04 ActionChunk 时间对齐与平滑融合闭环
L2-05 单步 Action 安全检查闭环
L2-06 单步 Action 到执行器 Topic 适配发送闭环
L2-07 ControlLoop 中央运行调度闭环
```

## 4. L2 依赖关系

```text
L2-01
  -> L2-02
  -> L2-03
  -> L2-04
  -> L2-05
  -> L2-06
  -> L2-07
```

更精确地说：

| L2 | 依赖 | 说明 |
|---|---|---|
| L2-01 | 无 | 全部后续 L2 的静态契约地基。 |
| L2-02 | L2-01 | 依赖 state/topic/image/config 契约。 |
| L2-03 | L2-01、L2-02 的 `ObservationSnapshot` 契约 | 可先用 mock snapshot 开发。 |
| L2-04 | L2-03 的 `ActionChunk` 契约 | 可用 fake chunk 单测。 |
| L2-05 | L2-01、L2-04 | 依赖 action schema 和单步 raw action。 |
| L2-06 | L2-01、L2-05 | 依赖 safe action 和 topic/hardware 配置。 |
| L2-07 | L2-02 至 L2-06 | 负责把前面所有 service 串成持续运行程序。 |

模块之间的协作接口、RAM 对象所有权、同步/异步边界详见 `02_L1_ACT功能模块协作架构.md`。

## 5. L1 验收口径

L1 完成不等于真机动作一定通过。L1 的完成状态分为三层：

| 验收层级 | 通过标准 |
|---|---|
| 本地单测 | L2-01 至 L2-05 在无 ROS / 无硬件条件下可用 mock 通过。 |
| dry-run / shadow-run | L2-06 至 L2-07 能启动 mock 或 ROS shadow 链路，能观察 action 和 command status。 |
| real-robot | 必须人工授权、硬件在场、急停准备完成后执行；默认不作为自动验收项。 |

L1 的最小自动化完成标准：

```text
配置契约通过
ObservationSnapshot 可构造
fake ACT action_chunk 可生成
chunk 平滑与 safety 单测通过
shadow-run action 到 command topic 转换通过
ControlLoop mock 闭环可持续 tick
```

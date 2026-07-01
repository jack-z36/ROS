---
title: Pi05VlaDeployNode 三条时间主轴可视化
aliases:
  - Pi05VlaDeployNode 三条时间主轴
tags:
  - ROS/Pi05
  - deploy/runtime
  - visualization
---

# Pi05VlaDeployNode 三条时间主轴可视化

本文用于解释 `Pi05VlaDeployNode` 在推理运行时的并发结构。重点不是画一条顺序调用链，而是突出 **三条相对独立、但会交换数据的时间主轴**。

> [!summary] 核心结论
> `Pi05VlaDeployNode` 可以被理解成三条并行时间主轴：
> - **A 轴：ROS callback 输入轴**，由外部 observation topic 到达触发。
> - **B 轴：ControlLoop 控制轴**，按照 `control_hz` 固定节拍运行。
> - **C 轴：InferenceWorker 推理轴**，在后台线程中异步调用模型。
>
> 三条轴之间通过 `SharedBuffer` 和 `LatestQueue` 交换数据。交换点不是同步阻塞点，也不是把三条轴合并成一条流水线。

## 1. 三条时间主轴图

> [!note] 读图方式
> 横向是时间推进：`t → t+1 → t+2 → t+3 → t+4 → t+5`。  
> 纵向是同一时间点上三条轴各自正在做的事。

| 时间点 | A 轴：ROS callback 输入轴 | B 轴：ControlLoop 控制轴 | C 轴：InferenceWorker 推理轴 | 跨轴数据交换 |
|---|---|---|---|---|
| `t` | ROS observation 消息到达 | control tick 到达 | worker 暂时空转 | - |
| `t+1` | 更新 `ObservationCollector` 字段缓存 | 读取 `SharedBuffer.latest_observation` | 从 request queue 取最新请求 | A 轴先前生成的 `Snapshot` 被 B 轴读取 |
| `t+2` | 字段完整且未过期，生成 `ObservationSnapshot` | 必要时提交 `InferenceRequest` | 调用模型，处于推理中 | B 轴把 `Request` 写入请求队列 |
| `t+3` | 继续接收新 observation，刷新缓存 | 如果没有可用 chunk，等待或 fallback | 推理完成，产出 `ActionChunk` | - |
| `t+4` | 新 snapshot 覆盖旧 snapshot | 从 chunk 中消费一步 action | 把 `ActionChunk` 写入结果队列 | C 轴产出的 `Chunk` 被 B 轴消费 |
| `t+5` | 继续监听 topic | 经过 `SafetyGuard` 后发布 `/pi05_vla/command/*` | 等待下一次 request | B 轴输出到 Pi05 command topic |

```text
时间推进  ───────────────────────────────────────────────────────────────>

A 轴：ROS callback     t:消息到达 ── t+1:更新缓存 ── t+2:生成Snapshot ── t+3:继续刷新 ── t+4:覆盖旧值 ── t+5:监听topic
                                      │
                                      │ Snapshot / SharedBuffer
                                      ▼
B 轴：ControlLoop      t:控制tick ── t+1:读观测 ── t+2:提交Request ── t+3:等待/兜底 ── t+4:取action ── t+5:发布命令
                                                       │                                      ▲
                                                       │ Request / queue                      │ Chunk / queue
                                                       ▼                                      │
C 轴：InferenceWorker  t:空转 ───── t+1:取请求 ───── t+2:模型推理 ───── t+3:产出Chunk ─── t+4:写结果 ─── t+5:等下次
```

## 2. 三条主轴的读法

| 主轴 | 时间来源 | 运行特点 | 与其他轴的数据交换 |
|---|---|---|---|
| A. ROS callback 输入轴 | 外部 ROS topic 到达 | 不固定频率。哪个 topic 到了，就更新哪个 observation 字段。 | 生成 `ObservationSnapshot`，写入 `SharedBuffer.latest_observation`。 |
| B. ControlLoop 控制轴 | `control_timer` | 固定 `control_hz` tick。它不等待 GPU 推理完成。 | 读取 observation，提交 request，消费 chunk，发布 command。 |
| C. InferenceWorker 推理轴 | 后台 daemon thread | 按 `inference_hz` 节流，异步调用模型。 | 从 request queue 取最新请求，把 `ActionChunk` 放回 result queue。 |

## 3. 主轴与数据交换关系

| 数据交换 | 发送方 | 接收方 | 数据对象 | 含义 |
|---|---|---|---|---|
| 交换 1 | A 轴：ROS callback | B 轴：ControlLoop | `ObservationSnapshot` | callback 聚合到完整观测后，把最新观测写入 `SharedBuffer`；控制循环下一次 tick 读取它。 |
| 交换 2 | B 轴：ControlLoop | C 轴：InferenceWorker | `InferenceRequest` | 控制循环判断需要新动作片段时，把最新 observation 包装成推理请求。 |
| 交换 3 | C 轴：InferenceWorker | B 轴：ControlLoop | `ActionChunk` | 推理线程异步产出多步 action，控制循环后续 tick 逐步消费。 |

## 4. 关键结论

- 这不是一条同步流水线，而是三条并行时间主轴。
- A 轴负责刷新最新 observation。
- B 轴负责按稳定控制节拍发布 command topic。
- C 轴负责异步生成未来一段 `ActionChunk`。
- 三条轴通过 latest-only 的 `SharedBuffer` 和 `LatestQueue` 交换数据。

## 5. 边界提醒

> [!warning]
> 这三条时间主轴属于 `Pi05VlaDeployNode` 节点内部。  
> 它们的输出边界停在 `/pi05_vla/command/*`。  
> 下游 `Pi05BridgeNode`、`CommandMuxNode`、`picotele` 不属于这三条内部时间轴。


---
tags:
  - term-explainer
  - pi05
  - data-definition
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# request

> [!abstract] 核心定义
> 在该语境中，`request` 是一个 `InferenceRequest` 实例，表示一次后台 VLA 推理任务。

## 数据结构

| 字段名 | 类型 | 含义 | 是否必填 |
|--------|------|------|----------|
| `observation` | ObservationSnapshot | 要送入模型的完整观测 | 是 |
| `obs_time` | float | 观测时间戳 | 是 |
| `request_id` | int | 推理请求编号 | 是 |
| `trigger_step` | int | 发起请求时的 active_cursor | 是 |

> [!info] 结构说明
> `request` 将推理数据和调度元数据放在同一个不可变对象里。

## 具体数值示例

> [!example]- 点击展开具体数据实例
> ```json
>
> {
>   "request_id": 17,
>   "obs_time": 12345.67,
>   "trigger_step": 5,
>   "observation": "ObservationSnapshot(...)"}
> ```
>
> 该示例展示该术语在 [[部署推理数据流框架|部署推理数据流框架]] 中承担的数据契约角色。

## 具象隐喻

> [!tip] 生活场景类比
> 像一张外卖订单：写清要用哪份原料、什么时间下单、订单号是多少。

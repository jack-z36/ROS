---
tags:
  - term-explainer
  - pi05
  - data-definition
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# InferenceWorker

> [!abstract] 核心定义
> 后台 VLA 推理线程对象，保存模型运行时、请求队列、结果队列和推理频率等状态。

## 数据结构

| 字段名 | 类型 | 含义 | 是否必填 |
|--------|------|------|----------|
| `policy_runtime` | object | 真正调用 VLA policy 的运行时 | 是 |
| `request_queue` | LatestQueue[InferenceRequest] | 控制循环写入的最新推理请求 | 是 |
| `result_queue` | LatestQueue[ActionChunk] | 推理线程写出的动作块结果 | 是 |
| `period_s` | float | 由 inference_hz 得到的推理周期 | 是 |

> [!info] 结构说明
> `InferenceWorker` 是带行为的类，但从笔记术语角度看，它首先是一个持有这些字段的运行时组件定义。

## 具体数值示例

> [!example]- 点击展开具体数据实例
> ```json
>
> {
>   "thread": "pi05_inference_worker",
>   "period_s": 0.1,
>   "request_queue": "LatestQueue[InferenceRequest]",
>   "result_queue": "LatestQueue[ActionChunk]"
> }
> ```
>
> 该示例展示该术语在 [[部署推理数据流框架|部署推理数据流框架]] 中承担的数据契约角色。

## 具象隐喻

> [!tip] 生活场景类比
> 像工厂里独立的加工车间：有自己的任务箱、成品箱、机器和工作节拍。

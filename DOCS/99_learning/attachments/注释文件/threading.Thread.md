---
tags:
  - term-explainer
  - pi05
  - data-definition
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# threading.Thread

> [!abstract] 核心定义
> Python 标准库的线程抽象，`InferenceWorker` 继承它来在后台异步执行 VLA 推理。

## 数据结构

| 字段名 | 类型 | 含义 | 是否必填 |
|--------|------|------|----------|
| `run()` | method | 线程启动后执行的主函数 | 是 |
| `daemon` | bool | 是否随主程序退出 | 否 |
| `name` | str | 线程名称 | 否 |

> [!info] 结构说明
> `threading.Thread` 定义并发执行单元的基本结构，业务类通过重写 `run()` 提供自己的循环逻辑。

## 具体数值示例

> [!example]- 点击展开具体数据实例
> ```json
>
> {
>   "class": "InferenceWorker(threading.Thread)",
>   "daemon": true,
>   "name": "pi05_inference_worker"
> }
> ```
>
> 该示例展示该术语在 [[部署推理数据流框架|部署推理数据流框架]] 中承担的数据契约角色。

## 具象隐喻

> [!tip] 生活场景类比
> 像另开一条生产线：主线不停，副线专门做耗时加工。

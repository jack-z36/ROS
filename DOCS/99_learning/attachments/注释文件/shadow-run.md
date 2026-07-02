---
tags:
  - term-explainer
  - pi05
  - data-definition
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# shadow-run

> [!abstract] 核心定义
> 一种部署模式，用于运行 VLA 链路并生成候选命令，便于观测或对照验证。

## 数据结构

| 字段名 | 类型 | 含义 | 是否必填 |
|--------|------|------|----------|
| `mode` | str | 值为 shadow-run | 是 |
| `publishes_command_topics` | bool | 在代码中为 true | 是 |

> [!info] 结构说明
> 具体是否成为最终硬件控制，还取决于下游 bridge/mux 配置。

## 具体数值示例

> [!example]- 点击展开具体数据实例
> ```json
>
> {
>   "runtime.mode": "shadow-run",
>   "publishes_command_topics": true
> }
> ```
>
> 该示例展示该术语在 [[部署推理数据流框架|部署推理数据流框架]] 中承担的数据契约角色。

## 具象隐喻

> [!tip] 生活场景类比
> 像副驾驶系统在旁边同步计算自己会怎么开，但不一定直接接管方向盘。

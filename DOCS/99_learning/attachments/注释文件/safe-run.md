---
tags:
  - term-explainer
  - pi05
  - data-definition
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# safe-run

> [!abstract] 核心定义
> 一种真实发布 VLA 命令的部署模式，命令需先经过安全过滤。

## 数据结构

| 字段名 | 类型 | 含义 | 是否必填 |
|--------|------|------|----------|
| `mode` | str | 值为 safe-run | 是 |
| `SafetyGuard` | component | 发布前必须通过的安全过滤器 | 是 |

> [!info] 结构说明
> `safe-run` 是最接近真实执行的模式，因此必须依赖 action clamp、delta clamp 和 hand clamp。

## 具体数值示例

> [!example]- 点击展开具体数据实例
> ```json
>
> {
>   "runtime.mode": "safe-run",
>   "safety.max_joint_delta_rad": 0.08
> }
> ```
>
> 该示例展示该术语在 [[部署推理数据流框架|部署推理数据流框架]] 中承担的数据契约角色。

## 具象隐喻

> [!tip] 生活场景类比
> 像自动驾驶真正接管，但车上还有限速器和紧急制动。

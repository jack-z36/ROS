---
tags: [program-principle, concept]
analysis: pi05-runtime-train-bundle
---

# Action chunk 预取与 blend

> [!abstract]
> 控制循环用 action chunk 分摊模型推理延迟，并用预取和 blend 降低 chunk 边界抖动。

## 在本代码库中的具体含义

`ControlLoop` 在 active chunk 接近 `execute_horizon - prefetch_steps` 时提交下一次推理请求。新 chunk 到达后先进入 pending，切换时可立即激活，也可通过 `smoothstep_alpha()` 和上一次命令做平滑过渡。

## 出现位置

| 位置 | 角色 |
| --- | --- |
| `control_loop.py:169-195` | 预取请求 |
| `control_loop.py:224-287` | pending chunk 激活或开始 blend |
| `control_loop.py:290-314` | blend 动作生成 |


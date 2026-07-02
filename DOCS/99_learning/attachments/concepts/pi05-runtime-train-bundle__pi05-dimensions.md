---
tags: [program-principle, concept]
analysis: pi05-runtime-train-bundle
---

# Pi0.5 14D action / 26D state

> [!abstract]
> 14D action 和 26D state 是本项目训练、部署、安全过滤之间必须保持一致的数据形状。

## 在本代码库中的具体含义

`builder.py:26-27` 定义默认 `DEFAULT_STATE_DIM = 26` 和 `DEFAULT_ACTION_DIM = 14`。`builder.py:68-71` 强制 action_dim 为 14，`builder.py:341-349` 把 state/action feature specs 写入 PI05 policy config。

## 和数据流的关系

- deploy 侧：`SafetyGuard` 用 `ensure_action_vector()` 和 `split_action()` 解释 14D action。
- train 侧：模型构建和 batch schema 必须匹配 26D state / 14D action。


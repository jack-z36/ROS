---
tags:
  - ROS
  - Pi05
  - term
  - orchestration-function
---

# Pi05PrepareStateTokenizerProcessorStep

> [!abstract] 核心定义
> `Pi05PrepareStateTokenizerProcessorStep` 负责把归一化后的机器人 state 离散化，并和 task 一起组织成 Pi0.5 tokenizer 可以处理的输入模板。

## 输入与输出

| 方向 | 内容 | 类型 |
|---|---|---|
| 输入 | `observation.state` | 已归一化 state tensor |
| 输入 | `task` | 任务文本 |
| 输出 | 更新后的 `task` | 包含 `Task: ... State: ... Action:` 结构的模型输入模板 |

## 运行逻辑

1. 从 transition 的 observation 中读取 `observation.state`。
2. 从 complementary data 中读取 `task`。
3. 把 state 转成 NumPy。
4. 将 state 离散化到 256 个 bin。
5. 把 task 和离散化 state 组织成完整的模型输入模板。

## 关键格式

```text
Task: <cleaned task>, State: <discretized states>;
Action:
```

## 为什么重要？

因为 Pi0.5 的语言模型部分不能直接理解连续 state 向量。

这一步相当于把：

```text
任务文本 + 离散化后的机器人状态
```

翻译成 tokenizer 能继续处理的 token 输入来源。

## 具象隐喻

> [!tip] 生活场景类比
> 机器人状态原本像一堆仪表盘读数，模型看不懂。这个 step 像秘书，把仪表盘读数先换成固定编号，再按固定表格格式整理好：“任务是什么、状态编号是什么、接下来要生成动作”。然后再交给 tokenizer。

## 源码证据

- `pi05_test/third_party/lerobot/src/lerobot/policies/pi05/processor_pi05.py:51-93`

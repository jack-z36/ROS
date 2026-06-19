---
tags:
  - program-principle
  - pi05-vla
  - control-loop
  - chunk-blend
  - scenario
source_note: "01-doing/pi05_test/learning/部署推理数据流框架.md"
source_code: "01-doing/pi05_test/pi05_test/pi05/deploy/src/pi05/deploy/runtime/control_loop.py"
concept: "ControlLoop chunk boundary blend"
---

# ControlLoop chunk 边界混合场景例子

> [!info] 返回主文
> 本文件是 [[部署推理数据流框架#Step 4：数值加工处理：chunk 边界平滑混合|chunk 边界平滑混合]] 的详细场景例子。

这个例子专门回答三个问题：

1. $O$ 是 `action_chunk_old` 中的哪一步？
2. $N_i$ 是 `action_chunk_new` 中的哪一步？
3. $B_i$ 到底代表最终执行动作，还是中间 raw action？

---

## 1. 场景参数

假设 VLA 程序从 `t = 0` 开始运行，控制参数如下：

| 参数 | 值 | 含义 |
|---|---:|---|
| `control_hz` | 30 Hz | 每约 0.033s 调一次 `ControlLoop.tick()` |
| `action_dt` | 1/30 s | action chunk 内相邻动作的时间间隔 |
| `chunk_size` | 30 | 模型一次输出 30 个 14D action |
| `execute_horizon` | 10 | 通常执行到 cursor 10 附近准备切换 chunk |
| `prefetch_steps` | 5 | cursor 到 5 时提前请求下一个 chunk |
| `blend_steps` | 3 | chunk 交接时混合 3 个控制帧 |

记：

$$
\Delta t = \frac{1}{30} \approx 0.033s
$$

---

## 2. t = 0：VLA 刚启动

刚启动时，控制循环内部状态大致是：

```text
active_chunk = None
pending_chunk = None
last_command = None
blend_active = False
```

此时没有旧 chunk，也没有上一条已执行动作，所以不可能做边界混合。

第一次 `tick()` 只能尝试提交推理请求：

```text
observation -> InferenceRequest R1 -> InferenceWorker
```

> [!important] 第一个 chunk 不会 blend
> 因为 blend 需要两个条件：旧动作端点 $O$ 和新 chunk。刚启动时二者都不完整。

---

## 3. t = 0.100：第一个 chunk 到达

假设第一个模型结果在 `t = 0.100s` 到达，称为旧 chunk：

$$
C^{old} = \{C^{old}_0, C^{old}_1, \dots, C^{old}_{29}\}
$$

它的观测时间是：

$$
C^{old}.obs\_time = 0.000
$$

激活这个 chunk 时，程序不会从 `C_old[0]` 开始执行，而是先做时间对齐：

$$
aligned = \left\lfloor \frac{0.100 - 0.000}{0.033} \right\rfloor = 3
$$

所以第一个真正执行的动作近似是：

$$
C^{old}_3
$$

---

## 4. 第一个 chunk 的执行时间线

简化后，旧 chunk 的执行过程如下：

| tick 时间 | tick 开始时 cursor | 本 tick 取出的 old chunk 动作 | tick 后 cursor |
|---:|---:|---|---:|
| 0.100 | 3 | $C^{old}_3$ | 4 |
| 0.133 | 4 | $C^{old}_4$ | 5 |
| 0.167 | 5 | $C^{old}_5$ | 6 |
| 0.200 | 6 | $C^{old}_6$ | 7 |
| 0.233 | 7 | $C^{old}_7$ | 8 |
| 0.267 | 8 | $C^{old}_8$ | 9 |
| 0.300 | 9 | $C^{old}_9$ | 10 |

在 `t = 0.167` 这一帧，`active_cursor = 5`，满足：

$$
active\_cursor \ge execute\_horizon - prefetch\_steps = 10 - 5 = 5
$$

因此程序会提前提交第二次推理请求，得到未来的新 chunk：

```text
InferenceRequest R2 -> later produces C_new
```

---

## 5. t = 0.333：准备交接 chunk

假设第二个 chunk 已经在 `t = 0.333s` 前到达，称为：

$$
C^{new} = \{C^{new}_0, C^{new}_1, \dots, C^{new}_{29}\}
$$

此时控制循环状态大致是：

```text
active_chunk = C_old
active_cursor = 10
pending_chunk = C_new
last_command ≈ SafetyGuard(C_old[9])
```

因为：

```text
active_cursor >= execute_horizon
pending_chunk is not None
```

所以 `_next_raw_action()` 不再取：

$$
C^{old}_{10}
$$

而是进入：

```text
_start_blend_or_switch()
```

这就是理解 $O$ 的关键。

---

## 6. O 是谁？

源码在进入 blend 时保存：

```python
self.blend_start_command = self.last_command
```

因此：

$$
O = \text{blend\_start\_command.as\_vector()}
$$

在这个具体场景中，进入 blend 前最后实际执行的是：

$$
C^{old}_9
$$

所以通常可以理解成：

$$
O \approx \operatorname{SafetyGuard}(C^{old}_9)
$$

如果 `SafetyGuard` 没有改变数值，则：

$$
O \approx C^{old}_9
$$

但严格说：

> $O$ 不是从旧 chunk 中按索引重新取的，而是 `last_command` 的快照。  
> `last_command` 表示上一帧实际通过安全过滤并被控制循环接受的动作。

---

## 7. N_i 是谁？

假设第二次推理请求使用的观测时间是：

$$
C^{new}.obs\_time = 0.167
$$

现在进入 blend 的时间是：

$$
now = 0.333
$$

新 chunk 的时间对齐索引为：

$$
k = \left\lfloor \frac{0.333 - 0.167}{0.033} \right\rfloor = 5
$$

所以新 chunk 不是从 `C_new[0]` 开始接入，而是从：

$$
C^{new}_5
$$

开始接入。

因此三步混合中的新动作是：

| 混合步 | 新动作 |
|---|---|
| 第 1 步 | $N_1 = C^{new}_5$ |
| 第 2 步 | $N_2 = C^{new}_6$ |
| 第 3 步 | $N_3 = C^{new}_7$ |

一般公式：

$$
N_i = C^{new}_{k+i-1}
$$

---

## 8. B_i 是谁？

三步 smoothstep 权重是：

| 混合步 | $\alpha_i$ |
|---:|---:|
| 1 | 0.259 |
| 2 | 0.741 |
| 3 | 1.000 |

混合 raw action 为：

$$
B_i = (1-\alpha_i)O + \alpha_iN_i
$$

代入本场景：

$$
B_1 = 0.741O + 0.259C^{new}_5
$$

$$
B_2 = 0.259O + 0.741C^{new}_6
$$

$$
B_3 = C^{new}_7
$$

其中 $B_i$ 是 `_blend_next_action()` 返回的 raw action，还需要继续经过安全过滤：

$$
A_i = \operatorname{SafetyGuard}(B_i)
$$

最终发布的是 $A_i$，不是裸的 $B_i$。

---

## 9. 为什么不是 C_old[9], C_old[10], C_old[11] 分别配对？

你的直觉对应的是这种设计：

$$
B_1 = (1-\alpha_1)C^{old}_9 + \alpha_1C^{new}_5
$$

$$
B_2 = (1-\alpha_2)C^{old}_{10} + \alpha_2C^{new}_6
$$

$$
B_3 = (1-\alpha_3)C^{old}_{11} + \alpha_3C^{new}_7
$$

这叫“旧轨迹和新轨迹逐点混合”。

但源码实际不是这样。原因是：当 `active_cursor >= execute_horizon` 且 `pending_chunk` 存在时，代码会先进入 `_start_blend_or_switch()`，然后直接调用 `_blend_next_action()`。这条路径不会继续执行：

$$
C^{old}_{10}, C^{old}_{11}, C^{old}_{12}
$$

旧 chunk 后续点在正常交接时被放弃了。

源码实际是：

$$
B_1 = (1-\alpha_1)O + \alpha_1C^{new}_5
$$

$$
B_2 = (1-\alpha_2)O + \alpha_2C^{new}_6
$$

$$
B_3 = (1-\alpha_3)O + \alpha_3C^{new}_7
$$

同一个 $O$ 被用于三步混合。

---

## 10. 混合结束后从哪里继续？

混合时，`next_cursor` 每用一次新 chunk 动作就加 1：

```text
start: next_cursor = 5
step 1 uses C_new[5], then next_cursor = 6
step 2 uses C_new[6], then next_cursor = 7
step 3 uses C_new[7], then next_cursor = 8
```

第 3 步结束后：

```text
active_chunk = C_new
active_cursor = 8
blend_active = False
```

所以下一个普通 tick 会从：

$$
C^{new}_8
$$

继续执行。

---

## 11. 如果新 chunk 来晚了怎么办？

上面的例子是假设 `C_new` 在 `active_cursor = 10` 时已经到了。

如果它没到，代码会继续消费旧 chunk：

```text
C_old[10]
C_old[11]
C_old[12]
...
```

等新 chunk 到了再 blend。

假设新 chunk 到达时，最后实际执行的是：

$$
C^{old}_{12}
$$

那么：

$$
O \approx \operatorname{SafetyGuard}(C^{old}_{12})
$$

但混合时仍然是固定端点：

$$
B_i = (1-\alpha_i)O + \alpha_iN_i
$$

不会变成：

$$
O_1=C^{old}_{12},\quad O_2=C^{old}_{13},\quad O_3=C^{old}_{14}
$$

---

## 12. 一句话总结

在当前源码中，chunk 边界混合不是“old chunk 后续轨迹”和“new chunk 后续轨迹”的逐点混合；它是：

```text
固定旧端点 O = 进入混合前最后实际执行的安全动作
  +
新 chunk 中从 aligned index 开始的连续动作 N1, N2, N3
  ↓
生成三步 raw blend B1, B2, B3
  ↓
再经过 SafetyGuard 变成最终 ControlCommand
```

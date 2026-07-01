---
tags:
  - term-explainer
  - pi05
  - numerical-computation
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# blending

> [!abstract] 核心定义
> 将上一个安全动作和新 chunk 动作按权重插值，以实现 chunk 切换时的平滑过渡。

## 输入与输出

| 方向 | 变量名 | 含义 | 值域/类型 |
|------|--------|------|-----------|
| 输入 | old | 上一个安全动作 | np.ndarray(14,) |
| 输入 | new | 新 chunk 中的当前动作 | np.ndarray(14,) |
| 输出 | blended | 混合后动作 | np.ndarray(14,) |

## 数学公式

$$
blended = (1-\alpha)\cdot old + \alpha\cdot new,\quad \alpha = 3s^2 - 2s^3
$$

- `alpha`：平滑过渡权重
- `s`：当前混合步数 / 总混合步数

## 具体数值示例

> [!example]- 点击展开数值计算过程
> 假设 old=0，new=10，s=0.5，则 alpha=0.5，blended=5。结果是从旧动作向新动作平滑过渡。

## 具象隐喻

> [!tip] 生活场景类比
> 像开车换道：不是瞬间打满方向盘，而是在几个瞬间内平滑转过去。

---
tags:
  - ROS
  - Pi05
  - term
  - concept
---

# GPU tensor device

> [!abstract] 核心定义
> `GPU tensor device` 指 PyTorch tensor 当前存放在哪个计算设备上，例如 CPU 或 `cuda:0`。Pi0.5 大模型推理通常需要把 tensor 放到 GPU 上。

## 基本概念

| 概念 | 含义 |
|---|---|
| CPU tensor | 数据在普通内存里，适合 Python、NumPy、tokenizer 等处理 |
| GPU tensor | 数据在显存里，适合大模型矩阵计算 |
| device | tensor 所在的设备，例如 `cpu`、`cuda:0` |

## 在本链路中的作用

部署代码中先执行：

```python
batch = self.preprocessor(self._build_batch(observation))
```

这一步主要留在 CPU。

然后执行：

```python
batch = _move_tensors_to_device(batch, self.device)
```

这一步才把 tensor 移动到 GPU。

## 为什么不一开始就放到 GPU？

因为 Pi0.5 preprocessor 中有一些步骤更适合 CPU，尤其是 state 离散化会用 NumPy。

如果太早放到 GPU，后面又要转回 CPU，反而会产生同步开销。

## 具象隐喻

> [!tip] 生活场景类比
> CPU 像办公室，适合整理文件、写说明、填表；GPU 像大型工厂，适合批量加工。你不会把一堆没整理好的纸直接送进工厂，而是先在办公室整理好，再送去工厂加工。

## 源码证据

- `pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py:65-69`
- `pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py:205-212`


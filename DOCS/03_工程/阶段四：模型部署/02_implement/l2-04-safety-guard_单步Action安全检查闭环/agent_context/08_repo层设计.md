# repo 层设计：L2-04

## 1. 本 L2 不在该层新增源码产物

原因：L2-04消费的 candidate、reference、config 都已在当前 Python 进程 RAM 中。它不读取 bundle、normalizer、配置文件、topic、硬件或网络资源。

## 2. 依赖与边界

- `repo/` 的 bundle/normalizer 读取属于 L2-01/L2-03。
- L2-04 不得通过 repo 反查 action 值域或硬件寄存器；ActionDomain 必须在启动前由 L2-01固定。
- service 允许依赖 repo，但本文件不需要该依赖。

## 3. Class/函数、Pi0.5 与验收

无 Class、无函数、无副作用。Pi0.5 也没有属于 safety guard 的外部资源读取微元。

验收如何确认：`PURITY-IMPORT` 确认 `service/safety_guard.py` 不 import repo loader，不打开路径或文件。

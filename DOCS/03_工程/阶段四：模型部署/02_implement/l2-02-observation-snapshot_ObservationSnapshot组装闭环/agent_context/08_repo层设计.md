# repo 层设计：L2-02

## 1. 目标源码路径

```text
本 L2 不在该层新增源码产物。
```

## 2. 原因

L2-02 不读取模型 bundle、normalizer、manifest、checkpoint 或外部文件。它处理的是已经通过 ROS topic 进入当前 Python 进程的消息，以及 L2-01 提供的 RAM 配置对象。

## 3. class 设计

无新增 class。

## 4. 函数设计

无新增函数。

## 5. 输入输出

| 输入 | 输出 |
|---|---|
| 无 repo 输入 | 无 repo 输出 |

## 6. 副作用

无文件、网络、模型权重或硬件读取副作用。

## 7. 依赖方向

`repo/` 不参与 L2-02。后续 L2-03 的 bundle / policy loader 才会使用 repo 层。

## 8. Pi0.5 参考

无直接 repo 参考。Pi0.5 observation collector 和 ROS node 都不属于外部文件读取层。

## 9. 验收如何确认

- L2-02 目标文件列表不包含 `src/model_deploy/act/repo/*`。
- L2-02 service/runtime/ui 中不加载 bundle、normalizer 或 checkpoint。
- `rg` 不应在 L2-02 目标源码中发现模型文件读取逻辑。

## 10. 边界继承声明

本文件服务当前 L1/L2 功能边界，不从旧 layer-based L2 卡片继承任务边界。


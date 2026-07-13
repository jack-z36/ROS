# repo 层设计：L2-05

> [!info] 元信息
> - 消费对象：L3 生成与边界验收 Agent。
> - 权威性：确认 repo 层无产物。
> - 上游来源：L2-05 只消费已进入 RAM 的 request/config。
> - 不负责范围：不读 bundle、文件、网络或硬件。
> - 读取时机：任何人提议为 L2-05 新建 reader/driver repository 时。

## 1. 结论

本 L2 不在该层新增源码产物。

原因：

- C7 配置已由 L2-01/启动装配送入 RAM。
- CLI 参数在启动入口解析后以 bool 注入，不由 repo 读取 argv。
- B1/B2/B3 不打开 YAML、bundle、checkpoint 或 normalizer。
- ROS topic 写出属于 ui 外部边界，不是 repo 资源读取。

验收如何确认：

- L2-05 目标文件清单无 `src/model_deploy/act/repo/` 修改。
- `action_output_adapter.py` / `action_publisher.py` 不使用 `open()`、Path 读取、网络客户端或硬件 SDK。
- bundle/checkpoint/normalizer 仍只由 L2-01/L2-03 处理。

## 2. 层职责与边界

repo 负责进程外资源读取和反序列化。本 L2 唯一外部副作用是 ROS publish，必须落 ui。把 driver 封成 repo 会掩盖硬件边界并违反“ACT 不直接调用厂商接口”。

## 3. class / function / 输入输出

```text
本层无 class。
本层无函数。
本层无输入输出。
本层无副作用。
```

## 4. 依赖关系

无新增依赖。任何 L2-05 service/ui 反向要求 repo reader 都必须先回到 L1/L2 边界重新设计。

## 5. Pi0.5 参考

Pi0.5 bridge/mux 读取 config 后直接订阅/发布，不构成可复用 repo；旧硬件 launch 参数也不能迁入 repo。

## 6. 边界继承声明

本结论继承当前 L1/L2 功能边界，不从旧 layer-based repo 卡片推导。无产物不是遗漏，而是对进程外读取边界的机械约束。

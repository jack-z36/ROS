# types 层设计：L2-01

## 1. 目标源码路径

```text
src/model_deploy/act/types/state_spec.py
src/model_deploy/act/types/action_spec.py
src/model_deploy/act/types/contract_result.py
```

## 2. 层职责

`types/` 只放数据结构、常量、维度、段序、codec、result 对象。不得读取配置、不得依赖 ROS、不得加载模型或硬件。

## 3. 文件设计

### state_spec.py

- 职责：定义部署侧 16D observation state 的维度、段序、字段语义和值域。
- class：`StateSpec` frozen dataclass。
- 函数：`ensure_state_vector(flat)`、`encode_state(structured)`。
- 不负责：触觉维度、ROS topic 订阅、运行时 snapshot 新鲜度。
- 验收覆盖：合法 16D 通过，非法维度失败。

### action_spec.py

- 职责：定义 16D single action 的维度、段序、字段语义和值域。
- class：`ActionSpec` frozen dataclass。
- 函数：`ensure_action_vector(flat)`、`split_action(flat)`。
- 不负责：ActionChunk 生命周期、cursor、平滑、blend、发布。
- 验收覆盖：合法 16D action 可拆分，非法维度失败。

### contract_result.py

- 职责：定义 bundle/normalizer 契约检查结果对象。
- class：`BundleContractResult`、`NormalizerContractResult`。
- 函数：无，纯数据对象。
- 验收覆盖：pass/fail 结果字段可读。

## 4. 边界继承声明

本文件边界来自当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

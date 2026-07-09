# types 层设计：L2-02

## 1. 目标源码路径

```text
src/model_deploy/act/types/observation.py
```

## 2. 层职责

`types/` 只定义跨模块数据结构、字段、维度和值域。它不得读取配置、不得 import ROS、不得维护 runtime buffer、不得执行图像预处理。

## 3. 文件设计

### `ObservationState`

- 职责：表达 L2-02 从 TCP pose 和 gripper state 组装出的结构化 ACT observation state。
- class：frozen dataclass。
- 字段建议：`left_tcp_position`、`left_tcp_orientation`、`left_gripper_width`、`right_tcp_position`、`right_tcp_orientation`、`right_gripper_width`。
- 输入：service 层已转换成 RAM 数组 / float 的 pose 与 gripper width。
- 输出：传给 L2-01 state codec 的结构化 state。
- 不负责：ROS message、topic 名、时间戳缓存。

### `ObservationSnapshot`

- 职责：定义 L2-02 对 L2-03 和 L2-06 暴露的完整 observation RAM 对象。
- class：frozen dataclass。
- 字段：
  - `images: Mapping[str, object]`
  - `state: ObservationState`
  - `encoded_state: np.ndarray`
  - `captured_at_s: float`
- 函数：可提供 `validate_encoded_state_dim(expected_dim=16)` 或在 `__post_init__` 中检查 shape。
- 输入：service 层组装结果。
- 输出：L2-03 batch adapter 和 L2-06 latest observation reader 消费。
- 不负责：snapshot 是否应该被写入 buffer。

### `ObservationFreshnessResult`

- 职责：表达 missing / stale 诊断，供 Gate、日志和 status 汇总使用。
- class：frozen dataclass。
- 字段：`missing_fields`、`stale_fields`、`field_ages_s`、`ready`。
- 不负责：发布 metrics topic。

## 4. 依赖方向

`types/observation.py` 可以依赖标准库、`typing`、`dataclasses` 和 `numpy`。不得依赖 `config/repo/service/runtime/ui`。

## 5. Pi0.5 参考

- `shared_buffer.py::ObservationSnapshot` 提供冻结 snapshot 结构参考。
- `state_codec.py::BimanualState` 提供 structured state 思路，但 ACT 必须改为 16D state 契约。

## 6. 验收覆盖

- `ObservationSnapshot.encoded_state` 是 16D。
- downstream 可以 import `ObservationSnapshot` 而不 import L2-02 service/runtime/ui。
- 非法 encoded_state 维度被拒绝。

## 7. 边界继承声明

本文件服务当前 L1/L2 功能边界，不从旧 layer-based L2 卡片继承任务边界。


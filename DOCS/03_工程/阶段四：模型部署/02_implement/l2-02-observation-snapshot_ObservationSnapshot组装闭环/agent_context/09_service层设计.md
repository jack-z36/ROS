# service 层设计：L2-02

## 1. 目标源码路径

```text
src/model_deploy/act/service/observation_collector.py
src/model_deploy/act/service/image_preprocess.py
```

## 2. 层职责

`service/` 负责 RAM 内业务计算、转换和校验。L2-02 的 service 层接收 ui 层转换后的 RAM 值，维护字段缓存，判断字段齐全和新鲜，调用 state codec 生成 16D state，构造 `ObservationSnapshot`。

service 层不得 import ROS，不得创建 timer/thread，不得写硬件或 topic。

## 3. 文件设计

### `observation_collector.py`

文件职责：

- 保存最新 image / TCP pose / gripper width RAM 值。
- 保存每个字段的 monotonic stamp。
- 判断 required fields 是否齐全。
- 判断字段是否 stale。
- 调 L2-01 state codec 生成 16D encoded_state。
- 构造 `ObservationSnapshot`。

class 设计：

| class | 封装微元 | 内部状态 | 为什么是 class |
|---|---|---|---|
| `ObservationCollector` | 字段缓存、update 函数、missing/stale 检查、snapshot 构造 | `_images`、`_values`、`_stamps`、`_lock`、required fields | callback 多次到达，需要跨调用保存字段和时间戳 |

函数 / method 设计：

| 函数 | 输入 | 输出 | 副作用 | 错误行为 |
|---|---|---|---|---|
| `update_image(name, image)` | image key、RAM image | 无 | 更新 image cache / stamp | unknown key 可拒绝或记录 |
| `update_tcp_pose(side, position, orientation)` | side、pose arrays | 无 | 更新 pose cache / stamp | shape 非法抛错 |
| `update_gripper_state(side, width)` | side、float width | 无 | 更新 gripper cache / stamp | width 非法抛错或记录 |
| `missing_fields()` | 无 | list[str] | 无 | 无 |
| `stale_fields(now, max_age_s)` | time、timeout | list[str] | 无 | 无 |
| `snapshot(max_age_s)` | freshness 参数 | `ObservationSnapshot` 或 `None` | 无 | state codec 失败则抛明确异常或返回 diagnostic |

> deploy_057 契约加固：`ObservationCollector` 接收注入的 `monotonic_clock`
> （默认 `time.monotonic`），所有字段 stamp 与 `captured_at_s` 均来自同一
> monotonic 时钟域；`snapshot()` 不再使用 `time.time()`。`ObservationSnapshot`
> 构造时对所有 ndarray 做深复制（见 `types/observation.py`），因此已发布的
> snapshot 不受 collector 缓存后续修改影响。

### `image_preprocess.py`

文件职责：

- 把 ui 层 decode 后的 RGB image RAM 对象转为 ACT 模型约定的 image tensor / array。
- 校验 image shape、dtype 和 resize 参数。
- 整数图像（如 uint8 0..255）归一化为 `[0,1]` float32；非有限值抛错。

函数设计：

| 函数 | 输入 | 输出 | 副作用 | 错误行为 |
|---|---|---|---|---|
| `preprocess_observation_image(image, image_config)` | RGB image、L2-01 image config | ACT image tensor / array（float32 [0,1]） | 无 | unsupported shape / dtype / 非有限值 抛错 |

## 4. 输入输出

| 输入 | 输出 |
|---|---|
| RAM image、TCP pose、gripper width、L2-01 state codec、max_age_s | `ObservationSnapshot` 或 diagnostics |

## 5. 依赖关系

允许依赖：

- `types/observation.py`
- L2-01 的 state spec / codec / config 对象
- 标准库、`numpy`

禁止依赖：

- `runtime/observation_buffer.py`
- `ui/observation_ros_adapter.py`
- ROS packages
- ACT policy runtime / model loader

## 6. Pi0.5 参考

- `ObservationCollector` 结构参考 Pi0.5 `observation_collector.py`。
- image preprocess 的调用边界参考 Pi0.5 `pi05_vla_deploy_node.py::_image_cb`。
- state 编码参考 Pi0.5 `state_codec.py`，但 ACT 必须使用 16D state。

## 7. 验收覆盖

- mock 全字段可生成 snapshot。
- 缺字段返回 `None` 和 missing list。
- stale 字段返回 `None` 和 stale list。
- service 层在无 ROS 环境下可 import 和单测。

## 8. 边界继承声明

本文件服务当前 L1/L2 功能边界，不从旧 layer-based L2 卡片继承任务边界。


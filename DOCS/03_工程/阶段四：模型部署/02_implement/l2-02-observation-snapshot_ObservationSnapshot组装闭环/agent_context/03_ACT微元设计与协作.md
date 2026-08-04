# ACT 微元设计与协作：L2-02

## 1. 设计目标

L2-02 的 ACT 版设计把 Pi0.5 中混在 collector、shared buffer 和 ROS node 里的 observation 能力拆成清晰分层：

- `types/` 定义跨 L2 公共数据语言。
- `service/` 完成 RAM 内字段汇聚、齐全性和新鲜度判断。
- `runtime/` 保存 latest-only observation。
- `ui/` 把外部 ROS message 转为 service 可消费的 RAM 值。

本设计不生成 L3 文件，也不实现源码。

## 2. ACT 微元设计表

| ACT 微元 | 3.5 type | target layer | target file | function/class | inputs | outputs | side effects | Pi0.5 reference |
|---|---|---|---|---|---|---|---|---|
| `ObservationSnapshot` | 数据 | `types` | `src/model_deploy/act/types/observation.py` | frozen dataclass | images、structured state、encoded_state、captured_at_s | 跨 L2 snapshot 对象 | 无 | `shared_buffer.py::ObservationSnapshot` |
| `ObservationState` | 数据 | `types` | `src/model_deploy/act/types/observation.py` | frozen dataclass | left/right TCP pose、left/right gripper width | state codec 输入对象 | 无 | `state_codec.py::BimanualState` |
| `ObservationFreshnessResult` | 数据 | `types` | `src/model_deploy/act/types/observation.py` | frozen dataclass | missing fields、stale fields、age map | 可观察诊断 | 无 | `ObservationCollector.missing_fields` |
| `ObservationCollector` | 内部状态更新函数 / 编排函数 | `service` | `src/model_deploy/act/service/observation_collector.py` | class | image tensors、TCP pose、gripper width、state codec、required fields | snapshot 或 `None`、diagnostics | 修改 RAM 内缓存和 stamps | `observation_collector.py::ObservationCollector` |
| `update_image` | 内部状态更新函数 | `service` | `src/model_deploy/act/service/observation_collector.py` | method | camera key、image tensor | 缓存更新 | 更新 images / stamps | `ObservationCollector.update_image` |
| `update_tcp_pose` | 内部状态更新函数 | `service` | `src/model_deploy/act/service/observation_collector.py` | method | side、position、orientation | 缓存更新 | 更新 pose / stamps | `ObservationCollector.update_vector` |
| `update_gripper_state` | 内部状态更新函数 | `service` | `src/model_deploy/act/service/observation_collector.py` | method | side、width | 缓存更新 | 更新 gripper / stamps | `ObservationCollector.update_hand` |
| `snapshot` | 计算函数 / 编排函数 | `service` | `src/model_deploy/act/service/observation_collector.py` | method | max_age_s、cached fields | `ObservationSnapshot` 或 `None` | 无外部副作用 | `ObservationCollector.snapshot` |
| `missing_fields` | 计算函数 | `service` | `src/model_deploy/act/service/observation_collector.py` | method | cached fields | list[str] | 无 | `ObservationCollector.missing_fields` |
| `preprocess_observation_image` | 计算函数 | `service` | `src/model_deploy/act/service/image_preprocess.py` | function | RGB image array、image config | ACT image tensor / array | 无 | `preprocess_rgb_image` call site in node |
| `ObservationBuffer` | 内部状态更新函数 | `runtime` | `src/model_deploy/act/runtime/observation_buffer.py` | class | snapshot、max_age_s | latest snapshot 或 `None` | 覆盖 latest snapshot、更新 counters | `SharedBuffer.set_observation` / `latest_observation` |
| `ObservationMetrics` | 数据 / 内部状态更新函数 | `runtime` | `src/model_deploy/act/runtime/observation_buffer.py` | dataclass | write/read events、missing/stale reason | observation_ready、missing_fields、stale_observation_count | 维护 RAM counters | `RuntimeMetrics.dropped_observation_count` |
| `ObservationRosAdapter` | 数据读写函数 / 编排函数 | `ui` | `src/model_deploy/act/ui/observation_ros_adapter.py` | class | ROS node、DeployConfig topics、collector、buffer | ROS subscriptions | 创建 subscription，处理 callback | `Pi05VlaDeployNode._create_subscriptions` |
| `decode_image_message` | 数据读写函数 / 计算函数 | `ui` | `src/model_deploy/act/ui/observation_ros_adapter.py` | function | ROS Image / CompressedImage | RGB image array | 读取 ROS message payload | `_decode_image` |
| `handle_*_callback` | 数据读写函数 / 编排函数 | `ui` | `src/model_deploy/act/ui/observation_ros_adapter.py` | methods | ROS messages | collector update + maybe buffer write | callback 副作用 | `_image_cb`、`_point_cb`、`_hand_cb` |

## 3. 六层产物设计表

| 层 | 是否需要 | 文件路径 | 职责 | 输入 | 输出 | 不负责 |
|---|---|---|---|---|---|---|
| types | 是 | `src/model_deploy/act/types/observation.py` | 定义 `ObservationSnapshot`、structured observation state 和诊断对象 | RAM values | 公共 dataclass | ROS、缓存、预处理 |
| config | 否 | 无新增 L2-02 专属文件 | 读取 L2-01 `DeployConfig` | topic/image/max_age 配置 | 无新增配置 schema | 不重复定义 topic schema |
| repo | 否 | 无新增 L2-02 专属文件 | 不读取外部文件 | 无 | 无 | 不读 bundle / normalizer |
| service | 是 | `src/model_deploy/act/service/observation_collector.py`, `src/model_deploy/act/service/image_preprocess.py` | RAM 内字段汇聚、预处理和 snapshot 生成 | image / pose / gripper RAM 值 | snapshot 或 diagnostics | ROS subscription、timer、模型 |
| runtime | 是 | `src/model_deploy/act/runtime/observation_buffer.py` | latest-only observation 保存和新鲜度读取 | snapshot | latest snapshot / counters | request queue、chunk queue、ControlLoop |
| ui | 是 | `src/model_deploy/act/ui/observation_ros_adapter.py` | ROS message 到 service 输入的 adapter | ROS messages | collector update / buffer write | 核心业务、推理、硬件发送 |

## 4. 内部协作关系

Creation order:

1. L2-01 生成 `DeployConfig`、state spec / codec、topic config 和 image config。
2. L2-02 创建 `ObservationCollector`，注入 required fields、state codec 和 image keys。
3. L2-02 创建 `ObservationBuffer`。
4. 在 ROS 环境中，`ObservationRosAdapter` 根据 config 绑定 callbacks。
5. callback 到达后，adapter 只做消息解码和类型转换，调用 collector update。
6. 每次 update 后尝试 `collector.snapshot(max_age_s)`。
7. 生成 snapshot 时写入 `ObservationBuffer.set_observation(snapshot)`。

State owner:

- `ObservationCollector` 持有单字段缓存和 stamps。
- `ObservationBuffer` 持有 latest complete snapshot。
- `ObservationSnapshot` 创建后只读。

Pure RAM calculations:

- required field 检查。
- stale field 检查。
- image preprocess。
- 16D state encode。
- missing / stale diagnostics。

External boundary reads/writes:

- `ObservationRosAdapter` 是唯一 ROS message 读取边界。
- L2-02 不写外部 topic；status / metrics 发布由后续 L2 统一装配。

Runtime orchestration point:

- L2-02 的局部编排点是 callback 后的 `try_publish_observation`。
- 全局控制节奏仍由 L2-06 `ControlLoop.tick()` 决定。

Failure propagation:

- 缺字段：collector 返回 `None` 和 missing fields，L2-06 不提交推理。
- 字段过期：collector 或 buffer 返回 `None`，L2-06 fallback。
- 图像 decode 失败：ui adapter 记录 warning / diagnostic，不更新对应字段。
- state encode 失败：snapshot 不生成，Gate 判为 local failure。

## 5. 失败传播

| 失败 | L2-02 发现位置 | 对外信号 | 下游行为 |
|---|---|---|---|
| 缺 image / pose / gripper 字段 | `ObservationCollector.missing_fields()` | missing field list | L2-06 继续 waiting / fallback，不提交推理 |
| 字段超时 | `snapshot(max_age_s)` 或 `ObservationBuffer.latest_observation(max_age_s)` | stale field / stale count | L2-06 fallback |
| image decode 失败 | `ObservationRosAdapter.decode_image_message` | warning / diagnostics | 不更新 image cache |
| 16D 编码失败 | state codec call | exception / diagnostic | Gate fail，禁止下游使用非法 snapshot |
| 无 ROS 环境 | import / adapter init | `env-blocked` | service/runtime mock 测试仍可通过 |

## 6. 确认状态

本设计已按当前计划锁定以下默认：

- `ObservationSnapshot` 放在 `types/observation.py`。
- L2-02 只生成 L2 设计包，不创建 L3 文件。
- Pi0.5 源码只结构复用，不照搬 26D state 或 legacy topic。


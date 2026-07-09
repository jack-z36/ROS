# service 层设计：L2-03

## 1. 目标源码路径

```text
src/model_deploy/act/service/batch_adapter.py
src/model_deploy/act/service/normalizer.py（可选；或直接复用 repo 持有的 normalizer 对象）
```

## 2. 层职责

`service/` 负责 RAM 内业务计算、转换、校验。L2-03 在这一层做：把 `ObservationSnapshot` 加工成 ACT batch（纯 RAM 内 dict 构造），以及 normalizer 的 normalize/unnormalize 调用（纯 RAM 内 min-max 变换）。不安排线程、不持有 queue、不做 ROS。

## 3. 文件设计

### batch_adapter.py

- **职责**：把 `ObservationSnapshot` 映射为 LeRobot ACT 可消费的 batch dict；处理 batch key；调 state normalizer 做 normalize。
- **函数设计**：

| 函数 | 类型 | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|
| `build_act_batch(observation, state_normalizer, task, image_names)` | 计算函数 | ObservationSnapshot + ActionStateNormalizer + str + tuple | dict[str, CPU float Tensor]（含 `observation.state`(16,) normalized、`observation.images.*`、`task`） | 无 | `Pi05PolicyRuntime._build_batch`（结构复用） |
| `_require_cpu_float_tensor(tensor, name)` | 计算函数 | Tensor | CPU float Tensor | 无 | 直接复用（或从 repo 共用） |

- **class 设计**：无 class。batch 构造是无状态纯转换，按判断原则优先函数。
- **不负责**：不做模型前向（属 repo `ActPolicyRuntime`）；不跨越 GPU 边界（batch 留 CPU，等 `ActPolicyRuntime` 内 `_move_tensors_to_device`）；不订阅 topic；不做单步选择；不做平滑。
- **依赖方向**：`service` → `types`（StateSpec）、`config`（无直接依赖，参数从 runtime 传入）、`repo`（normalizer 对象来自 repo 加载）。禁止 import `runtime`/`ui`。
- **Pi0.5 参考**：`Pi05PolicyRuntime._build_batch`（结构复用，batch key 按 ACT 要求）。
- **验收覆盖**：合法 snapshot 生成正确 batch dict；缺图像 key 抛 `KeyError`；state 已归一化到 [-1,1]。

> [!note] _build_batch 落点选择
> Pi0.5 把 `_build_batch` 作为 `Pi05PolicyRuntime` 的 method。ACT 第一版可选择：
> (a) 作为独立函数放 `service/batch_adapter.py`（符合六层职责，batch 构造是 service 层 RAM 内计算）；
> (b) 作为 `ActPolicyRuntime._build_batch` method 保留（与 Pi0.5 一致，但让 repo 持有 service 逻辑）。
> **推荐 (a)**：保持六层职责清晰，`ActPolicyRuntime.predict_action_chunk` 调用 `build_act_batch`。

### normalizer.py（可选）

- **职责**：封装 normalizer 的使用（normalize/unnormalize 调用）。
- **现状**：`ActionStateNormalizer`（来自 Pi0.5 `common/data/normalization.py`）已经是成熟 class，`normalize`/`unnormalize` 是其 method。第一版**推荐直接复用该 class 对象**（由 repo `load_act_policy_runtime` 加载并持有），不需要额外 service 封装。
- **若需封装**：提供 `normalize_state(state, normalizer)` / `unnormalize_action_chunk(norm_chunk, normalizer)` 薄函数，纯 RAM 内变换。
- **验收覆盖**：normalize→unnormalize 往返一致；长度匹配 16D。

## 4. 与去除平滑处理的关系

第一版没有独立 action smoothing service。本 L2 不创建 smoother、chunk blender、RTC aligner、smoothstep service。`batch_adapter.py` 只做 batch 构造，不做 chunk 内插值或跨 chunk 融合。

## 5. 验收如何确认

- `batch_adapter` 单测：合法 snapshot → 正确 batch dict。
- normalizer 往返测试：16D 向量 normalize→unnormalize 一致。
- `rg` 检查 `service/` 下不存在 smoother/blender/RTC 平滑逻辑。

## 6. 边界继承声明

本文件边界来自当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

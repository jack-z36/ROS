# types 层设计：L2-03

## 1. 本层新增产物

```text
src/model_deploy/act/types/action_chunk.py
```

本 L2 只在 `types/` 新增一个跨模块结果类型：`ActionChunk`。

## 2. 类型职责

`ActionChunk` 表示“一次 ACT 前向业务计算已经完成后的 physical actions”。它是 L2-03 到 L2-06 的唯一跨模块输出，不是 runtime result record。

```text
ActionChunk
└── actions: np.ndarray (chunk_size, 16), float32
```

它不表达：请求身份、观测时间、推理耗时、队列、active 状态、cursor、错误、fallback 或发布结果。

## 3. 数据与构造约束

建议实现为 frozen dataclass，使字段引用在构造后不能重新绑定。数组内容的所有权处理可在实现时选择 copy 或只读标记，但不得改变公开字段语义。

| 字段 | 内部结构 | 数值类型 | 说明 |
|---|---|---|---|
| `actions` | 二维 `np.ndarray` | `float32` | 每行一个完整 16D physical action |

构造阶段必须验证：

- `actions.ndim == 2`。
- `actions.shape[1] == ACTION_DIM == 16`。
- `actions.dtype == np.float32`。
- 所有元素有限。
- action 行数大于零。

`chunk_size` 的精确相等关系由 service 阶段三对照 `DeployConfig.runtime.chunk_size` 验证；types 不持有 `DeployConfig`，不得反向 import config。

## 4. 固定 16D 语义

`ActionChunk.actions` 的每一行与 L1 §1.5 完全一致：

```text
[0:3]   left TCP position in m / left_arm_base
[3:7]   left TCP quaternion (x,y,z,w) / left_arm_base
[7:10]  right TCP position in m / right_arm_base
[10:14] right TCP quaternion (x,y,z,w) / right_arm_base
[14]    left gripper in ACT [0,1]
[15]    right gripper in ACT [0,1]
```

本 type 不负责 split、frame 转换、quaternion 修正、gripper 映射或安全检查；这些分别已有静态 action spec、L2-04 和 L2-05 的边界。

## 5. 明确不存在的字段和方法

以下 Pi0.5 runtime 结构不得进入本 type：

```text
obs_time
infer_start_time
ready_time
action_dt
request_id
cursor
aligned_index(now)
latency/error/metrics
```

原因：这些都是 L2-06 运行记录或消费逻辑。L2-06 可在接收 `ActionChunk` 后创建自己的 result record，但不得反向向 `ActionChunk` 添加字段。

## 6. 依赖关系

```text
types/action_chunk.py
-> 可复用 types/action_spec.py 的 ACTION_DIM
-> 不 import config/repo/service/runtime/ui
```

`ObservationSnapshot` 是输入 type，来自 L2-02；它不需要被 `ActionChunk` 引用或嵌套。

## 7. 验收

`tests/types/test_action_chunk.py` 至少验证：

- 合法 `(N,16)` float32 finite array 可以构造。
- rank、最后一维、dtype、NaN/Inf、空 chunk 分别失败。
- 对象没有运行元数据字段。
- L2-06 只通过 `actions` 读取每一步 raw action。

## 8. 边界声明

本层新增的是业务结果值对象，不是 L2-06 的 queue item、active chunk 或带时间戳的 runtime record。

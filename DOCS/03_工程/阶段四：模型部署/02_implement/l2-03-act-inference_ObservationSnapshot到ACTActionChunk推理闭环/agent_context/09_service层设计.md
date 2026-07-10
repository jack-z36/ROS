# service 层设计：L2-03

## 1. 目标源码树

```text
src/model_deploy/act/service/
├── act_inference.py
├── observation_batch.py
└── action_chunk_postprocess.py
```

`service/` 只进行当前 Python 进程内的业务计算。它可使用 tensor/GPU 计算，但不读文件、不碰 ROS、不向机器人发命令，也不拥有运行调度状态。

## 2. 聚合总览

```text
ActInferenceService
└── predict_action_chunk(snapshot)                 # 总编排入口
    ├── prepare_observation_batch(...)              # 一级阶段一
    │   └── 7 个输入计算微元
    ├── run_act_inference(policy, batch)            # 一级阶段二
    └── postprocess_action_chunk(...)               # 一级阶段三
        └── 6 个输出计算微元
```

`ActInferenceService` 是唯一新增 class。三个一级阶段使用函数，以保持输入输出显式、可独立单测。

## 3. `act_inference.py`

### 3.1 class：`ActInferenceService`

| 数据字段 | 内部结构 | 数值/对象类型 | 用途 |
|---|---|---|---|
| config 引用 | immutable config object | `DeployConfig` | 读取 16D/chunk/device 语义 |
| state normalizer 引用 | normalizer object | `ActionStateNormalizer` | 阶段一 normalize |
| action normalizer 引用 | normalizer object | `ActionStateNormalizer` | 阶段三 unnormalize |
| policy 引用 | loaded model object | ACT policy protocol | 阶段二 chunk forward |
| 输入规格 | tuple/mapping 等只读内部结构 | feature key、shape、device、dim | snapshot 到 batch 的确定性适配 |

class 构造只允许从 RAM 引用提取输入规格和做适配前置检查。它不得读文件、加载权重、配置 policy、建立 queue/thread 或保存当前请求数据。

### 3.2 总编排入口

```text
predict_action_chunk(observation: ObservationSnapshot) -> ActionChunk
```

| 步骤 | 调用 | 输入 -> 输出 | 失败行为 |
|---|---|---|---|
| ① | `prepare_observation_batch` | snapshot -> device batch | 立即向上传播 |
| ② | `run_act_inference` | batch -> raw tensor | 立即向上传播 |
| ③ | `postprocess_action_chunk` | raw tensor -> ActionChunk | 立即向上传播 |

该方法是 L2-06 唯一允许调用的 L2-03 service 接口。L2-06 不得直接调三个内部阶段函数。

### 3.3 一级阶段二：`run_act_inference`

```text
run_act_inference(policy, batch) -> raw_action_tensor
```

| 微元 | 类型 | 输入 | 输出/异常 |
|---|---|---|---|
| 推理执行上下文 | 计算函数 | device batch | 无梯度的当前调用上下文 |
| ACT chunk API 调用 | 计算函数 | loaded policy + batch | policy 原始 tensor 或前向异常 |
| 原始结果交接 | 数据边界 | policy return | 未修改 raw tensor |

仅允许调用 `policy.predict_action_chunk(batch)`。不调用 `select_action`，不做 unnormalize，不做 shape 修补，不记录耗时。

## 4. `observation_batch.py`

### 4.1 一级阶段一：`prepare_observation_batch`

```text
prepare_observation_batch(snapshot, state_normalizer, input_spec, device)
    -> dict[str, Tensor]
```

| 顺序 | 计算微元 | 输入 | 输出/异常 |
|---|---|---|---|
| ① | 模型输入兼容性检查 | snapshot + input spec | 通过或具体不兼容异常 |
| ② | State tensor 表达转换 | physical ndarray `(16,)` | CPU float32 Tensor `(16,)` |
| ③ | State 数值归一化 | state Tensor + state normalizer | normalized Tensor `(16,)` |
| ④ | Image tensor 绑定 | logical camera mapping + snapshot images | full feature key 到 `(C,H,W)` Tensor 的映射 |
| ⑤ | Batch 维度添加 | state/image single-sample tensor | `(1,16)` / `(1,C,H,W)` |
| ⑥ | ACT batch 组装 | batched state/images | ACT observation batch dict |
| ⑦ | Device 对齐 | CPU batch + policy device | 全部 tensor 位于 policy device |

关键限制：

- ② 与 ③必须是两个可独立测试的函数，不得合并。
- ④不做 decode、resize、颜色、layout 或数值尺度修复。
- ⑥不写 `task`、`action`、request/time 字段。
- ⑦不移动 policy，不创建 pinned-memory cache，也不自动切换 device。

## 5. `action_chunk_postprocess.py`

### 5.1 一级阶段三：`postprocess_action_chunk`

```text
postprocess_action_chunk(raw_chunk, action_normalizer, expected_chunk_size)
    -> ActionChunk
```

| 顺序 | 计算微元 | 输入 | 输出/异常 |
|---|---|---|---|
| ① | Raw 输出结构检查 | policy return | 仅接受 finite `(1,N,16)` Tensor |
| ② | Batch 维移除 | `(1,N,16)` | `(N,16)` Tensor |
| ③ | Action 反归一化 | normalized Tensor + action normalizer | physical Tensor `(N,16)` |
| ④ | CPU float32 array 转换 | physical Tensor | contiguous numpy float32 `(N,16)` |
| ⑤ | 最终输出契约检查 | physical array + expected N | 合法 array 或异常 |
| ⑥ | ActionChunk 构造 | validated physical array | 只含 actions 的 ActionChunk |

关键限制：

- ①必须同时验证 B=1、N=`chunk_size`、D=16；不接受“接近正确”的输出。
- ③只调用 `action_normalizer.unnormalize()` 一次。
- ⑤不调用 L2-04 安全检查。
- 全流程禁止 clamp、crop、pad、repeat、reorder、quaternion/gripper 修正。

## 6. 依赖方向

```text
service
-> types: ObservationSnapshot / ActionChunk / ACTION_DIM
-> config: DeployConfig（只读）
-> repo: ActionStateNormalizer 类型（只读引用）
-> third_party: 已加载 ACT policy 的公开 chunk API

service -X-> runtime
service -X-> ui
service -X-> bundle/checkpoint I/O
```

## 7. 异常语义

service 层可以把错误分类为输入适配、policy 前向或输出契约错误，但不得改变以下规则：

```text
任意子功能异常
-> 当前一级阶段停止
-> 总入口停止
-> L2-06 接收异常
-> L2-06 决定 metrics/fallback/下一次调度
```

不允许 `try/except: return None`、`return zeros`、`return last_chunk` 或内部 retry。

## 8. service 验收

- 每个一级阶段独立单测。
- 总入口端到端 stub policy 单测。
- 两个 normalizer 的方向和调用次数测试。
- `select_action` spy 测试。
- raw 错 shape、NaN/Inf、policy 抛错的失败传播测试。
- 静态检查 service 中没有 ROS、I/O、runtime、safety 或 smoothing 代码。

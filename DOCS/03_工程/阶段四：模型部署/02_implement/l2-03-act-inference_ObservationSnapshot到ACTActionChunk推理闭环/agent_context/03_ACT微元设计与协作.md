# ACT 微元设计与协作：L2-03

## 1. 总体结构

L2-03 对 L2-06 只暴露一个同步入口：

```text
ObservationSnapshot -> ActionChunk
```

内部第一次封装为三个一级阶段：

```text
总编排入口
│
├── ① Observation 批次准备
│      ObservationSnapshot
│      -> ACT batch on policy device
│
├── ② ACT 前向推理
│      ACT batch
│      -> raw normalized action tensor
│
└── ③ ActionChunk 后处理
       raw normalized action tensor
       -> physical ActionChunk
```

batch 和 raw tensor 都是 service 内部临时数据，不进入 `types/`，也不允许 L2-06 逐阶段调用。

## 2. 3.25 层聚合

### 2.1 唯一 service class

推荐 `ActInferenceService` 统一持有：

```text
config: DeployConfig
state_normalizer: ActionStateNormalizer
action_normalizer: ActionStateNormalizer
policy: loaded ACT policy
derived policy input specification（只读）
```

选择 class 的原因：四项资源在程序全生命周期稳定存在，并被多次同步调用复用。class 只打包稳定依赖和总入口，不拥有运行调度状态。

禁止放入实例字段：

```text
current/last snapshot
current batch or raw chunk
request_id or request status
thread/event/queue/lock
active chunk/cursor/history
latency/error/metrics
retry/fallback state
last selected/published action
```

### 2.2 三个一级阶段不分别建 class

三个阶段没有独立生命周期、可变状态或资源所有权，使用函数即可。为每个阶段创建 class 只会隐藏输入输出，不提供状态封装价值。

## 3. 启动期只读上下文

L2-06 在启动组装阶段把 L2-01 产出的四项资源注入 service。service 只在 RAM 内完成以下适配准备：

1. 确认 policy 暴露 `predict_action_chunk`。
2. 从 config/policy RAM 元数据得到预期 `state_dim=16`、`action_dim=16`、`chunk_size`、device。
3. 从 policy input features 得到完整图像 feature key 和 shape。
4. 建立 `observation.images.<camera>` 到 snapshot logical camera key `<camera>` 的确定性映射。

这些是模型适配契约提取，不是 bundle 契约重验：不读文件、不加载权重、不修改 policy、不创建第五项 processor 依赖。

若 L2-01 已保证的 policy/config/normalizer 契约在 RAM 中仍然互相矛盾，service 应在创建或首次调用前失败，不得运行中裁剪输出补救。

## 4. 一级阶段一：Observation 批次准备

### 4.1 输入输出

```text
输入:
  ObservationSnapshot
  state_normalizer
  只读 policy input specification
  policy device

输出:
  dict[str, torch.Tensor]
  observation.state               -> (1, 16)
  observation.images.<camera>     -> (1, C, H, W)
  所有 tensor 位于 policy device
```

batch 不含 `task`、`action`、时间、request ID 或 runtime metadata。

### 4.2 七个子功能模块

| 顺序 | 子功能 | 3.5 类型 | 输入 | 输出/失败 | 精确边界 |
|---|---|---|---|---|---|
| 1 | 模型输入兼容性检查 | 计算函数 | snapshot + expected input spec | 通过或异常 | 检查 state 16D/有限值、必需相机、图像 shape/dtype/数值契约；不检查 freshness |
| 2 | State tensor 表达转换 | 计算函数 | physical `np.ndarray (16,)` | CPU `torch.float32 Tensor (16,)` | 只改变表示/dtype/连续性，不改变数值尺度 |
| 3 | State 数值归一化 | 计算函数 | physical state tensor + state normalizer | normalized Tensor `(16,)` | 只调用一次 `normalize()`；检查 shape 与有限值 |
| 4 | Image tensor 绑定 | 计算函数 | snapshot images + expected feature keys | `{full_policy_key: Tensor(C,H,W)}` | 精确相机键绑定和 tensor 化；不做像素级预处理 |
| 5 | Batch 维度添加 | 计算函数 | state/image single-sample tensors | state `(1,16)`、image `(1,C,H,W)` | 只增加 B=1；不 squeeze 其他维 |
| 6 | ACT batch 组装 | 计算函数 | batched state/images | batch dict | 只写 ACT policy 需要的 observation keys |
| 7 | Device 对齐 | 计算函数 | CPU batch + policy device | device-aligned batch | 产生 device tensors；不改 snapshot、不缓存 batch、不自动切换 device |

### 4.3 为什么 State 拆成两步

```text
physical ndarray (16,)
-> physical torch.float32 tensor (16,)    # 表达转换
-> normalized tensor (16,)                # 数值尺度转换
-> normalized batch tensor (1,16)         # batch 结构转换
```

这样可独立区分三类失败：输入不能 tensor 化、normalizer 计算失败、batch 结构错误。不得把 tensor 化和 normalize 合成一个不可观察步骤。

### 4.4 图像边界

L2-02 必须产出模型就绪单帧图像。L2-03 允许：

- 确认逻辑相机 key。
- 确认单帧 shape/dtype/数值约定。
- `np.ndarray`/tensor 到 policy tensor 表示适配。
- 添加 batch 维、移动 device。

L2-03 禁止：

- 解码 ROS image。
- BGR/RGB 转换。
- resize/crop/pad。
- HWC/CHW 等像素布局的猜测性修正。
- `/255`、mean/std 或其他未由上游契约声明的数值变换。
- 缺相机时复制另一相机图像。

## 5. 一级阶段二：ACT 前向推理

### 5.1 输入输出

```text
输入: ACT batch on policy device
输出: raw action tensor，预期 (1, chunk_size, 16)，仍是模型尺度
```

### 5.2 子功能模块

| 顺序 | 子功能 | 3.5 类型 | 职责 |
|---|---|---|---|
| 1 | 推理执行上下文 | 计算保护 | 禁止梯度记录，保证本次调用只有推理语义 |
| 2 | ACT chunk API 调用 | 计算函数 | 调用一次 `policy.predict_action_chunk(batch)` |
| 3 | 原始结果交接 | 数据边界 | 将 policy 返回对象交给阶段三；不在此 unnormalize、裁剪或选单步 |

该阶段故意保持很薄。它不调用 `select_action`，不捕获后重试，不记录时间，不更新任何 service-owned 状态。

## 6. 一级阶段三：ActionChunk 后处理

### 6.1 输入输出

```text
输入: raw model-scale tensor，必须是 (1, chunk_size, 16)
输出: ActionChunk(actions=(chunk_size,16), float32, physical semantics)
```

### 6.2 六个子功能模块

| 顺序 | 子功能 | 3.5 类型 | 输入 | 输出/失败 | 精确边界 |
|---|---|---|---|---|---|
| 1 | Raw 输出结构检查 | 计算函数 | policy return value | 合法 tensor 或异常 | 类型为 Tensor、rank=3、B=1、N=chunk_size、D=16、有限值；不修补 |
| 2 | Batch 维移除 | 计算函数 | `(1,N,16)` | `(N,16)` | 只移除已验证的 B=1 维 |
| 3 | Action 反归一化 | 计算函数 | normalized `(N,16)` + action normalizer | physical `(N,16)` | 只调用一次 `unnormalize()`；不 clamp |
| 4 | CPU float32 array 转换 | 计算函数 | physical tensor | contiguous CPU `np.ndarray float32` | 最终跨 L2 表示固定为 numpy float32 |
| 5 | 最终输出契约检查 | 计算函数 | physical array | 合法 array 或异常 | 严格 `(chunk_size,16)`、float32、有限值；不做 L2-04 安全范围判断 |
| 6 | ActionChunk 构造 | 数据构造 | validated physical array | `ActionChunk` | 只写 actions，不写任何运行元数据 |

### 6.3 不允许的“预处理”

阶段三的“后处理”只指模型表示到部署表示的转换，不等于安全处理。明确禁止：

- normalized action clamp 到 `[-1,1]`。
- 用 `[:chunk_size]` 截断过长输出。
- 对过短输出 padding/repeat。
- 重排左右 TCP/gripper 段。
- quaternion 归一化、gripper clamp、TCP delta 限制。

最后三项安全修正属于 L2-04，不得提前发生。

## 7. 总编排入口

总入口的唯一编排逻辑：

```text
predict_action_chunk(observation):
    batch = prepare_observation_batch(observation, ...)
    raw_chunk = run_act_inference(policy, batch)
    action_chunk = postprocess_action_chunk(raw_chunk, ...)
    return action_chunk
```

调用条件由 L2-06 决定。总入口内部没有 skip/retry/timeout/fallback 分支；任一步失败立即终止，不构造 `ActionChunk`。

## 8. 3.5 层总账

| 微元类型 | L2-03 数量/内容 |
|---|---|
| 数据 | 四项稳定依赖、只读派生输入规格、`ActionChunk`；batch/raw tensor 为单次临时变量 |
| 计算函数 | 阶段一 7 个、阶段二 policy 计算、阶段三 5 个转换/判断 |
| 内部状态更新函数 | 0；不修改 queue/cache/cursor/metrics |
| 数据读写函数 | 0；不读文件/ROS/网络，不写机器人硬件 |
| 编排函数 | 阶段一、阶段三、总入口；阶段二是一级计算边界 |

## 9. 变量所有权与生命周期

| 变量/对象 | 创建方 | 持有方 | 生命周期 | 可否跨 L2 |
|---|---|---|---|---|
| DeployConfig | L2-01 | service 只读引用 | 程序生命周期 | 是 |
| state/action normalizer | L2-01 | service 只读引用 | 程序生命周期 | 是 |
| loaded policy | L2-01 | service 只读引用；模型内部计算由 policy 自身完成 | 程序生命周期 | 是 |
| policy input specification | L2-03 从 RAM 元数据派生 | service 只读 | service 生命周期 | 否 |
| ObservationSnapshot | L2-02 | 当前调用局部引用 | 单次调用 | 是 |
| state/image tensors | L2-03 阶段一 | 当前调用栈 | 单次调用 | 否 |
| ACT batch | L2-03 阶段一 | 当前调用栈 | 阶段一至二 | 否 |
| raw action tensor | policy/L2-03 阶段二 | 当前调用栈 | 阶段二至三 | 否 |
| physical action array | L2-03 阶段三 | ActionChunk | chunk 生命周期 | 仅经 ActionChunk |
| ActionChunk | L2-03 | L2-06 接收后只读消费 | 单次推理结果 | 是 |

## 10. 失败传播

```text
任一叶子计算失败
-> 当前一级阶段立即失败
-> 总入口不继续后续阶段
-> 异常返回 L2-06
-> L2-06 记录 request/time/error/metrics
-> L2-06 决定继续旧 chunk、等待或 fallback
```

L2-03 可以给异常增加“处于哪个阶段”的静态上下文，但不能吞掉原始原因，也不能把异常转换为零 chunk、`None` 或旧结果。

## 11. L2 协作边界

| 协作者 | 向 L2-03 提供/从 L2-03 接收 | L2-03 不得反向承担 |
|---|---|---|
| L2-01 | config、两个 normalizer、loaded policy | 文件读取、policy 加载或 test/real 选择 |
| L2-02 | 模型就绪图像 + 16D state 的 snapshot | 图像预处理、freshness、字段缓存 |
| L2-06 | 调用和资源组装；接收 ActionChunk/异常 | thread、queue、时间、metrics、active chunk、cursor、fallback |
| L2-04 | 间接接收 L2-06 选择的单步 action | 安全校验和必要修正 |
| L2-05 | 无直接数据调用 | ROS message 适配和 publish |

## 12. 推荐代码聚合

```text
types/action_chunk.py
  ActionChunk

service/observation_batch.py
  一级阶段一 + 7 个输入计算微元

service/action_chunk_postprocess.py
  一级阶段三 + 6 个输出微元

service/act_inference.py
  ActInferenceService
  总编排入口
  一级阶段二
```

具体字段、函数职责和测试落点分别见 `06_types层设计.md` 与 `09_service层设计.md`。

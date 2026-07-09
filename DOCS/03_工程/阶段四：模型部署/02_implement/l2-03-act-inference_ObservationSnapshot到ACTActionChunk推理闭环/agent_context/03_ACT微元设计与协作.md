# ACT 微元设计与协作：L2-03

## 1. 设计原则

L2-03 是后台计算角色，只消费 `InferenceRequest` 产出 `ActionChunk`，不决定 action 何时执行。它通过 request/result queue 与 L2-06 异步解耦，保证 GPU 推理不阻塞 control tick。

第一版已去除独立平滑处理：本 L2 不实现 action smoothing、smoothstep blend、跨 chunk 融合、RTC 类平滑或复杂时间对齐。L2-06 第一版只按 cursor 直取 active chunk 的当前 step。

设计上 L2-03 与 Pi0.5 推理链路高度同构（`InferenceWorker` + policy runtime + queue 三件套几乎可直接复用），主要差异在模型框架（Pi0.5 VLA → ACT）和维度（14→16）。

## 2. ACT 微元设计

| ACT 微元 | 3.5 类型 | target layer | target file | function/class | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|---|---|---|
| ActPolicyRuntime（真实） | 数据+计算+编排 | repo | `src/model_deploy/act/repo/policy_loader.py` | class | DeployConfig + bundle | 加载好的 policy runtime 对象 | 加载权重到 RAM/GPU | `Pi05PolicyRuntime`（结构复用） |
| ActPolicyRuntime（fake） | 数据+计算 | repo | `src/model_deploy/act/repo/policy_loader.py` | class | DeployConfig（mode=fake） | fake policy runtime 对象 | 无（不加载权重） | ACT 增量（保证无 bundle 可验收） |
| load_act_policy_runtime | 编排函数+数据读写 | repo | `src/model_deploy/act/repo/policy_loader.py` | function | DeployConfig | ActPolicyRuntime | 读 bundle 文件 | `load_policy_runtime`（结构复用） |
| act batch adapter | 计算函数 | service | `src/model_deploy/act/service/batch_adapter.py` | function | ObservationSnapshot | dict[str, Tensor]（ACT batch） | 无 | `_build_batch`（结构复用） |
| act predict action chunk | 编排函数 | service | `src/model_deploy/act/service/policy_runtime.py` 或 repo 内 method | method | ObservationSnapshot | np.ndarray (chunk_size,16) | GPU 推理 | `predict_action_chunk`（结构复用） |
| normalizer 使用（normalize/unnormalize） | 计算函数 | service | `src/model_deploy/act/service/normalizer.py` 或复用 repo normalizer | function/method | RAM 向量 | RAM 向量 | 无 | `ActionStateNormalizer.normalize/unnormalize`（直接复用） |
| ActionChunk 数据结构 | 数据 | runtime | `src/model_deploy/act/runtime/shared_buffer.py` | frozen dataclass | actions/times/request_id | 值对象 | 无 | `ActionChunk`（直接复用，14→16） |
| InferenceRequest 数据结构 | 数据 | runtime | `src/model_deploy/act/runtime/shared_buffer.py` | frozen dataclass | observation/obs_time/request_id | 值对象 | 无 | `InferenceRequest`（直接复用） |
| ObservationSnapshot 引用 | 数据 | runtime | `src/model_deploy/act/runtime/shared_buffer.py` | frozen dataclass | images/state/encoded_state/captured_at_s | 值对象 | 无 | `ObservationSnapshot`（直接复用，L2-02 也用） |
| LatestQueue | 内部状态更新+数据 | runtime | `src/model_deploy/act/runtime/shared_buffer.py` | class | T | put_latest/get_latest_or_none | 锁保护 deque | `LatestQueue`（直接复用） |
| SharedBuffer 引用 | 数据+内部状态更新 | runtime | `src/model_deploy/act/runtime/shared_buffer.py` | class | — | 聚合 observation/request/result/metrics | record_* 方法 | `SharedBuffer`（直接复用） |
| RuntimeMetrics 引用 | 数据+计算 | runtime | `src/model_deploy/act/runtime/shared_buffer.py` | dataclass | — | 计数器 + latency EMA | record_latency/as_dict | `RuntimeMetrics`（直接复用） |
| InferenceWorker | 编排+内部状态更新 | runtime | `src/model_deploy/act/runtime/inference_worker.py` | class | policy_runtime + queues + hz | 后台循环副作用 | 写 result_queue + metrics | `InferenceWorker`（直接复用） |

> [!note] shared_buffer 落点说明
> `shared_buffer.py` 同时被 L2-02（写 latest_observation）、L2-03（读写 request/result/metrics）、L2-06（读写所有）使用。第一版推荐由 L2-03 首先落地该文件（因为它定义了推理链路全部数据结构），L2-02 和 L2-06 后续 import 复用。若 L2-01 在 types 层统一提供这些数据结构，则本 L2 改为 import 复用，不在 runtime 层重复定义（见 `01_L2功能边界.md` §9 待决策项 1）。

## 3. 内部协作关系

```text
Creation order（启动期，由 L2-06 或装配代码触发）:
1. L2-01 加载 DeployConfig + bundle 契约校验。
2. repo 层 load_act_policy_runtime(config) 加载真实或 fake ActPolicyRuntime。
   2a. 复用 L2-01 的 bundle_reader/manifest_parser/normalizer_loader/experiment_config_loader。
   2b. 构建 ACT policy + preprocessor（fake 分支跳过权重加载）。
   2c. 加载 state/action normalizer（长度校验 16D，复用 L2-01 契约）。
3. runtime 层创建 SharedBuffer（含 inference_request_queue、chunk_result_queue、metrics）。
   - 注：SharedBuffer 也被 L2-02（latest_observation）和 L2-06 使用。
4. runtime 层创建 InferenceWorker(policy_runtime, request_queue, result_queue, shared_buffer, inference_hz, control_hz)。
5. 启动 InferenceWorker 后台线程（daemon=True）。

State owner:
- ActPolicyRuntime：model/policy/preprocessor/normalizer/device，启动期创建后稳定只读。
- InferenceWorker：_stop_event/period_s/action_dt，后台线程生命周期。
- SharedBuffer.metrics：全局计数器，锁保护，被 InferenceWorker 和 L2-06 共同更新。

Pure RAM calculations:
- act batch adapter（snapshot→batch dict）
- normalizer.normalize（state 推理前）/ unnormalize（action 推理后）
- clamp_normalized_action（可选，推理后 clamp 到 [-1,1]）
- shape 校验（actions.shape[1]==16）
- aligned_index（时间对齐，供 L2-06 用）

External boundary reads/writes:
- 启动期：load_act_policy_runtime 读 bundle 文件 + 加载权重到 GPU（跨进程/设备边界）。
- 稳态：policy.predict_action_chunk 调 GPU 推理（跨进程-设备边界，最耗时的边界跨越）。
- 本 L2 不写外部文件、不订阅 topic、不发布 topic。

Runtime orchestration point:
- InferenceWorker.run()：后台循环，按 inference_hz 限速，消费 request→推理→写 result。
- 本 L2 不进入 ControlLoop.tick()；tick 由 L2-06 驱动，通过 queue 与本 L2 协作。

Failure propagation:
- 推理异常：InferenceWorker._run_request 用 try/except 捕获 → record_inference_error(message) → log_warning → 继续下一个 request，不崩溃。
- L2-06 在 tick 时发现 chunk_result_queue 长期无新 chunk / metrics.inference_error_count 增长 → 进入 fallback（hold/continue_old_chunk/safe_stop）。
- shape 非法（policy 输出非 16D）：predict_action_chunk 内抛 ValueError → 被同 try/except 捕获 → record_inference_error。
```

## 4. 去除平滑处理后的协作影响

- `InferenceWorker` **不包含** `blend_steps`、`smoothstep_alpha`、`_blend_next_action`、`_start_blend_or_switch` 任何平滑逻辑。
- `predict_action_chunk` 只输出整个 chunk，**不做** 单步选择、cursor 推进或跨 chunk 加权融合。
- `ActionChunk` 保留 `cursor` 字段（向后兼容），但第一版由 L2-06 按 cursor 直取，**不在本 L2 内推进 cursor**。
- `RuntimeMetrics` 不包含 `blend_active` 等平滑状态字段（这些若需要归 L2-06）。
- L2-06 若后续要引入平滑优化，必须新增设计变更并同步更新 L1/L2 文档和 Gate；不得从 L2-03 暗含未声明能力。
- `load_act_policy_runtime` 不读取 `blend_steps` 配置；该字段在 L2-01 的 `RuntimeConfig` 中已去除。

## 5. fake-policy 设计

为保证无真实 bundle / 无 GPU 时仍能本地验收推理链路与调度行为，本 L2 提供统一推理接口的 fake 实现：

```text
fake-policy runtime 实现 predict_action_chunk(observation) -> np.ndarray (chunk_size, 16):
  - 不加载真实权重，不调用 GPU。
  - 输出 shape 严格 (chunk_size, 16) float32。
  - 生成策略可配置（默认推荐：零向量，或基于 request_id 的可复现伪随机），保证：
    a. shape 契约与 real-policy 完全一致；
    b. 延迟可观察（fake 可注入可配置 sleep 模拟推理耗时）；
    c. InferenceWorker 的 queue 消费、metrics 记录、失败处理链路与 real 完全一致。
  - 通过 DeployConfig.runtime.mode 或独立 fake 标志选择 fake/real 分支。
```

fake-policy 是 L2-03 Gate 的**必选项**：fake 路径必须通过，real 路径在真实 bundle 就绪后补验（可标 `env-blocked` 或 `hardware-blocked` 直到 bundle 可用）。

## 6. 待用户确认的阻断项

以下决策若未确认，L3 生成时必须标记为 blocking（当前已给出推荐默认）：

1. `shared_buffer.py`（ActionChunk/InferenceRequest/ObservationSnapshot/LatestQueue/SharedBuffer/RuntimeMetrics）由本 L2 在 runtime 层落地，还是由 L2-01 在 types 层统一提供？**推荐**：runtime 层落地，与 Pi0.5 一致。
2. ACT 模型复用 LeRobot `lerobot.policies.act`？**推荐**：是。
3. fake-policy 默认生成策略？**推荐**：零向量 + 可配置 sleep。

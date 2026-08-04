# types 层设计：L2-06

## 1. 产物结论

本 L2 不在该层新增源码产物。

原因：L2-06 与相邻 L2 的公共业务语言已经由 L2-02～05 定义；`InferenceRequest`、`InferenceResult` 和 runtime metrics 只描述 L2-06 内部线程/调度生命周期，落在 `runtime/`，不升级成跨 L2 通用类型。

验收如何确认：`src/model_deploy/act/types/` 不出现 L2-06 queue/worker/cursor 类型；L2-03 `ActionChunk` 字段仍只有 `actions`；L2-06 runtime 必须存在自己的 envelope 和 snapshot。

## 2. 复用的公共类型

| 来源 | type | L2-06 使用位置 | 只消费的字段/语义 |
|---|---|---|---|
| L2-01 | `DeployConfig`、`RuntimeConfig` | A4/A5 构造期 | scheduling、16D、fallback、topics、command static switch |
| L2-01 repo | `PolicyInputSpec`、`ActRuntimeResources` | B11/B12 启动期 | 唯一 policy metadata 与已加载资源；不进入 tick envelope |
| L2-01 | `ActionSpec` | A4 previous-safe | 一条 16D 物理 action；不当作静态 spec 空壳 |
| L2-02 | `ObservationSnapshot` | C1、B7 | images、state、encoded_state、monotonic capture time（前置修复后） |
| L2-03 | `ActionChunk` | C2 success payload、A4 active/pending | `actions: ndarray[N,16] float32` |
| L2-04 | `SafetyResult`、`SafetyStatus`、`SafetyFinding` | B7/C18/C19 | PASS/ADJUSTED/REJECTED、action、findings |
| L2-05 | `CommandPermit` | B9→B3 | `allowed`、`reason_code` |
| L2-05 | `ActionPublishRequest` | C18 | action_id、SafetyResult、permit、双时钟 |
| L2-05 | `ActionPublishResult`、`PublishOutcome` | B7/C19 | 六种 outcome、startup switch/permit echo、发布计数、failure provenance、driver/hardware unknown 字段 |

## 3. 明确不复用或不修改的类型

- 不新增 `ControlCommand`、`ControlDecision`、`SafeAction` 或 `FallbackAction` 跨 L2 中间对象。
- 不向 `ActionChunk` 添加 `request_id/obs_time/ready_time/cursor/error/latency`。
- 不把 L2-02 `metrics_snapshot() -> dict` 冒充 L2-06 全局 metrics。
- 不读取不存在的 `SafetyResult.accepted` 或 `ActionPublishResult.sent_to_driver`。
- 不用全零 16D action 表示 safe-stop；零 quaternion 本身可能非法。
- `ObservationSnapshot` 必须拥有与 collector cache 不别名的 arrays；A3/A4 只读，不把可写 view 传回 L2-02。

## 4. L2-06 内部数据为何属于 runtime

| runtime 数据 | 生命周期 | 消费者 | 不能成为公共 types 的原因 |
|---|---|---|---|
| C1 `InferenceRequest` | 一个 request 从 tick 到 worker | A3/A4 | request id、submit time、trigger cursor 是调度细节 |
| C2 `InferenceResult` | worker 完成到 ControlLoop 收取 | A3/A4 | error/latency/correlation 是 L2-06 线程协议 |
| C3 `FallbackReason` | 单次/最近一次 fallback | A4/A2/A5 | 是运行状态枚举，不是模型或安全业务结果 |
| C4 `RuntimeMetricsSnapshot` | metrics publish 间隔 | A2/A5 | 只服务 L2-06 UI 可观测性 |
| C5-C7 mutable state | process lifetime | owning class | 绝不能跨 L2 暴露可变引用 |

## 5. 依赖与副作用

- types 层不依赖 runtime/ui，不发生副作用。
- runtime 只可从稳定 package facade 或明确 public module import 上述合同，不读取 `_input_spec` 等私有字段；types/repo/service 不能反向 import L2-06 runtime。
- 如未来其他进程需要稳定消费 C4，必须另行提升为公共 telemetry contract；第一版不提前泛化。

## 6. Pi0.5 与验收

Pi0.5 参考：`runtime/shared_buffer.py:22-69` 把 observation、action metadata 和 request 放在同一公共文件；ACT 按当前 L2 ownership 拆分，只借结构，不复制字段。

验收覆盖：

- `ACTION_CHUNK_PURITY`：字段集合严格为 `actions`。
- `OBS_SNAPSHOT_ISOLATION`：snapshot arrays 与 collector/cache 不别名，跨线程只读。
- `NO_PUBLIC_RUNTIME_TYPES`：`types/` 无 L2-06 internal envelope。
- `PUBLIC_CONTRACT_IMPORTS`：runtime 只通过公共 L2-02～05 type 路径导入。
- `NO_LEGACY_CONTROL_DECISION`：无旧中间决策对象。

本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

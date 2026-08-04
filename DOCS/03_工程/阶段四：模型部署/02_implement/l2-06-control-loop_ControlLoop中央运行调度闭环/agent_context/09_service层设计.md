# service 层设计：L2-06

## 1. 产物结论

本 L2 不在该层新增源码产物。

原因：模型推理、安全计算和 action payload/message 业务已经分别由 L2-03、L2-04、L2-05 封装。L2-06 只决定何时、在哪个线程、以什么状态调用，不复制这些业务计算。

验收如何确认：`src/model_deploy/act/service/` 不新增 worker/queue/cursor/fallback；ControlLoop 通过以下真实 public interface 调用；mock 不得伪造不存在的方法。

`model_deploy.act.service` facade 必须增量公开 `ActInferenceService`，并保留已有 `SafetyGuard`、`ActionPublishContractError`、action-output helper 等 L2-04/05 public export；不得用新 `__all__` 造成上游回归。A3/A4 不从私有模块或下划线字段导入。L2-05 publisher 由 A5 从同 package 的明确 public sibling module `.action_publisher` 构造，不在 `act_deploy_node.py` 内反向导入 `model_deploy.act.ui` 自身 facade，避免 `ui.__init__ ↔ act_deploy_node` 循环；A4 只接收绑定 callable。

## 2. 三个真实能力接口

### 2.1 L2-03 同步推理

启动构造必须消费 L2-01 aggregate 中唯一的 spec：

```python
ActInferenceService(
    config,
    state_normalizer,
    action_normalizer,
    policy,
    input_spec=resources.policy_input_spec,
)
```

当前源码自行派生 private `_input_spec`，属于 P0-04；修复后不得在 L2-03 再派生第二份 camera/image/chunk 合同。

启动 metadata 只允许增加一个 read-only property：

```python
@property
def input_spec(self) -> PolicyInputSpec:
    return self._input_spec
```

它必须返回构造时注入的同一对象，不复制、不重算；这不是第二个 runtime capability，A3 仍只调用 `predict_action_chunk`。

L2-03 内部 `prepare_observation_batch/postprocess_action_chunk` 也必须消费 typed `PolicyInputSpec` attribute，不再调用 Dict `.get()` 或以 DeployConfig default 补 policy metadata。

```python
ActInferenceService.predict_action_chunk(
    observation: ObservationSnapshot,
) -> ActionChunk
```

- 调用者：A3/B2 worker，不是 timer thread。
- 输出：只有 `actions` 的 L2-03 `ActionChunk`。
- 失败：异常由 L2-03 抛出，B2 转成 C2 error result。
- 禁止：把 queue/thread/error recovery 放回 L2-03。

### 2.2 L2-04 safety

```python
SafetyGuard.filter_action(
    candidate,
    previous_safe_action: ActionSpec | None = None,
    latest_observation: ObservationSnapshot | None = None,
) -> SafetyResult
```

- 调用者：A4/B7，candidate 必须是独立 `(16,) float32` copy 或 ActionSpec。
- `PASS/ADJUSTED`：均有 action，可构造 publish request。
- `REJECTED`：action=None；可以交 L2-05 形成 rejected status，同一 tick 不再发 fallback action。
- Guard 不检查 freshness、不保存 previous；A4 提供新鲜 observation 并拥有 previous。

### 2.3 L2-05 publish port

```python
ActionPublisher.publish(
    request: ActionPublishRequest,
) -> ActionPublishResult
```

A4 不 import `ui.action_publisher.ActionPublisher` class，而注入绑定 callable：

```python
publish_action: Callable[[ActionPublishRequest], ActionPublishResult]
```

这样 runtime 依赖公共 types 和 callable，不反向 import UI。A5 负责把真实 `ActionPublisher.publish` 绑定进去。

P0-10 同时要求 L2-05 纠正 `type(...).__r` 非法输入异常，并冻结以下 provenance：

```text
ActionPublishResult.failure_stage:
  Literal["safety", "policy_publish", "command_build", "command_publish"] | None
ActionPublishResult.failed_topic: str | None
```

`REJECTED/PARTIAL/FAILED` 的 `reason_code` 必须非空；REJECTED stage=`safety`，PARTIAL/FAILED 精确记录 stage，发生具体 publish I/O 时还记录 failed topic。`PUBLISHED/OBSERVED/BLOCKED` 的 stage/topic 为 None（BLOCKED 继续用 permit reason）。已有 `command_output_enabled` 与 `command_permitted` echo 字段必须保留，C19 分别与 A4 的 startup-only switch、原始 request permit 交叉校验。status publisher 自身失败无法可靠形成 status result时，抛带 public `label="status"` 的 `ActionPublishIoError`，由 B7/C19 记录。A4 只保存这些返回/异常事实、SafetyFinding 和自己的 orchestration reason，不能从 `outcome` 反推 L2-05 内部失败位置。

## 3. 固定调用顺序

```text
candidate
  -> SafetyGuard.filter_action(candidate,
                               previous_safe_action=...,
                               latest_observation=...)
  -> SafetyResult
  -> build_action_publish_request(action_id,
                                  safety_result,
                                  command_permit,
                                  ros_time_s,
                                  monotonic_s)
  -> publish_action(request)
  -> ActionPublishResult
  -> C19 outcome reducer
```

不存在以下接口或字段：

```text
SafetyGuard.filter(...)
SafetyResult.accepted
L2-05.publish_safe(...)
L2-05.emit_fallback(...)
ActionPublishResult.sent_to_driver
```

## 4. fallback 与 service 边界

- 非 safety runtime 失败没有合法 `SafetyResult`，只进入 L2-06 metrics/status-only，不调用 L2-05。
- `hold_last_action` 和 `continue_old_chunk` 只有生成真实 candidate 后才重新经过 L2-04/L2-05。
- `safe_stop` 本 tick 不调用 service、不构造全零 action；下一 tick 可恢复。主动硬件 stop 若存在，应是独立 driver port。
- `PARTIAL/FAILED` 是发布事实，A4 fault latch；service 不自行 retry。

## 5. class、函数、I/O 与依赖

- class 设计：无 L2-06 service class。
- 函数设计：无新增 service 纯函数；C13/C14/C18 属 runtime RAM 计算。
- 输入/输出：如上三个 public interface。
- 副作用：L2-03 policy forward 发生在 worker；L2-05 publish 可能写 ROS；L2-04 纯 RAM。L2-06 记录但不隐藏这些副作用。
- 依赖方向：runtime 可依赖 service/types；service 不依赖 runtime/UI。

## 6. Pi0.5 与验收

Pi0.5 参考：`control_loop.py:125-138,316-333` 的推理后 safety/fallback 顺序。旧 `accepted/reason/ControlCommand` 接口不复用。

验收标签：`SERVICE_INFERENCE_SYNC`、`SERVICE_CANONICAL_INPUT_SPEC`、`SERVICE_SAFETY_SIGNATURE`、`SAFETY_PUBLISH_REAL_API`、`SAFETY_REJECT_ZERO_WRITE`、`NO_FAKE_PORT_NAMES`、`PUBLIC_CONTRACT_IMPORTS`。

集成测试允许 fake policy/FakeNode/fake clock，但必须使用真实 `ActInferenceService`、`SafetyGuard`、`ActionPublishRequest` 和 `ActionPublisher`。

本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

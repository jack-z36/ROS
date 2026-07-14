# L3 微元改造任务：L2-02 观测流水线契约修复

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
接口 owner：l2-02-observation-snapshot ObservationSnapshot 组装闭环
L3 编号：deploy_057
改造类型：cross-l2-interface-remediation
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_057_L2-02观测流水线契约修复.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_057_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：direct-local
辅助验收模式：[env-blocked, downstream-l2]
本地验收是否必须：true
真机风险等级：none
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 用户授权的跨 L2 修复
> 本任务修改 L2-02 owner 源码和设计投影，但不得修改冻结中的 deploy_051/052。开始前必须取得 deploy_056 的 canonical PolicyInputSpec/config PASS_LOCAL 证据；不得复制一个临时 Dict spec 来绕过依赖。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_057
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_057_L2-02观测流水线契约修复.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G03]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_057_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [env-blocked, downstream-l2]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 4
  parallel_group: l2-06-control-loop-p4-owner-remediation
  depends_on: [deploy_051, deploy_052, deploy_056]
  must_run_after: [deploy_051, deploy_052, deploy_056]
  can_run_parallel_with: []
  blocks: [deploy_053, deploy_054, deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/types/observation.py
      - src/model_deploy/act/service/image_preprocess.py
      - src/model_deploy/act/service/observation_collector.py
      - src/model_deploy/act/runtime/observation_buffer.py
      - src/model_deploy/act/ui/observation_ros_adapter.py
      - src/model_deploy/act/ui/observation_pipeline.py
      - src/model_deploy/act/ui/__init__.py
      - src/model_deploy/act/tests/types/test_observation.py
      - src/model_deploy/act/tests/service
      - src/model_deploy/act/tests/runtime/test_observation_buffer.py
      - src/model_deploy/act/tests/ui
      - src/model_deploy/act/tests/integration/test_l2_02_gate.py
      - DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环
    modules:
      - model_deploy.act.ui.observation_pipeline
      - model_deploy.act.ui.observation_ros_adapter
      - model_deploy.act.service.observation_collector
      - model_deploy.act.runtime.observation_buffer
    config_keys: [topics.observation.images, image, runtime.max_observation_age_sec]
    runtime_modes: [local, ros-observation]
    hardware_paths:
      - /act/observation/*
  robot_risk: none
  dispatch_status: blocked
~~~

## 3. 本次唯一目标

提供一个 typed、fail-fast、单时钟、无数组别名的 ObservationPipeline，使 L2-06 只用 DeployConfig、同一个 PolicyInputSpec、node 和 monotonic clock 即可得到可直接送入 L2-03 的 ObservationSnapshot。

## 4. 冻结 public seam

~~~python
@dataclass(frozen=True)
class ObservationPipeline:
    collector: ObservationCollector
    buffer: ObservationBuffer
    adapter: ObservationRosAdapter
    input_spec: PolicyInputSpec
    monotonic_clock: Callable[[], float]

def build_observation_pipeline(
    *,
    node: object,
    config: DeployConfig,
    input_spec: PolicyInputSpec,
    monotonic_clock: Callable[[], float],
) -> ObservationPipeline:
    ...
~~~

- owner/落点固定为 src/model_deploy/act/ui/observation_pipeline.py，并由 model_deploy.act.ui 增量导出。
- pipeline.input_spec 必须与传入对象 identity 相同；pipeline.monotonic_clock 也必须保留同一 callable。
- factory 在第一个 subscription 前完成 config/spec/camera/image/message class 的纯 RAM 校验。

## 5. 当前源码断点与修复判据

| 断点 | 当前事实 | 修复判据 |
|---|---|---|
| typed config | adapter 接受 Dict 并链式 get，schema 是 dataclass | 只消费 DeployConfig/PolicyInputSpec，无 Dict fallback |
| camera | adapter 期待 images map，旧 schema 是 left/right flat | 只消费 deploy_056 canonical logical mapping，keys 精确等于 spec |
| image | preprocess/adapter 输出 HWC，L2-03 要 CHW | owned float32 CHW，有限且范围 [0,1]，shape 精确等于 spec |
| snapshot ownership | images/state/encoded_state 为浅复制或共享 ndarray | snapshot 全部 ndarray 深复制且不可被 callback cache 后续修改 |
| freshness | collector 写 wall clock、buffer 用另一时钟域 | collector/buffer/factory 共用注入 monotonic callable |
| gripper | subscription 声明 Pose，handler 对 Point 做 float | message class 与 scalar decoder 一致；未知真实 topology 单独记录，不掩盖 local FAIL |
| fail-fast | create_subscriptions 捕获所有 Exception 并标 env_blocked | 只有 ROS package/runtime allowlist 可归环境；配置/node/decoder错误传播 |

## 6. 实施步骤

1. 先用 fake node/messages/clock 写 camera mismatch、CHW/range、deep ownership、freshness、gripper wire 与 subscription rollback 红测试。
2. 让 image_preprocess、collector、buffer 接收同一 monotonic callable并消除 time.time；强化 ObservationSnapshot 构造不变量和深复制边界。
3. 重构 ObservationRosAdapter 为 typed dependencies，不再读取 raw Dict；冻结与 decoder 匹配的 gripper message seam。
4. 新建 canonical factory；校验全部通过后才创建 subscriptions，创建中途失败必须回收已创建 handles 或让 A5 可确定回收。
5. 更新 L2-02 agent_context 的边界、微元、验收和六层落点，并同步 HTML 中 camera/image/clock/gripper/factory 语义。
6. 运行 L2-02 全量测试与真实 L2-02 Gate；无 ROS 时只能把 ROS graph 补验记 BLOCKED_ENV，本地 typed pipeline 不得 skip。

## 7. 允许修改

- src/model_deploy/act/types/observation.py
- src/model_deploy/act/service/image_preprocess.py
- src/model_deploy/act/service/observation_collector.py
- src/model_deploy/act/runtime/observation_buffer.py
- src/model_deploy/act/ui/observation_ros_adapter.py
- src/model_deploy/act/ui/observation_pipeline.py
- src/model_deploy/act/ui/__init__.py
- 对应 src/model_deploy/act/tests/types、service、runtime、ui、integration/test_l2_02_gate.py
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/L2架构交互可视化.html

## 8. 禁止修改

- deploy_051/052 的任何冻结产物和 L2-06 runtime 实现。
- L2-01 canonical spec/config、L2-03 batch/service；接口问题回到 owner task。
- 在 L2-06 Node 内补转置、缩放、硬编码 camera 或猜 gripper 数据。
- 以 broad except 把代码错误降级为环境 BLOCKED。
- 连接真实 driver 或发送 command。

## 9. 验证方式

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_observation.py \
  src/model_deploy/act/tests/service/test_image_preprocess.py \
  src/model_deploy/act/tests/service/test_observation_collector.py \
  src/model_deploy/act/tests/runtime/test_observation_buffer.py \
  src/model_deploy/act/tests/ui/test_observation_ros_adapter.py \
  src/model_deploy/act/tests/integration/test_l2_02_gate.py -v
~~~

~~~bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环'
~~~

~~~bash
! rg -n "Dict\\[|config\\.get\\(|time\\.time\\(|Pose,.*gripper|left_image|right_image" \
  src/model_deploy/act/ui/observation_pipeline.py \
  src/model_deploy/act/ui/observation_ros_adapter.py \
  src/model_deploy/act/service/observation_collector.py \
  src/model_deploy/act/runtime/observation_buffer.py
~~~

## 10. 成功标准

- [x] public factory 签名、aggregate 字段和 facade export 精确。
- [x] pipeline 的 spec 与 clock 均通过 identity 检查。
- [x] camera keys、CHW shape、float32、[0,1] 在 subscription 前 fail-fast。
- [x] snapshot images/state/encoded_state 均为深拥有，源缓存修改不影响已发布 snapshot。
- [x] captured_at_s 与 buffer freshness 只用同一 monotonic clock。
- [x] gripper message/decoder 内部一致，真实 topology 未知项单独报告。
- [x] ROS 环境缺失与代码/配置错误有稳定、互斥的判定。
- [x] L2-02 HTML 和 agent_context 与源码及 public seam 同步。
- [x] 未改动冻结的 deploy_051/052。

## 11. 回滚与交接

回滚只撤销 L2-02 typed pipeline、相关测试和设计投影，不恢复 Dict/HWC/wall-clock 兼容旁路。交接必须给出 factory import/构造示例、spec/clock identity 证据、array alias 测试、订阅创建顺序和可供 deploy_053/054 使用的稳定异常分类。

## 18. 执行摘要（deploy_057 执行子 Agent）

### 18.1 改动文件

源码（均在 conflict_scope.files 允许内）：

- `src/model_deploy/act/types/observation.py`：ObservationSnapshot 构造期深复制 images/state/encoded_state，校验有限性与 encoded_state shape；新增 `_owned_array` 辅助。
- `src/model_deploy/act/service/observation_collector.py`：注入 `monotonic_clock`（默认 `time.monotonic`），所有 stamp 与 `captured_at_s` 改用该时钟；移除 `time.time()` / `time.monotonic()` 直接调用。
- `src/model_deploy/act/runtime/observation_buffer.py`：注入 `monotonic_clock`；`latest_observation` 新鲜度年龄与 `updated_at_s` 改用该时钟。
- `src/model_deploy/act/service/image_preprocess.py`：整数图像（uint8 等）归一化为 `[0,1]` float32；非有限值报错。
- `src/model_deploy/act/ui/observation_ros_adapter.py`：重构为 typed 依赖（只消费 `DeployConfig` + `PolicyInputSpec`，无 Dict fallback）；camera keys 与 spec 对齐校验；图像在边界转 CHW float32 [0,1] 并校验 shape/range；gripper 订阅消息类型与 `decode_gripper_width` 解码器一致，真实 topology 置 `gripper_topology_unknown`；订阅创建失败 rollback 并传播；仅 ROS packages 缺失记 `env_blocked`。
- `src/model_deploy/act/ui/observation_pipeline.py`（新增）：冻结 `ObservationPipeline` dataclass + `build_observation_pipeline(node, config, input_spec, monotonic_clock)`，订阅前纯 RAM 校验，spec/clock 保持 identity。
- `src/model_deploy/act/ui/__init__.py`：增量导出 `ObservationPipeline` / `build_observation_pipeline`。

测试（均在冲突范围允许内）：

- `tests/types/test_observation.py`（既有，仍通过）
- `tests/service/test_image_preprocess.py`：更新 uint8 归一化断言
- `tests/service/test_observation_collector.py`（既有，仍通过）
- `tests/runtime/test_observation_buffer.py`：新鲜度测试改用可控 FakeClock
- `tests/ui/test_observation_ros_adapter.py`：重写为 typed 契约测试
- `tests/ui/test_observation_pipeline.py`（新增）：public seam / identity / fail-fast / 深拥有 / monotonic 新鲜度 / rollback
- `tests/integration/test_l2_02_gate.py`（既有，仍通过）

设计投影（L2-02 agent_context 权威 MD + HTML）：

- `agent_context/11_ui层设计.md`、`09_service层设计.md`、`10_runtime层设计.md`：补充 typed pipeline / monotonic / 深拥有 / gripper topology 说明
- `L2架构交互可视化.html`：追加 deploy_057 契约小节（MD 为权威；HTML 结构校验器缺口为 deploy_056 已记录预存问题）

### 18.2 关闭的 P0-02 项（owner-remediation）

- P0-05（typed config / 无 Dict fallback）：adapter 只消费 `DeployConfig` + `PolicyInputSpec`。
- P0-06-pipeline（camera 契约 / CHW / float32 / [0,1]）：camera keys fail-fast 对齐；图像边界转 CHW float32 [0,1] 并校验。
- P0-07（monotonic freshness）：collector / buffer / pipeline 共用注入 monotonic clock。
- P0-08（深拥有 snapshot）：ObservationSnapshot 构造期深复制，已发布 snapshot 免疫源缓存修改。
- P0-09-runtime（gripper / fail-fast / rollback）：gripper 消息-解码器一致、真实 topology 单独记录、订阅 rollback、ROS 缺失与代码错误互斥判定。

### 18.3 验证命令与结果

L3 验收命令（§9）：

```
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_observation.py \
  src/model_deploy/act/tests/service/test_image_preprocess.py \
  src/model_deploy/act/tests/service/test_observation_collector.py \
  src/model_deploy/act/tests/runtime/test_observation_buffer.py \
  src/model_deploy/act/tests/ui/test_observation_ros_adapter.py \
  src/model_deploy/act/tests/ui/test_observation_pipeline.py \
  src/model_deploy/act/tests/integration/test_l2_02_gate.py -v
```
结果：**84 passed, 4 skipped**（4 skipped = ROS 缺失路径测试，本环境 rclpy 可用故跳过）。

结构禁令检查（§9 rg 等价）：

```
Dict\[|config\.get\(|time\.time\(|Pose,.*gripper|left_image|right_image
```
在 `observation_pipeline.py` / `observation_ros_adapter.py` / `observation_collector.py` / `observation_buffer.py` 中：**无匹配**（已改用 `Mapping` 注解并修正文档中的 `time.time()` 字样）。

### 18.4 回归结果（broad）

```
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
```
结果：**751 passed, 4 skipped, 2 warnings**（与 deploy_056 验收记录一致：normalization 除零 RuntimeWarning 与 inference_worker KeyboardInterrupt 警告均为预存，非本任务引入）。冻结的 deploy_051/052 实现与测试（`test_inference_channel.py` / `test_runtime_metrics.py` / `test_inference_worker.py`）全部随回归运行通过，**未改动**。

### 18.5 未验证项（如实登记）

- **真实 ROS graph / 真机订阅**：本环境虽有 rclpy，订阅创建以 mock node 验证；真实 driver、真实 gripper message 拓扑、真实 image transport（compressed）未接真机，属 `BLOCKED_ENV` / `BLOCKED_HARDWARE_EXPECTED`，不计入本地 FAIL。
- **gripper 真实 topology**：置 `gripper_topology_unknown=True`，以 `Pose` 占位订阅 + 一致解码器，待真实硬件确认（不掩盖 local FAIL）。
- **HTML 结构校验器**：`validate_l2_design_package.py` 在 L2-02 设计包的失败为 deploy_056 已记录的预存缺口（缺 03a / io-flow / ovtab 等结构块），MD 为权威，未计入本任务失败。

### 18.6 交接要点（供 deploy_053/054）

- factory 示例：
  ```python
  from model_deploy.act.ui import build_observation_pipeline
  pipeline = build_observation_pipeline(
      node=node, config=deploy_config, input_spec=policy_input_spec,
      monotonic_clock=time.monotonic,
  )
  snap = pipeline.buffer.latest_observation(max_age_s=deploy_config.runtime.max_observation_age_sec)
  ```
- spec/clock identity：`pipeline.input_spec is policy_input_spec`、`pipeline.monotonic_clock is monotonic_clock`（测试已断言）。
- 异常分类：camera keys 不一致 / 类型错误 → `ValueError`/`TypeError` 传播；ROS packages 缺失 → `adapter.env_blocked == True`；订阅中途失败 → 已创建 handles rollback 后抛 `RuntimeError`。
- 数组别名：新增 `TestDeepOwnership::test_source_mutation_does_not_affect_snapshot` 证明已发布 snapshot 不受源缓存修改影响。

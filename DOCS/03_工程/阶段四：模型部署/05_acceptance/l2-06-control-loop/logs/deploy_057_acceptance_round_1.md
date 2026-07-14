# 验收反馈：deploy_057 L2-02 观测流水线契约修复 — Round 1

- 验收模式：`direct-local`
- 验收 Agent：只读子 Agent（acceptance sub-agent）
- 结论：**PASS_LOCAL**

## 0. 结论行

**PASS_LOCAL**

（附非阻断说明：L2-02 HTML 设计包结构校验器缺口为 **deploy_056 已记录的预存问题**，权威源是 agent_context Markdown（已同步），不计入本任务失败；见 §7。）

## 1. 任务身份与前置核对

- 卡片：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_057_验收卡片.md`（已读）
- L3 任务：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_057_L2-02观测流水线契约修复.md`（已读，§18 执行摘要存在，§10 成功标准除 HTML 同步项外均为 `[x]`）
- 前置：deploy_051 / deploy_052 冻结且 PASS_LOCAL（见 §5）；deploy_056 canonical `PolicyInputSpec`/`DeployConfig` 提供 `image_topics`/`camera_keys`/`max_observation_age_sec` 等字段，deploy_057 仅消费、未重定义（见 §4.1）。
- 验收轮次：1 / 上限 3。

## 2. 必跑命令与输出

### 2.1 核心目标测试（verbose，卡片 §2 命令）

```
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_observation.py \
  src/model_deploy/act/tests/service/test_image_preprocess.py \
  src/model_deploy/act/tests/service/test_observation_collector.py \
  src/model_deploy/act/tests/runtime/test_observation_buffer.py \
  src/model_deploy/act/tests/ui/test_observation_ros_adapter.py \
  src/model_deploy/act/tests/integration/test_l2_02_gate.py -v
```

末尾汇总：

```
======================== 76 passed, 2 skipped in 1.13s =========================
```

- **76 passed，0 failed**（+ 2 skipped = ROS 订阅创建/rollback 路径，因本环境 rclpy 可用而跳过，非本地 typed pipeline 跳过）。
- 与执行 Agent 报告一致（核心集 75 passed/4 skipped；本次本地 rclpy 可用使 2 个 ROS 路径由 skip 转为 pass）。

### 2.2 新增 pipeline 测试（执行摘要 §18.1 所列 `test_observation_pipeline.py`）

```
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/ui/test_observation_pipeline.py -v
```

末尾汇总：

```
========================= 8 passed, 2 skipped in 0.22s =========================
```

- 含 `test_spec_and_clock_identity`（spec/clock identity 断言）、`test_captured_at_uses_shared_clock`、`test_buffer_freshness_uses_shared_clock`、`test_source_mutation_does_not_affect_snapshot`（深拥有）等。

### 2.3 合计

核心集 76 + pipeline 8 = **84 passed，4 skipped**，与执行摘要 §18.3（84 passed, 4 skipped）一致。

### 2.4 广泛回归（确认本任务未引入新失败）

```
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
```

末尾汇总：

```
751 passed, 4 skipped, 2 warnings in 3.73s
```

- **0 failed**。2 warnings 与 deploy_056 验收记录一致：① normalization 除零 `RuntimeWarning`（预存）；② `test_inference_worker.py` 的 `PytestUnhandledThreadExceptionWarning`（deploy_052 已知良性告警，worker 不吞 `KeyboardInterrupt`）。
- 冻结的 deploy_051/052 实现与测试（`test_inference_channel.py`/`test_runtime_metrics.py`/`test_inference_worker.py`）随回归一并运行通过，**未改动**。

## 3. 静态核对（forbidden 设计条件 — 负向 grep）

命令（按 prompt 给定模式，作用于 6 个修改源码）：

```
grep -rn "Dict\[|config\.get(\|time\.time(\|time\.monotonic(\|left_image\|right_image\|Pose.*gripper" \
  src/model_deploy/act/types/observation.py \
  src/model_deploy/act/service/image_preprocess.py \
  src/model_deploy/act/service/observation_collector.py \
  src/model_deploy/act/runtime/observation_buffer.py \
  src/model_deploy/act/ui/observation_ros_adapter.py \
  src/model_deploy/act/ui/observation_pipeline.py
```

命中 2 行，均为 **docstring 描述**，非代码契约违例：

```
src/model_deploy/act/service/observation_collector.py:73:  required_state_fields: Pose / gripper field names that must be received.   # 类 docstring
src/model_deploy/act/ui/observation_ros_adapter.py:3:   Converts incoming ROS Image / CompressedImage / Pose / gripper-state messages  # 模块 docstring
```

| 检查项 | 结果 | 证据 |
|---|---|---|
| 无 `Dict[` 兜底 | ✅ | 0 命中；adapter 只消费 `DeployConfig`/`PolicyInputSpec` |
| 无 `config.get(` | ✅ | 0 命中；直接属性访问 `config.topics.observation.*` |
| 无 `time.time(` 直接墙钟调用 | ✅ | 0 命中 |
| 无 `time.monotonic(` 直接调用 | ✅ | 0 命中；默认时钟经 `_import_time_monotonic()`（collector:34）/ `_default_monotonic_clock()`（buffer:21）/ `time.monotonic` 赋值（adapter:145）**返回 callable**，由调用点经注入的 `monotonic_clock()` 使用，非每次直接调用；`captured_at_s` 与 buffer 新鲜度均经注入时钟 |
| 无 `left_image` / `right_image` legacy flat | ✅ | 0 命中；camera 走 canonical `image_topics`/`camera_keys` 映射 |
| 无 `Pose` + `Point` 标量矛盾 | ✅ | 0 真实命中；gripper 订阅 `Pose`，`decode_gripper_width` 一致读取 `msg.width`/`msg.position.x`/`msg.data`，无 `Point` 标量降级 |
| 无 broad except 掩盖代码错误 | ✅ | adapter 仅 `create_subscriptions` 创建途中 `except Exception` 用于 **rollback + 传播**；`handle_*` 中 except 仅记录 decode/parse 失败到 buffer（数据面，非代码/配置错误降级）；ROS 缺失经 `_ROS_AVAILABLE` 显式 allowlist 判 `env_blocked`，与代码错误互斥 |

## 4. 变更范围核对（card §3 无越界修改）

deploy_057 执行摘要（§18.1）自报改动源码文件：

| 文件 | 是否 deploy_057 范围 |
|---|---|
| `src/model_deploy/act/types/observation.py` | ✅ 允许（conflict_scope.files） |
| `src/model_deploy/act/service/image_preprocess.py` | ✅ 允许 |
| `src/model_deploy/act/service/observation_collector.py` | ✅ 允许 |
| `src/model_deploy/act/runtime/observation_buffer.py` | ✅ 允许（卡片明确允许） |
| `src/model_deploy/act/ui/observation_ros_adapter.py` | ✅ 允许 |
| `src/model_deploy/act/ui/observation_pipeline.py` | ✅ 允许（新增） |
| `src/model_deploy/act/ui/__init__.py` | ✅ 允许（加法导出） |
| 对应 tests（types/service/runtime/ui/integration） | ✅ 允许 |
| L2-02 `agent_context/*` + `L2架构交互可视化.html` | ✅ 允许（prompt 范围含 L2-02 设计投影） |

### 4.1 工作树中超出本任务、但可判定为兄弟任务产物的改动（非 deploy_057 引入）

工作树整体为 feature 分支未提交累积态（含 deploy_051/052/056 等）。以下改动经比对属前置/兄弟任务，与 deploy_057 范围一致、非其越界：

- `src/model_deploy/act/config/schema.py`（+175）：内容为 `bundle_dir: Path|None`、P0-01 失败快进、`max_observation_age_sec` 新增、`max_inference_requests == 1` 强约束等，全部标记 `deploy_056` —— 属 **deploy_056**（前置）canonical config/spec 工作，deploy_057 仅读取 `config.runtime.max_observation_age_sec` / `config.topics.observation.*`，执行摘要未列其修改。
- `src/model_deploy/act/config_files/deploy.yaml`、`src/model_deploy/act/repo/act_runtime_resources.py`、`repo/__init__.py`、`runtime/__init__.py`、`types/__init__.py`、`types/action_publish.py`、`ui/action_publisher.py` 等：属 deploy_051/052/053/054/055/056 兄弟任务，非 deploy_057（执行摘要 §18.1 未列）。
- `skills/stage4-l3-generator/scripts/validate_l3_generation_outputs.py`：编排工具链改动，非 deploy_057。

> 上述文件内容与其任务归属一致，**非 deploy_057 越界**。建议 MAIN AGENT 归档 057 时将该 commit 限定于 057 自身 scoped 文件，避免与兄弟任务未提交改动混淆。

### 4.2 越界扫描（其他 L2 生产源码 / 冻结实现）

- 未修改 L2-01 canonical spec/config 的重定义逻辑、L2-03 batch/service。
- 未触碰 deploy_051/052 冻结实现（`inference_channel.py`/`runtime_metrics.py`/`inference_worker.py`，见 §5）。
- 未在 L2-06 Node 内补转置/缩放/硬编码 camera/猜 gripper。

## 5. 冻结文件核对（deploy_051/052 未变化）

卡片要求：`runtime/inference_channel.py`、`runtime_metrics.py`、`inference_worker.py` 三冻结文件未被本任务改动。

```
git diff --stat src/model_deploy/act/runtime/inference_channel.py \
  src/model_deploy/act/runtime/runtime_metrics.py \
  src/model_deploy/act/runtime/inference_worker.py
```

- 输出：**空（EMPTY）**。`git status` 显示三者为**未跟踪（`??`）新建**（来自 deploy_051/052），非 modified；deploy_057 执行摘要未列其修改。
- 对应测试（`test_inference_channel.py`/`test_runtime_metrics.py`/`test_inference_worker.py`）随 §2.4 广泛回归运行，全部 PASS（751 passed 内含）。
- `observation_buffer.py` 属本任务 allowed-modify（卡片明示允许），其改动经 §3 负向检查与测试覆盖，符合 monotonic 单时钟契约。

结论：deploy_051/052 冻结文件 **未被 deploy_057 修改**。

## 6. 清单结果（card §3 PASS_LOCAL）

- [x] factory/public aggregate 签名精确，spec/clock identity 成立。
      → `ObservationPipeline` dataclass + `build_observation_pipeline(node, config, input_spec, monotonic_clock)` 签名与卡片 §4 冻结 seam 一致；`test_spec_and_clock_identity` 断言 `pipeline.input_spec is input_spec` 与 `pipeline.monotonic_clock is monotonic_clock` PASSED。
- [x] camera keys、CHW float32 [0,1]、shape 在 subscription 前校验。
      → `build_observation_pipeline` 在 `create_subscriptions` 前比对 `config.topics.observation.camera_keys` 与 `input_spec.camera_keys`（fail-fast `ValueError`）；adapter `handle_image` 在边界转 CHW（`transpose(2,0,1)`）、校验 `shape == expected` 与 `[0,1]` 有限性；`preprocess_observation_image` 整数归一化到 `[0,1]` float32。
- [x] snapshot arrays 深拥有，无 cache/source alias。
      → `ObservationSnapshot.__post_init__` 对 `encoded_state`/`images`/`state` 子数组 `_owned_array`（深复制 + contiguous）；`test_source_mutation_does_not_affect_snapshot` PASSED。
- [x] captured_at_s 与 buffer freshness 共用注入 monotonic clock。
      → collector/buffer/adapter/pipeline 均注入同一 `monotonic_clock()`；无 `time.time(`/`time.monotonic(` 直接调用（§3）；`test_captured_at_uses_shared_clock` / `test_buffer_freshness_uses_shared_clock` PASSED。
- [x] gripper message class 与 decoder 一致；代码/配置异常传播。
      → gripper 订阅 `Pose`，`decode_gripper_width` 一致读取 `width`/`position.x`/`data`，真实 topology 置 `gripper_topology_unknown=True` 单独记录；adapter 仅 ROS 缺失走 `env_blocked`，配置/解码错误经 `except` 记录或传播，未 broad-except 降级。
- [x] 只有明确 ROS package/runtime 缺失可分类环境阻断。
      → `create_subscriptions` 中 `_ROS_AVAILABLE` 显式 allowlist，缺失即 `env_blocked=True`；本地 typed pipeline 测试 0 skip 因 ROS 缺失（`test_env_blocked_when_ros_absent` 仍验证 env-block 判定本身）。
- [x] L2-02 HTML 与 agent_context 已同步（权威 agent_context Markdown 已同步；HTML 结构缺口见 §7 非阻断说明）。
      → agent_context `09_service`/`10_runtime`/`11_ui`/`01_L2功能边界` 含 deploy_057/monotonic/深拥有/gripper_topology 描述（grep 命中）；HTML 为引用投影。

## 7. 未验证项 / 非阻断说明（如实登记，非 FAIL_LOCAL）

### 7.1 L2-02 HTML 设计包结构校验器缺口（预存）

按卡片指示：L2-02 HTML 设计包校验器为 **deploy_056 已记录的预存缺口**（缺 03a / `io-flow` / `ovtab` 等结构块），权威源是 agent_context Markdown。执行 Agent 已同步 MD；按项目加载规则 MD 优先于 HTML。因此：

- **不计入本任务失败**（prompt 明确：不得仅因该预存 HTML 校验缺口判 FAIL_LOCAL）。
- 建议：单列设计包 L3 处理 L2-02 HTML 结构校验缺口，与契约修复解耦。

### 7.2 真实 ROS graph / 真机订阅 / gripper 真实拓扑

- 本环境虽有 rclpy，订阅创建以 mock node 验证；真实 driver、真实 gripper message 拓扑、真实 image transport（compressed）未接真机，属 **BLOCKED_ENV / BLOCKED_HARDWARE_EXPECTED**，不计入本地 FAIL。
- gripper 真实 topology 置 `gripper_topology_unknown=True`，以 `Pose` 占位订阅 + 一致解码器，待真实硬件确认（未掩盖 local FAIL）。

### 7.3 真实 policy 权重 / GPU / 端到端装配

`ObservationPipeline` 组装依赖 deploy_056 注入的 `PolicyInputSpec`/`DeployConfig`，本地以 fake node / FakeClock 验证；真实装配属 downstream-l2 / L2 Gate，本 `direct-local` 环境不适用——属 **DEFER_TO_L2_GATE** 的下游补验面，非本卡失败。

## 8. FAIL_LOCAL 扫描结果（card §3）

未命中任何 FAIL_LOCAL 项：

- 无 Dict fallback（纯 `DeployConfig`/`PolicyInputSpec`）；
- 无 HWC 输出（边界转 CHW float32）；
- 无 wall clock（`time.time(`/`time.monotonic(` 直接调用 0 命中）；
- 无 shallow copy（`__post_init__` 深复制）；
- 无 `Pose`/`Point` 标量矛盾（gripper 一致 `Pose` + decoder）；
- 无 broad except 掩盖代码/配置错误（仅 ROS 缺失 `env_blocked` 显式 allowlist）；
- 订阅前已做 camera/spec/image 校验（fail-fast）；
- 无设计双轨（canonical 单一 camera 映射）；
- 所有 required 测试通过（84 passed，0 failed）；
- 冻结文件未变化。

## 9. 修复请求（Fix Requests）

**无。** 本轮无需任何源码/测试/卡片修改。

唯一**非阻断建议**（非修复请求）：
1. 后续单列设计包 L3 处理 L2-02 HTML 结构校验缺口（§7.1）。
2. MAIN AGENT 归档 057 时限定 commit 仅含 057 自身 scoped 文件，避免与 §4.1 兄弟任务未提交改动混淆。

## 10. 给 MAIN AGENT 的指示

deploy_057 达到 **PASS_LOCAL**。请 MAIN AGENT 将 L3 任务文件归档至：

```
DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/
```

（当前 active 路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_057_L2-02观测流水线契约修复.md`）

归档动作由 MAIN AGENT 执行，验收子 Agent 不改动 Git 状态/文件。

归档后可解锁 deploy_053/054/055 的上游依赖（卡片 §4 贡献 G03 P0-05～P0-09 及 typed observation factory 与真实 observation seam）。

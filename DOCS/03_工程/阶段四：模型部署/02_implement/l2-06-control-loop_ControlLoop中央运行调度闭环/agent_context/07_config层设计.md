# config 层设计：L2-06

## 1. 产物结论

本 L2 不在该层新增源码产物。

原因：静态部署参数由 L2-01 `DeployConfig` 统一定义和解析。L2-06 只在启动期读取 typed config 并做跨资源 preflight，不能再定义第二套 YAML schema 或在 tick 中解析配置。

验收如何确认：`src/model_deploy/act/config/` 无 L2-06 新 schema；A4/A5 构造只消费 `DeployConfig` 子对象；所有缺失字段由 L2-01 修复并通过真实 loader Gate。

## 2. L2-06 实际消费字段

| config path | 使用者 | 语义 | 启动不变量 |
|---|---|---|---|
| `bundle.bundle_dir` | B11/L2-01 repo | production bundle；`None` 只表示尚未绑定的模板 config | production main 必须非 None 且交给 canonical loader |
| `runtime.control_hz` | A5 timer | control tick 频率 | `>0` |
| `runtime.inference_hz` | A3 worker | 相邻 inference start 最小间隔 | `>0`；worker stop-aware wait |
| `runtime.device/warmup_steps/compile_model/compile_mode` | L2-01 resource loader | policy device、warmup、compile 决策 | 全部在 worker/timer 前完成并记录 |
| `runtime.chunk_size` | C13/A4 | result 精确行数 | 必须等于 policy chunk size |
| `runtime.execute_horizon` | A4 | 正常 chunk 最大消费行数 | `1 <= horizon <= chunk_size` |
| `runtime.prefetch_steps` | C14 | horizon 前预取触发 | `0 <= prefetch <= horizon` |
| `runtime.action_dim/state_dim` | startup/C13 | ACT 16D 契约 | 两者必须严格为 16 |
| `runtime.max_action_age_sec` | C13/A4 | capture→当前拍 action age 上限 | `>0`，不能用 ready time 起算 |
| `runtime.max_inference_requests` | A1 | request channel 容量 | 第一版必须严格为 1 |
| `runtime.max_pending_chunks` | A1/A4 | result/pending 容量 | 第一版必须严格为 1 |
| `runtime.fallback_policy` | B8 | hold/continue/safe-stop | 仅现有三值 |
| `runtime.publish_metrics_hz` | A5 | C20 timer | `>0` |
| `image.*` | L2-02 public factory/B12 | transport 与预处理配置 | 必须满足 canonical PolicyInputSpec |
| `topics.observation.images` + pose/gripper topics | L2-02 adapter | logical camera→topic mapping与 state subscriptions | image keys 精确等于 PolicyInputSpec.camera_keys，topic 非空 |
| `topics.command.policy_action/left_arm_target/right_arm_target/left_gripper_target/right_gripper_target/status` | L2-05 ActionPublisher | policy、四路 command 与 status | L2-06 不重复写 status |
| `command_output.command_output_enabled` | L2-05/A5 preflight | 启动期真实 command 总开关 | 只能由 CLI 显式透传，不能从 YAML 开启，不可热切换 |
| `command_output.pose_frame_id/gripper_*/qos_depth` | L2-05 ActionPublisher | pose frame、gripper mapping/rate、publisher QoS | 使用 L2-05 既有 schema 校验 |
| `safety.*` | L2-04 SafetyGuard | action-domain 限制与 frame/domain | `SafetyGuard(config.safety)` 单一实例 |
| `topics.command.metrics` | C20 | L2-06 telemetry topic | 与 command status 分离 |

`runtime.mode`、`runtime.max_delta_per_step`、`runtime.task` 不是 L2-06 控制权限：`mode` 最多用于兼容日志，不参与 command gate；`max_delta_per_step` 不得覆盖 L2-04 `SafetyConfig`；`task` 若未来为 policy 必需输入，由 L2-03 typed batch contract 消费，L2-06 不向 batch 塞值。

## 3. 必须由 L2-01 补齐的配置合同

### 3.1 observation freshness

L2-01 `RuntimeConfig` 必须新增：

```text
runtime.max_observation_age_sec: float > 0
```

它只控制 snapshot 是否可用于新 inference/safety，不能复用 `max_action_age_sec`。A5 将该值注入 A4，A4 绑定 `ObservationBuffer.latest_observation(max_age_s)`。

### 3.2 CLI static switch

公共入口必须支持：

```python
load_deploy_config(
    path,
    *,
    command_output_enabled: bool = False,
) -> DeployConfig
```

默认必须 False；只有显式 `--enable-command-output` 可传 True。A5 不得绕过 loader 手工解析 YAML。

### 3.3 bundle 与 policy mode

- `BundleConfig.bundle_dir` 与 `resolved_bundle_dir` 上游都改为 `Path | None`；非 None 才执行 expand/resolve。仓库默认 YAML 的 `null` 可被 typed loader 解析为“模板尚未绑定”，所以 config schema Gate 可独立 PASS。
- production `B11 main` 只允许 real policy，且没有 `--policy`/`--bundle-dir` 旁路；所选 `--config` 内的 `bundle_dir` 为 None 时，`load_act_runtime_resources` 以稳定 `BUNDLE_NOT_CONFIGURED` 启动 FAIL。
- real config 指定路径后必须完整校验；不能因 `Path.exists()==False` 静默跳过。验收环境缺少预期 artifact 只有在 loader 已 local-PASS 时才可 `BLOCKED_ARTIFACT`。
- fake policy 只由 verify/test harness 显式注入 `ActRuntimeResources`，不进入 production C21/B11，也不得由 bundle 缺失隐式选择。

### 3.4 camera/image contract

职责冻结为两半且不得重复：

```text
DeployConfig.topics.observation.images: logical camera key -> ROS topic
PolicyInputSpec: expected camera keys + image shape/layout/dtype/range
```

L2-06 把两者原样交给 L2-02 `build_observation_pipeline`；B12 要求 key set 精确相等。不允许 A5 按 `left/right` 猜测映射或维护第二份转换表。

`topics.observation.images` 是唯一图像 topic 权威。当前 `left_image/right_image` 扁平字段不能与新 map 并存后由运行时猜优先级：上游迁移必须同步更新 schema、默认 YAML 和 L2-02 测试，并对 legacy-only/冲突配置抛稳定 `DeployConfigError`。TCP pose/gripper topic 仍保持明确命名字段，不从 image key 派生。

## 4. 启动交叉校验

B11 在启动 worker 前调用 B12 `run_startup_preflight`，至少验证：

1. config state/action dim、normalizer vector dim、policy metadata 均为 16；
2. config/manifest/experiment/policy chunk size 完全相等；
3. policy camera keys 与 L2-02 observation pipeline keys 完全相等；
4. 每个 image shape/layout/dtype/range 可被 L2-02 实产 snapshot 满足；
5. observation/action age 使用同一 monotonic domain；
6. queue size 第一版均为 1；L2-01 schema 主校验必须是 `== 1`，B12 只做防御性复核；
7. command enabled 时 permit source 已接入，否则不启动真实 command 路径；
8. `safe_stop` 只允许逐 tick fail-closed/no-output；若声称主动硬件 stop，必须有明确 driver port。

## 5. class、函数、I/O 与依赖

- class 设计：无 L2-06 config class。
- 函数设计：无 L2-06 YAML parser；B12 preflight 属 UI 启动编排，输入均为 RAM 对象。
- 输入：L2-01 `DeployConfig` 与已加载资源 metadata。
- 输出：启动成功或结构化失败原因；失败时 worker/timer 均未启动。
- 副作用：无配置文件写入；CLI 只影响 startup-only RAM flag。
- 依赖方向：A5/UI 可依赖 config；config 不依赖 runtime/UI。

## 6. Pi0.5 与验收

Pi0.5 参考：`pi05_vla_deploy_node.py:42-89` 读取 control/inference/horizon/prefetch/age 并装配 runtime；ACT 只参考装配顺序，不复制旧 `mode.publishes_command_topics` 作为动态 permit。

验收标签：`STARTUP_DEFAULT_CONFIG_LOAD`、`CONFIG_COMMAND_ENABLE_FORWARD`、`CONFIG_POLICY_CROSS_CONTRACT`、`CONFIG_OBSERVATION_AGE`、`CONFIG_QUEUE_CAPACITY_ONE`。

任一缺字段、默认配置不可加载或交叉维度不一致均是 FAIL，不是环境 BLOCKED。

本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

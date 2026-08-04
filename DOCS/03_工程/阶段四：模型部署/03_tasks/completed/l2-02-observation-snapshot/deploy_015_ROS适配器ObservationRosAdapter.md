# L3 微元改造任务：ROS 适配器 ObservationRosAdapter

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-02-observation-snapshot 传感器订阅与 ObservationSnapshot 组装闭环
L3 编号：deploy_015
改造类型：source-adaptation
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_015_ROS适配器ObservationRosAdapter.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-observation-snapshot/deploy_015_验收卡片.md`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/`
验收模式：direct-local
辅助验收模式：[env-blocked]
本地验收是否必须：true
真机风险等级：none
L2 分支：`feat/model_deploy/l2-02-observation-snapshot`
集成分支：`model_deploy`

`当前任务文件路径` 必须使用相对仓库根目录路径。当前代码路径必须使用 `src/model_deploy/act/...`，不得把 Pi0.5 历史路径写成当前源码路径。

`l2-02-observation-snapshot` 必须是新版 L2 ID 白名单中的 ID。任务文件、dispatch、验收卡片和 acceptance 目录不得位于 `_legacy_layer_based_act/` 或 `_archived_pi05/`。

> [!warning] 产物落点约束
> 本 L3 产出的源码、测试、配置、launch 和验收脚本必须落到 `ACT代码树分层与产物落点约束.md` 规定的位置。实际产物与本任务声明不一致时，验收判失败。

## 2. 调度元数据

本节用于主 Agent 判断当前 L3 在阶段四任务池中的串行 / 并行关系。必须使用 YAML；所有路径必须是相对仓库根目录路径。

```yaml
dispatch:
  task_id: deploy_015
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_015_ROS适配器ObservationRosAdapter.md
  group: l2-02-observation-snapshot
  branch: feat/model_deploy/l2-02-observation-snapshot
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot
  acceptance_scenarios: [S5]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-observation-snapshot/deploy_015_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [env-blocked]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs
  wave: 4
  parallel_group: l2-02-observation-snapshot-p4
  depends_on: [deploy_011, deploy_012, deploy_014]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/ui/observation_ros_adapter.py
      - src/model_deploy/act/tests/ui/test_observation_ros_adapter.py
    modules:
      - model_deploy.act.ui.observation_ros_adapter
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

`dispatch_status` 只允许 `ready`、`blocked`、`waiting_user`。如果 `robot_risk` 是 `real-robot`，必须在验收方式中写明人工确认、急停准备、限幅策略和回滚路径。

### Agent 执行 / 验收边界

- 执行 sub-agent 只负责本 L3 的实现、局部验证和执行摘要。
- 执行 sub-agent 可以阅读验收卡片理解通过标准，但不得替验收 sub-agent 修改验收结论。
- 验收 sub-agent 只能读取验收卡片、L3 文件、执行摘要、允许查看的 diff / 日志，并按 `acceptance_mode` 输出结论。
- 验收 sub-agent 不得改源码、测试、dispatch、任务状态或 Git。
- `FAIL_LOCAL` 反馈最多回到执行 sub-agent 迭代 3 轮；超过 3 轮必须由主 Agent 停止自动推进并要求人工介入。
- `downstream-l2`、`hardware-blocked`、`env-blocked` 不是免验收，而是要求写清由哪个 L2 场景覆盖、缺什么环境或缺什么硬件。

## 3. 本次唯一目标

```text
在 ui/observation_ros_adapter.py 中实现 ObservationRosAdapter class，将 ROS observation messages 转换为 service 层可消费的 RAM 值，并在 callback 完成后尝试将 ready snapshot 写入 ObservationBuffer。无 ROS 环境时，核心模块 import 不失败，真实 subscription 验收标记为 env-blocked。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 创建 observation topic 的订阅入口设计。
- 将 ROS image 消息转换为 ACT 需要的 RAM 内图像对象。
- 接收左右臂 TCP pose 和左右夹爪 gripper state。
- 调用 ObservationCollector.update_* 和 snapshot，ready 时写入 ObservationBuffer。

### L2 不负责

- 不实现核心 snapshot 业务规则（属 deploy_012 collector）。
- 不调用 ACT 模型、不发布硬件命令。
- 不维护 ControlLoop tick 状态。

### 本 L3 在 L2 中的位置

```text
本 L3 是 L2-02 的外部交互边界。它是 ROS 世界进入 ACT 程序的唯一入口：ROS callbacks 到达 → decode message → 调用 collector.update_* → try snapshot → ready 时写入 buffer。ui 层不得实现核心业务规则，只做消息转换和编排。无 ROS 环境时本模块 import 不失败（延迟 import 策略），真实 subscription 验收标记为 env-blocked。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/02_pi05源码3.5层微元拆解.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/03_ACT微元设计与协作.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/04_L2验收机制.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/05_人类验收机制.md`
9. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/agent_context/11_ui层设计.md`

## 5. Pi0.5 源码盘点

必须具体到文件、入口、class、函数、配置或命令；不得只写"参考现有代码"。

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| `Pi05VlaDeployNode._create_subscriptions` | `deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py` | 数据读写函数 / 编排函数 | 根据 DeployConfig 创建 ROS subscriptions | ACT 拆成独立 adapter class，不嵌入 deploy node | 参考理解 |
| `Pi05VlaDeployNode._image_cb` | `deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py` | 数据读写函数 / 编排函数 | decode image + preprocess + update collector | ACT 拆成 adapter 的 handle_image callback | 参考理解 |
| `Pi05VlaDeployNode._point_cb` / `_vec3_cb` / `_hand_cb` | `deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py` | 数据读写函数 | 更新 collector 的 pose/vector/hand 字段 | ACT 改为 TCP pose 和 gripper width adapter | 参考理解 |
| `Pi05VlaDeployNode._publish_observation_if_ready` | `deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py` | 编排函数 | 检查 snapshot 并写 shared buffer | ACT 拆成 adapter 的 try_publish_observation | 结构复用 |
| `_decode_image` | `deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py` | 数据读写函数 / 计算函数 | ROS Image/CompressedImage -> RGB array | ACT 保留 decode 逻辑在 ui 层 | 结构复用 |

### 必须保留的源码启发

- callback 后尝试 snapshot → ready 时写入 buffer 的编排模式。
- 图像 decode 对 CompressedImage 和 raw Image 的支持。
- 缺字段时不生成 snapshot，只记录 diagnostics。

### 禁止照搬的源码行为

- 禁止把整套 Pi0.5 `Pi05VlaDeployNode` 照搬为 L2-02 adapter。
- 禁止在 ui 层实现核心 snapshot 业务规则（齐全性/新鲜度检查属 service 层）。
- 禁止在 callback 中直接调用模型推理或硬件发送。
- 禁止在无 ROS 环境时 import 即报错（必须延迟 import）。

### 已知风险

- 无 ROS 环境时，真实 topic 订阅无法测试，标记为 `env-blocked`。
- `DeployConfig.topics.observation` 的具体字段名需与 L2-01 实现一致。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `src/model_deploy/act/ui/__init__.py`（如目录不存在则创建目录）。
- 新建 `src/model_deploy/act/ui/observation_ros_adapter.py`。
- 实现 `ObservationRosAdapter` class：
  - `__init__(self, collector, buffer, config)`：持有 collector、buffer 和 topic/image config，ROS node 延迟注入。
  - `create_subscriptions(node)`：根据 config 中的 topic 名创建 ROS subscriptions；如 ROS 不可用则标记 env-blocked 并记录。
  - `decode_image_message(msg)`：ROS Image/CompressedImage → RGB numpy array。
  - `handle_image(name, msg)`：decode + preprocess + collector.update_image + try_publish_observation。
  - `handle_tcp_pose(side, msg)`：解析 pose message + collector.update_tcp_pose + try_publish_observation。
  - `handle_gripper_state(side, msg)`：解析 gripper message + collector.update_gripper_state + try_publish_observation。
  - `try_publish_observation()`：调 collector.snapshot(max_age_s)，ready 时写 buffer，否则记录 missing fields。
- 新建 `src/model_deploy/act/tests/ui/__init__.py`（如需）。
- 新建 `src/model_deploy/act/tests/ui/test_observation_ros_adapter.py`，覆盖 mock callback、decode、import 不失败。

### 本次不做

- 不在无 ROS 环境声明真实 topic 订阅已通过（标记 env-blocked）。
- 不实现 ROS node 全生命周期（属 L2-06 ControlLoop 的装配范围）。
- 不实现模型推理、safety check、硬件命令发送。
- 不修改 service/observation_collector.py 或 runtime/observation_buffer.py。

### 明确禁止修改

- `src/model_deploy/act/types/observation.py`。
- `src/model_deploy/act/service/observation_collector.py`。
- `src/model_deploy/act/service/image_preprocess.py`。
- `src/model_deploy/act/runtime/observation_buffer.py`。
- `src/model_deploy/act/config/`、`src/model_deploy/act/repo/`。
- `src/model_deploy/pi05/`、`pi05_old/`。

### 函数 / class 策略

```text
ObservationRosAdapter 封装为 class，原因：
- 需要持有 ROS node handle、collector、buffer 和 config 依赖。
- 随 ROS node 生命周期存在，callback 事件驱动。
- create_subscriptions 需要 node 参数（延迟注入），不能简单函数化。
- handle_* 方法需要访问 self.collector 和 self.buffer。

decode_image_message 可以是模块级函数或 static method，不依赖实例状态。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否（只 import deploy_011 产物） | — | — |
| config | 否 | — | — |
| repo | 否 | — | — |
| service | 否（只 import deploy_012/003 产物） | — | — |
| runtime | 否（只 import deploy_014 产物） | — | — |
| ui | 是 | `src/model_deploy/act/ui/observation_ros_adapter.py` | ROS message 到 service 输入的 adapter |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/ui/test_observation_ros_adapter.py` | mock callback/import 测试 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `.../agent_context/06_types层设计.md` | 不涉及（deploy_011 已完成） |
| `.../agent_context/07_config层设计.md` | 不涉及（本 L2 无 config 产物） |
| `.../agent_context/08_repo层设计.md` | 不涉及（本 L2 无 repo 产物） |
| `.../agent_context/09_service层设计.md` | 不涉及（deploy_012/003 已完成） |
| `.../agent_context/10_runtime层设计.md` | 不涉及（deploy_014 已完成） |
| `.../agent_context/11_ui层设计.md` | 完整实现 §3 中 ObservationRosAdapter class 的全部方法和 ROS import 策略 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `ui/observation_ros_adapter.py` | `ObservationRosAdapter.__init__` | 编排函数 | collector, buffer, config | adapter 实例 | 无外部副作用 | adapter.no_ros_importable |
| `ui/observation_ros_adapter.py` | `create_subscriptions(node)` | 数据读写函数 / 编排函数 | ROS node | subscription handles | 注册 ROS subscriptions | adapter.real_subscription (env-blocked) |
| `ui/observation_ros_adapter.py` | `decode_image_message(msg)` | 数据读写函数 / 计算函数 | ROS Image/CompressedImage | RGB numpy array | 读取 message payload | adapter.no_ros_importable |
| `ui/observation_ros_adapter.py` | `handle_image(name, msg)` | 数据读写函数 / 编排函数 | camera name, ROS message | 无 | decode + preprocess + update collector + try publish | adapter.no_ros_importable |
| `ui/observation_ros_adapter.py` | `handle_tcp_pose(side, msg)` | 数据读写函数 / 编排函数 | side, ROS Pose message | 无 | 解析 + update collector + try publish | adapter.no_ros_importable |
| `ui/observation_ros_adapter.py` | `handle_gripper_state(side, msg)` | 数据读写函数 / 编排函数 | side, ROS gripper message | 无 | 解析 + update collector + try publish | adapter.no_ros_importable |
| `ui/observation_ros_adapter.py` | `try_publish_observation()` | 编排函数 | collector、buffer | bool | ready 时写 buffer，否则记录 diagnostics | adapter.no_ros_importable |

## 9. 实施步骤

每一步都必须服务于"本次唯一目标"，不得顺手重构无关代码。

1. 确保 `src/model_deploy/act/ui/` 目录存在，含 `__init__.py`。
2. 创建 `src/model_deploy/act/ui/observation_ros_adapter.py`。
3. 实现 ROS import 延迟策略：在模块顶层尝试 `import rclpy` 等，失败时设置 `_ROS_AVAILABLE = False` 但不抛异常；`create_subscriptions` 中检查此标志。
4. 实现 `decode_image_message(msg)`：处理 `sensor_msgs.msg.Image` 和 `sensor_msgs.msg.CompressedImage`，输出 RGB numpy array（H, W, 3, uint8）。
5. 实现 `ObservationRosAdapter.__init__(self, collector, buffer, config)`。
6. 实现 `handle_image(name, msg)`：decode → `preprocess_observation_image(image, config.image)` → `collector.update_image(name, processed)` → `self.try_publish_observation()`。
7. 实现 `handle_tcp_pose(side, msg)`：解析 Pose 消息的 position (x,y,z) 和 orientation (x,y,z,w) → `collector.update_tcp_pose(side, position, orientation)` → `self.try_publish_observation()`。
8. 实现 `handle_gripper_state(side, msg)`：解析 gripper width → `collector.update_gripper_state(side, width)` → `self.try_publish_observation()`。
9. 实现 `try_publish_observation()`：调 `collector.snapshot(max_age_s)`，非 None 时 `buffer.set_observation(snapshot)` 返回 True；为 None 时 `buffer.record_missing_fields(collector.missing_fields())` 返回 False。
10. 实现 `create_subscriptions(node)`：根据 config.topics.observation 创建 6 个 subscriptions（2 image + 2 pose + 2 gripper），绑定对应 callback。
11. 创建 `src/model_deploy/act/tests/ui/test_observation_ros_adapter.py`，编写测试：
    - `test_import_without_ros`：无 ROS 环境 import 模块不抛异常。
    - `test_decode_image_message_mock`：mock ROS Image message，decode 输出正确 shape/dtype。
    - `test_handle_image_mock`：mock collector + buffer，验证 callback 调用链。
    - `test_handle_tcp_pose_mock`：mock collector，验证 pose 解析和 update 调用。
    - `test_try_publish_ready`：mock collector.snapshot 返回 snapshot，验证 buffer.set_observation 被调用。
    - `test_try_publish_missing`：mock collector.snapshot 返回 None，验证 buffer.record_missing_fields 被调用。
    - `test_no_ros_subscription_blocked`：无 ROS 时 create_subscriptions 记录 env-blocked 不抛异常。
12. 运行 `python3 -m pytest src/model_deploy/act/tests/ui/test_observation_ros_adapter.py -v`，确认全部通过。

## 10. 允许修改

> [!warning] 产物落点声明（必填）
> 本节每个允许修改 / 新增的产物，必须标注其落点路径，且路径必须符合 `ACT代码树分层与产物落点约束.md`。
> 允许修改路径只能落在 `src/model_deploy/act/`、当前 L2 设计目录、当前 L2 task/card/acceptance 目录。Pi0.5 路径只能列入"只读参考"，不能列入允许修改。

- `src/model_deploy/act/ui/__init__.py`（如需新建目录）
- `src/model_deploy/act/ui/observation_ros_adapter.py`（新建）
- `src/model_deploy/act/tests/ui/__init__.py`（如需新建目录）
- `src/model_deploy/act/tests/ui/test_observation_ros_adapter.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| ObservationRosAdapter class | `src/model_deploy/act/ui/observation_ros_adapter.py` | ui |
| 单测 | `src/model_deploy/act/tests/ui/test_observation_ros_adapter.py` | tests/ui |

## 11. 禁止修改

- `src/model_deploy/act/types/observation.py`。
- `src/model_deploy/act/service/observation_collector.py`。
- `src/model_deploy/act/service/image_preprocess.py`。
- `src/model_deploy/act/runtime/observation_buffer.py`。
- `src/model_deploy/act/config/`、`src/model_deploy/act/repo/`。
- `src/model_deploy/pi05/`、`pi05_old/`。
- `DOCS/03_工程/阶段四：模型部署/03_tasks/归档/`。

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/ui/test_observation_ros_adapter.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | 无 ROS 环境 import 不失败；mock callback 调用链正确；decode 正确 | pytest 全部通过 |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| shadow-run | 否 | 需要 ROS 环境，当前标记 env-blocked | — |
| real-robot | 否 | 不触发硬件 | — |

### 真机风险控制

不适用，本 L3 的 ROS 订阅不触发真机动作。真机传感器接入不是本 L3 的自动验收条件。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/
对应运行验收场景：S5
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S5 无 ROS 环境可 import |
| 本 L3 提供的运行能力 | ROS message 解码和转换、collector 更新编排、buffer 写入编排；无 ROS 环境 import 不失败 |
| 本 L3 的局部命令 | `python3 -m pytest src/model_deploy/act/tests/ui/test_observation_ros_adapter.py -v` |
| L2 Gate 仍需后续 L3 补齐的内容 | deploy_016 端到端集成验证；真实 ROS 环境下的 topic 订阅验收（env-blocked） |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/`

### 必读代码

1. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（_create_subscriptions, _image_cb, _point_cb, _hand_cb, _publish_observation_if_ready, _decode_image 参考）
2. `src/model_deploy/act/types/observation.py`（deploy_011 产物）
3. `src/model_deploy/act/service/observation_collector.py`（deploy_012 产物，collector 接口）
4. `src/model_deploy/act/service/image_preprocess.py`（deploy_013 产物，preprocess 函数）
5. `src/model_deploy/act/runtime/observation_buffer.py`（deploy_014 产物，buffer 接口）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游 L3：deploy_011 观测类型定义、deploy_012 ObservationCollector、deploy_014 ObservationBuffer。
2. 同组无并行 L3（wave4 仅本 L3）。

## 14. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：
正文 L3 编号：
dispatch.task_id：
是否一致：
所属 L2 ID：
是否属于新版 L2 白名单：
是否命中旧 L2 ID：
是否位于 legacy/archive 目录：
```

执行前必须读取 `dispatch` YAML，确认：

- `task_id` 与正文 L3 编号一致。
- `task_file` 与当前文件路径一致。
- `task_file` 位于 `03_tasks/task/active/<new-l2>/`。
- `group` 是新版 L2 ID。
- `branch` 是当前 L2 分支。
- `integration_branch` 是 `model_deploy`。
- `acceptance_dir` 指向所属 L2 的 `05_acceptance` 子目录。
- `acceptance_card` 指向当前 L3 的验收卡片。
- `acceptance_mode` 已明确。
- `acceptance_round_limit` 固定为 `3`。
- `depends_on` 已完成或明确无需等待。
- `dispatch_status` 不是 `blocked` 或 `waiting_user`。
- `robot_risk` 与验收方式一致。

执行前必须全文检查当前 L3 和 dispatch：

- 不得把 `ACT Contract Delta` 作为任务来源。
- 不得把 `AS-IS Contract -> TO-BE Contract -> Contract Delta` 作为当前主线。
- 不得引用旧 L2 ID 作为所属 L2、任务 group、分支 topic、dispatch 或 acceptance。
- 不得允许修改 `src/model_deploy/pi05/`、`pi05_old/` 或 `_legacy_layer_based_act/`。

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须采用测试优先或最小复现优先：

```text
最小复现 / 测试
-> 最小实现
-> 验证通过
-> 必要整理
```

不得为了通过当前 L3 验收而擅自扩大修改范围。

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] 已完成任务文件身份校验。
- [ ] 已确认所属 L2 ID 属于新版 L2 白名单，且任务不位于 legacy/archive 目录。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] 已读取当前 L2 功能边界、Pi0.5 源码 3.5 层微元拆解、ACT 微元设计、L2 验收机制、人类验收机制与六层设计文档。
- [ ] 已完成 Pi0.5 源码盘点中列出的相关代码确认。
- [ ] 改动没有越过当前 L2 的责任边界。
- [ ] 产物路径符合六层落点约束。
- [ ] 已完成本 L3 的自动化验收或说明无法自动化的原因。
- [ ] 已确认本 L3 的验收卡片、验收模式和本地验收边界。
- [ ] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [ ] 如涉及真机发送链路，已完成真机风险控制说明。
- [ ] 已写明回滚方式。

## 16. 回滚方式

说明如何回到改造前行为。优先写可操作路径：

```text
关闭参数 / 配置：不适用。
切回旧入口：不适用（本 L3 新建 ui adapter，无旧入口）。
移除 adapter：不适用。
回退文件：删除 src/model_deploy/act/ui/observation_ros_adapter.py 和 src/model_deploy/act/tests/ui/test_observation_ros_adapter.py。
不可自动回滚的人工步骤：如 L2-06（ControlLoop）或后续 L2 已 import ObservationRosAdapter，需同步移除 import 后再回退。
```

## 17. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 所属 L2 的 `05_acceptance/l2-02-observation-snapshot/验收结果.md`：登记本 L3 贡献的运行验收场景、实际命令、测试输入、观察点、通过 / 失败现象、证据链接、未验证项和是否影响 L2 Gate。
- 对应 L3 验收卡片：供验收 agent 独立评估；执行 agent 不得自行改验收结论。
- 不得擅自更新阶段级 `当前进度.md` 或共享 `执行记录.md`，除非当前 L3 明确要求。
- 执行 sub-agent 完成单个 L3 后不得自行提交或推送；主 Agent 在验收进入可提交终态后，按阶段四 Git 规则处理。所属 L2 Gate 通过后，才允许合入 `model_deploy`。

交接摘要必须包含：

1. 读取了哪些 L2 设计文档、Pi0.5 源码、ACT 源码和历史任务。
2. 任务文件身份校验结论。
3. 修改了哪些文件。
4. 新增或修改了哪些函数、class、配置、测试或脚本。
5. 如何验证，实际命令是什么。
6. 哪些成功标准已勾选，哪些未验证。
7. 是否影响 dry-run、fake-policy、real-policy、shadow-run 或 real-robot。
8. 回滚方式。
9. 本次明确没有做什么。
10. 后续建议生成或执行的 L3。

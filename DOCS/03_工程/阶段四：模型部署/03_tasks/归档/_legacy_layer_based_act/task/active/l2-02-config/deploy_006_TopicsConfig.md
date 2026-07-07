# L3 微元改造任务：新建 ACT TopicsConfig（observation TCP/gripper + 单路 command）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-02 ACT Config 层
来源 ACT Delta：A4（topic `/act/*`、observation 字段、command 单路）
L3 编号：deploy_006
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_006_TopicsConfig.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-02-config`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/`
对应 L2 运行验收场景：S2
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_006_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_006
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_006_TopicsConfig.md
  group: l2-02-config
  branch: feat/model_deploy/l2-02-config
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config
  acceptance_scenarios: [S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_006_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs
  wave: 1b
  parallel_group: l2-02-config-w1
  depends_on: [deploy_005]
  must_run_after: []
  can_run_parallel_with: [deploy_007]
  blocks: [deploy_008]
  conflict_scope:
    files:
      - src/model_deploy/act/config/schema.py
    modules:
      - act.config.schema
    config_keys: [topics]
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
在 deploy_005 的 schema 骨架中填充 TopicsConfig：ObservationTopicsConfig（双目图像 + 左右TCP + 左右gripper，
topic 全部 /act/* namespace）、CommandTopicsConfig（单路 policy_action + status + metrics）。
删除同事的 BridgeTopicsConfig/MuxTopicsConfig（ACT 用 command_bridge 替代，不需 bridge/mux topic）。
将 TopicsConfig 接入 DeployConfig 顶层。
```

## 4. 来源契约

| 字段 | 内容 |
|---|---|
| Delta | A4 |
| AS-IS | 同事 `ObservationTopicsConfig`（`:94-115`）含 top/left_wrist/right_wrist 三相机 + proprioception + hand_state + ee_pos/rpy + tactile 可选。`CommandTopicsConfig`（`:118-127`）四路关节/手命令。`BridgeTopicsConfig`/`MuxTopicsConfig`（`:130-163`）picotele/teleop 仲裁。 |
| TO-BE | ObservationTopicsConfig 改为：left_image/right_image（双目鱼眼）+ left_tcp_pose/right_tcp_pose + left_gripper_state/right_gripper_state，namespace `/act`。CommandTopicsConfig 改为单路 policy_action + status + metrics。删 Bridge/Mux。 |

所属 L2：[[L2-02-ACT Config层]]，契约依据 [[ACT部署契约]] topic 表。

## 5. 现有程序盘点

| 现有对象 | 路径 | 已有能力 | 差距 | 复用方式 |
|---|---|---|---|---|
| `ObservationTopicsConfig` | `pi05_old/.../schema.py:94-115` | frozen dataclass，13 字段（3 相机+本体感知） | 字段全换：→ 双目+TCP+gripper | **结构复用**（框架保留，字段重写） |
| `CommandTopicsConfig` | `:118-127` | 四路 left/right arm/hand target + status + metrics | 四路 → 单路 policy_action | **结构复用**（字段重写） |
| `BridgeTopicsConfig` | `:130-140` | picotele safe_joint_target/trigger/deadman | ACT 不需要 | **删除，不搬** |
| `MuxTopicsConfig` | `:142-163` | teleop/VLA 仲裁 topic | ACT 不需要 | **删除，不搬** |
| `TopicsConfig` 顶层 | `:166-174` | namespace + observation + command + bridge_output + mux | 删 bridge_output/mux | **结构复用** |
| `_observation_topics()`/`_command_topics()` 工厂 | `:341-374` | 从 YAML 构建 topic config | 字段映射需重写 | **结构复用** |

## 6. 真实改造边界

### 本次允许做

- 在 `act/config/schema.py` 新增/替换：
  - `ObservationTopicsConfig`：6 字段（left_image, right_image, left_tcp_pose, right_tcp_pose, left_gripper_state, right_gripper_state），全部 str 必填。
  - `CommandTopicsConfig`：3 字段（policy_action, status, metrics）。
  - `TopicsConfig`：namespace + observation + command（**不含** bridge_output/mux）。
  - `_act_observation_topics(raw, namespace)` 工厂：默认 topic 名按 `/act/observation/...` 拼装。
  - `_act_command_topics(raw, namespace)` 工厂：默认 `/act/policy_action`、`/act/status`、`/act/metrics`。
- 将 TopicsConfig 接入 `DeployConfig` 顶层和 `_deploy_from_mapping`（替换 deploy_005 的占位）。
- 新建 `act/tests/config/test_topics.py`。

### 本次不做

- 不改 SafetyConfig（deploy_007）。
- 不改 RuntimeConfig 默认值（deploy_007）。
- 不写 deploy.yaml（deploy_008）。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`、`act/types/**`
- deploy_005 已完成的 BundleConfig/ImageConfig/辅助函数

## 7. 实施步骤

1. 编辑 `act/config/schema.py`：
   - 定义 `ObservationTopicsConfig`（6 字段）。
   - 定义 `CommandTopicsConfig`（3 字段）。
   - 定义 `TopicsConfig`（namespace + observation + command）。
   - 删除 deploy_005 占位的 topics 注释，接入正式 TopicsConfig。
   - `_act_observation_topics`：默认名 `f"{namespace}/observation/image/left_gripper_fisheye"` 等（对照 [[ACT部署契约]] topic 表）。
   - `_act_command_topics`：默认 `f"{namespace}/policy_action"` 等。
   - `_deploy_from_mapping` 中 `topics=TopicsConfig(...)` 替换占位。
2. 新建 `act/tests/config/test_topics.py`：加载含 topics 段的 YAML；observation 字段对齐 `/act/observation/*`；command 单路 policy_action；namespace 默认 `/act`。
3. 运行 pytest。

## 8. 验证方式

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/test_topics.py -v
```

| 层级 | 通过标准 |
|---|---|
| unit | test_topics.py PASSED；observation 6 字段、command 3 字段、topic 前缀 `/act/` |

L2 贡献：TopicsConfig 接入，topic 契约可配置化。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 |
|---|---|---|
| schema.py 补充 TopicsConfig | `src/model_deploy/act/config/schema.py` | config |
| 单测 | `src/model_deploy/act/tests/config/test_topics.py` | tests/config |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`、`act/types/**`
- deploy_005 的 BundleConfig/ImageConfig/辅助函数/RuntimeConfig 框架

## 11. 必读上下文

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-02-ACT Config层.md`
- `DOCS/03_工程/阶段四：模型部署/01_contracts/ACT部署契约.md`（topic 表，权威）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`（`:94-174, 341-386` AS-IS）
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-02-config`。
- 依赖校验：deploy_005 已完成（schema 骨架存在）。
- 注意与 deploy_007 的冲突：两者都改 schema.py，但**改不同段落**（006 改 topics，007 改 safety/runtime）。若并行，各自只动自己的 dataclass 和工厂函数。dispatch 已标注 `can_run_parallel_with`。
- 落点校验。

## 13. 成功标准

- [ ] `ObservationTopicsConfig` 6 字段（双目+TCP+gripper）。
- [ ] `CommandTopicsConfig` 3 字段（policy_action/status/metrics）。
- [ ] topic 默认名前缀 `/act/`。
- [ ] TopicsConfig 接入 DeployConfig，无 Bridge/Mux 残留。
- [ ] `test_topics.py` PASSED。
- [ ] 未修改 pi05/types/deploy_005 的基础 dataclass。

## 14. 回滚方式

`git checkout -- src/model_deploy/act/config/schema.py`（回退 topics 段，保留 005 骨架）。

## 15. 完成后交接

（执行 sub-agent 完成后填写）

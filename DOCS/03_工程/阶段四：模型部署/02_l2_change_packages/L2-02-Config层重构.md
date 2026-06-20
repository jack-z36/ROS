# L2-02 · Config 层重构

> [!info] 归属
> - 对应分层：**Config**（依赖 Types，不依赖 Repo/Service/Runtime）。
> - 上游：[[00_L2改造工作包总览]]、依赖 [[L2-01-Types层重构]]。
> - 下游：L2-03（Repo/Service 读 config 拿 topic 名和维度）。
> - 关联 Delta：D2（launch 入口）、D7（topic 命名空间）。

## 一句话定位

把 config schema 里的 topic 名、维度默认值、安全配置从 AS-IS 的关节/realsense/inspire 语义，改成 TO-BE 的 TCP/鱼眼/夹爪width 语义。改完可单测（校验 config 加载）。

## 对应分层

**Config 层**。集中管理所有随部署环境变化的参数（topic 名、维度、安全阈值）。依赖 Types（引用 `ACTION_DIM`/`STATE_DIM`），不被 Types 反向依赖。

## 涉及的现有代码

| 文件 | 类 | AS-IS 现状 |
|---|---|---|
| `deploy/config/schema.py` | `ObservationTopicsConfig`（L94-115） | realsense 三路 image + proprioception + hand_state + ee_position/rpy |
| | `CommandTopicsConfig`（L118-127） | 四路关节/手部目标 + status + metrics |
| | `BridgeTopicsConfig`（L130-139） | bridge 输出 topic（/vla/*） |
| | `MuxTopicsConfig`（L142-163） | mux 仲裁 topic |
| | `TopicsConfig`（L166-174） | 聚合 observation+command+bridge+mux |
| | `RuntimeConfig`（L33-91） | mode/inference_hz/control_hz/`action_dim=14`/`state_dim=26`/fallback 等 |
| | `JointLimitsConfig`（L177-185） | 关节限位（rad） |
| | `SafetyConfig`（L188+） | max_joint_delta_rad/hand_min/hand_max 等 |
| `deploy/config/deploy.yaml` | — | 实际配置值，字段名跟随 schema |

## 已有能力盘点

**保留的能力**：
- `frozen dataclass` + `__post_init__` 硬校验模式（缺字段/非法值直接报错）——保留，这是 C5-3 边界校验的好实践。
- `RuntimeConfig` 的调度参数（inference_hz/control_hz/chunk_size/execute_horizon/prefetch_steps/blend_steps/max_action_age_sec/fallback_policy）——**全部保留，不动**。
- `RuntimeConfig.mode` 三档（dry-run/shadow-run/safe-run）+ `publishes_command_topics` 属性——保留（Q4 已确认三档）。
- `from_mapping` 通用工厂模式——保留。

**必须保留的原始行为**：
- config 加载的严格校验语义（字段缺失报错而非静默默认）。
- mode 三档语义。

## 真实改造边界

### 改 `ObservationTopicsConfig`

AS-IS 字段（删）：`top_image`/`left_wrist_image`/`right_wrist_image`/`*_raw`/`proprioception`/`left_hand_state`/`right_hand_state`/`left_ee_position`/`left_ee_rpy`/`right_ee_*`。

TO-BE 字段（加）：
- `left_fisheye_image` / `right_fisheye_image`（+ raw 变体）
- `left_tcp_pose` / `right_tcp_pose`
- `left_gripper_state` / `right_gripper_state`
- `tactile_l1`/`tactile_l2`/`tactile_r1`/`tactile_r2`（**第一版可选/预留，默认 None**，后续版本启用）
- 删除 `proprioception_order`（picotele 专有）

### 改 `CommandTopicsConfig`

AS-IS（删）：`left_arm_joint_target`/`right_arm_joint_target`/`left_hand_target`/`right_hand_target`。

TO-BE（加）：`policy_action`（单路，替代四路）。

### 删除 `BridgeTopicsConfig` 和 `MuxTopicsConfig`

TO-BE 删了 bridge 和 mux 节点（D1）。这两个 config 类整个删除。`TopicsConfig` 移除对它们的引用。

> [!note] 保留旧类还是删除？
> 工作流要求「保护原始可运行路径」。但 bridge/mux 节点本身在 TO-BE 已停用（D1），保留 config 类没有运行意义。建议删除，回滚靠 git。如果担心影响，可保留类但标注 `@deprecated`，不接入新 launch。

### 改 `RuntimeConfig` 默认维度

- `action_dim` 默认 14→16
- `state_dim` 默认 26→16（第一版）

### 改 `SafetyConfig`

AS-IS（关节空间）：`max_joint_delta_rad`/`JointLimitsConfig`/`hand_min=300`/`hand_max=1000`。

TO-BE（policy-action 层通用检查）：`max_tcp_delta_m`（TCP 单步位移限幅）/ `max_quat_delta`（姿态变化限幅）/ `gripper_width_min=0.0`/`gripper_width_max=1.0`/ 保留 `clamp_normalized_action`。

> [!warning] 关节限位去哪了
> `JointLimitsConfig`（关节限位）下移到 bridge（L2-04/L2-05），因为关节限位是硬件层检查。本 L2 只保留 policy-action 层的 TCP/width 检查配置。但 `ARM_JOINT_NAMES` 和关节限位数据可保留在 config 作为 bridge 的配置来源。

## adapter 优先策略

Config 层直接修改。不用 adapter。旧 config 文件保留（deploy.yaml 旧版），回滚时切回旧 config + 旧 schema（git）。

## 真机风险

**低**。纯配置定义，单测覆盖。

## 验收路径

1. **单测**：构造新 config YAML，加载后断言 topic 名、维度、mode 三档正确。
2. **非法值测试**：缺必需字段时 `__post_init__` 报错。
3. **触觉预留测试**：tactile 字段默认 None 时不阻塞 config 加载。

## L2 Gate

| 字段 | 内容 |
|---|---|
| L2 分支 | `model_deploy-l2-02-config` |
| 集成分支 | `model_deploy` |
| required L3 | deploy_005、deploy_006、deploy_007、deploy_008 |
| 验收运行目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/` |
| 验收结果文档 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/验收结果.md` |
| 最低验证层级 | unit / config load |
| 真机风险 | none |

通过标准：

- deploy_005~deploy_008 全部完成，并在 L3 任务文件中勾选成功标准。
- Config schema 单测和 `deploy.yaml` 加载验证通过。
- topic、维度、mode、SafetyConfig 与 TO-BE Contract 一致。
- 当前代码路径全部指向 `src/model_deploy/pi05/...`。
- `验收结果.md` 已记录运行命令、测试输入、观察点、通过现象、实际结果、证据链接和未验证项。
- 未触发真机动作。

Gate 通过后，允许按 `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md` 自动同步 L2 分支并 `--no-ff` 合入 `model_deploy`。

## 回滚方式

git 回退 schema.py + 切回旧 deploy.yaml（Q7 三件套绑定）。

## 可拆分的 L3 草案

| L3 | 目标 | 改的文件 |
|---|---|---|
| L3-02a | 重构 `ObservationTopicsConfig` 字段为鱼眼/TCP/gripper/触觉预留 | schema.py |
| L3-02b | 重构 `CommandTopicsConfig` 为单路 policy_action；删除 Bridge/Mux config | schema.py |
| L3-02c | 改 `RuntimeConfig` 默认维度（16/16）；改 `SafetyConfig` 为 TCP/width 检查 | schema.py |
| L3-02d | 更新 deploy.yaml 示例配置 + 单测 | deploy.yaml, tests/ |

# L2-02 ACT Config 层

> [!info] 归属
> - 对应分层：Config（依赖 Types，不依赖 Repo/Service）
> - 关联 ACT Delta：A4
> - 关联契约：[[ACT部署契约]]

## 一句话定位

定义 ACT 部署的运行配置：observation topic（`/act/*`）、维度（state=16/action=16）、bundle 路径、safety 阈值、fps、cameras，用 frozen dataclass 在加载时校验合法性。

## 本次唯一目标

- 新建 `src/model_deploy/act/config/schema.py`：部署配置（observation topic、bundle、safety、runtime mode、维度引用 L2-01 的 Types）。
- frozen dataclass + `__post_init__` 校验。

## 同事源码复用边界

| ACT 目标 | 同事源文件 | 方式 | 复用要点 |
|---|---|---|---|
| `act/config/schema.py` | `pi05_old/.../deploy/src/pi05/deploy/config/schema.py` (561行) | **结构复用** | DeployConfig 框架整体保留：frozen dataclass + `__post_init__` 校验 + `load_deploy_config()` 加载器。各子 config（Bundle/Runtime/Safety/Topics）结构保留。改：`state_dim=26/action_dim=14` → `16/16`；observation topic `/pi05/*` → `/act/*` 且字段改 TCP/gripper；command topic 四路 → 单路 `policy_action`；删 `BridgeConfig`/`MuxConfig`（ACT 用 command_bridge 替代）；SafetyConfig 关节项 → TCP 项；`ImageConfig` 三相机 → 双目 |

> [!note] 复用要点
> 同事的 config schema（561 行）是整套调度参数的总开关，**框架质量很高，几乎整体复用**。改动集中在默认值替换（维度、topic 名）和删除两个无用配置段（Bridge/Mux）。**不要重写 dataclass 框架和校验逻辑**，只改字段值和增删配置段。同事的 `paths.yaml`、`runtime.yaml` 等 config 实例放 `act/config_files/`（参见落点约束第三节 config_files/）。

## 明确不做

- 不硬编码 topic 名到业务代码（topic 全部走 config schema）。
- 不预留触觉 config 字段（升级时再加）。
- 不修改 Pi0.5 config。

## 配置结构

### ObservationTopicsConfig（订阅 `act` 节点的 topic）

- `left_image`: `/act/observation/image/left_gripper_fisheye`
- `right_image`: `/act/observation/image/right_gripper_fisheye`
- `left_tcp_pose`: `/act/observation/arm/left_tcp_pose`
- `right_tcp_pose`: `/act/observation/arm/right_tcp_pose`
- `left_gripper_state`: `/act/observation/gripper/left_state`
- `right_gripper_state`: `/act/observation/gripper/right_state`

### PolicyTopicsConfig（发布 topic）

- `policy_action`: `/act/policy_action`
- `status`: `/act/status`
- `metrics`: `/act/metrics`

### BundleConfig

- `bundle_dir`: 指向 ACT bundle 目录（如 `/home/hit/ROS/model_bundles/current`）
- `policy_type`: 固定 `"act"`

### RuntimeConfig

- `mode`: `dry-run` / `shadow-run` / `safe-run`（三档枚举）
- `inference_hz`、`control_hz`、`chunk_size`、`n_action_steps`、`prefetch_steps`、`max_action_age_sec`、`fallback_policy`
- `state_dim`: 固定 16
- `action_dim`: 固定 16
- `fps`: 15

### SafetyConfig

- `max_tcp_step_m`: 单步 TCP 位移上限（m）
- `max_quat_delta`: 单步 quaternion 变化上限
- `gripper_width_min`: 0.0
- `gripper_width_max`: 1.0
- `enable_quaternion_check`: True
- `enable_nan_inf_check`: True

## 边界校验要求

`__post_init__` 必须校验：
- `state_dim == 16` 且 `action_dim == 16`，否则 DeployConfigError。
- `policy_type == "act"`，否则报错。
- topic 字段非空。
- `mode` 属于三档枚举。
- safety 阈值非负。

## L3 草案

| L3 | 目标 | 验收模式 |
|---|---|---|
| deploy_005 | 从同事 schema.py 结构复用：建 `act/config/schema.py` 框架（frozen dataclass + 校验），改 topic `/act/*`、删 Bridge/Mux | direct-local 单测 |
| deploy_006 | 维度/默认值调整：`state_dim=16/action_dim=16`、observation topic 字段改 TCP/gripper | direct-local 单测 |
| deploy_007 | SafetyConfig 改 TCP 步长/quaternion + RuntimeConfig mode 三档 | direct-local 单测 |
| deploy_008 | `act/config_files/deploy.yaml` 示例 + 全量 config 单测（合法通过/非法报错） | direct-local 单测 |

## 真机风险

低。纯配置定义与单测。

## 回滚方式

删除 `src/model_deploy/act/config/`。

## L2 Gate（AI 侧自动化）

- required L3：deploy_005 ~ deploy_008 全部 PASS_LOCAL。
- 运行命令：`pytest src/model_deploy/act/tests/ -v -k config`
- 通过现象：合法 config 加载成功；非法 config（维度错/policy_type 错/topic 空/mode 非法）抛 DeployConfigError。

## 人类验收标准

验收性质全部为「机械」：

| 验收项 | 运行命令 | 通过现象 |
|---|---|---|
| 1 | `pytest src/model_deploy/act/tests/test_config.py -v` | 全部 PASSED |
| 2 | 加载合法 deploy.yaml（含 /act/* topic、dim=16、mode=shadow-run） | 加载成功，state_dim=16，action_dim=16 |
| 3 | 构造非法 config（state_dim=26）单测 | 抛 DeployConfigError，错误信息含 dim |

用户签字位置：`05_acceptance/l2-02-config/验收结果.md` 末尾「人类验收」段。

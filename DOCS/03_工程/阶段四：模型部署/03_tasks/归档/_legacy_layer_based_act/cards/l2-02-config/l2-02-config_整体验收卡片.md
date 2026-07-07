# L2-02 ACT Config 层整体验收卡片

> 本卡片用于 L2 Gate（AI 侧自动化整体验收）。Gate 通过后产出 `05_acceptance/l2-02-config/验收结果.md` 与 `L2整体验收报告.md`，再转交《人类验收清单》由人类签字。
> 规则依据：`DOCS/02_约束/工作流/阶段四开发工作流/attachments/人类验收关卡规则.md`。

## 整体验收元数据

| 字段 | 内容 |
|---|---|
| L2 改造工作包 | L2-02 ACT Config 层 |
| required L3 | deploy_005 / deploy_006 / deploy_007 / deploy_008 |
| L2 Git 分支 | `feat/model_deploy/l2-02-config` |
| 集成分支 | `model_deploy` |
| 验收运行目录 | `/home/hit/ROS` |
| 最低验证层级 | unit |
| 对应运行验收场景 | S2（Config 层加载与校验） |

## required L3 验收状态

| L3 | 验收卡片 | 预期结论 | 实际结论 |
|---|---|---|---|
| deploy_005 | `deploy_005_验收卡片.md` | PASS_LOCAL |  |
| deploy_006 | `deploy_006_验收卡片.md` | PASS_LOCAL |  |
| deploy_007 | `deploy_007_验收卡片.md` | PASS_LOCAL |  |
| deploy_008 | `deploy_008_验收卡片.md` | PASS_LOCAL |  |

> required L3 全部达到可解释状态（PASS_LOCAL / DEFER_TO_L2_GATE / BLOCKED_ENV / BLOCKED_HARDWARE_EXPECTED）后方可执行 L2 Gate。

## L2 Gate 运行命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/ -v
```

## 通过现象

- `pytest src/model_deploy/act/tests/config/ -v` 全部 PASSED（含 005~008 所有测试）。
- 维度 16/16 固化：`RuntimeConfig.action_dim==16`、`state_dim==16`。
- topic 全部 `/act/*` 前缀：observation 6 字段（双目+TCP+gripper）、command 单路（policy_action/status/metrics）。
- SafetyConfig 含 TCP 检查项：`max_tcp_step_m` / `max_quat_delta` / `gripper_width_min` / `gripper_width_max` / `enable_quaternion_check` / `enable_nan_inf_check`。
- 无残留：schema.py 中无 `BridgeTopicsConfig` / `MuxTopicsConfig` / `max_joint_delta_rad` / `hand_min` / `hand_max` / `JointLimitsConfig`。
- deploy.yaml 完整实例加载成功，负向测试（缺段/错 mode/topic 空）覆盖完整。
- 无对 `pi05/`、`third_party/`、`pi05_old/`、`act/types/`（L2-01 产物）的修改。

## 失败现象与排查入口

| 失败现象 | 可能原因 | 排查入口 |
|---|---|---|
| `ModuleNotFoundError: No module named 'act.config...'` | 包路径/`__init__.py` 缺失，或未从仓库根目录运行 | 检查 `src/model_deploy/act/config/__init__.py`、`act/tests/config/__init__.py` 是否存在；确认 cwd=`/home/hit/ROS` |
| 维度断言失败（`action_dim`/`state_dim`≠16） | deploy_007 未改 RuntimeConfig 默认值 | 检查 `act/config/schema.py` 的 `RuntimeConfig.action_dim/state_dim` 是否为 16/16 |
| topic 前缀非 `/act/*`（如残留 `/pi05_vla/*`） | deploy_006 topic 默认名拼装错 | 检查 `_act_observation_topics`/`_act_command_topics` 工厂的 `f"{namespace}/..."` |
| observation 字段不是 6 个 / command 不是单路 | deploy_006 字段未按 TO-BE 重写 | 检查 `ObservationTopicsConfig`（6 字段）/`CommandTopicsConfig`（3 字段单路） |
| 残留 Bridge/Mux | deploy_006 未删同事的 Bridge/Mux 段 | grep schema.py 确认无 `BridgeTopicsConfig`/`MuxTopicsConfig` |
| 残留关节检查项 | deploy_007 未删 `max_joint_delta_rad`/`JointLimitsConfig` | grep schema.py 确认无 `max_joint_delta_rad`/`hand_min`/`hand_max`/`JointLimitsConfig` |
| 缺段未报错（负向测试漏） | `_deploy_from_mapping` 未校验必填段 | 检查 `_deploy_from_mapping` 的 `_required_mapping("bundle")` 等校验 |
| deploy.yaml 加载失败 | yaml 字段名与 dataclass 不匹配 | 对照 deploy.yaml 与 schema.py 字段名；检查 `_deploy_from_mapping` 映射 |

## 未验证项

- 无（纯单测，无硬件依赖、无 dry-run/shadow-run/真机环节；Config 层只验加载与校验逻辑，不涉及实际推理）。

## 下游与 Git 同步判定

| 判定项 | 结论 |
|---|---|
| 是否允许进入下游 L2（L2-03 等依赖 Config 的 L2） | 是（下游依赖 Config 层的 DeployConfig 加载与维度/topic/safety 契约） |
| 是否允许触发 Git 自动同步（合入 `model_deploy` + 删分支） | 否（待人类验收关卡签字通过后允许） |

## L2 Gate 结论

- L2 Gate 结论：`GATE_PASS` / `GATE_FAIL`
- 执行 agent：
- Gate 时间：
- 产物：
  - `05_acceptance/l2-02-config/验收结果.md`
  - `L2整体验收报告.md`
- 备注：

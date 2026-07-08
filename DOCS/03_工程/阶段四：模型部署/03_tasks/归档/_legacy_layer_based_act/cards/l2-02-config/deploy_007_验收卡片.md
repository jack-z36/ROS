# deploy_007 验收卡片

> 本卡片由验收 sub-agent 使用，配合任务文件 `03_tasks/task/active/l2-02-config/deploy_007_SafetyConfig与RuntimeDim.md`。

## 验收元数据

| 字段 | 内容 |
|---|---|
| L3 编号 | deploy_007 |
| 任务 | 新建 ACT SafetyConfig + RuntimeConfig 维度与 mode |
| 验收模式 | direct-local |
| 辅助验收模式 | 无 |
| 本地验收是否必须 | 是 |
| 最低验证层级 | unit |
| 验收运行目录 | `/home/hit/ROS` |
| L2 Git 分支 | `feat/model_deploy/l2-02-config` |
| 验收场景 | S2（Config 层加载与校验） |
| 验收证据落点 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/deploy_007_pytest.txt` |

## 验收对象

`src/model_deploy/act/config/schema.py` 中 SafetyConfig 段 + RuntimeConfig 维度（在 deploy_005 骨架上填充），重点核对：

- `SafetyConfig`（TCP 检查项）：`max_tcp_step_m` / `max_quat_delta` / `gripper_width_min` / `gripper_width_max` / `enable_quaternion_check` / `enable_nan_inf_check`（及 `clamp_normalized_action` / `hold_last_action` / `stale_observation_timeout_s`）。
- 无关节检查残留：`max_joint_delta_rad` / `hand_min` / `hand_max` / `JointLimitsConfig`。
- `RuntimeConfig`：`action_dim=16` / `state_dim=16`（从 14/26 改为 16/16）；mode 三档枚举不变。
- SafetyConfig 已接入 `DeployConfig` 顶层与 `_deploy_from_mapping`（替换 005 占位）。

## 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/test_safety.py -v
```

## 静态检查清单

| 检查项 | 通过标准 |
|---|---|
| SafetyConfig TCP 检查项 | 含 `max_tcp_step_m`/`max_quat_delta`/`gripper_width_min`/`gripper_width_max`/`enable_quaternion_check`/`enable_nan_inf_check` |
| 无关节检查残留 | schema.py 中无 `max_joint_delta_rad`/`hand_min`/`hand_max`/`JointLimitsConfig` |
| RuntimeConfig dim | `action_dim==16` 且 `state_dim==16`（已从 14/26 改） |
| mode 枚举 | 三档枚举（dry-run/shadow-run/safe-run）不变 |
| SafetyConfig 接入 | `_deploy_from_mapping` 中 `safety=SafetyConfig(...)` 替换 005 占位，TODO 注释已清除 |
| 合法 safety 加载 | `max_tcp_step_m>0`、`gripper_width_min/max` 合理时加载成功 |
| 非法 mode 报错 | runtime mode 非三档时抛 `DeployConfigError` |
| 禁改边界 | 未修改 deploy_005 的 Bundle/Image/辅助函数；未改 deploy_006 的 TopicsConfig；未改 `pi05/`、`pi05_old/`、`act/types/` |
| 产物落点 | 源码在 `act/config/schema.py`，测试在 `act/tests/config/test_safety.py`，符合 `ACT代码树分层与产物落点约束.md` |

## 落点校验

| 产物 | 声明落点 | 实际是否存在 | 是否一致 |
|---|---|---|---|
| schema.py 补充 SafetyConfig + 改 dim | `src/model_deploy/act/config/schema.py` |  |  |
| 单测 | `src/model_deploy/act/tests/config/test_safety.py` |  |  |

> 落点与声明不符时判 `FAIL_LOCAL`。

## 结论

- 验收结论：`PASS_LOCAL` / `FAIL_LOCAL` / `BLOCKED_ENV`
- 验收 sub-agent：
- 验收时间：
- 备注（若 FAIL/BLOCKED 填失败项与排查入口）：

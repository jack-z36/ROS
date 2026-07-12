# 验收反馈：deploy_032 SafetyConfig 契约协调（round 1）

| 字段 | 值 |
|---|---|
| L3 | `deploy_032` |
| L2 | `l2-04-safety-guard` |
| 验收模式 | `direct-local` |
| 轮次 | 1 |
| 结论 | **PASS_LOCAL** |
| 分支 | `feat/model_deploy/l2-04-safety-guard` |
| 验收 Agent | 只读；未改源码 / 测试 / dispatch / 卡片 / Git |

## 1. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_safety_config.py src/model_deploy/act/tests/config/test_schema.py -v
```

| 结果 | 详情 |
|---|---|
| 退出码 | 0 |
| 收集用例 | 41 |
| 通过 | 41 passed in 0.09s |
| 失败 / 跳过 | 无 |

## 2. PASS 条件核对

| # | 条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | `SafetyConfig` 含 `max_translation_step_m`、`max_rotation_step_rad`、`gripper_min`、`gripper_max`、`max_gripper_step`、`quaternion_norm_tolerance` | PASS | `schema.py` frozen dataclass 字段齐全；另有可选 `pose_frame` / `quaternion_order` / `gripper_domain` |
| 2 | 平移/旋转阈值 `> 0` 校验生效；非法值拒绝 | PASS | `__post_init__` + `_positive_float`；测试 `test_translation_step_negative/zero_rejected`、`test_rotation_step_zero_rejected` |
| 3 | `gripper_min <= gripper_max` 校验生效 | PASS | `__post_init__`；`test_gripper_min_exceeds_max_rejected` |
| 4 | 默认夹爪域不是硬件寄存器风格 `300~1000` | PASS | 默认 `0.0~1.0`；`test_default_gripper_is_action_domain_not_hardware_register` |
| 5 | `deploy.yaml` safety 段与新字段一致 | PASS | `max_translation_step_m: 0.03`、`max_rotation_step_rad: 0.1`、`gripper_min/max: 0.0/1.0`、`max_gripper_step: 0.2`、`quaternion_norm_tolerance: 0.001` 等 |
| 6 | 未引入 joint limits 或 F100 寄存器映射逻辑 | PASS | `SafetyConfig` 无 joint 字段；legacy `hand_min/max` 显式 `DeployConfigError` 拒绝 |
| 7 | pytest 相关 config 测试全部通过 | PASS | 41 passed |
| 8 | 产物路径与 L3 声明一致 | PASS | `config/schema.py`、`config_files/deploy.yaml`、`tests/config/test_safety_config.py`（+ 允许的 `test_schema.py` / `test_l2_01_gate.py` 最小适配） |
| 9 | 未修改 `src/model_deploy/pi05/` 或 service 安全算法 | PASS | `git status` 无 `pi05/` / `service/` 变更；无 service safety 文件 |

## 3. 静态审查要点

### 旧键兼容策略（执行摘要：破坏性迁移）

- `_SAFETY_LEGACY_KEYS`：`max_tcp_delta_per_step`、`hand_min`、`hand_max`、`quaternion_check`
- 出现任一旧键 → `DeployConfigError`，列出迁移目标字段；**不**静默映射 300~1000
- 测试覆盖：`test_legacy_max_tcp_delta_rejected`、`test_legacy_hand_min_max_rejected`、`test_legacy_quaternion_check_rejected`

### 职责边界

- 未实现 SafetyGuard / 投影算法
- `fallback_policy` 仍在 `RuntimeConfig`，未塞入 `SafetyConfig`
- `types/` 与 `safety_result*` 变更属并行 `deploy_031`，非本 L3 范围；本任务未触碰禁止路径

### 变更文件（与执行摘要一致，在允许范围内）

- `src/model_deploy/act/config/schema.py`
- `src/model_deploy/act/config_files/deploy.yaml`
- `src/model_deploy/act/tests/config/test_safety_config.py`
- `src/model_deploy/act/tests/config/test_schema.py`（最小适配）
- `src/model_deploy/act/tests/integration/test_l2_01_gate.py`（字段名最小适配，L3 允许）

## 4. FAIL / BLOCKED 条件

| 条件 | 是否命中 |
|---|---|
| PASS 任一不满足 | 否 |
| 默认值仍为 F100/`300~1000` | 否 |
| 非法阈值静默接受 | 否 |
| fallback policy 塞进 SafetyConfig | 否 |
| 缺 Python3 / pytest | 否 |

## 5. 结论

**PASS_LOCAL**

主 Agent 应：

1. 将 L3 任务文件从  
   `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_032_SafetyConfig契约协调.md`  
   归档到  
   `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-04-safety-guard/deploy_032_SafetyConfig契约协调.md`
2. 验收 sub-agent **不**执行归档、**不** commit/push。

## 6. 残留风险（不阻断本 L3）

- SafetyGuard 消费侧（deploy_033/034）尚未实现；A1 构造期断言属后续 L3。
- 下游若仍写旧 YAML 键会在加载期失败（有意破坏性迁移）。

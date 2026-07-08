# L3 微元改造任务：ACT deploy.yaml 实例与全量 config 单测

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-02 ACT Config 层
来源 ACT Delta：A4（config 实例 + 全量校验）
L3 编号：deploy_008
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_008_deploy_yaml与全量单测.md`
改造类型：runbook-doc + test-coverage
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-02-config`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/`
对应 L2 运行验收场景：S2
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_008_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_008
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_008_deploy_yaml与全量单测.md
  group: l2-02-config
  branch: feat/model_deploy/l2-02-config
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config
  acceptance_scenarios: [S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_008_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs
  wave: 2
  parallel_group: l2-02-config-w2
  depends_on: [deploy_005, deploy_006, deploy_007]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/config_files/deploy.yaml
      - src/model_deploy/act/tests/config/test_deploy_config_full.py
    modules: []
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 act/config_files/deploy.yaml 完整配置实例（含 bundle/runtime/topics/safety 全段，/act/* topic，dim=16/16）；
新建全量 config 单测 test_deploy_config_full.py：加载完整 deploy.yaml 成功；
补全负向测试（缺段、错 dim、错 mode、topic 空等报错）。
确保 L2-02 Gate 跑全部 config 测试通过。
```

## 4. 来源契约

| 字段 | 内容 |
|---|---|
| Delta | A4 |
| AS-IS | deploy_005~007 已建 schema 各段，但无完整 yaml 实例，全量集成测试未做。 |
| TO-BE | 完整 deploy.yaml 实例 + 全量单测覆盖（正向+负向），Config 层可进入 L2 Gate。 |

所属 L2：[[L2-02-ACT Config层]]

## 5. 现有程序盘点

| 现有对象 | 路径 | 已有能力 | 差距 | 允许修改 |
|---|---|---|---|---|
| schema.py 全段 | `act/config/schema.py`（005~007） | Bundle/Runtime/Image/Topics/Safety 全 dataclass + 加载链路 | 无完整 yaml 实例验证 | 否（只读，不改） |
| 各 test_*.py | `act/tests/config/`（005~007） | 分段单测 | 缺全量集成测试 + 负向覆盖 | 是（补测试） |

## 6. 真实改造边界

### 本次允许做

- 新建 `src/model_deploy/act/config_files/deploy.yaml`：完整配置实例。
- 新建 `act/tests/config/test_deploy_config_full.py`：加载完整 yaml + 全字段断言 + 负向测试。
- 补 `act/tests/config/conftest.py`（公共 fixture：合法/非法 yaml 构造器）。
- **允许微调 schema.py**：若全量测试暴露 005~007 的遗漏 bug，可修（外科手术式，只修 bug 不改结构）。

### 本次不做

- 不改 dataclass 结构或字段定义（已固化）。
- 不改辅助函数。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`、`act/types/**`

## 7. 实施步骤

1. 新建 `act/config_files/deploy.yaml`：
   ```yaml
   bundle:
     bundle_dir: /home/hit/ROS/model_bundles/current
   runtime:
     mode: shadow-run
     device: cuda:0
     dtype: float32
     inference_hz: 10.0
     control_hz: 15.0
     chunk_size: 100
     execute_horizon: 30
     prefetch_steps: 10
     action_dim: 16
     state_dim: 16
     fallback_policy: hold_last_action
     task: "bimanual manipulation"
   image:
     image_size: 224
     resize_mode: resize_pad
   topics:
     namespace: /act
     observation:
       left_image: /act/observation/image/left_gripper_fisheye
       right_image: /act/observation/image/right_gripper_fisheye
       left_tcp_pose: /act/observation/arm/left_tcp_pose
       right_tcp_pose: /act/observation/arm/right_tcp_pose
       left_gripper_state: /act/observation/gripper/left_state
       right_gripper_state: /act/observation/gripper/right_state
     command:
       policy_action: /act/policy_action
       status: /act/status
       metrics: /act/metrics
   safety:
     max_tcp_step_m: 0.05
     max_quat_delta: 0.1
     gripper_width_min: 0.0
     gripper_width_max: 1.0
     enable_quaternion_check: true
     enable_nan_inf_check: true
   ```
2. 新建 `conftest.py`：`valid_deploy_yaml_text()`、`make_invalid_yaml(mutation)` fixture。
3. 新建 `test_deploy_config_full.py`：
   - 正向：加载 deploy.yaml，断言 action_dim==16/state_dim==16、mode==shadow-run、topic 前缀 `/act/`、safety.max_tcp_step_m>0。
   - 负向：缺 bundle 段报错；action_dim=26 报错（若 schema 强校验，否则记录为建议）；mode=invalid 报错；topic 空/非 str 报错。
4. 运行 `pytest src/model_deploy/act/tests/config/ -v`（全量 config 测试）。

## 8. 验证方式

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/ -v
```

| 层级 | 通过标准 |
|---|---|
| unit | tests/config/ 全部 PASSED（含 005~008 所有测试）；负向覆盖完整 |

L2 贡献：Config 层全量验证通过，可进入 L2 Gate。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 |
|---|---|---|
| 配置实例 | `src/model_deploy/act/config_files/deploy.yaml` | config_files |
| 全量单测 | `src/model_deploy/act/tests/config/test_deploy_config_full.py` | tests/config |
| 公共 fixture | `src/model_deploy/act/tests/config/conftest.py` | tests/config |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`、`act/types/**`
- schema.py 的 dataclass 字段定义（除非修 bug 且标注）

## 11. 必读上下文

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-02-ACT Config层.md`
- `DOCS/03_工程/阶段四：模型部署/01_contracts/ACT部署契约.md`
- deploy_005/006/007 任务文件（依赖）
- `DOCS/02_约束/编程执行/Agent编程执行原则.md`（第四节验收闭环）
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-02-config`。
- 依赖：deploy_005/006/007 全部 PASS_LOCAL。
- TDD：负向测试先写，验证边界。
- 落点校验。

## 13. 成功标准

- [ ] `deploy.yaml` 完整实例存在，含全段，topic `/act/*`，dim 16/16。
- [ ] `test_deploy_config_full.py` 加载完整 yaml 成功，全字段断言通过。
- [ ] 负向测试：缺段/错 mode/topic 空 等均抛 DeployConfigError。
- [ ] `pytest tests/config/ -v` 全部 PASSED。
- [ ] 未修改 pi05/types。

## 14. 回滚方式

删除 `deploy.yaml` + `test_deploy_config_full.py` + `conftest.py`。

## 15. 完成后交接

（执行 sub-agent 完成后填写）

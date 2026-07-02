# L3 微元改造任务：deploy.yaml 更新 + Config 层单测

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-02 Config 层重构
来源 Delta：D2/D3/D7/D9/D11/D12/D13（config 整体改造的配置文件与测试覆盖）
L3 编号：deploy_008
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_008_deploy_yaml与单测.md`
改造类型：test-coverage
真机风险等级：none

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_008
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_008_deploy_yaml与单测.md
  group: l2-02-config
  branch: model_deploy
  wave: 4
  parallel_group: l2-02-config-p4
  depends_on: [deploy_005, deploy_006, deploy_007]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/config/deploy.yaml
      - pi05_test/pi05/deploy/tests/test_config_tcp_width.py
    modules:
      - tests.config_layer
    config_keys:
      - topics
      - runtime.action_dim
      - runtime.state_dim
      - safety
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
更新 deploy.yaml 示例配置以匹配 deploy_005/006/007 改后的 schema（新 observation topic、单路 policy_action、16/16 维度、TCP/width safety、无 bridge/mux），并编写 Config 层单测，覆盖 config 加载、字段正确性、触觉可选、维度默认值。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D2/D3/D7/D9/D11/D12/D13 综合 |
| 变更对象 | Config 层整体 |
| AS-IS 契约 | deploy.yaml 用旧字段（realsense/proprio/四路command/bridge/mux/14/26/关节safety）。无 config 单测。 |
| TO-BE 契约 | deploy.yaml 用新字段；config 加载单测守护。 |
| 兼容性要求 | 旧 deploy.yaml 保留作回滚（git）。 |
| 回滚要求 | 删新 deploy.yaml 测试，切回旧 deploy.yaml。 |

### 所属 L2 改造工作包

- L2 名称：L2-02 Config 层重构
- 本 L3 在该 L2 中的位置：最后一个，验收前三者。L2-02 完成标志。
- 本 L3 完成后解锁：L2-02 整体完成，L2-03（数据装配）可开始。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `deploy.yaml` | `deploy/config/deploy.yaml` | 旧字段配置 | 全字段更新 | 是 |
| config 加载逻辑 | `load_deploy_config`/`from_mapping`（deploy_005/006/007 改后） | 新 schema | 缺测试守护 | 否（只测不改） |
| 测试目录 | `deploy/tests/`（待确认存在） | — | 需新建 | 是（新建） |

### 必须保留的现有行为

- 不改 schema.py（前三 L3 产物）。
- config 加载的严格校验语义。

### 已知风险

- deploy.yaml 加载需要能 import deploy.config.schema。但 deploy_005/006/007 完成后，deploy_node 等上层可能仍无法 import（读旧字段）——但 `load_deploy_config` 本身只依赖 schema.py，应能独立加载。需确认 import 链不触发 deploy_node。
- 如果 common 包 `__init__` 级联 import deploy，测试需绕过（参考 deploy_004 的同类问题）。

## 6. 真实改造边界

### 本次允许做

**更新 deploy.yaml：**
- `topics.observation`：改用新字段（left_fisheye_image/right_fisheye_image/left_tcp_pose/right_tcp_pose/left_gripper_state/right_gripper_state）；触觉字段注释掉（第一版可选）。
- `topics.command`：改用 policy_action（删四路）。
- 删除 `topics.bridge_output`/`topics.mux` 段。
- 删除 `bridge`/`mux` 段。
- `runtime.action_dim`/`state_dim`：16/16（或依赖默认值，注释说明）。
- `safety`：max_tcp_delta_m/gripper_width_min=0.0/gripper_width_max=1.0（删 max_joint_delta_rad/hand_min/hand_max）。
- 保留 runtime 调度参数、mode、bundle、image 段。

**新建单测 `test_config_tcp_width.py`：**
- `test_load_new_config`：加载新 deploy.yaml，断言 observation/command 字段正确。
- `test_dims_default_16`：RuntimeConfig action_dim/state_dim == 16。
- `test_safety_tcp_width`：SafetyConfig max_tcp_delta_m/gripper_width_min/max 存在，hand_min/max 不存在。
- `test_no_bridge_mux`：DeployConfig 无 bridge/mux 属性。
- `test_tactile_optional`：deploy.yaml 不配触觉时，加载成功，tactile 字段为 None。
- `test_old_config_rejected`：旧字段（如 proprioception）在新 schema 下加载失败或被忽略。

### 本次不做

- 不改 schema.py/topics.py（前三 L3 已改）。
- 不改 deploy_node（L2-03/04 做）。
- 不测上层加载（那是后续 L2 的 dry-run）。

### 明确禁止修改

- 禁止改 schema.py/topics.py。
- 禁止改 deploy 包非 config 代码。
- 禁止为让 deploy_node 能 import 而改上层。

### Adapter / 直接修改策略

```text
配置文件更新 + 新增测试。不碰被测 schema 代码。
```

## 7. 实施步骤

1. **确认 deploy.yaml 当前路径和内容**（`deploy/config/deploy.yaml`），确认 import 链。
2. **更新 deploy.yaml**：字段如上重构；保留 bundle/runtime 调度/image；触觉注释。
3. **写 test_config_tcp_width.py**：6 个测试 case 如上。
4. **运行 pytest**：确认 config 加载 + 字段断言通过。

## 8. 验证方式

### 自动化验收命令

```bash
cd pi05_test/pi05 && python3 -m pytest pi05/deploy/tests/test_config_tcp_width.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | pytest 全部通过 | 所有 case pass |
| dry-run | 否 | — | — |

### 真机风险控制

不适用。

## 9. 允许修改

- `pi05_test/pi05/deploy/config/deploy.yaml`
- 新建 `pi05_test/pi05/deploy/tests/test_config_tcp_width.py`

## 10. 禁止修改

- schema.py/topics.py（前三 L3 产物）。
- deploy 包非 config 代码。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（topic 表）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-02-Config层重构.md`

### 必读代码

1. `pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`（deploy_005/006/007 改后）
2. `pi05_test/pi05/deploy/config/deploy.yaml`（本 L3 更新）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_005/006/007（全部完成）。
2. 同组已完成：deploy_005/006/007。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_005,006,007]` 全部完成。

```text
确认 deploy.yaml 路径和 import 链
→ 更新 deploy.yaml
→ 写测试
→ pytest 通过
```

如果 config 加载因 import 链失败（common __init__ 级联 deploy），记录问题，不强行改 __init__。

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] deploy.yaml 字段更新为新 schema。
- [ ] 触觉字段在 deploy.yaml 中为可选（注释/省略）。
- [ ] pytest 全部通过。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- deploy.yaml；删除 test_config_tcp_width.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、更新 deploy.yaml 字段、新建测试 case 数、pytest 结果、成功标准勾选、真机影响（无）、回滚、未做事项（没改 schema/上层）、后续建议（L2-02 完成，可开始 L2-03）。

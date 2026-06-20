# L3 微元改造任务：observation_collector 改造为 TCP+width 装配

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-03 数据装配 Service 层
来源 Delta：D3（相机）、D7（topic）、D8（臂状态语义）、D9（encoded_state）
L3 编号：deploy_009
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_009_observation_collector改造.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：model_deploy-l2-03-assembly
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
对应 L2 运行验收场景：[S1, S2, S3]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_009_验收卡片.md
验收模式：static-review
辅助验收模式：['downstream-l2']
本地验收是否必须：false
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_009
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_009_observation_collector改造.md
  group: l2-03-assembly
  branch: model_deploy-l2-03-assembly
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
  acceptance_scenarios: [S1, S2, S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_009_验收卡片.md
  acceptance_mode: static-review
  acceptance_secondary_modes: [downstream-l2]
  local_acceptance_required: false
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs
  wave: 1
  parallel_group: l2-03-assembly-p1
  depends_on: [deploy_002, deploy_005]
  must_run_after: []
  can_run_parallel_with: [deploy_011]
  blocks: [deploy_010, deploy_012]
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py
    modules:
      - pi05.deploy.runtime.observation_collector
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 observation_collector 从关节角+EE 装配改造为 TCP pose + gripper width 装配：换必需字段集、换 update 方法、换 snapshot 构造（用新 BimanualState），预留触觉接口（第一版 disabled），保留字段齐全+时效性门控框架。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D3 + D7 + D8 + D9 |
| 变更对象 | 相机 + topic + 臂状态 + encoded_state |
| AS-IS 契约 | `ObservationCollector`（observation_collector.py:1-154）：REQUIRED_IMAGE_KEYS=(top,left_wrist,right_wrist)；_required_value_keys=（left_arm_q/right_arm_q/left_hand_q/right_hand_q/left_ee_pos/left_ee_rpy/right_ee_pos/right_ee_rpy）；update_proprioception/update_hand/update_vector；snapshot 构造 BimanualState(关节+EE) + encode_bimanual_state(26D)。 |
| TO-BE 契约 | REQUIRED_IMAGE_KEYS=(left_fisheye,right_fisheye)；必需值=（left_tcp_pose/right_tcp_pose/left_gripper_width/right_gripper_width）；update_tcp_pose/update_gripper_width；预留 update_tactile（disabled）；snapshot 构造新 BimanualState(TCP+width) + encode_bimanual_state(16D)。 |
| 兼容性要求 | 破坏性。 |
| 回滚要求 | git 回退。 |

### 所属 L2 改造工作包

- L2 名称：L2-03 数据装配 Service 层
- 本 L3 在该 L2 中的位置：第一个。collector 是装配核心。
- 本 L3 完成后解锁：deploy_010（deploy_node 订阅侧，callback 调新方法）、deploy_012（dry-run）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `REQUIRED_IMAGE_KEYS` | observation_collector.py:23 | 必需图像 key (top,left_wrist,right_wrist) | 改 (left_fisheye,right_fisheye) | 是 |
| `_required_value_keys` | observation_collector.py:144-154 | 关节+EE 必需值 | 改 TCP+width | 是 |
| `update_proprioception` | observation_collector.py:48-62 | 解关节角 + decode_picotele_proprioception | 删，换 update_tcp_pose | 是 |
| `update_hand` | observation_collector.py:64-67 | 写 hand_q | 删，换 update_gripper_width | 是 |
| `update_vector` | observation_collector.py:69-73 | 通用向量写（ee_pos/rpy） | 删（tcp_pose 专用方法替代） | 是 |
| `snapshot` | observation_collector.py:75-103 | 构造 BimanualState(关节+EE)+encode 26D | 改新 BimanualState+encode 16D | 是 |
| `_has_stale_field_locked` | observation_collector.py:118-131 | 时效检查（关节/EE stamp key） | 改 TCP/width stamp key | 是 |
| `missing_fields` | observation_collector.py:105-111 | 报缺失字段 | 跟随新字段 | 是 |
| `__init__.proprioception_order` | observation_collector.py:28/35 | picotele 顺序参数 | 删（不再需要） | 是 |
| import | observation_collector.py:16 | 引用 decode_picotele_proprioception | 改（删 decode_picotele，保留 encode/BimanualState） | 是 |

### 必须保留的现有行为

- 「字段齐全 + 未过期才生成 snapshot」门控模式（核心，只改字段名）。
- `set_required_image_keys` 从 bundle manifest 动态确定图像。
- `_normalize_image_keys` 去重/空校验。
- latest-only 语义（不保留历史）。
- missing fields 节流日志框架。
- 线程锁 `_lock`。

### 已知风险

- snapshot 构造新 BimanualState 需要 deploy_002（state_codec）已改好——`depends_on: [deploy_002]` 保证。
- collector 改后，deploy_node 的旧 callback（_proprio_cb/_hand_cb/_point_cb/_vec3_cb）调用的 update 方法不存在了——deploy_010 改 deploy_node 订阅侧。本 L3 完成后 deploy_node 暂时无法运行，预期中间状态。

## 6. 真实改造边界

### 本次允许做

- `REQUIRED_IMAGE_KEYS`（L23）：改 `(left_fisheye, right_fisheye)`。
- `_required_value_keys`（L144-154）：改 `(left_tcp_pose, right_tcp_pose, left_gripper_width, right_gripper_width)`。
- 删 `update_proprioception`/`update_hand`/`update_vector`（L48-73）。
- 新增 `update_tcp_pose(side, pose_quat_7d)`：接收 `[x,y,z,qx,qy,qz,qw]`，校验维度=7，写 `_values[f"{side}_tcp_pose"]` + stamp。可选校验 quaternion 归一化（warn 不阻塞）。
- 新增 `update_gripper_width(side, width)`：接收 float（[0,1]），写 `_values[f"{side}_gripper_width"]` + stamp。
- 预留 `update_tactile(chip_id, matrix)`：第一版 disabled（不列入 _required_value_keys），方法存在供后续启用。
- `snapshot`（L75-103）：构造新 BimanualState(left_tcp_pose, right_tcp_pose, left_gripper_width, right_gripper_width) + encode_bimanual_state(include_tactile=False)。
- `_has_stale_field_locked`（L118-131）：stamp key 改 tcp_pose/gripper_width。
- `missing_fields`（L105-111）和 `_required_value_keys`（L144-154）：字段名跟随。
- `__init__`：删 proprioception_order 参数。
- import（L16）：删 decode_picotele_proprioception。

### 本次不做

- 不改 deploy_node（deploy_010 做）。
- 不改 policy_loader（deploy_011 做）。
- 不改 shared_buffer（ObservationSnapshot 泛型持有 BimanualState，自动跟随 deploy_002）。
- 不实现触觉聚合算法（预留接口位即可）。
- 不补单测/dry-run（deploy_012 做）。

### 明确禁止修改

- 禁止改 observation_collector.py 以外的文件。
- 禁止改门控框架逻辑（_has_required_locked/_has_stale_field_locked 的检查机制，只改字段名）。
- 禁止改 set_required_image_keys/_normalize_image_keys（保留）。
- 禁止改线程锁机制。

### Adapter / 直接修改策略

```text
直接修改。collector 字段装配整体替换，但保留门控框架（required/stale 检查机制）。触觉用方法预留 + 不列入必需字段（第一版 disabled）。回滚靠 git。
```

## 7. 实施步骤

1. **改 import**（L16）：删 decode_picotele_proprioception，保留 encode_bimanual_state/BimanualState。
2. **改 `__init__`**（L25-36）：删 proprioception_order 参数。
3. **改 `REQUIRED_IMAGE_KEYS`**（L23）：(left_fisheye, right_fisheye)。
4. **删 `update_proprioception`/`update_hand`/`update_vector`**（L48-73）。
5. **新增 `update_tcp_pose`**：接收 side + 7D 向量，校验维度，写 _values + stamp。
6. **新增 `update_gripper_width`**：接收 side + float，写 _values + stamp。
7. **预留 `update_tactile`**：方法存在，第一版不列入必需字段。
8. **改 `snapshot`**（L75-103）：构造新 BimanualState，调 encode_bimanual_state(include_tactile=False)。
9. **改 `_has_stale_field_locked`**（L118-131）/`missing_fields`（L105-111）/`_required_value_keys`（L144-154）：字段名跟随。
10. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
src = open('src/model_deploy/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py', encoding='utf-8').read()
for m in ['update_tcp_pose','update_gripper_width','update_tactile']:
    assert f'def {m}' in src, f'{m} missing'
for f in ['left_tcp_pose','right_tcp_pose','left_gripper_width','right_gripper_width']:
    assert f in src, f'{f} missing'
assert 'left_fisheye' in src and 'right_fisheye' in src
for m in ['update_proprioception','update_hand','update_vector']:
    assert f'def {m}' not in src, f'{m} should be removed'
assert 'decode_picotele_proprioception' not in src
assert '_has_required_locked' in src and '_has_stale_field_locked' in src
print('deploy_009 验收通过: collector→TCP+width装配, 触觉预留, 门控保留')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 方法/字段断言 | 上述命令通过 |
| dry-run | 否（deploy_012 做） | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py`

## 10. 禁止修改

- observation_collector.py 以外的任何文件。
- 门控框架机制（_has_required_locked/_has_stale_field_locked 的逻辑，只改字段名）。
- set_required_image_keys/_normalize_image_keys/线程锁。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D3/D7/D8/D9 + Q6 触觉分两版）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-03-数据装配Service层.md`

### 必读代码

1. `src/model_deploy/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py`（本 L3 修改）
2. `src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py`（deploy_002 改后，确认新 BimanualState/encode_bimanual_state 签名）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_002（state_codec，提供新 BimanualState）、deploy_005（observation topic 字段）。
2. 同组：无已完成（本 L3 是 L2-03 第一个）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_002, deploy_005]` 已完成。

```text
最小复现 / 测试（AST 断言）
→ 最小实现（改 collector）
→ 验证通过
→ 必要整理（docstring）
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] REQUIRED_IMAGE_KEYS 改为鱼眼双目。
- [ ] _required_value_keys 改为 TCP+width。
- [ ] update_tcp_pose/update_gripper_width 新增。
- [ ] update_tactile 预留（第一版不列入必需）。
- [ ] snapshot 构造新 BimanualState + encode 16D。
- [ ] 门控框架保留。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- observation_collector.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、修改内容、新增方法、验收结果、成功标准勾选、真机影响（无）、回滚、未做事项（没改 deploy_node/policy_loader/shared_buffer/触觉聚合）、后续建议（deploy_010/011）。

# L3 微元改造任务：新建 ACT observation_collector（16D snapshot 装配）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-03 ACT 数据装配与模型加载
来源 ACT Delta：A6（observation_collector，16D snapshot 装配）
L3 编号：deploy_010
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_010_observation_collector.md`
改造类型：behavior-change（结构复用同事源码，改字段）
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-03-assembly`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/`
对应 L2 运行验收场景：S3
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_010_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_010
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_010_observation_collector.md
  group: l2-03-assembly
  branch: feat/model_deploy/l2-03-assembly
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
  acceptance_scenarios: [S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_010_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs
  wave: 1
  parallel_group: l2-03-assembly-w1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_009, deploy_011]
  blocks: [deploy_012]
  conflict_scope:
    files:
      - src/model_deploy/act/service/observation_collector.py
      - src/model_deploy/act/service/__init__.py
    modules:
      - act.service.observation_collector
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 src/model_deploy/act/service/observation_collector.py，装配 16D state snapshot。
结构复用同事 ObservationCollector（线程安全 + 时效性门控 + snapshot 完整性判断），
字段从 8 个关节/EE 字段改为 4 个 TCP/gripper 字段，encoded_state 用 L2-01 的 encode_state（16D 分组段序）。
```

## 4. 来源契约

| 字段 | 内容 |
|---|---|
| Delta | A6 |
| AS-IS | 同事 `observation_collector.py`（155行）：`ObservationCollector`，`_required_value_keys` 8 字段（left_arm_q/right_arm_q/left_hand_q/right_hand_q/left_ee_pos/left_ee_rpy/right_ee_pos/right_ee_rpy），`update_proprioception`/`update_hand`/`update_vector`，`snapshot()` 拼 `BimanualState` + `encode_bimanual_state`。 |
| TO-BE | 新建 ACT 版：`_required_value_keys` 4 字段（left_tcp_pose/right_tcp_pose/left_gripper_width/right_gripper_width）；新增 `update_tcp_pose(side, pose)`/`update_gripper_state(side, width)`；`snapshot()` 拼 `ActBimanualState` + `encode_state`（16D 分组段序）。 |

所属 L2：[[L2-03-ACT数据装配与模型加载]]。

## 5. 现有程序盘点

| 现有对象 | 路径 | 行数 | 已有能力 | 复用方式 |
|---|---|---|---|---|
| `ObservationCollector` 类骨架 | `pi05_old/.../runtime/observation_collector.py:20-141` | 122 | 线程锁 `_lock` + `_images/_values/_stamps` dict + `set_required_image_keys` + `update_image` + `snapshot` + `missing_fields` | **结构复用**（框架保留，改字段） |
| `snapshot()` | `:75-103` | 29 | 完整性+时效性门控 → 拼 BimanualState → encode | **结构复用**（拼 ActBimanualState + encode_state） |
| `_required_value_keys()` | `:144-154` | 11 | 8 关节字段 | **重写**（4 TCP/gripper 字段） |
| `update_proprioception()` | `:48-62` | 15 | picotele [right6,left6] 解码 | **不搬**（ACT 不用 picotele） |
| `update_hand()` | `:64-67` | 4 | hand_q 更新 | **改为** `update_gripper_state(side, width)` |
| `_has_stale_field_locked()` | `:118-131` | 14 | 时效检查 stamp keys | **结构复用**（stamp keys 改） |
| `REQUIRED_IMAGE_KEYS` | `:23` | 1 | `("top","left_wrist","right_wrist")` | **改** `("left_gripper_fisheye","right_gripper_fisheye")` |

## 6. 真实改造边界

### 本次允许做

- 新建 `src/model_deploy/act/service/__init__.py`。
- 新建 `src/model_deploy/act/service/observation_collector.py`：
  - `ObservationCollector` 类，保留线程锁 + `_images/_values/_stamps` + `update_image` + `set_required_image_keys` + `missing_fields` 结构。
  - `REQUIRED_IMAGE_KEYS = ("left_gripper_fisheye", "right_gripper_fisheye")`。
  - `_required_value_keys()` 返回 `("left_tcp_pose","right_tcp_pose","left_gripper_width","right_gripper_width")`。
  - `update_tcp_pose(side, pose)`：pose 是 7D (xyz+quat)，存到 `_values[f"{side}_tcp_pose"]`。
  - `update_gripper_state(side, width)`：width 是 float，存到 `_values[f"{side}_gripper_width"]`。
  - `snapshot()`：门控 → 拼 `ActBimanualState`（用 L2-01 的 dataclass）→ `encode_state`（16D）→ 返回 `ObservationSnapshot`。
- 新建 `act/tests/service/__init__.py` + `test_observation_collector.py`。

### 本次不做

- 不实现 policy_loader（deploy_009）。
- 不接 ROS 回调（L2-04 的 deploy_node 负责 ROS 订阅 → 调 update_*）。
- 不改 shared_buffer 的 ObservationSnapshot（L2-04 复用，只 import）。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/**`、`act/config/**`、`act/runtime/**`、`act/repo/**`

## 7. 实施步骤

1. 新建 `act/service/__init__.py`、`act/service/observation_collector.py`。
2. import：`from act.types.state_codec import ActBimanualState, encode_state`、`from act.runtime.shared_buffer import ObservationSnapshot`。
3. 实现 `ObservationCollector`（参照同事结构，改字段和 update 方法）。
4. `snapshot()`：用 `ActBimanualState(left_tcp_pose=values["left_tcp_pose"], ...)` + `encode_state(state)` 产出 16D encoded_state。
5. 新建 `act/tests/service/test_observation_collector.py`：喂双目+TCP+gripper → snapshot 非 None 且 encoded_state shape [16]；缺任一字段 → snapshot None；时效过期 → None。
6. 运行 pytest。

## 8. 验证方式

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/service/test_observation_collector.py -v
```

| 层级 | 通过标准 |
|---|---|
| unit | snapshot 完整时 encoded_state shape [16] 段序分组；缺字段返回 None；过期返回 None |

L2 贡献：16D observation snapshot 装配就绪。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 |
|---|---|---|
| observation_collector 源码 | `src/model_deploy/act/service/observation_collector.py` | service |
| service 包标记 | `src/model_deploy/act/service/__init__.py` | service |
| 单测 | `src/model_deploy/act/tests/service/test_observation_collector.py` | tests/service |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/**`、`act/config/**`、`act/runtime/**`、`act/repo/**`

## 11. 必读上下文

### 必读任务文档
- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-03-ACT数据装配与模型加载.md`
- `DOCS/03_工程/阶段四：模型部署/01_contracts/ACT部署契约.md`（observation.state 段序）

### 必读代码（AS-IS 参考）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py`（155行）

### 必读约束文档
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`（第三节 shape 边界校验）
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-03-assembly`。
- 依赖：L2-01（encode_state/ActBimanualState）、shared_buffer.ObservationSnapshot 可 import。
- TDD：先写 snapshot 完整性/时效性单测。
- 落点校验。

## 13. 成功标准

- [ ] `act/service/observation_collector.py` 存在。
- [ ] `_required_value_keys` 4 字段（left/right_tcp_pose + left/right_gripper_width）。
- [ ] `update_tcp_pose`/`update_gripper_state` 方法存在。
- [ ] `snapshot()` 完整时返回 ObservationSnapshot，encoded_state shape [16] 分组段序。
- [ ] 缺字段/过期时 snapshot 返回 None。
- [ ] `test_observation_collector.py` PASSED。
- [ ] 未修改 pi05/types/config/runtime/repo。

## 14. 回滚方式

删除 `src/model_deploy/act/service/observation_collector.py`。

## 15. 完成后交接

（执行 sub-agent 完成后填写）

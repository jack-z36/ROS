# L3 微元改造任务：Topic 候选载荷生成

## 1. 任务定位

阶段：阶段四：模型部署  
L1：ACT 部署程序开发  
所属 L2：`l2-05-action-publisher` 单步 Action 到执行器 Topic 适配发送闭环  
L3 编号：deploy_042  
改造类型：`source-adaptation`  
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_042_Topic候选载荷生成.md`  
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_042_验收卡片.md`  
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/`  
验收模式：`direct-local`  
辅助验收模式：[]  
本地验收是否必须：`true`  
真机风险等级：`none`  
L2 分支：`feat/model_deploy/l2-05-action-publisher`  
集成分支：`model_deploy`

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_042
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_042_Topic候选载荷生成.md
  group: l2-05-action-publisher
  branch: feat/model_deploy/l2-05-action-publisher
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher
  acceptance_scenarios: [G04, G05, G06]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_042_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/logs
  wave: 2
  parallel_group: l2-05-action-publisher-p2
  depends_on: [deploy_041]
  must_run_after: [deploy_041]
  can_run_parallel_with: [deploy_043]
  blocks: [deploy_044, deploy_045]
  conflict_scope:
    files:
      - src/model_deploy/act/service/action_output_adapter.py
      - src/model_deploy/act/service/__init__.py
      - src/model_deploy/act/tests/service/test_action_output_adapter.py
    modules:
      - model_deploy.act.service.action_output_adapter
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 Agent 只改 service 候选载荷生成与局部测试；验收 Agent 保持只读。
- 执行-验收最多 3 轮；本 L3 不创建 ROS 对象、publisher 或运行状态。

## 3. 本次唯一目标

```text
实现 B1 build_topic_payloads 与 C9-C11，将 PASS/ADJUSTED SafetyResult 纯 RAM 转换为完整 C4 TopicPayloadBundle。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 复核 safe 16D action，按 `[0:7]/[7:14]/[14]/[15]` 拆分，构造统一 frame 臂目标与 `0..100` 夹爪载荷。

### L2 不负责

- 不做 L2-04 的投影算法，不做 TF，不读 CLI/permit，不 import ROS，不写 Topic。

### 本 L3 在 L2 中的位置

```text
依赖 deploy_041 的 C3/C4/C7。产出 C4 供 deploy_043 B2 打包，最终由 deploy_044 B3 调用。
```

### 必读 L2 设计文档

- L1 边界/协作 Markdown。
- 目标 L2 `agent_context/00_INDEX.md`、`01`、`02`、`03`、`03a`、`04`、`05`、`06_types`、`07_config`、`09_service`、`10_runtime`、`11_ui`。
- HTML 不是任务来源。

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 类型 | 已有能力 | 差距 | 复用 |
|---|---|---|---|---|---|
| `split_bimanual_action` | `common/src/pi05/common/robot/action_spec.py:42-52` | 计算函数 | 旧 14D 拆分 | ACT 是 TCP7+TCP7+2 夹爪 | 仅结构复用 |
| `hand_command_to_trigger` | `common/src/pi05/common/robot/action_spec.py:55-59` | 计算函数 | 300..1000 -> 0..1 | 当前为 0..1 -> 0..100，方向相反 | 不复用 |
| `_filter_joint_target` | `deploy/.../pi05_bridge_node.py:82-94` | 计算+状态更新 | joint clamp | 安全与输出混杂 | 不复用 |

### 必须保留的启发

- 先验证完整单步契约，再一次性返回强类型 payload，不返回部分结果。

### 禁止照搬

- 旧 14D、joint 输出、旧夹爪量纲、clip/双尺度猜测、bridge 状态。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `service/action_output_adapter.py`。
- C9 `require_publishable_action`：仅 `PASS/ADJUSTED` + 非空 `ActionSpec`，复核 16D/finite/爪域；`REJECTED` 抛稳定契约错误。
- C10 `build_arm_pose_target`：TCP7 + 非空单一 `pose_frame_id` -> C3，不做 TF。
- C11 `map_gripper_command`：按 C7 线性映射 `[0,1] -> [0,100]`，越域直接失败。
- B1 按 C9 -> C10×2 -> C11×2 -> C4 的顺序组织；任一失败无部分 C4。
- 更新 service 稳定导出与纯函数测试。

### 本次不做

- 不实现 B2/B3、ROS message/status/publisher/deadband。
- 不修改 `SafetyGuard`、`ActionSpec` 或 C1-C7 契约语义。

### 函数 / class 策略

```text
B1 和 C9-C11 全部是模块级无状态函数；不创建 class。
```

## 7. 六层产物落点

| 层 | 涉及 | 路径 | 职责 |
|---|---|---|---|
| service | 是 | `src/model_deploy/act/service/action_output_adapter.py` | B1/C9-C11 纯 RAM 转换 |
| tests | 是 | `src/model_deploy/act/tests/service/test_action_output_adapter.py` | G04-G06 |
| types/config | 只读 | deploy_041 产物 | 输入/输出契约 |
| repo/runtime/ui | 否 | — | 无产物 |

### 对应六层设计文档

| 文档 | 内容 |
|---|---|
| `09_service层设计.md` | B1/C9-C11 签名、失败和边界 |
| `06_types层设计.md` | 只读 C3/C4 |
| `07_config层设计.md` | 只读 C7 |
| `08_repo层设计.md` / `10_runtime层设计.md` / `11_ui层设计.md` | 本 L3 不落产物 |

## 8. 文件内 3.5 层功能微元

| 文件 | 微元 | 类型 | 输入 | 输出 | 副作用 | 验收 |
|---|---|---|---|---|---|---|
| `action_output_adapter.py` | B1 | 编排函数 | SafetyResult+C7 | C4 | 无 | G04-G06 |
| 同上 | C9 | 计算函数 | SafetyResult | ActionSpec/异常 | 无 | G04/G05 |
| 同上 | C10 | 计算函数 | TCP7+frame | C3 | 无 | G06 |
| 同上 | C11 | 计算函数 | gripper+C7 | float 0..100 | 无 | G05/G06 |

## 9. 实施步骤

1. 先编写 PASS/ADJUSTED/REJECTED、16D 分段、finite、frame 与夹爪边界测试。
2. 实现 C9-C11，再实现 B1 编排。
3. 更新 `service/__init__.py`，运行局部测试与 service 回归。

## 10. 允许修改

- `src/model_deploy/act/service/action_output_adapter.py`
- `src/model_deploy/act/service/__init__.py`
- `src/model_deploy/act/tests/service/test_action_output_adapter.py`

## 11. 禁止修改

- `src/model_deploy/act/types/`、`config/`、`repo/`、`runtime/`、`ui/`
- `src/model_deploy/pi05/`、`pi05_old/`
- HTML/L1 文档与其他 L2 任务

## 12. 验证方式

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/service/test_action_output_adapter.py -v
```

| 层级 | 需要 | PASS |
|---|---|---|
| unit/import | 是 | G04-G06 全通过，无 ROS import |
| dry-run/mock | 否 | B3 后续覆盖 |
| real-robot | 否 | 无外部副作用 |

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 场景 | G04-G06 |
| 能力 | safe/adjusted 16D -> 完整 transport-neutral C4 |
| 后续 | deploy_043 消费 C4；deploy_044 组织输出 |

## 13. 必读上下文

- 阶段四工作流、ACT 落点约束、L3 模板、目标 L2 `agent_context/00-11`。
- `types/action_publish.py`、`types/action_spec.py`、`types/safety_result.py`、`config/schema.py`。
- Pi0.5 对应 action spec/codec 仅作只读参考。

## 14. 执行要求

- 身份校验：路径、文件名、正文、dispatch 均为 `deploy_042`；前置 `deploy_041` 可用。
- 测试优先，不得将纯 RAM 边界扩展到 ROS/硬件。

## 15. 成功标准

- [x] PASS/ADJUSTED 返回完整 C4，REJECTED/非法输入稳定失败。
- [x] 左右 TCP 分段、单一 frame、xyzw 和米制数值不变。
- [x] `0/0.5/1 -> 0/50/100`，50/100 输入失败而不 clip。
- [x] 无部分 C4，无可变跨调用状态，无 ROS 依赖。

## 16. 回滚方式

```text
删除 action_output_adapter.py 与局部测试，还原 service/__init__.py 导出。
```

## 17. 完成后交接

- 登记实际 pytest 命令/结果与边界扫描；不自行归档、commit 或 push。

## 18. 执行摘要（deploy_042，sub-agent 填写）

执行 Agent：deploy_042 单一 L3 实现 + 本地验证，已于 `feat/model_deploy/l2-05-action-publisher` 分支完成。

### 身份校验（实现前）

- 文件名 / 正文编号 / dispatch `task_id` 均为 `deploy_042` ✓
- `group=l2-05-action-publisher`、`branch=feat/model_deploy/l2-05-action-publisher`，与当前分支一致 ✓
- 路径位于 `03_tasks/task/active/l2-05-action-publisher/` ✓
- 依赖 `deploy_041`（C3/C4/C7 契约，已在树中 `types/action_publish.py`、`config/schema.py`）可用，未修改。

### 改动文件（均在允许修改列表内）

- 新增 `src/model_deploy/act/service/action_output_adapter.py`（B1 + C9-C11 + `ActionPublishContractError`）
- 修改 `src/model_deploy/act/service/__init__.py`（稳定导出 4 个函数 + 错误类）
- 新增 `src/model_deploy/act/tests/service/test_action_output_adapter.py`（G04-G06，18 例）

未触碰 `types/`、`config/`、`repo/`、`runtime/`、`ui/`、`pi05/`、`pi05_old/`，无 B2/B3、无 ROS import、无 CLI/launch/HTML。

### 验证命令与结果

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/service/test_action_output_adapter.py -v
# => 18 passed in 0.09s

PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/service/
# => 188 passed in 1.82s（含本 L3 18 例，无回归）
```

### 覆盖与证据

- §15 四项目标全部达成：PASS/ADJUSTED -> 完整 C4；REJECTED/非有限/爪域越界/形状错误稳定抛 `ActionPublishContractError`；左右 TCP7 按 `[0:7]/[7:14]` 分段、共用 `config.pose_frame_id`、xyzw 与米制数值原样保留（float32 round-trip）；gripper `0/0.5/1 -> 0/50/100`，`50/100/-0.1/1.5` 越域失败不 clip；任一子步骤异常不构造部分 C4；模块无 ROS import、无可变跨调用状态。
- 纯 RAM 边界：函数全部为模块级无状态函数，不创建 class；不 import rclpy/geometry_msgs/std_msgs；不 publish。

### 未验证项

- 下游消费（deploy_043 B2 打包、deploy_044 B3 调用 `build_topic_payloads`）属其他 L3，本 L3 不覆盖。
- 真机/ROS runtime 行为不在 `direct-local` 范围；本 L3 真机风险等级 `none`。
- 验收卡片 `deploy_042_验收卡片.md` 的标准化判定（含静态边界扫描）尚未运行，需主 Agent 派发验收 sub-agent。

### 版本/依赖

- pytest 7.4.4；numpy 已作为依赖引入（ActionSpec 已 import numpy，本 L3 复用，仅用于 shape/finite 转换）。


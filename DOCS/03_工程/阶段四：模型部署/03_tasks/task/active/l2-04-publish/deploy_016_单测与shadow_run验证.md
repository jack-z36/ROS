# L3 微元改造任务：L2-04 单测与 shadow-run 验证

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-04 action 处理与发布层
来源 Delta：D12/D13/D17/D18（action 发布 + safety + 可观测性 + mode）
L3 编号：deploy_016
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-publish/deploy_016_单测与shadow_run验证.md`
改造类型：test-coverage
真机风险等级：dry-run-only（shadow-run 发 policy_action 但不接 bridge/真机）
L2 Git 分支：model_deploy-l2-04-publish
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish
对应 L2 运行验收场景：[S1, S2, S3, S4]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-publish/deploy_016_验收卡片.md
验收模式：direct-local
辅助验收模式：['env-blocked']
本地验收是否必须：true
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_016
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-publish/deploy_016_单测与shadow_run验证.md
  group: l2-04-publish
  branch: model_deploy-l2-04-publish
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish
  acceptance_scenarios: [S1, S2, S3, S4]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-publish/deploy_016_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [env-blocked]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish/logs
  wave: 3
  parallel_group: l2-04-publish-p3
  depends_on: [deploy_013, deploy_014, deploy_015]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/tests/test_safety_guard_tcp.py
      - src/model_deploy/pi05/deploy/tests/test_publish_dry_run.py
    modules:
      - tests.publish
    config_keys: []
    runtime_modes:
      - dry-run
      - shadow-run
    hardware_paths: []
  robot_risk: dry-run-only
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
为 L2-04 的 safety_guard + deploy_node 发布侧编写单测和 dry-run/shadow-run 验证：safety 检查单测（NaN/非归一化 quaternion/越界 width 被拒绝）、policy_action 发布 dry-run（16D 正确）、shadow-run（policy_action 有输出但 bridge 不接）、mode 三档切换。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D12/D13/D17/D18 综合 |
| 变更对象 | action 发布 + safety + 可观测性 + mode |
| AS-IS 契约 | 无针对 TCP+width policy-action 的 safety 单测和 shadow-run 验证。 |
| TO-BE 契约 | safety 单测覆盖六步检查；dry-run/shadow-run 验证 policy_action 16D 发布 + mode 三档。 |
| 兼容性要求 | 新增测试。 |
| 回滚要求 | 删除测试文件。 |

### 所属 L2 改造工作包

- L2 名称：L2-04 action 处理与发布层
- 本 L3 在该 L2 中的位置：最后一个，验收前三者。L2-04 完成标志。
- 本 L3 完成后解锁：L2-04 整体完成，L2-05（硬件执行栈）可开始。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| 被测 safety_guard | safety_guard.py（deploy_013 改后） | policy-action 六步检查 | 缺单测 | 否（只测） |
| 被测 deploy_node 发布侧 | pi05_vla_deploy_node.py（deploy_014/015 改后） | 单路 policy_action + metrics | 缺 dry-run/shadow 验证 | 否 |
| 测试目录 | deploy/tests/（008/012 建过） | config/assembly 测试 | 加 publish/safety 测试 | 是（新建） |

### 必须保留的现有行为

- 不改被测代码。

### 已知风险

- shadow-run 会发 `/pi05/policy_action` topic。如果 bridge（L2-05）未启动，topic 有输出但无下游消费——这正是 shadow-run 的语义（验证 Pi05 侧，不动真机）。安全。
- safety_guard 单测需要构造 ObservationSnapshot stub（提供 TCP anchor）。用简单 stub 绕过完整 snapshot 构造。
- 不接真模型（Q2），_control_tick 的 dry-run 验证用 stub policy 或只验证 publish 调用（mock publisher）。

## 6. 真实改造边界

### 本次允许做

**新建 `test_safety_guard_tcp.py`：**
- `test_action_shape_16d`：16D 通过，非 16D 拒绝。
- `test_finite_check`：含 NaN/Inf 拒绝。
- `test_quaternion_normalization`：非归一化 quaternion（模长≠1）拒绝；归一化通过。
- `test_tcp_delta_limit`：TCP 位移超 max_tcp_delta_m 拒绝。
- `test_gripper_width_range`：width ∉ [0,1] 拒绝。
- `test_valid_action_passes`：合法 16D 通过，返回 SafetyResult(accepted=True)。

**新建 `test_publish_dry_run.py`（用 stub/mock）：**
- `test_policy_action_16d`：mode=shadow，_control_tick 发 Float32MultiArray，data 长度 16，段序正确（用 mock publisher 捕获）。
- `test_dry_run_no_publish`：mode=dry-run，policy_action 不发布。
- `test_metrics_fields`：_publish_metrics 含新字段（observation_ready/policy_ready 等）+ 原计数。

### 本次不做

- 不改被测代码。
- 不接真模型/真机（Q2）。
- 不做 ROS 端到端完整 launch（留给后续 runbook）。

### 明确禁止修改

- 禁止改被测代码。
- 禁止为测试改 safety_guard/deploy_node 签名。

### Adapter / 直接修改策略

```text
纯新增测试。safety 单测用 stub ObservationSnapshot（TCP anchor）。publish 测试用 mock publisher 捕获 Float32MultiArray。不接真机。
```

## 7. 实施步骤

1. **确认 import 路径**：safety_guard/deploy_node 能否独立 import。
2. **写 test_safety_guard_tcp.py**：六步检查 case，用 stub snapshot 提供 TCP anchor。
3. **写 test_publish_dry_run.py**：mock publisher 捕获 policy_action；mode 三档切换。
4. **运行 pytest**。

## 8. 验证方式

### 自动化验收命令

```bash
cd src/model_deploy/pi05 && python3 -m pytest tests/deploy/test_safety_guard_tcp.py pi05/deploy/tests/test_publish_dry_run.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | safety 六步单测 + publish mock | 全部 pass |
| dry-run | 是 | policy_action 16D + mode dry-run 不发 | 断言通过 |
| shadow-run | 是（逻辑层） | mode shadow 发 policy_action（mock 验证） | mock 捕获 16D |
| fake-policy | 否（Q2） | — | — |
| real-policy | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不触发真机。dry-run-only/shadow-run 逻辑层：用 mock + stub，不接硬件、不接真模型、bridge 不启动。
- 是否会真实发送命令：否（mock publisher 不真发 ROS）
- 默认是否关闭真实发送：是
- 回滚到原始发送路径：不适用

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish/logs/
```
## 9. 允许修改

- 新建 `src/model_deploy/pi05/deploy/tests/test_safety_guard_tcp.py`
- 新建 `src/model_deploy/pi05/deploy/tests/test_publish_dry_run.py`

## 10. 禁止修改

- 被测代码（safety_guard/deploy_node/shared_buffer）。
- 任何非测试文件。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D12/D13/D17/D18 + Q4 三档 + Q5 检查）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-04-action处理与发布层.md`

### 必读代码

1. `src/model_deploy/pi05/deploy/src/pi05/deploy/runtime/safety_guard.py`（deploy_013 改后）
2. `src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（deploy_014/015 改后）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_013/014/015（全部完成）。
2. 同组已完成：deploy_013/014/015。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_013,014,015]` 全部完成。

```text
确认 import 路径
→ 写 safety 单测（stub snapshot）
→ 写 publish mock 测试
→ pytest 通过
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] safety 六步检查单测通过。
- [ ] policy_action 16D 发布 mock 验证通过。
- [ ] mode dry-run 不发 / shadow 发 验证通过。
- [ ] metrics 新字段验证通过。
- [ ] pytest 全部通过。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：删除 test_safety_guard_tcp.py, test_publish_dry_run.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新建测试 case 数、pytest 结果、stub/mock 策略说明、成功标准勾选、真机影响（dry-run/shadow 逻辑层，不触发真机）、回滚、未做事项（没改被测代码、没做 ROS 端到端 launch）、后续建议（L2-04 完成，可开始 L2-05 硬件执行栈——真机风险最高）。

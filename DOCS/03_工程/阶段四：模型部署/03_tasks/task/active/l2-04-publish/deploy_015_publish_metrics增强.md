# L3 微元改造任务：_publish_metrics 字段增强

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-04 action 处理与发布层
来源 Delta：D17（可观测性 status/metrics 迁移与字段扩展）
L3 编号：deploy_015
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-publish/deploy_015_publish_metrics增强.md`
改造类型：behavior-change
真机风险等级：none

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_015
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-publish/deploy_015_publish_metrics增强.md
  group: l2-04-publish
  branch: model_deploy
  wave: 2
  parallel_group: l2-04-publish-p2
  depends_on: [deploy_014]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_016]
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py
      - pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py
    modules:
      - pi05.deploy.ros_nodes.pi05_vla_deploy_node
      - pi05.deploy.runtime.shared_buffer
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
增强 _publish_metrics 的 metrics payload 字段：新增 observation_ready/policy_ready/缺失字段诊断/最近 policy_action 发布时间，并确认 RuntimeMetrics（shared_buffer）能提供这些数据，保留原有计数（inference/latency/chunk/safety/published）。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D17 |
| 变更对象 | Observability |
| AS-IS 契约 | `_publish_metrics`（pi05_vla_deploy_node.py:213-218）发 /pi05_vla/metrics（JSON：inference/latency/chunk/safety/published 计数）。RuntimeMetrics（shared_buffer.py）持有这些计数。 |
| TO-BE 契约 | /pi05/metrics 保留原计数，新增 observation_ready/policy_ready/缺失字段诊断/最近 policy_action 发布时间。topic 名改 /pi05/*（跟随 config）。 |
| 兼容性要求 | 增量（不删原计数）。 |
| 回滚要求 | git 回退。 |

### 所属 L2 改造工作包

- L2 名称：L2-04 action 处理与发布层
- 本 L3 在该 L2 中的位置：第二个，依赖 deploy_014（发布侧改完，metrics publisher 就位）。
- 本 L3 完成后解锁：deploy_016（shadow-run 验证 metrics）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `_publish_metrics` | pi05_vla_deploy_node.py:213-218 | 发 JSON metrics（原计数） | 加新字段 | 是 |
| `RuntimeMetrics` | shared_buffer.py:31-40 | 持有 inference/latency/chunk/safety/published 计数 | 加 observation_ready/policy_ready/last_action_publish_ts | 是 |
| status publisher | _create_publishers | /pi05_vla/status | topic 名跟随 config（deploy_006 已改 /pi05/*） | 否（topic 来源跟随） |

### 必须保留的现有行为

- 原计数（inference/latency/chunk/safety/published）不删。
- RuntimeMetrics 的 dataclass 结构。
- metrics JSON 序列化方式。

### 已知风险

- RuntimeMetrics 是 shared_buffer.py 的类，改它可能影响 InferenceWorker/ControlLoop 的写入。新增字段用默认值（如 None/0.0），不破坏现有写入。
- observation_ready/policy_ready 的数据来源：collector 的 snapshot 是否就绪、policy 是否推理就绪。需 deploy_node 能拿到这些状态。

## 6. 真实改造边界

### 本次允许做

- `RuntimeMetrics`（shared_buffer.py:31-40）：新增字段 `observation_ready: bool`、`policy_ready: bool`、`last_action_publish_ts: float | None`、`missing_fields: list[str] | None`（默认值，不破坏现有）。
- `_publish_metrics`（pi05_vla_deploy_node.py:213-218）：metrics JSON 增加新字段（从 RuntimeMetrics 取）；保留原计数。

### 本次不做

- 不改 InferenceWorker/ControlLoop 的写入逻辑（新字段由 deploy_node 在 _control_tick/_publish_metrics 时填充，或留默认）。
- 不改 _create_publishers（deploy_014 已改 publisher）。
- 不补单测（deploy_016 做）。

### 明确禁止修改

- 禁止删原计数。
- 禁止改 InferenceWorker/ControlLoop 核心调度。
- 禁止改 RuntimeMetrics 的现有字段。

### Adapter / 直接修改策略

```text
增量修改。新字段追加（默认值），不破坏现有。回滚靠 git。
```

## 7. 实施步骤

1. **改 RuntimeMetrics**（shared_buffer.py）：加 observation_ready/policy_ready/last_action_publish_ts/missing_fields（默认值）。
2. **改 _publish_metrics**（pi05_vla_deploy_node.py:213-218）：JSON 加新字段。
3. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
sb = open('pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py', encoding='utf-8').read()
dn = open('pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py', encoding='utf-8').read()
for f in ['observation_ready','policy_ready','last_action_publish_ts']:
    assert f in sb, f'{f} missing in RuntimeMetrics'
    assert f in dn, f'{f} missing in _publish_metrics'
# 原计数保留
for f in ['inference','latency','safety','published']:
    assert f in sb, f'original metric {f} should be preserved'
print('deploy_015 验收通过: metrics字段增强, 原计数保留')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 字段断言 | 上述命令通过 |
| dry-run | 否（deploy_016 做） | — | — |

### 真机风险控制

不适用。

## 9. 允许修改

- `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（_publish_metrics 部分）
- `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py`（RuntimeMetrics）

## 10. 禁止修改

- 原计数字段。
- InferenceWorker/ControlLoop 核心。
- _create_publishers（deploy_014 已改）。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D17）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-04-action处理与发布层.md`

### 必读代码

1. `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（deploy_014 改后）
2. `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py`

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_014（发布侧改完）。
2. 同组已完成：deploy_013、deploy_014。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_014]` 已完成。

```text
最小复现 / 测试（AST 断言）
→ 最小实现（加字段）
→ 验证通过
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] RuntimeMetrics 新增 4 个字段。
- [ ] _publish_metrics JSON 含新字段。
- [ ] 原计数保留。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- shared_buffer.py pi05_vla_deploy_node.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新增字段、验收结果、成功标准勾选、真机影响（无）、回滚、未做事项（没改 InferenceWorker/ControlLoop 写入逻辑）、后续建议（deploy_016 shadow-run）。

# L3 微元改造任务：L2-03 数据装配 dry-run 验证

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-03 数据装配 Service 层
来源 Delta：D3/D7/D8/D9/D10（数据装配链路的端到端验证）
L3 编号：deploy_012
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_012_dry_run验证.md`
改造类型：test-coverage
真机风险等级：dry-run-only

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_012
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_012_dry_run验证.md
  group: l2-03-assembly
  branch: model_deploy
  wave: 3
  parallel_group: l2-03-assembly-p3
  depends_on: [deploy_009, deploy_010, deploy_011]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/tests/test_assembly_dry_run.py
    modules:
      - tests.assembly
    config_keys: []
    runtime_modes:
      - dry-run
    hardware_paths: []
  robot_risk: dry-run-only
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
编写并运行 dry-run 验证脚本/测试，确认数据装配链路（ROS topic 数据 → observation_collector.snapshot → encoded_state 16D → policy_loader._build_batch）端到端正确，不接真机、不接真模型（用构造数据或 stub）。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D3/D7/D8/D9/D10 综合（装配链路验证） |
| 变更对象 | 数据装配 Service 层端到端 |
| AS-IS 契约 | 无针对 TCP+width 装配链路的集成测试。 |
| TO-BE 契约 | dry-run 下：构造鱼眼图像 + TCP PoseStamped + gripper Float32 数据 → collector 生成 snapshot → encoded_state 16D → batch 构建。验证装配正确。 |
| 兼容性要求 | 新增测试，不改被测代码。 |
| 回滚要求 | 删除测试文件。 |

### 所属 L2 改造工作包

- L2 名称：L2-03 数据装配 Service 层
- 本 L3 在该 L2 中的位置：最后一个，验收前三者（collector/订阅侧/build_batch）。L2-03 完成标志。
- 本 L3 完成后解锁：L2-03 整体完成，L2-04（action 发布）可开始。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| 被测 collector | observation_collector.py（deploy_009 改后） | TCP+width 装配 | 缺集成测试 | 否（只测） |
| 被测 build_batch | policy_loader.py（deploy_011 改后） | encoded_state + image 拼 batch | 缺集成测试 | 否 |
| 被测 state_codec | state_codec.py（deploy_002 改后） | encode 16D | 缺集成测试 | 否 |
| 测试目录 | deploy/tests/（deploy_008 建过） | config 单测 | 加装配集成测试 | 是（新建） |

### 必须保留的现有行为

- 不改被测代码。

### 已知风险

- **dry-run 不接真模型**（Q2：不做 fake-policy）。所以 _build_batch 的测试要么用 stub policy_runtime（mock image_names + 不真推理），要么只测到 snapshot→encoded_state 层（不进 _build_batch 的推理）。
- 建议拆两层验证：①collector snapshot + encoded_state 维度（纯单测，不需模型）；②build_batch 拼 batch 结构（用 stub Pi05PolicyRuntime，image_names=鱼眼，不调真推理）。
- deploy_node 订阅侧（deploy_010）的集成测试需要 rclpy 环境（发布构造的 PoseStamped/Float32/Image topic），可能较重。本 L3 优先做 collector + build_batch 的直接单元集成（绕过 ROS），ROS 层的端到端留给后续 dry-run runbook。

## 6. 真实改造边界

### 本次允许做

**新建 `test_assembly_dry_run.py`：**
- `test_collector_snapshot_tcp_width`：构造 collector，喂 update_tcp_pose(左右 7D) + update_gripper_width(左右 float) + update_image(鱼眼)，调 snapshot，断言非 None，encoded_state 维度 16，images 含两路鱼眼。
- `test_collector_missing_tcp_blocks_snapshot`：只喂图像不喂 TCP，snapshot 返回 None。
- `test_collector_tactile_disabled_first_version`：不喂触觉，snapshot 仍生成（触觉不列入必需）。
- `test_encoded_state_16d`：encode_bimanual_state(include_tactile=False) 输出 16D。
- `test_build_batch_structure`（用 stub）：构造最小 Pi05PolicyRuntime stub（image_names=鱼眼，state_normalizer=identity），喂 ObservationSnapshot，调 _build_batch，断言 batch 含 observation.state(16D) + observation.images.left_fisheye/right_fisheye + task。

### 本次不做

- 不改被测代码（collector/policy_loader/state_codec）。
- 不做真模型推理测试（Q2 不接真模型）。
- 不做 ROS 端到端（发布 topic → node → snapshot），留给后续 runbook。
- 不测 deploy_node 发布侧（L2-04 范围）。

### 明确禁止修改

- 禁止改被测代码。
- 禁止为测试改 collector/policy_loader 的签名。

### Adapter / 直接修改策略

```text
纯新增测试。用 stub 避开真模型（_build_batch 用 stub Pi05PolicyRuntime）。collector 直接喂数据（绕过 ROS）。
```

## 7. 实施步骤

1. **确认测试 import 路径**：collector/state_codec/policy_loader 能否独立 import（不触发 deploy_node 级联）。
2. **写 collector snapshot 测试**：构造数据，测 snapshot 生成 + encoded_state 16D + missing 阻断 + 触觉 disabled。
3. **写 build_batch stub 测试**：构造 stub Pi05PolicyRuntime（image_names=鱼眼，normalizer=identity），测 _build_batch 输出结构。
4. **运行 pytest**。

## 8. 验证方式

### 自动化验收命令

```bash
cd pi05_test/pi05 && python3 -m pytest pi05/deploy/tests/test_assembly_dry_run.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | pytest 全部通过 | 所有 case pass |
| dry-run | 是 | snapshot 生成 + encoded_state 16D + batch 结构 | 断言通过 |
| fake-policy | 否（Q2 不做） | — | — |
| real-policy | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不触发真机动作。dry-run-only：用构造数据，不接硬件、不接真模型、不发命令。`robot_risk: dry-run-only`。

- 是否会真实发送命令：否
- 默认是否关闭真实发送：是（不涉及发送）
- 回滚到原始发送路径：不适用（测试文件删除即可）

## 9. 允许修改

- 新建 `pi05_test/pi05/deploy/tests/test_assembly_dry_run.py`

## 10. 禁止修改

- 被测代码（collector/policy_loader/state_codec/deploy_node）。
- 任何非测试文件。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D3/D7/D8/D9/D10 + Q2 不做 fake-policy）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-03-数据装配Service层.md`

### 必读代码

1. `pi05_test/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py`（deploy_009 改后）
2. `pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py`（deploy_011 改后）
3. `pi05_test/pi05/common/src/pi05/common/data/state_codec.py`（deploy_002 改后）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_009/010/011（全部完成）。
2. 同组已完成：deploy_009/010/011。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_009,010,011]` 全部完成。

```text
确认 import 路径（避开 deploy_node 级联）
→ 写 collector 测试（直接喂数据）
→ 写 build_batch stub 测试（stub policy_runtime）
→ pytest 通过
```

如果 import 失败（级联问题），记录，不强行改 __init__。

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] collector snapshot 测试通过（TCP+width 装配 + 16D）。
- [ ] missing 阻断测试通过。
- [ ] 触觉 disabled 测试通过（第一版不依赖触觉）。
- [ ] build_batch stub 测试通过（batch 结构含鱼眼 + 16D state）。
- [ ] pytest 全部通过。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：删除 test_assembly_dry_run.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新建测试 case 数、pytest 结果、stub 策略说明（如何避开真模型）、成功标准勾选、真机影响（dry-run-only，不触发真机）、回滚、未做事项（没改被测代码、没做 ROS 端到端、没接真模型）、后续建议（L2-03 完成，可开始 L2-04 action 发布）。

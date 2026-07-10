# deploy_025 验收反馈 -- Round 1

## 元数据

| 字段 | 值 |
|---|---|
| L3 编号 | `deploy_025` |
| 所属 L2 | `l2-03-act-inference` |
| 验收卡片 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_025_验收卡片.md` |
| 验收轮次 | 1 |
| 验收日期 | 2026-07-10 |
| 验收模式 | `direct-local` + `static-review` |
| 验收结论 | `PASS_LOCAL` |

## 1. 产物存在性检查

| 产物 | 路径 | 存在 |
|---|---|---|
| Gate 集成测试 | `src/model_deploy/act/tests/integration/test_l2_03_gate.py` | PASS |
| 验收脚本 | `src/model_deploy/act/scripts/l2_03_verify.sh` | PASS |

## 2. 验收脚本运行结果

```text
=== L2-03 ACT Inference 验收 ===

[ types ]
  PASS  types.action_chunk_contract  ActionChunk 只含合法 physical actions

[ config / repo ]
  PASS  boundary.reuse_only  未新增 config/repo 产物

[ service ]
  PASS  service.batch.tensorize_state  state 表达转换
  PASS  service.batch.normalize_state  state 只归一化一次
  PASS  service.batch.bind_images  图像按 policy key 绑定
  PASS  service.batch.add_dimension  batch 维度添加
  PASS  service.batch.assemble  ACT batch 组装
  PASS  service.batch.device  设备对齐
  PASS  service.policy.predict_chunk  只调用 policy chunk API
  PASS  service.policy.error_propagation  前向失败传播
  PASS  service.output.raw_shape  raw 输出结构检查
  PASS  service.output.unbatch  batch 维移除
  PASS  service.output.unnormalize  action 反归一化
  PASS  service.output.float32_cpu  CPU float32 转换
  PASS  service.output.final_contract  最终输出契约检查
  PASS  service.output.no_repair  不裁剪、不补齐、不 clamp
  PASS  service.full_chain  snapshot 到 ActionChunk 闭环
  PASS  service.policy.no_select_action  select_action 未被调用
  PASS  service.observation_batch_full  阶段一批次准备全量测试
  PASS  service.postprocess_full  阶段三后处理全量测试
  PASS  service.inference_full  ActInferenceService 全量测试

[ integration ]
  PASS  service.error_stops_chain  各阶段失败时链停止
  PASS  gate.full_chain  三阶段闭环 Gate 集成测试

[ runtime / ui / boundary ]
  PASS  boundary.no_resource_io  无 bundle/checkpoint/path 加载器
  PASS  boundary.no_runtime_state  无 worker/queue/cursor/metrics
  PASS  boundary.no_ros_or_hardware  无 ROS/硬件交互
  PASS  boundary.no_safety_or_smoothing  无 safety/smoothing/clamp/IK
  PASS  boundary.only_allowed_layers  文件只在 types/service/tests

────────────────────────────────
  28 PASS / 0 FAIL / 0 BLOCKED  (共 28 标签)
```

退出码: **0**

## 3. PASS_LOCAL 条件逐项判定

| # | 条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | `test_l2_03_gate.py` 存在于指定路径 | PASS | 文件已读取，19 个测试用例，覆盖全部 Gate 场景 |
| 2 | `l2_03_verify.sh` 存在于指定路径 | PASS | 文件已读取，285 行 bash 脚本 |
| 3a | `service.full_chain` 测试覆盖 | PASS | `TestFullChain` 类 5 个测试：完整闭环、sentinel 传递、normalizer 方向/次数、select_action 未调用、无运行时元数据 |
| 3b | `service.error_stops_chain` 测试覆盖 | PASS | `TestErrorStopsChain` 类 8 个测试：阶段 1/2/3 分别失败、longer/shorter/2D/NaN 输出拒绝 |
| 3c | `service.policy.predict_chunk` 测试覆盖 | PASS | `test_select_action_not_called` 使用 `StubPolicyWithRaisingSelectAction` |
| 3d | `service.output.no_repair` 测试覆盖 | PASS | `test_no_repair_longer/shorter/2D/nan_output_rejected` 四个测试 |
| 3e | `boundary.no_resource_io` 静态扫描 | PASS | `test_no_resource_io` 使用 AST import 检查 + stripped-source regex |
| 3f | `boundary.no_runtime_state` 静态扫描 | PASS | `test_no_runtime_state` 使用 AST + regex |
| 3g | `boundary.no_ros_or_hardware` 静态扫描 | PASS | `test_no_ros_or_hardware` 使用 AST + regex |
| 3h | `boundary.no_safety_or_smoothing` 静态扫描 | PASS | `test_no_safety_or_smoothing` 使用 regex |
| 3i | `boundary.only_allowed_layers` 文件列表检查 | PASS | `test_only_allowed_layers` 检查 config/repo/runtime/ui/launch 无 L2-03 文件 |
| 4a | 分层输出格式 | PASS | `[ types ]`, `[ config / repo ]`, `[ service ]`, `[ runtime / ui / boundary ]` 四个分层块 |
| 4b | 每行格式 `PASS|FAIL  <label>  <description>` | PASS | 全部 28 行符合格式 |
| 4c | FAIL 行紧随定位块 | N/A | 无 FAIL 行 |
| 4d | 末尾汇总 | PASS | `28 PASS / 0 FAIL / 0 BLOCKED (共 28 标签)` |
| 5 | 退出码 0 | PASS | `echo $?` 返回 0 |
| 6 | 无 FAIL 标签 | PASS | 28 行全部 PASS |
| 7 | 产物路径与 L3 声明一致 | PASS | 产落在 `tests/integration/` 和 `scripts/`，符合声明 |
| 8 | 未修改 deploy_021~004 产物 | PASS | `git diff --name-only` 不包含 ACT 源文件；ACT 源文件全部为 untracked (新增) |
| 9 | 未修改 `pi05/`、其他层、dispatch | PASS | `git status -- src/model_deploy/pi05/` 无输出 |

## 4. static-review 补充检查

- 集成测试全部使用 stub policy + recording normalizer + sentinel snapshot，不依赖真实 bundle、GPU 或 ROS -- PASS
- 静态边界扫描同时使用 AST import 检查（明确无误）和 stripped-source regex（排除 docstring/注释干扰），扫描方式可靠 -- PASS
- 代码审查未发现未声明的副作用、全局状态或越界依赖 -- PASS

## 5. BLOCKED 条件检查

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 缺少 Python3/pytest/torch/bash | 否 | 全部可用，verify.sh 运行成功 |
| 真实 policy 补验缺 bundle/GPU | 不适用 | 本 L3 真机风险等级 `none`，不涉及 policy 补验 |

## 6. FAIL_LOCAL 条件检查

无任一 FAIL 条件命中：
- 无必须项 FAIL
- verify.sh 退出码 0
- 集成测试不依赖真实 bundle/GPU/ROS
- 静态边界扫描使用 AST + stripped-source regex，可靠
- 未修改 deploy_021~004 产物

## 7. 结论

**PASS_LOCAL**

deploy_025 的 L2-03 Gate 集成测试与验收脚本已通过全面验收。所有 28 个标签 PASS，退出码 0，产物落点正确，未越界修改。

后续操作建议：
- 主 Agent 将 L3 任务文件从 `03_tasks/task/active/l2-03-act-inference/deploy_025_Gate集成测试与验收脚本.md` 移动到 `03_tasks/completed/l2-03-act-inference/`
- 进入 L2 Gate 验收流程（`l2-03-act-inference_整体验收卡片.md`）

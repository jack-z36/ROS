# L2-02 整体验收卡片：传感器订阅与 ObservationSnapshot 组装闭环

> [!info] 归属
> - 所属 L2：`l2-02-observation-snapshot`
> - L2 设计目录：`DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/`
> - L2 功能边界：`agent_context/01_L2功能边界.md`
> - L2 验收机制：`agent_context/04_L2验收机制.md`
> - 人类验收机制：`agent_context/05_人类验收机制.md`
> - 本卡片是 L2 Gate 总验收入口，用于确认 L2-02 全部 required L3 已达到可解释状态、L2 Gate 通过后进入人类验收。

## 1. L2 目标

从外部 observation topics 接收图像、TCP pose 和 gripper state，生成完整、合法、新鲜的 `ObservationSnapshot`，写入 latest-only observation buffer。

## 2. Required L3 清单

| L3 ID | 名称 | 状态要求 | 验收模式 |
|---|---|---|---|
| deploy_011 | 观测类型定义 ObservationState / ObservationSnapshot / ObservationFreshnessResult | PASS_LOCAL | direct-local |
| deploy_012 | 观测收集器 ObservationCollector | PASS_LOCAL | direct-local |
| deploy_013 | 图像预处理 preprocess_observation_image | PASS_LOCAL | direct-local |
| deploy_014 | 观测缓冲区 ObservationBuffer 与 ObservationMetrics | PASS_LOCAL | direct-local |
| deploy_015 | ROS 适配器 ObservationRosAdapter | PASS_LOCAL + env-blocked（真实 ROS 订阅） | direct-local + env-blocked |
| deploy_016 | L2 Gate 集成测试与验收脚本 l2_02_verify.sh | PASS_LOCAL | direct-local |

## 3. L2 Gate 运行命令

```bash
# 运行全部 L3 单元测试
python3 -m pytest src/model_deploy/act/tests/types/test_observation.py src/model_deploy/act/tests/service/test_observation_collector.py src/model_deploy/act/tests/service/test_image_preprocess.py src/model_deploy/act/tests/runtime/test_observation_buffer.py src/model_deploy/act/tests/ui/test_observation_ros_adapter.py -v

# 运行 L2 Gate 集成测试
python3 -m pytest src/model_deploy/act/tests/integration/test_l2_02_gate.py -v

# 运行统一验收脚本
bash src/model_deploy/act/scripts/l2_02_verify.sh
```

## 4. L2 Gate PASS 条件

- [ ] 全部 6 个 L3 达到 PASS_LOCAL（或可解释的 BLOCKED_ENV）。
- [ ] deploy_016 集成测试全部通过。
- [ ] `l2_02_verify.sh` 输出无 FAIL（BLOCKED 可接受），退出码 0。
- [ ] 12 个验证标签全部覆盖且可追溯。
- [ ] 无 ROS 环境下 types/service/runtime/ui 全模块栈可 import。
- [ ] L2-02 源码无越界（不包含推理、ActionChunk、SafetyGuard、硬件命令、ControlLoop）。
- [ ] config/ 和 repo/ 目录无 L2-02 新增产物。
- [ ] ObservationSnapshot.encoded_state 为 16D。
- [ ] 所有产物路径符合六层落点约束。

## 5. L2 Gate FAIL 条件（任一命中则 Gate 不通过）

- 任一 required L3 未达到 PASS_LOCAL（且无法解释为 BLOCKED_ENV 或 DEFER_TO_L2_GATE）。
- deploy_016 集成测试失败。
- `l2_02_verify.sh` 输出含 FAIL。
- ObservationSnapshot 被放在 service/ 或 runtime/（非 types/）。
- snapshot() 在缺字段时仍生成对象。
- stale timeout 不生效。
- ROS adapter 的 import 使无 ROS 环境无法运行 service/runtime 单测。
- L2-02 中出现模型推理、action chunk 消费、safety 或硬件发送逻辑。

## 6. Blocked 项

| blocked 项 | 类型 | 处理 |
|---|---|---|
| 真实 ROS topic 订阅验收 | `BLOCKED_ENV` | deploy_015 的 adapter.real_subscription 标签；不影响 mock Gate 通过，等待 ROS 环境补验 |
| L2-01 state codec / DeployConfig 未落地 | `BLOCKED_ENV` 或上游未完成 | L2-02 使用 mock state codec 完成核心逻辑测试；真实 codec 替换等待 L2-01 就绪 |
| 真机传感器未接入 | `BLOCKED_HARDWARE_EXPECTED` | 本 L2 不要求 real-robot 通过 |

## 7. L2 Gate 场景覆盖矩阵

| 场景 | 描述 | 覆盖 L3 | Gate 验证方式 |
|---|---|---|---|
| S1 | Mock 全字段 snapshot 组装 | deploy_011, deploy_012, deploy_014, deploy_016 | test_full_mock_pipeline, l2_02_verify.sh |
| S2 | 缺字段 / 过期拒绝 | deploy_012, deploy_014, deploy_016 | test_missing_field_pipeline, test_stale_pipeline, l2_02_verify.sh |
| S3 | 图像预处理 | deploy_013, deploy_016 | preprocess.image 标签, l2_02_verify.sh |
| S4 | Latest-only buffer 语义 | deploy_014, deploy_016 | buffer.latest_only / buffer.max_age 标签, l2_02_verify.sh |
| S5 | 无 ROS 环境可 import | deploy_015, deploy_016 | test_import_without_ros, l2_02_verify.sh |
| S6 | 边界不越界 | deploy_016 | test_boundary_no_overreach, l2_02_verify.sh |

## 8. 人类验收

L2 Gate 通过后，按 `agent_context/05_人类验收机制.md` 执行人类验收：

```text
验收人：
验收日期：
验收结论：[ ] 已通过  [ ] 不通过
签字位置：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/验收结果.md
```

## 9. Git 合入条件

只有满足以下全部条件，才允许合入 `model_deploy`：

- [ ] L2 Gate 通过（本卡片所有 PASS 条件满足）。
- [ ] 人类验收签字通过。
- [ ] 真机风险记录完整。
- [ ] Git 状态符合 `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`。

# 验收卡片：deploy_060 L2-05 发布失败追因契约

> [!info] 归属
> - 所属调度组：l2-06-control-loop
> - 接口 owner：l2-05-action-publisher
> - 验收 Agent 只读；只用进程内 FakeNode，不连接 driver。

| L3 编号 | `deploy_060` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_060_L2-05发布失败追因契约.md |
| 源码 | action_publish types、ActionPublisher、facades 与 tests |
| 设计 | L2-05 HTML + agent_context |
| 前置 | deploy_051/052 PASS_LOCAL |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_action_publish.py \
  src/model_deploy/act/tests/ui/test_action_publisher_messages.py \
  src/model_deploy/act/tests/ui/test_action_publisher.py \
  src/model_deploy/act/tests/integration/test_l2_05_gate.py -v
```

```bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-05-action-publisher_单步Action到执行器Topic适配发送闭环'
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] invalid input 不再触发 __r AttributeError，异常类型/消息稳定。
- [ ] ActionPublishResult 的 reason/failure_stage/failed_topic 六 outcome invariant 不可违反。
- [ ] policy/status/四路 command 每个故障点均有精确 provenance 且无后续 command 泄漏。
- [ ] request echo、startup switch、permit echo 完整。
- [ ] /act/command/status 仍是 L2-05 单 writer；status failure 不伪造 result。
- [ ] L2-05 HTML 与 agent_context 已同步。

### FAIL_LOCAL

负向 outcome 无 reason、猜 stage、具体 I/O 无 topic、失败后继续 command、双 writer、fail-open、设计双轨或任一 required test 失败。

### BLOCKED

真实 ROS/driver/hardware 只允许在 local PASS 后补记外部阻断；本卡不得自动发送真实 command。

## 4. L2 Gate 贡献

| 场景 | G03/G07 |
|---|---|
| 贡献 | P0-10、六 outcome provenance、L2-06 C19 reducer 所需事实 |
| 未完成影响 | deploy_053/054/055 不得执行 |

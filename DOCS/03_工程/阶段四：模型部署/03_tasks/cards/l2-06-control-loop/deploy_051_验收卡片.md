# 验收卡片：deploy_051 推理通道与运行指标基础

> [!info] 归属
> - 所属 L2：l2-06-control-loop
> - 对应 L3：deploy_051
> - 验收模式：direct-local
> - 验收轮次上限：3
> - 验收 Agent 只读，不修改源码、任务、dispatch 或 Git。

| L3 编号 | `deploy_051` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_051_推理通道与运行指标基础.md |
| 允许查看 | inference_channel.py、runtime_metrics.py、runtime facade、对应 unit tests、执行摘要 |
| 前置 | dispatch 已由主 Agent 从 blocked 显式解锁 |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py -v
```

```bash
! rg -n "InferenceRequest|InferenceResult|LatestQueue|RuntimeMetricsSnapshot" \
  src/model_deploy/act/types
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] C1/C2 frozen、success/error XOR、时间/id/error 边界完整。
- [ ] LatestQueue 无参且 CAPACITY=1；replace、timeout、spurious wakeup、close、重复 close、closed put/take 全通过。
- [ ] 正常 drop 与 shutdown clear 分开计数。
- [ ] RuntimeMetrics 线程安全，snapshot 不暴露 mutable dict/reference。
- [ ] facade additive，observation_buffer import 不回归；types 无 runtime 污染。

### FAIL_LOCAL

- 缺文件/测试、关闭后仍交付残留、worker waiter 无法唤醒、mutable snapshot、facade 回归或任一命令非零退出。

### BLOCKED

- required local 验收没有环境型 BLOCKED；上游 P0 未放行时本任务保持 dispatch blocked，不启动验收。

## 4. L2 Gate 贡献

| 场景 | G04 |
|---|---|
| 贡献 | RUNTIME_ENVELOPE_CONTRACT、LATEST_QUEUE_CLOSE、RUNTIME_REASON_PRESERVED 的基础 |
| 未完成影响 | deploy_052～055 不得执行 |


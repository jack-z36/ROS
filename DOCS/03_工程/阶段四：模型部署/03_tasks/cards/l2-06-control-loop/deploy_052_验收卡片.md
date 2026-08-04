# 验收卡片：deploy_052 InferenceWorker 串行异步执行

> [!info] 归属
> - 所属 L2：l2-06-control-loop
> - 对应 L3：deploy_052
> - 验收模式：direct-local
> - 验收轮次上限：3
> - 验收 Agent 只读。

| L3 编号 | `deploy_052` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_052_InferenceWorker串行异步执行.md |
| 允许查看 | inference_worker.py、runtime facade、channel/metrics依赖、worker tests、线程/调用探针 |
| 前置 | deploy_051 PASS_LOCAL 且 dispatch 已解锁 |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py \
  src/model_deploy/act/tests/runtime/test_inference_worker.py -v
```

```bash
! rg -n "SafetyGuard|ActionPublisher|create_timer|create_publisher|rclpy|yaml|torch\\.load" \
  src/model_deploy/act/runtime/inference_worker.py
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] policy 最大并发始终为 1；慢 policy 不要求 timer等待。
- [ ] 普通异常形成 terminal error result，worker 存活并可处理下一请求。
- [ ] start-to-start 限频、clock nonfinite/negative/regression 由 fake clock 确定验证。
- [ ] stop-before/while/after policy、closed result queue和late result均有界收敛。
- [ ] worker 不拥有 request策略、cursor、fallback、safety、permit或publish。

### FAIL_LOCAL

- 线程泄漏、异常杀 worker、未产 error result、busy wait、shutdown 后写 queue、吞 BaseException 或任一测试/扫描失败。

### BLOCKED

- required local 验收无环境型 BLOCKED；前置未满足时保持 dispatch blocked。

## 4. L2 Gate 贡献

| 场景 | G05 |
|---|---|
| 贡献 | WORKER_TICK_NONBLOCKING、WORKER_SERIAL_POLICY、WORKER_ERROR_RECOVERY、WORKER_SHUTDOWN |
| 未完成影响 | deploy_053～055 不得执行 |


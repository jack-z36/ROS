# 验收卡片：deploy_053 ControlLoop 中央调度状态机

> [!info] 归属
> - 所属 L2：l2-06-control-loop
> - 对应 L3：deploy_053
> - 验收模式：direct-local
> - 辅助模式：downstream-l2
> - 验收轮次上限：3
> - 验收 Agent 只读；只允许进程内 FakePublisher。

| L3 编号 | `deploy_053` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_053_ControlLoop中央调度状态机.md |
| 允许查看 | control_loop.py、runtime facade、control loop tests、真实 Safety/Publish public contracts、执行摘要 |
| 前置 | deploy_051/052 与 deploy_056～060 全部 PASS_LOCAL |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py \
  src/model_deploy/act/tests/runtime/test_inference_worker.py \
  src/model_deploy/act/tests/runtime/test_control_loop.py -v
```

```bash
! rg -n "publish_safe|emit_fallback|\\.filter\\(|\\.accepted|ControlDecision|ControlCommand|smoothstep|blend|aligned|RTC|rclpy|create_publisher" \
  src/model_deploy/act/runtime
```

## 3. PASS / FAIL / DEFER

### PASS_LOCAL

- [ ] tick 非阻塞且最多一个 outstanding；matching success/error 都终结 request。
- [ ] active/pending/prefetch/horizon/continue/age/乱序由 fake clock完整覆盖。
- [ ] normal/continue/hold action 与 previous 深复制，重复发布不刷新 source age。
- [ ] 每 candidate safety=1、publish<=1；非 safety 失败不伪造 SafetyResult。
- [ ] 六 outcome 与 failure provenance/echo 矩阵正确；矛盾锁存 PUBLISH_RESULT_INVARIANT。
- [ ] deferred reason、output/runtime fault和safe-stop可恢复边界符合设计。
- [ ] 无 UI/ROS/status writer/smoothing/假接口污染。

### FAIL_LOCAL

- 并发 request、过期 action、越 horizon、第二次 fallback publish、权限/安全 echo矛盾未锁存、PARTIAL/FAILED 后继续 command，或任一测试/扫描失败。

### DEFER_TO_L2_GATE

- ROS timer与真实 topic可见性由 deploy_055 补验；这不替代本卡required local PASS。

## 4. L2 Gate 贡献

| 场景 | G06-G07 |
|---|---|
| 贡献 | worker correlation、chunk/cursor、fallback、safety/publish reducer与fail-closed latches |
| 未完成影响 | deploy_054/055 不得执行；上游接缝失败退回 deploy_056～060 owner task |

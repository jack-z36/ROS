# 验收卡片：deploy_054 ActDeployNode 原子装配与生命周期

> [!info] 归属
> - 所属 L2：l2-06-control-loop
> - 对应 L3：deploy_054
> - 验收模式：direct-local
> - 辅助模式：env-blocked / hardware-blocked
> - 验收轮次上限：3
> - 验收 Agent 只读；hardware-blocked 不能写成真机通过。

| L3 编号 | `deploy_054` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_054_ActDeployNode原子装配与生命周期.md |
| 允许查看 | act_deploy_node.py、ui/runtime facades、preflight/node/main tests、FakeNode handle/thread记录 |
| 前置 | deploy_051-053 与 deploy_056～060 全部 PASS_LOCAL |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/ui/test_startup_preflight.py \
  src/model_deploy/act/tests/ui/test_act_deploy_node.py \
  src/model_deploy/act/tests/ui/test_act_deploy_main.py -v
```

```bash
PYTHONPATH=src python3 -c "import model_deploy.act.ui; import model_deploy.act.runtime; import model_deploy.act.ui.act_deploy_node"
```

```bash
! rg -n "publish_safe|emit_fallback|_input_spec|torch\\.load|yaml\\.safe_load|create_subscription\\(|/act/command/status|smoothstep|blend" \
  src/model_deploy/act/ui/act_deploy_node.py
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] B12 identity、16D/chunk/camera/image/queue/clock/permit contracts全部通过。
- [ ] preflight先于output/worker/timer，worker先于两个timer。
- [ ] subscription/preflight/publisher/worker-start/timer每个失败点均无live handle/thread且保留原异常。
- [ ] 未start worker不join；正常shutdown=STOPPED，join timeout=SHUTDOWN_TIMEOUT/FAIL。
- [ ] permit缺失/异常deny-by-default；C20唯一写/act/metrics。
- [ ] production main real-only，CLI/exit/finally/import/facade无副作用或循环。

### FAIL_LOCAL

- 私下加载/转换/猜配置、timer提前、cleanup覆盖原异常、双writer、fail-open、未start join或任一required测试缺失/失败。

### BLOCKED

- 真 ROS graph缺失可在deploy_055记BLOCKED_ENV；permit/driver/E-stop缺失记对应外部BLOCKED。
- required FakeNode local composition不能因环境缺失跳过；hardware-blocked 不能写成真机通过。

## 4. L2 Gate 贡献

| 场景 | G08 |
|---|---|
| 贡献 | STARTUP_PREFLIGHT_CANONICAL_SPEC、STARTUP_ATOMIC_ORDER、ENTRYPOINT、UI timer/permit/metrics/shutdown |
| 未完成影响 | deploy_055 不得执行 |

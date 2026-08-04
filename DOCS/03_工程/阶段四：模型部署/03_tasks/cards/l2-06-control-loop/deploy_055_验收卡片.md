# 验收卡片：deploy_055 L2 Gate 跨模块集成与验收脚本

> [!info] 归属
> - 所属 L2：l2-06-control-loop
> - 对应 L3：deploy_055
> - 验收模式：direct-local
> - 辅助模式：env-blocked / hardware-blocked
> - 验收轮次上限：3
> - 验收 Agent 只读；hardware-blocked 不能写成真机通过。

| L3 编号 | `deploy_055` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_055_L2Gate跨模块集成与验收脚本.md |
| 允许查看 | 三条real-chain tests、test_l2_06_gate.py、fixture、verify script、L2-06 HTML/agent_context、完整输出、acceptance记录 |
| 前置 | deploy_051-054 与 deploy_056～060 全部 PASS_LOCAL |

## 2. 必跑命令

```bash
bash src/model_deploy/act/scripts/l2_06_verify.sh \
  --scope local --policy fake \
  --config src/model_deploy/act/tests/fixtures/l2_06_fake.yaml
```

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/integration/test_observation_to_inference_real_chain.py \
  src/model_deploy/act/tests/integration/test_control_loop_publish_chain.py \
  src/model_deploy/act/tests/integration/test_control_loop_fallback_matrix.py \
  src/model_deploy/act/tests/integration/test_l2_06_gate.py -v
```

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] real-chain tests使用production contracts，只替换policy/ROS node/clock/permit等外部边界。
- [ ] verify标签、分层、FAIL定位、summary、exit code和skip allowlist符合04验收合同。
- [ ] P0-01～10、A1-A5、C1-C26、六outcome、fallback、startup/shutdown、HTML alignment均有证据。
- [ ] L2-06 agent_context 与 HTML 已按最终源码同步，结构校验和旧接口负向扫描均通过。
- [ ] local与baseline为0 FAIL；代码/fixture/script缺失从不转BLOCKED。
- [ ] acceptance结果保存实际config/policy mode/命令/日志/未验证项。

### FAIL_LOCAL

- fake掉业务对象、缺required文件、unknown skip、command泄漏、结果标签/退出码错误、HTML仍STALE或任一baseline失败。

### BLOCKED

- local PASS后，ROS不可用可记BLOCKED_ENV；bundle不可取得可记BLOCKED_ARTIFACT；permit/driver/E-stop/硬件/授权按稳定外部reason记录。
- hardware-blocked 不能写成真机通过；BLOCKED不替代local PASS。

## 4. L2 Gate 贡献

| 场景 | G01-G12 |
|---|---|
| 贡献 | 完整L2 Gate、唯一verify入口、外部补验与人类签字证据 |
| 未完成影响 | L2-06不可进入人类验收或Git合入 |

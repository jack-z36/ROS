# 验收卡片：deploy_059 L2-04 安全端口与设计投影对齐

> [!info] 归属
> - 所属调度组：l2-06-control-loop
> - 接口 owner：l2-04-safety-guard
> - 主模式为静态合同复核；required local tests 仍必须执行。

| L3 编号 | `deploy_059` |
| 验收模式 | `static-review` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_059_L2-04安全端口与设计投影对齐.md |
| 源码/测试 | SafetyGuard、SafetyResult 只读审计；窄接口/Gate tests |
| 设计 | L2-04 HTML + agent_context |
| 前置 | deploy_051/052 PASS_LOCAL |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_safety_guard.py \
  src/model_deploy/act/tests/service/test_safety_primitives.py \
  src/model_deploy/act/tests/types/test_safety_result.py \
  src/model_deploy/act/tests/integration/test_l2_04_gate.py -v
```

```bash
! rg -n "SafetyResult\\.accepted|result\\.accepted|accepted=(True|False)|observation=" \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环'
```

## 3. 静态评审清单（PASS / FAIL）

### PASS_LOCAL

- [ ] exact filter_action(candidate, previous_safe_action=..., latest_observation=...) 被测试冻结。
- [ ] SafetyResult 只使用 PASS/ADJUSTED/REJECTED、action、findings。
- [ ] 无 accepted alias、跨 tick state、fallback、publish、permission ownership。
- [ ] L2-04 HTML 与 agent_context 无旧 accepted/observation 双轨。
- [ ] 若 production 本来正确，验收明确记录无行为改动。

### FAIL_LOCAL

签名漂移、accepted 兼容、旧参数名、source/doc 双轨、无机械回归、无理由改写算法或任一 required test 失败。

## 4. L2 Gate 贡献

| 场景 | G03/G07 |
|---|---|
| 贡献 | L2-06 B7 唯一真实 safety port 与三状态语义 |
| 未完成影响 | deploy_053/054/055 不得执行 |

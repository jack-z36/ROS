# 验收卡片：deploy_058 L2-03 Canonical Spec 消费接缝

> [!info] 归属
> - 所属调度组：l2-06-control-loop
> - 接口 owner：l2-03-act-inference
> - 验收 Agent 只读；不得把 runtime ownership 迁回 L2-03。

| L3 编号 | `deploy_058` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_058_L2-03CanonicalSpec消费接缝.md |
| 源码 | act_inference、observation_batch、postprocess seam、service facade 与 tests |
| 设计 | L2-03 HTML + agent_context |
| 前置 | deploy_051/052/056 PASS_LOCAL |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_observation_batch.py \
  src/model_deploy/act/tests/service/test_act_inference.py \
  src/model_deploy/act/tests/service/test_action_chunk_postprocess.py \
  src/model_deploy/act/tests/integration/test_l2_03_gate.py -v
```

```bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环'
```

## 3. PASS / FAIL / DEFER

### PASS_LOCAL

- [ ] constructor 显式接收 typed PolicyInputSpec；public property 保持 object identity。
- [ ] _derive_input_spec、Dict.get/default、private consumer seam 全部消失。
- [ ] predict_action_chunk 仍同步、一次 policy call、异常原样传播。
- [ ] ActionChunk 仍纯净且所有 shape/dtype/finite 合同通过。
- [ ] L2-03 无 worker/queue/thread/request/metrics/cursor/fallback。
- [ ] facade additive；HTML 与 agent_context 已同步。

### FAIL_LOCAL

重复派生 spec、metadata fallback、identity 失败、异步/runtime ownership 回流、ActionChunk 污染、设计双轨或任一回归失败。

### DEFER_TO_L2_GATE

真实 GPU/bundle 性能由 G11 补验；本卡只允许可控 fake policy 验证 production service contract。

## 4. L2 Gate 贡献

| 场景 | G03 |
|---|---|
| 贡献 | P0-04 service side、canonical spec identity、同步 inference capability |
| 未完成影响 | deploy_053/054/055 不得执行 |


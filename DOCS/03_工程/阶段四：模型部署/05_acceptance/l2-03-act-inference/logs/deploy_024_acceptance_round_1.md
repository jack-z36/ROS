# L3 Acceptance Feedback: deploy_024 ActInferenceService 与编排入口

- **验收轮次**: 1
- **验收 Agent**: stage4-l3-orchestrator acceptance sub-agent
- **验收模式**: `direct-local`
- **验收时间**: 2026-07-10

## 结论

**PASS_LOCAL**

## 验收命令与结果

```bash
PYTHONPATH="src:src/model_deploy/third_party/lerobot/src" python3 -m pytest src/model_deploy/act/tests/service/test_act_inference.py -v
```

结果: **20 passed, 0 failed, 0 skipped** (耗时 0.88s)

## PASS_LOCAL 逐项检查

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | `act_inference.py` 存在于 `src/model_deploy/act/service/act_inference.py` | PASS |
| 2 | `ActInferenceService` class 存在，字段只含 `_config/_state_normalizer/_action_normalizer/_policy/_input_spec/_device`（6 个私有字段，均为只读引用或派生值） | PASS (test_only_allowed_private_fields) |
| 3 | class 不含 forbidden 字段（snapshot/batch/raw_chunk/request_id/queue/cursor/metrics/retry/fallback 等） | PASS (test_no_forbidden_field_names) |
| 4 | 构造时从 policy RAM 元数据派生 `input_spec`（state_dim/camera_keys/image_shapes/action_dim/chunk_size） | PASS (test_input_spec_derived_from_policy_metadata) |
| 5 | 构造时验证：policy 暴露 `predict_action_chunk`；config/normalizer/policy 维度一致；不一致时构造失败 | PASS (TestContractValidation: 3 tests) |
| 6 | 总编排入口 `predict_action_chunk(observation: ObservationSnapshot) -> ActionChunk` 存在 | PASS |
| 7 | 总入口串联顺序：阶段一 → 阶段二 → 阶段三 | PASS (代码 review: prepare_observation_batch → run_act_inference → postprocess_action_chunk) |
| 8 | `run_act_inference` 在 `torch.no_grad()` 下只调用 `policy.predict_action_chunk(batch)` 一次 | PASS (代码 review) |
| 9 | 端到端 stub policy 测试：合法 snapshot → 返回只含 actions 的 `ActionChunk` | PASS (test_full_chain_returns_action_chunk) |
| 10 | `select_action` spy 测试：stub policy 的 `select_action` 设为 `raise`，总入口仍通过 | PASS (test_select_action_never_called) |
| 11 | state normalizer 只调 `normalize`，action normalizer 只调 `unnormalize` | PASS (test_state_normalizer_only_calls_normalize, test_action_normalizer_only_calls_unnormalize) |
| 12 | 两个 normalizer 各调用一次 | PASS (assert_called_once) |
| 13 | 异常传播测试：阶段一/二/三分别注入失败，后续阶段不执行 | PASS (TestFailurePropagation: 3 tests) |
| 14 | 不存在 `try/except: return None`、`return zeros` 或内部 retry | PASS (TestNoSwallowNoFallback: 3 tests) |
| 15 | pytest 全部通过，无 skip | PASS (20/20) |
| 16 | 正确 import deploy_021 的 `ActionChunk`、deploy_022 的 `prepare_observation_batch`、deploy_023 的 `postprocess_action_chunk` | PASS (代码 review) |
| 17 | 产物路径与 L3 声明一致 | PASS (`service/act_inference.py` + `tests/service/test_act_inference.py`) |
| 18 | 未修改 deploy_021~023 的产物文件 | PASS (git diff 确认无变更) |
| 19 | 未修改 `src/model_deploy/pi05/`、其他层文件或 dispatch | PASS (git diff 确认无变更) |

## 上游依赖确认

- deploy_021 (`action_chunk.py`): 已归档于 `completed/l2-03-act-inference/`，产物文件存在
- deploy_022 (`observation_batch.py`): 已归档于 `completed/l2-03-act-inference/`，产物文件存在
- deploy_023 (`action_chunk_postprocess.py`): 已归档于 `completed/l2-03-act-inference/`，产物文件存在

## FAIL_LOCAL 条件检查

所有 FAIL 条件均未命中：

- 无请求状态、queue、cursor、metrics 或 fallback 字段
- 未调用 `policy.select_action()`
- 两个 normalizer 未被交换使用
- 无 clamp/crop/pad/reorder 或 L2-04 安全逻辑
- 总入口内无 skip/retry/timeout/fallback 分支
- pytest 全部通过，无 skip
- 未修改 deploy_021~023 产物文件
- 未修改禁止修改的文件

## 归档指令

验收结论为 PASS_LOCAL。主 Agent 必须将 L3 任务文件从:

```
DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_024_ActInferenceService与编排入口.md
```

移动到:

```
DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-03-act-inference/deploy_024_ActInferenceService与编排入口.md
```

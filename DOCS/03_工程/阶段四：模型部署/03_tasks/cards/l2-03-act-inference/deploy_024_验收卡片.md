# 验收卡片：deploy_024 ActInferenceService 与编排入口

> [!info] 归属
> - 所属 L2：`l2-03-act-inference`
> - 对应 L3：`deploy_024`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_024` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_024_ActInferenceService与编排入口.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/service/act_inference.py`、`src/model_deploy/act/tests/service/test_act_inference.py`、执行摘要、pytest 输出 |
| 前置条件 | deploy_021、deploy_022、deploy_023 均已完成并通过验收 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit 测试（使用 stub policy + recording normalizer + sentinel snapshot）。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_act_inference.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `act_inference.py` 存在于 `src/model_deploy/act/service/act_inference.py`。
- [ ] `ActInferenceService` class 存在，字段只含：
  - [ ] `config: DeployConfig`（只读引用）
  - [ ] `state_normalizer: ActionStateNormalizer`（只读引用）
  - [ ] `action_normalizer: ActionStateNormalizer`（只读引用）
  - [ ] `policy`（只读引用，loaded ACT policy）
  - [ ] 派生的只读 `input_spec`（image feature keys、shapes、state_dim、action_dim、chunk_size、device）
- [ ] class 字段不含：`current/last snapshot`、`current batch`、`raw chunk`、`request_id`、`thread/event/queue/lock`、`active chunk/cursor/history`、`latency/error/metrics`、`retry/fallback state`。
- [ ] 构造时从 policy RAM 元数据派生 `input_spec`。
- [ ] 构造时验证：policy 暴露 `predict_action_chunk`；config/normalizer/policy 维度一致；不一致时构造失败。
- [ ] 总编排入口 `predict_action_chunk(observation: ObservationSnapshot) -> ActionChunk` 存在。
- [ ] 总入口串联顺序：阶段一（`prepare_observation_batch`）→ 阶段二（`run_act_inference`）→ 阶段三（`postprocess_action_chunk`）。
- [ ] `run_act_inference` 在 `torch.no_grad()` 下只调用 `policy.predict_action_chunk(batch)` 一次。
- [ ] 端到端 stub policy 测试：合法 snapshot + recording normalizer + deterministic stub policy → 返回只含 actions 的 `ActionChunk`。
- [ ] `select_action` spy 测试：stub policy 的 `select_action` 设为 `raise`，总入口仍通过，证明未调用 `select_action`。
- [ ] 两个 normalizer 调用方向正确：state normalizer 只调 `normalize`、action normalizer 只调 `unnormalize`。
- [ ] 两个 normalizer 各调用一次。
- [ ] 异常传播测试：阶段一/二/三分别注入失败，后续阶段不执行，异常原样或带上下文向上传播。
- [ ] 不存在 `try/except: return None`、`return zeros`、`return last_chunk` 或内部 retry。
- [ ] pytest 全部通过，无 skip。
- [ ] 正确 import deploy_021 的 `ActionChunk`、deploy_022 的阶段一函数、deploy_023 的阶段三函数。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 deploy_021~003 的产物文件。
- [ ] 未修改 `src/model_deploy/pi05/`、其他层文件或 dispatch。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- `ActInferenceService` 持有请求状态、queue、cursor、metrics 或 fallback 字段。
- 调用了 `policy.select_action()`。
- 两个 normalizer 被交换使用（state normalizer 做 unnormalize 或反之）。
- 存在 clamp/crop/pad/reorder 或 L2-04 安全逻辑。
- 总入口内有 skip/retry/timeout/fallback 分支。
- pytest 失败或有未解释的 skip。
- 修改了 deploy_021~003 的产物文件。
- 修改了禁止修改的文件。

### BLOCKED_ENV

- 缺少 Python3、pytest 或 torch，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S2（阶段一）、S3（阶段二）、S4（阶段三） |
| 场景覆盖 | 证明三阶段完整闭环：snapshot → ActionChunk |
| L2 Gate 依赖本 L3 | 是。本 L3 是 L2-03 所有业务能力的汇总串联点 |
| 未完成影响 | deploy_025 的集成测试无完整 service 可测；L2 Gate 无法证明三阶段闭环 |

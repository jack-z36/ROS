# 验收卡片：deploy_023 ActionChunk 后处理（一级阶段三）

> [!info] 归属
> - 所属 L2：`l2-03-act-inference`
> - 对应 L3：`deploy_023`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_023` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_023_ActionChunk后处理.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/service/action_chunk_postprocess.py`、`src/model_deploy/act/tests/service/test_action_chunk_postprocess.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit 测试（使用 recording action normalizer + sentinel raw tensor）。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_action_chunk_postprocess.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `action_chunk_postprocess.py` 存在于 `src/model_deploy/act/service/action_chunk_postprocess.py`。
- [ ] 实现一级阶段三函数 `postprocess_action_chunk(raw_chunk, action_normalizer, expected_chunk_size) -> ActionChunk`。
- [ ] 6 个计算微元均存在且可独立测试：
  - [ ] Raw 输出结构检查：仅接受 finite `(1, chunk_size, 16)` Tensor；`(1,N,14)`、`(1,N+1,16)`、`(2,N,16)`、`(N,16)` 等均拒绝。
  - [ ] Batch 维移除：只移除已验证 B=1 维，得到 `(N,16)`。
  - [ ] Action 反归一化：只调用 `action_normalizer.unnormalize()` 一次；输入是 `(N,16)`。
  - [ ] CPU float32 array 转换：得到 contiguous CPU numpy float32 `(N,16)`。
  - [ ] 最终输出契约检查：严格 `(chunk_size, 16)`、float32、有限值。
  - [ ] ActionChunk 构造：只写 actions，不写运行元数据。
- [ ] 无 clamp、crop、pad、repeat、reorder 行为。
- [ ] 无 quaternion 归一化、gripper clamp、TCP delta 限制（属于 L2-04）。
- [ ] 不调用 L2-04 安全检查。
- [ ] 错误 raw shape 时直接失败，不 squeeze/截断/补齐。
- [ ] raw/final action 含 NaN/Inf 时拒绝，不 clamp 或替换。
- [ ] action unnormalize 失败时拒绝，不把 normalized action 当 physical action 返回。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 正确 import deploy_021 的 `ActionChunk`。
- [ ] 未修改 `src/model_deploy/pi05/`、其他层文件或 dispatch。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- 存在 normalized action clamp（`torch.clamp` 到 `[-1,1]`）。
- 存在 chunk 截断（`[:chunk_size]`）或补齐（padding/repeat）。
- 存在 16D 段序重排。
- 把 `obs_time`、`infer_start_time` 等运行元数据写入 ActionChunk。
- pytest 失败或有未解释的 skip。
- 修改了禁止修改的文件。

### BLOCKED_ENV

- 缺少 Python3、pytest 或 torch，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S4（阶段三：ActionChunk 后处理） |
| 场景覆盖 | 证明 raw normalized tensor 可严格转换为 physical ActionChunk |
| L2 Gate 依赖本 L3 | 是。deploy_024 的 ActInferenceService 需要 import 本 L3 的阶段三函数 |
| 未完成影响 | deploy_024 无法完成三阶段串联 |

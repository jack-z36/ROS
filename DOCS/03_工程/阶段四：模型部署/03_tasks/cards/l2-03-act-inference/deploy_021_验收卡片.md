# 验收卡片：deploy_021 ActionChunk 类型定义

> [!info] 归属
> - 所属 L2：`l2-03-act-inference`
> - 对应 L3：`deploy_021`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_021` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_021_ActionChunk类型定义.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/types/action_chunk.py`、`src/model_deploy/act/tests/types/test_action_chunk.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit / import 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_action_chunk.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `action_chunk.py` 存在于 `src/model_deploy/act/types/action_chunk.py`。
- [ ] `ActionChunk` 是 `@dataclass(frozen=True)`，字段只包含 `actions: np.ndarray`。
- [ ] 构造时校验 `actions.ndim == 2`、`actions.shape[1] == 16`、`actions.dtype == np.float32`、全部元素有限、行数 > 0。
- [ ] 合法 `(N,16)` float32 finite array 可成功构造。
- [ ] rank 错误（如 `(16,)` 或 rank 3）抛异常，不静默接受。
- [ ] 最后一维不是 16（如 15 或 17）抛异常。
- [ ] 非 float32 dtype（如 float64、int）抛异常或在明确转换点统一后验证。
- [ ] 含 NaN 或 Inf 抛异常，不替换为零或 clamp。
- [ ] 空 chunk（0 行）抛异常。
- [ ] frozen 特性验证通过（修改字段抛 `FrozenInstanceError`）。
- [ ] `ActionChunk` 不含 `obs_time`、`infer_start_time`、`ready_time`、`action_dt`、`request_id`、`cursor`、`latency`、`error`、`metrics` 等运行元数据字段或方法。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致（`types/action_chunk.py` + `tests/types/test_action_chunk.py`）。
- [ ] 未修改 `src/model_deploy/pi05/`、其他层文件或 dispatch。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- ActionChunk 不是 frozen dataclass。
- 字段包含运行元数据（时间、request ID、cursor、error 等）。
- 存在 Pi0.5 的 `aligned_index()` 或类似 chunk 消费方法。
- pytest 失败或有未解释的 skip。
- 修改了禁止修改的文件（如 `action_spec.py` 语义变更）。
- 从 `config/` 或 `DeployConfig` import 来做构造校验（types 不能反向依赖 config）。

### BLOCKED_ENV

- 缺少 Python3 或 pytest，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S1（类型契约） |
| 场景覆盖 | 证明 ActionChunk 只含合法 physical actions，无运行元数据 |
| L2 Gate 依赖本 L3 | 是。ActionChunk 是 L2-03 到 L2-06 的唯一跨模块输出类型，所有下游 L3 依赖它 |
| 未完成影响 | deploy_022、deploy_023、deploy_024 无法正常 import，阻塞全部后续 L3 |

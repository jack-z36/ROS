# 验收卡片：deploy_022 Observation 批次准备（一级阶段一）

> [!info] 归属
> - 所属 L2：`l2-03-act-inference`
> - 对应 L3：`deploy_022`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_022` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_022_Observation批次准备.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/service/observation_batch.py`、`src/model_deploy/act/tests/service/test_observation_batch.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit 测试（使用 stub normalizer + sentinel snapshot）。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_observation_batch.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `observation_batch.py` 存在于 `src/model_deploy/act/service/observation_batch.py`。
- [ ] 实现一级阶段一函数 `prepare_observation_batch(snapshot, state_normalizer, input_spec, device) -> dict[str, Tensor]`。
- [ ] 7 个计算微元均存在且可独立测试：
  - [ ] 模型输入兼容性检查：合法 snapshot 通过；缺相机/错 shape 明确失败。
  - [ ] State tensor 表达转换：physical ndarray `(16,)` → CPU float32 Tensor `(16,)`，数值不改变。
  - [ ] State 数值归一化：只调用 `state_normalizer.normalize()` 一次，输出仍为 `(16,)`。
  - [ ] Image tensor 绑定：按完整 policy key（`observation.images.<camera>`）精确绑定；不按 dict 顺序猜测。
  - [ ] Batch 维度添加：state 变 `(1,16)`，image 变 `(1,C,H,W)`；不 squeeze 其他维。
  - [ ] ACT batch 组装：只含 `observation.state` 和必需 `observation.images.*`；无 `task`/`action`/时间字段。
  - [ ] Device 对齐：所有 tensor 位于 policy device；不改 snapshot、不缓存 batch、不自动切换 device。
- [ ] state tensor 表达转换与 state 数值归一化是两个独立可测函数（不得合并）。
- [ ] 不做图像 decode、resize、颜色转换、layout 修正或数值尺度修复。
- [ ] 不写 `task`、`action`、request/time 字段到 batch。
- [ ] 不移动 policy 或自动切换 device。
- [ ] pytest 全部通过（7 个微元独立测试 + 阶段一集成测试），无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 `src/model_deploy/pi05/`、其他层文件或 dispatch。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- state tensor 化与 normalize 合并为一个不可观察函数。
- 图像按 dict 顺序猜测相机而非按 policy feature key 精确映射。
- batch 包含 `task` 或 `action` 字段。
- 在 observation_batch.py 中做了图像像素级预处理。
- 调用了完整 LeRobot ACT preprocessor（含 NormalizerProcessorStep）。
- pytest 失败或有未解释的 skip。
- 修改了禁止修改的文件。
- 未 import deploy_021 的 `ActionChunk` 类型（但本文件不应需要 import ActionChunk，它产出 batch 而非 chunk）。

### BLOCKED_ENV

- 缺少 Python3、pytest 或 torch，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S2（阶段一：Observation 批次准备） |
| 场景覆盖 | 证明 snapshot 可正确转换为 policy device batch |
| L2 Gate 依赖本 L3 | 是。deploy_024 的 ActInferenceService 需要 import 本 L3 的阶段一函数 |
| 未完成影响 | deploy_024 无法完成三阶段串联 |

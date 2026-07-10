# deploy_022 验收反馈 — Round 1

## 元数据

| 字段 | 值 |
|---|---|
| 验收卡片 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_022_验收卡片.md` |
| 验收轮次 | 1 |
| 验收模式 | `direct-local` |
| 验收 Agent | acceptance sub-agent |
| 验收时间 | 2026-07-10 |
| 结论 | **PASS_LOCAL** |

## 验收过程

### 1. 静态检查

逐条对照验收卡片 PASS_LOCAL 条件：

- [x] `observation_batch.py` 存在于 `src/model_deploy/act/service/observation_batch.py`。
- [x] 实现一级阶段一函数 `prepare_observation_batch(snapshot, state_normalizer, input_spec, device) -> dict[str, Tensor]`。
- [x] 7 个计算微元均存在且可独立测试：
  - [x] 模型输入兼容性检查（`check_model_input_compatibility`）—— 合法 snapshot 通过；缺相机、错 shape、NaN/Inf state、NaN image 均明确失败。
  - [x] State tensor 表达转换（`tensorize_state`）—— physical ndarray `(16,)` 转为 CPU float32 Tensor `(16,)`，数值不改变。
  - [x] State 数值归一化（`normalize_state`）—— 只调用 `state_normalizer.normalize()` 一次，检查 shape 和有限值，输出仍为 `(16,)`。
  - [x] Image tensor 绑定（`bind_images`）—— 按完整 policy key（`observation.images.<camera>`）通过 `image_prefix` + `camera_name` 精确绑定；不按 dict 顺序猜测。
  - [x] Batch 维度添加（`add_batch_dim`）—— state 变 `(1,16)`，image 变 `(1,C,H,W)`；使用 `unsqueeze(0)`，不 squeeze 其他维。
  - [x] ACT batch 组装（`assemble_act_batch`）—— 只含 `observation.state` 和 `observation.images.*`；无 `task`/`action`/时间字段。
  - [x] Device 对齐（`align_to_device`）—— 所有 tensor 移动到 policy device；不改 snapshot、不缓存 batch、不自动切换 device。
- [x] `tensorize_state` 与 `normalize_state` 是两个独立可测函数（未合并）。
- [x] 不做图像 decode、resize、颜色转换、layout 修正或数值尺度修复。
- [x] 不写 `task`、`action`、request/time 字段到 batch。
- [x] 不移动 policy 或自动切换 device。
- [x] 产物路径与 L3 声明一致（`src/model_deploy/act/service/observation_batch.py`、`src/model_deploy/act/tests/service/test_observation_batch.py`）。
- [x] 未修改 `src/model_deploy/pi05/`、其他层文件或 dispatch。

### 2. direct-local 命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_observation_batch.py -v
```

结果：**29 passed in 1.02s**，无 skip，无失败。

测试覆盖详情：
- `TestCheckModelInputCompatibility`: 7 tests（正路径 + 6 条负路径：state dim、NaN、Inf、missing camera、shape mismatch、NaN image）
- `TestTensorizeState`: 3 tests（dtype/shape、值保持、非 view）
- `TestNormalizeState`: 4 tests（shape 保持、identity-like 值、shape 不匹配异常、NaN 输出异常）
- `TestBindImages`: 2 tests（policy key 绑定、missing camera 异常）
- `TestAddBatchDim`: 4 tests（state B=1、image B=1、多 tensor、值保持）
- `TestAssembleActBatch`: 3 tests（keys 正确、不含 task/action、自定义 state_key）
- `TestAlignToDevice`: 3 tests（设备对齐、shape 保持、空 batch）
- `TestPrepareObservationBatch`: 3 tests（完整 pipeline、compatibility 异常传播、missing camera 异常传播）

### 3. 禁止修改检查

- `src/model_deploy/act/service/` 下仅新增 `observation_batch.py`（未修改已有文件）。
- `src/model_deploy/act/types/` 下仅新增 `action_chunk.py`（deploy_021 产物，非 deploy_022 修改）。
- `src/model_deploy/pi05/`、`pi05_old/` 无修改。
- dispatch 文件无修改。

### 4. FAIL_LOCAL 条件排查

- state tensor 化与 normalize 未合并为单一函数 —— **通过**。
- 图像按 policy key 精确映射，未按 dict 顺序猜测 —— **通过**。
- batch 不含 `task` 或 `action` 字段 —— **通过**。
- `observation_batch.py` 中未做图像像素级预处理 —— **通过**。
- 未调用完整 LeRobot ACT preprocessor —— **通过**。
- pytest 全部通过，无 skip —— **通过**。
- 未修改禁止修改的文件 —— **通过**。

## 结论

**PASS_LOCAL**

所有 PASS_LOCAL 条件均已满足，无 FAIL_LOCAL 或 BLOCKED 条件命中。

## 后续动作

主 Agent 必须将匹配的 L3 任务文件从 active 归档至 completed：

```
from: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_022_Observation批次准备.md
to:   DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-03-act-inference/deploy_022_Observation批次准备.md
```

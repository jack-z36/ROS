# deploy_022 执行证据 -- L3 微元实现交付

## 执行时间

2026-07-10

## 任务身份

| 字段 | 值 |
|---|---|
| L3 编号 | deploy_022 |
| 所属 L2 | l2-03-act-inference |
| 改造类型 | source-adaptation |
| 分支 | feat/model_deploy/l2-03-act-inference |

## 产物

| 文件 | 路径 | 类型 |
|---|---|---|
| observation_batch.py | `src/model_deploy/act/service/observation_batch.py` | 新建 |
| test_observation_batch.py | `src/model_deploy/act/tests/service/test_observation_batch.py` | 新建 |

## 7 个微元实现

| 顺序 | 函数 | 类型 | 验收覆盖标签 |
|---|---|---|---|
| 1 | `check_model_input_compatibility` | 计算函数 | service.batch.compatibility |
| 2 | `tensorize_state` | 计算函数 | service.batch.tensorize_state |
| 3 | `normalize_state` | 计算函数 | service.batch.normalize_state |
| 4 | `bind_images` | 计算函数 | service.batch.bind_images |
| 5 | `add_batch_dim` | 计算函数 | service.batch.add_dimension |
| 6 | `assemble_act_batch` | 计算函数 | service.batch.assemble |
| 7 | `align_to_device` | 计算函数 | service.batch.device |

编排函数: `prepare_observation_batch(snapshot, state_normalizer, input_spec, device) -> dict[str, torch.Tensor]`

## 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_observation_batch.py -v
```

## 运行输出

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-7.4.4, pluggy-1.4.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/hit/ROS/worktrees/l2-03-act-inference
plugins: launch-testing-3.4.10, ament-copyright-0.17.5, ament-pep257-0.17.5,
         launch-testing-ros-0.26.11, ament-flake8-0.17.5, ament-lint-0.17.5,
         ament-xmllint-0.17.5, cov-4.1.0, colcon-core-0.20.1
collecting ... collected 29 items

src/model_deploy/act/tests/service/test_observation_batch.py::TestCheckModelInputCompatibility::test_passes_on_valid_snapshot PASSED [  3%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestCheckModelInputCompatibility::test_raises_on_wrong_state_dim PASSED [  6%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestCheckModelInputCompatibility::test_raises_on_nan_state PASSED [ 10%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestCheckModelInputCompatibility::test_raises_on_inf_state PASSED [ 13%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestCheckModelInputCompatibility::test_raises_on_missing_camera PASSED [ 17%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestCheckModelInputCompatibility::test_raises_on_image_shape_mismatch PASSED [ 20%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestCheckModelInputCompatibility::test_raises_on_nan_image PASSED [ 24%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestTensorizeState::test_converts_ndarray_to_float32_tensor PASSED [ 27%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestTensorizeState::test_preserves_values PASSED [ 31%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestTensorizeState::test_output_is_not_input_backed PASSED [ 34%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestNormalizeState::test_calls_normalizer_and_preserves_shape PASSED [ 37%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestNormalizeState::test_identity_normalizer_preserves_near_zero_values PASSED [ 41%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestNormalizeState::test_raises_on_contradictory_normalizer_shape PASSED [ 44%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestNormalizeState::test_rejects_nan_output PASSED [ 48%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestBindImages::test_binds_by_policy_key PASSED [ 51%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestBindImages::test_raises_on_missing_camera PASSED [ 55%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAddBatchDim::test_adds_b1_to_state_tensor PASSED [ 58%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAddBatchDim::test_adds_b1_to_image_tensor PASSED [ 62%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAddBatchDim::test_handles_multiple_tensors PASSED [ 65%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAddBatchDim::test_preserves_values PASSED [ 68%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAssembleActBatch::test_writes_state_and_image_keys PASSED [ 72%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAssembleActBatch::test_no_task_or_action_keys PASSED [ 75%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAssembleActBatch::test_custom_state_key PASSED [ 79%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAlignToDevice::test_moves_all_tensors_to_target_device PASSED [ 82%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAlignToDevice::test_preserves_tensor_shapes PASSED [ 86%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestAlignToDevice::test_empty_batch PASSED [ 89%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestPrepareObservationBatch::test_full_pipeline_on_cpu PASSED [ 93%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestPrepareObservationBatch::test_pipeline_propagates_compatibility_error PASSED [ 96%]
src/model_deploy/act/tests/service/test_observation_batch.py::TestPrepareObservationBatch::test_pipeline_propagates_missing_camera_error PASSED [100%]

============================== 29 passed in 0.94s ==============================
```

## 边界逐项确认

| # | 条件 | 结果 |
|---|---|---|
| 1 | state tensor 表达转换与 state 数值归一化是两个独立可测函数 | PASS: `tensorize_state` + `normalize_state` 独立存在 |
| 2 | 只调用 state_normalizer.normalize() 一次 | PASS: `normalize_state` 只调用一次 normalize |
| 3 | 图像不 resize、不换色、不缩放 | PASS: `bind_images` 仅做 tensor 化 + key 绑定 |
| 4 | batch dict 不含 task 字段 | PASS: `assemble_act_batch` 仅写 observation.state + observation.images.* |
| 5 | batch dict 不含 action 或 runtime metadata | PASS: 测试 `test_no_task_or_action_keys` 通过 |
| 6 | device 对齐产生新 tensor，不修改 snapshot、不缓存 batch | PASS: `align_to_device` 返回新 dict |
| 7 | 异常传播：任一微元失败则停止 | PASS: 集成测试 `test_pipeline_propagates_*` 通过 |
| 8 | 产物路径仅 `service/observation_batch.py` + 对应 test | PASS: 仅新建两个文件 |
| 9 | 未修改 `types/`、`config/`、`repo/`、`runtime/`、`ui/` | PASS: 仅 import 现有类型 |
| 10 | 未修改 `pi05/`、`pi05_old/` | PASS: 未触及 |
| 11 | `torch.no_grad()` 保护推理上下文 | PASS: `prepare_observation_batch` 使用 |
| 12 | pytest 全部通过 | PASS: 29/29 |

## L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S2 (阶段一: Observation 批次准备) |
| 本 L3 提供的运行能力 | snapshot 到 policy device batch 的完整转换 |
| 局部命令 | `python3 -m pytest src/model_deploy/act/tests/service/test_observation_batch.py -v` |
| 待后续 L3 补齐 | deploy_024 阶段二 policy 前向、deploy_023 阶段三后处理、总编排入口、集成 Gate |

## 后续动作

- 验收 sub-agent 应读取 `deploy_022_验收卡片.md` 执行 formal acceptance round 1。
- 主 Agent 在验收通过 (PASS_LOCAL) 后负责归档本 L3 任务文件。

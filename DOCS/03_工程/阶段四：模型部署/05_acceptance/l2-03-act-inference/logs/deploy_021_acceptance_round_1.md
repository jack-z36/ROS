# deploy_021 验收日志 -- Round 1

## 验收时间

2026-07-10

## 验收模式

`direct-local`

## 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_021_ActionChunk类型定义.md` |
| 源码 | `src/model_deploy/act/types/action_chunk.py` |
| 测试 | `src/model_deploy/act/tests/types/test_action_chunk.py` |

## 运行命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_action_chunk.py -v
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
collecting ... collected 15 items

src/model_deploy/act/tests/types/test_action_chunk.py::test_valid_construction PASSED [  6%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_valid_single_row PASSED [ 13%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_valid_large_chunk PASSED [ 20%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_invalid_rank_1d PASSED [ 26%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_invalid_rank_3d PASSED [ 33%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_invalid_dim_too_small PASSED [ 40%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_invalid_dim_too_large PASSED [ 46%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_invalid_dtype_float64 PASSED [ 53%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_invalid_dtype_int PASSED [ 60%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_nan_rejected PASSED [ 66%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_inf_rejected PASSED [ 73%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_neg_inf_rejected PASSED [ 80%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_empty_chunk_rejected PASSED [ 86%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_frozen_immutable PASSED [ 93%]
src/model_deploy/act/tests/types/test_action_chunk.py::test_no_runtime_metadata_fields PASSED [100%]

============================== 15 passed in 0.07s ==============================
```

## PASS_LOCAL 条件逐项检查

| # | 条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | `action_chunk.py` 存在于正确路径 | [x] PASS | 文件确认存在于 `src/model_deploy/act/types/action_chunk.py` |
| 2 | `@dataclass(frozen=True)`, 字段仅 `actions: np.ndarray` | [x] PASS | 源码第16行 `@dataclass(frozen=True)`，第28行 `actions: np.ndarray` |
| 3 | `__post_init__` 五项校验: ndim==2, shape[1]==16, dtype==float32, all finite, rows>0 | [x] PASS | 源码第30-56行含全部五项校验 |
| 4 | 合法 (N,16) float32 finite 可成功构造 | [x] PASS | test_valid_construction, test_valid_single_row, test_valid_large_chunk 均 PASS |
| 5 | rank 错误 (1D, 3D) 抛异常，不静默接受 | [x] PASS | test_invalid_rank_1d, test_invalid_rank_3d 均 PASS |
| 6 | 最后一维 != 16 (15, 17) 抛异常 | [x] PASS | test_invalid_dim_too_small, test_invalid_dim_too_large 均 PASS |
| 7 | 非 float32 dtype (float64, int32) 抛异常 | [x] PASS | test_invalid_dtype_float64, test_invalid_dtype_int 均 PASS |
| 8 | NaN / Inf 抛异常，不替换为零或 clamp | [x] PASS | test_nan_rejected, test_inf_rejected, test_neg_inf_rejected 均 PASS |
| 9 | 空 chunk (0行) 抛异常 | [x] PASS | test_empty_chunk_rejected PASS |
| 10 | frozen: 修改字段抛 FrozenInstanceError | [x] PASS | test_frozen_immutable PASS |
| 11 | 不含运行元数据字段/方法 | [x] PASS | test_no_runtime_metadata_fields PASS (11 项 forbidden 属性全部缺失) |
| 12 | pytest 全部通过，无 skip | [x] PASS | 15 passed, 0 skipped |
| 13 | 产物路径与 L3 声明一致 | [x] PASS | types/action_chunk.py + tests/types/test_action_chunk.py |
| 14 | 未修改 pi05/、其他层、dispatch | [x] PASS | `git diff --name-only` 对 act/、pi05/、pi05_old/ 无输出；action_spec.py 未被修改 |

## FAIL_LOCAL 条件检查 (全部清除)

| 条件 | 结果 | 说明 |
|---|---|---|
| 任一 PASS 条件不满足 | 未命中 | 14 项全部 PASS |
| ActionChunk 不是 frozen dataclass | 未命中 | 是 frozen dataclass |
| 字段含运行元数据 | 未命中 | 仅 `actions` 一个字段 |
| 存在 Pi0.5 aligned_index() 或类似方法 | 未命中 | 无任何方法 |
| pytest 失败或有未解释 skip | 未命中 | 全部 PASS |
| 修改了禁止文件 | 未命中 | 仅新建两个声明文件 |
| 从 config/ 或 DeployConfig import | 未命中 | 仅从 action_spec import ACTION_DIM |

## BLOCKED 检查

- `BLOCKED_ENV`: 不适用。Python 3.12.3 + pytest 可用，15 个测试全部运行通过。
- `BLOCKED_HARDWARE_EXPECTED`: 不适用。本 L3 为纯类型定义，无硬件依赖。

## 验收结论

**PASS_LOCAL**

全部 14 项 PASS_LOCAL 条件满足，0 项 FAIL_LOCAL 命中，0 项 BLOCKED。ActionChunk 类型定义正确，构造时五项校验完备，frozen 不可变，无运行元数据，15 个测试全部通过。

## 归档要求

主 Agent 须将匹配的 L3 任务文件从 active 移至 completed：

```
from: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_021_ActionChunk类型定义.md
to:   DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-03-act-inference/deploy_021_ActionChunk类型定义.md
```

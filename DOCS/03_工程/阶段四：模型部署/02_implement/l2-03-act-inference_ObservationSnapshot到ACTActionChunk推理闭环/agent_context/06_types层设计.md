# types 层设计：L2-03

## 1. 本 L2 不在该层新增源码产物

原因：

- `types/` 只放数据结构、常量、维度、段序、codec、result 对象，且不得依赖 ROS、不得加载模型。
- L2-03 的数据结构（`ActionChunk` / `InferenceRequest` / `ObservationSnapshot` / `LatestQueue` / `SharedBuffer` / `RuntimeMetrics`）携带 queue / lock / 后台线程语义，属于运行时状态对象，落 `runtime/shared_buffer.py`，不落 `types/`（见 `10_runtime层设计.md`）。
- 16D 维度校验复用 L2-01 的 `ActionSpec` / `StateSpec`，本 L2 不重复定义。

## 2. 复用的 types 产物

| 对象 | 来源 | 用途 |
|---|---|---|
| `StateSpec` / `ACTION_DIM=16` | L2-01 `types/state_spec.py` | 校验 encoded_state 是 16D |
| `ActionSpec` / `ensure_action_vector` | L2-01 `types/action_spec.py` | 校验 chunk 的 actions.shape[1]==16 |
| `ContractResult` | L2-01 `types/contract_result.py` | bundle/normalizer 契约结果（启动期 L2-01 已校验） |

## 3. 验收如何确认

- L2-03 不产生 `src/model_deploy/act/types/*.py` 产物。
- `rg` 检查 L2-03 范围内 `actions.shape[1]` 校验引用的是 L2-01 的 16D 常量，不是硬编码 14（Pi0.5 残余）。

## 4. 边界继承声明

本文件边界来自当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

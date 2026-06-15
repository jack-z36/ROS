# PoseFilterSampleRecord

## 定义

`PoseFilterSampleRecord` 是位姿滤波器对单个 pose 样本的样本级审计记录。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[位姿滤波器]]。

## 现实语义

它回答“这个 pose 样本是否参与滤波、滤波前后差异是多少、最终采用原值还是滤波值、为什么”。它是滤波审计记录，不是 MCAP 消息本体。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `sample_record_id` | string | 滤波样本记录 id |
| `sample_ref` | [[SignalSampleRef]] | 样本定位 |
| `segment_id` | string/null | 所属连续可靠片段 |
| `status` | enum string | `filtered` / `kept_original` / `skipped_boundary` / `filter_rejected_by_guard` |
| `original_pose` | object | 滤波前 [[CommonFrameTcpPose]] 值 |
| `filtered_pose` | object/null | 候选滤波值；未计算时为空 |
| `final_pose` | object | 最终向下游输出的 pose |
| `position_delta_m` | number/null | 滤波前后位置差 |
| `orientation_delta_deg` | number/null | 滤波前后姿态角度差 |
| `reason` | string | 保留、跳过或拒绝原因 |
| `config_ref` | string / [[PoseFilterConfig]] | 本样本使用的滤波配置引用 |

## 有效性规则

- 每个输入 pose 样本必须最多对应一条样本记录。
- `filtered` 状态必须有 `filtered_pose`，且 `final_pose == filtered_pose`。
- `filter_rejected_by_guard` 状态必须保留 `filtered_pose`，且 `final_pose == original_pose`。
- `kept_original` 和 `skipped_boundary` 必须写明 reason。
- pose 值必须包含位置和归一化四元数姿态。

## 上游来源

- [[PoseFilterInputSequence]]
- [[PoseFilterConfig]]
- [[SignalSampleRef]]

## 下游消费者

- [[PoseFilterResult]]
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_pose_filter`。

## 不负责

- 不承载完整序列 artifact。
- 不决定最终 mask。
- 不替代 [[SignalRepairSampleRecord]]。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 样本级审计是否长期全部保存 | v1 要求开发者检验产物完整保存；生产可后续压缩 |

## 相关链接

- [[PoseFilterResult]]
- [[PoseFilterSegmentSummary]]
- [[CommonFrameTcpPose]]

# SignalRepairRun

## 定义

`SignalRepairRun` 是数据补全器对连续异常样本形成的一次补全决策单元。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[数据补全器]]。

## 现实语义

虽然异常检测输出是点级的，但连续异常样本必须作为一个 run 统一补全，避免后一个异常点把前一个刚修复出来的值当作合法邻居。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `repair_run_id` | string | run id |
| `source_topic` | string | 来源 topic |
| `modality` | enum string | `pose` / `tactile` / `gripper` |
| `replacement_unit` | enum string | `pose.position` / `pose.orientation` / `pose.whole_pose` / `tactile.frame` / `gripper.value` |
| `sample_issue_ids` | list[string] | run 内样本级异常 id |
| `sample_refs` | list[[SignalSampleRef]] | run 内样本引用 |
| `status` | [[RepairDecisionStatus]] | run 级处理状态 |
| `repair_method` | [[RepairMethod]] | 实际修复方法，未修时为 `no_op` |
| `previous_neighbor_ref` | [[SignalSampleRef]]/null | run 外侧前合法邻居 |
| `next_neighbor_ref` | [[SignalSampleRef]]/null | run 外侧后合法邻居 |
| `reason` | string | 成功、拒绝或跳过原因 |
| `sample_records` | list[[SignalRepairSampleRecord]] | run 内样本级记录 |

## 有效性规则

- 聚合条件必须为同一 `source_topic + modality + replacement_unit + compatible suggested_action`。
- 样本必须 message_index 连续，或时间间隔小于配置阈值。
- run 不得跨越未处理的 [[MissingIntervalIssue]]。
- run 内只要出现 mixed repairability，整个 run 拒绝自动补全。
- 插值不得使用 run 内刚修复出的值作为邻居，只能使用 run 外侧合法邻居。

## 上游来源

- [[SampleReliabilityIssue]]
- [[MissingIntervalIssue]]
- [[SignalRepairPolicyConfig]]

## 下游消费者

- [[SignalRepairResult]]
- Parquet 标注与验证报告生成器。

## 不负责

- 不重新发现异常。
- 不新增、删除或重采样消息。
- 不写 MCAP_A。

## 相关链接

- [[SignalRepairSampleRecord]]
- [[RepairDecisionStatus]]
- [[RepairMethod]]

# RepairMethod

## 定义

`RepairMethod` 是数据补全器实际采用的修复方法枚举。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[数据补全器]]。

## 现实语义

它和 [[SuggestedRepairAction]] 分离：上游建议说明“理论上适合怎么处理”，`RepairMethod` 说明补全器实际做了什么。

## 字段或取值

| 取值 | 现实含义 |
|---|---|
| `linear_interpolate` | 按时间比例线性插值，用于 position、gripper、触觉整帧矩阵逐元素 |
| `slerp_interpolate` | 四元数 SLERP 插值，用于 pose orientation |
| `hold_previous` | 使用前一个合法邻居 |
| `hold_next` | 使用后一个合法邻居 |
| `copy_nearest` | 使用时间上最近的合法邻居 |
| `no_op` | 未修改值，仅记录跳过或拒绝 |

## 有效性规则

- `pose.orientation` 插值固定使用 `slerp_interpolate`，不得使用普通四元数分量线性插值。
- `pose.position` 和 `gripper.value` 插值使用按时间比例的 `linear_interpolate`。
- `tactile.frame` v1 只支持整帧矩阵逐元素 `linear_interpolate`。
- `repairable_hold` 不得升级为插值。
- `repairable_interpolate` 降级为 hold 类方法必须由 [[SignalRepairPolicyConfig]] 显式允许，并记录 fallback reason。

## 上游来源

- [[SuggestedRepairAction]]
- [[SignalRepairPolicyConfig]]
- 合法邻居查找结果。

## 下游消费者

- [[SignalRepairRun]]
- [[SignalRepairSampleRecord]]
- [[SignalRepairResult]]

## 不负责

- 不定义异常发现规则。
- 不定义最终 mask 类型。

## 相关链接

- [[SuggestedRepairAction]]
- [[SignalRepairPolicyConfig]]

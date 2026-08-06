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
| `no_op` | 未修改值，仅记录跳过或拒绝 |

## 有效性规则

- `pose.orientation` 插值固定使用 `slerp_interpolate`，不得使用普通四元数分量线性插值。
- `pose.position` 和 `gripper.value` 插值使用按时间比例的 `linear_interpolate`。
- `tactile.frame` v1 只支持整帧矩阵逐元素 `linear_interpolate`。
- 新运行只使用 `linear_interpolate`、`slerp_interpolate` 和 `no_op`；历史 hold/copy 方法不得由当前 dispatcher 调用。
- 缺少任一合法邻居时保持原值并记录 `unrepairable`，不得降级。

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

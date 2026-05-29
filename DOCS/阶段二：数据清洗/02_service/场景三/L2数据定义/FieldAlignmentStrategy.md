# FieldAlignmentStrategy

## 定义

`FieldAlignmentStrategy` 是场景三每类字段投影到统一 step 时间轴时使用的策略枚举和参数集合。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它定义图像、位姿、触觉和夹爪字段的默认对齐口径，只约束契约，不展开具体算法实现。

## 字段或取值

| 取值 | 适用字段 | 现实含义 |
|---|---|---|
| `nearest_neighbor` | image | 图像只做最近邻匹配，不插值 |
| `interpolation_slerp` | pose | position 线性插值，orientation 四元数 slerp |
| `window_aggregate` | tactile | 以 step 时间戳为中心按配置窗口聚合 |
| `follow_image_nearest` | gripper | 夹爪宽度跟随同侧图像最近邻来源 |

## 有效性规则

- 图像字段默认 `nearest_neighbor`，默认阈值 `1000 / target_step_hz / 2` ms。
- 位姿字段默认 `interpolation_slerp`；若只有单侧邻居或插值窗口不足，按配置 fallback 到 `nearest_neighbor`。
- 位姿 fallback 必须在 [[AlignmentIndex]] 中记录 `fallback_reason`。
- 触觉字段默认 `window_aggregate`，必须记录窗口范围、样本数和覆盖率。
- 夹爪字段默认 `follow_image_nearest`，保持与来源图像的追溯关系。

## 上游来源

- [[Scene3AlignmentConfig]]。
- 场景三功能模块清单。
- 用户意图澄清结论。

## 下游消费者

- 多策略字段对齐器。
- [[AlignmentIndex]]。
- [[AlignmentReport]]。

## 不负责

- 不实现插值、slerp 或窗口聚合算法。
- 不决定某个 step 是否进入训练。
- 不定义场景四 mask 类型。

## 相关链接

- [[FieldAlignmentStatus]]
- [[AlignmentIndex]]
- [[Scene3AlignmentConfig]]

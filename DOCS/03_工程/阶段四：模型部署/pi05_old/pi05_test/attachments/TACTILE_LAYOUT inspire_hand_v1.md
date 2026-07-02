---
tags:
  - 附件
---

# TACTILE_LAYOUT (inspire_hand_v1 触觉排布)

> [!abstract]
> 一只灵巧手的 11 个 taxel（触觉传感点）在 224×224 画布上的固定矩形排布规则，构成本仓库 `TACTILE_LAYOUT_VERSION = "inspire_hand_v1"`。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `TACTILE_LAYOUT` |
| 数据类型 | `dict[str, tuple[int, int, int, int]]` |
| 数据结构 | `{taxel_id: (y0, y1, x0, x1)}` 切片坐标字典 |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:189-201` |
| 现实含义 | 把 11 个不规则分布的手指 taxel 摊平到一张 224×224 伪图像上，让模型能用 VLM 的视觉主干处理触觉 |

## 排布规则

```
行 1 (y=  0-89):   taxel 12 | 22 | 32 | 42 | 52   (指尖阵列，5 列)
行 2 (y= 89-179):  taxel 13 | 23 | 33 | 43 | 54   (中段阵列，5 列)
行 3 (y=179-224):  taxel 61 横向拉伸铺满整行     (掌心阵列)
```

每个 taxel ID 对应一组 `sensor_msgs/Image mono16` 话题：

```
/inspire/{left,right}_hand/tactile_12
/inspire/{left,right}_hand/tactile_13
/inspire/{left,right}_hand/tactile_22
/inspire/{left,right}_hand/tactile_23
/inspire/{left,right}_hand/tactile_32
/inspire/{left,right}_hand/tactile_33
/inspire/{left,right}_hand/tactile_42
/inspire/{left,right}_hand/tactile_43
/inspire/{left,right}_hand/tactile_52
/inspire/{left,right}_hand/tactile_54
/inspire/{left,right}_hand/tactile_61
```

`TACTILE_IDS = ("12","13","22","23","32","33","42","43","52","54","61")`

## 通道含义

每个 taxel 渲染成 3 通道：

| 通道 | 含义 | 公式 |
| --- | --- | --- |
| R | 接触强度 | `clip(\|raw - baseline\| / pressure_scale, 0, 1) * 255` |
| G | 正向时间差分 | `clip(max(pressure - prev_pressure, 0) / delta_scale, 0, 1) * 255` |
| B | 负向时间差分 | `clip(max(prev_pressure - pressure, 0) / delta_scale, 0, 1) * 255` |

`baseline` = 从第一帧 top 相机 anchor 开始前 `TACTILE_BASELINE_SECONDS=1.0` 秒触觉值的中位数。

## 在数据流中的位置

- **上游**：11 个 mono16 触觉 topic → `_freeze_image_msg` → 各自的 `ImageSeriesBuffer`
- **处理**：`_render_tactile_hand_image` 第 1267–1311 行，按 `TACTILE_LAYOUT` 把每个 taxel 缩放到对应矩形，再 cv2 贴到 canvas 上
- **下游**：单手最终输出 `observation.images.{left,right}_tactile`（shape=`EXPECTED_IMAGE_SHAPE`）

## 关键约束

- **排布是数据契约的一部分**：任何升级（如 6 DoF 手指、升级四代手）需要新增 `TACTILE_LAYOUT_VERSION` 而不是改这个
- **append 校验**：旧数据集的 tactile layout_version 必须和当前请求一致（`_validate_existing_tactile_preprocess_metadata`）
- 与 [[TACTILE_SCALE_PERCENTILE q99.5 fixed scale]] 共同决定伪图像的取值范围

---
tags:
  - 附件
---

# EXPECTED_IMAGE_SHAPE (224x224x3 视觉 schema)

> [!abstract]
> 固定的视觉特征 shape：高度 224、宽度 224、3 通道 RGB。所有进入 LeRobot 数据集的图像（top/left/right 相机 + 可选 tactile 伪图像）都被离线等比缩放+黑边填充到这个尺寸。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `EXPECTED_IMAGE_SHAPE` |
| 数据类型 | `tuple[int, int, int]` |
| 数据结构 | (H, W, C) 形状元组 |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:171` |
| 现实含义 | LeRobot v3 数据集中所有图像特征的统一尺寸，保证下游训练 dataloader 不需要做图像缩放 |

## 使用位置

| 用途 | 位置 |
| --- | --- |
| 特征 schema 注册 | `build_features_pi05` 第 291–306 行 |
| 图像预处理目标尺寸 | `preprocess_to_vla_shape` 第 259 行 |
| 形状校验 | `_require_expected_image_shape` 第 1488 行 |
| Tactile 伪图像 canvas | `_render_tactile_hand_image` 第 1277 行 |

## 视觉特征列表

| Key | 来源 topic |
| --- | --- |
| `observation.images.top` | `/realsense/top/color/image_raw/compressed` |
| `observation.images.left_wrist` | `/realsense/left_hand/color/image_rect_raw/compressed` |
| `observation.images.right_wrist` | `/realsense/right_hand/color/image_rect_raw/compressed` |
| `observation.images.left_tactile` | `/inspire/left_hand/tactile_{12,13,...,61}`（可选） |
| `observation.images.right_tactile` | `/inspire/right_hand/tactile_{12,13,...,61}`（可选） |

## 关键约束

- **不可变 schema**：CLI 参数 `--image-size` 已弃用，被代码忽略并打印 WARN（第 2531 行）
- **等比缩放+黑边**：`preprocess_to_vla_shape` 用 `min(scale_w, scale_h)` 做缩放，黑边填在右下两侧居中，**不做中心裁剪**（"尽量保留完整视野"）
- **append 时强制匹配**：如果在已有数据集上 resume，image keys 必须完全一致（`open_or_resume_dataset` 第 390–395 行）—— 避免把三路 RGB 和五路 VTLA 混进同一个数据集
- 与 [[ACTION_DIM]]、[[STATE_DIM]] 共同构成 LeRobot 数据集的完整特征 schema

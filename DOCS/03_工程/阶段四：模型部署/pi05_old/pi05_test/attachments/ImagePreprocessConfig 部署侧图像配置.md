---
tags:
  - 附件
---

# ImagePreprocessConfig (部署侧图像配置)

> [!abstract]
> 部署侧图像预处理的 dataclass 配置，由 `pi05_vla_deploy_node.py` 从 `DeployConfig.image` 转换得到；调用 `preprocess_rgb_image(rgb, config)` 把 ROS 图像转成 `torch.float32[3, 224, 224]` 给策略网络。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `ImagePreprocessConfig` (frozen dataclass) |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/data/image_preprocess.py:21-26` |
| 使用位置 | `pi05_vla_deploy_node.py:35-38, 154-159` |
| 现实含义 | 决定每张 ROS 图像在送入模型前如何等比缩放 + 居中补黑边（与训练时一致） |

## 字段

| 字段 | 类型 | 默认 | 含义 |
| --- | --- | --- | --- |
| `image_size` | `int` | `224` | 输出方形尺寸（HxW） |
| `mode` | `Literal["resize_crop", "resize_pad"]` | `"resize_pad"` | 缩放策略 |

## 两种缩放模式

| 模式 | 行为 | 适用 |
| --- | --- | --- |
| `resize_pad`（默认） | 等比缩放使短边到 `image_size`，长边居中补黑边 | 不希望裁掉视野（如 wrist 相机） |
| `resize_crop` | 双线性缩放到 `image_size`，再 `center_crop` 回 `image_size` | 主体在图像中心时（保留语义对齐） |

## 与 `DeployConfig.image` 的对应

```python
# pi05_vla_deploy_node.py:35-38
self.image_config = ImagePreprocessConfig(
    image_size=config.image.image_size,
    mode=config.image.resize_mode,  # "resize_pad" or "resize_crop"
)
```

注意 `DeployConfig.image` 还多一个 `transport: "raw"|"compressed"|"both"`，这个是 ROS 订阅层的事，不在 `ImagePreprocessConfig` 里。

## 在数据流中的位置

```text
ROS sensor_msgs/CompressedImage  →  _decode_image  →  np.uint8[H, W, 3] RGB
    ↓
preprocess_rgb_image(rgb, ImagePreprocessConfig(224, "resize_pad"))
    ↓
torch.float32[3, 224, 224]  (CHW, range [0, 1])
    ↓
collector.update_image(name, tensor)
    ↓
ObservationSnapshot.images[name]
```

## 关键约束

- **必须与训练时一致**：训练 dataloader 用 `pi05/common/data/image_preprocess.py` 的同一个函数 + 同样的 `image_size` + 同样的 `mode`，否则 distribution shift
- **dtype 锁死 float32**：见 `image_preprocess.py:51, 68` `_resize_crop` / `_resize_pad` 末尾 `.to(dtype=torch.float32)`
- **`resize_pad` 用 cv2 + INTER_AREA**（见 `image_preprocess.py:71-76`），downsample 不锯齿
- 与 [[ObservationCollector 观测收集器]]、[[Pi05VlaDeployNode ROS2 部署节点]] 配套使用

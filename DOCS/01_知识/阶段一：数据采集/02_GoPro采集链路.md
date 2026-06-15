# GoPro 采集链路

GoPro 链路负责提供图像模态的 ROS2 topic。当前 GoPro 资料中既有稳定链路知识，也有历史优化日志；长期知识放在本页，调试记录和运行命令保留在工程或 learning 中。

## 链路模型

```text
GoPro / 相机设备
  -> 系统视频设备或采集驱动
  -> ROS2 image publisher
  -> image topic
  -> Octopus 显示与录制
```

## 关键理解

- 图像 topic 是阶段一 raw MCAP 的重要模态之一。
- 图像显示成功不等于 MCAP 录制成功。
- 相机链路涉及设备识别、帧率、编码格式、ROS Image 消息和 Octopus 配置。

## 与新相机关系

GoPro 链路保留为既有相机知识。新相机替换链路单独沉淀到 `03_新相机采集链路.md`，避免把新旧硬件知识混写。

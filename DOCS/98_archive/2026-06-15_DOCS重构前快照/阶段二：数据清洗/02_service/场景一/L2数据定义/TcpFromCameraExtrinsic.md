# TcpFromCameraExtrinsic

## 状态

`TcpFromCameraExtrinsic` 是已废弃命名。该名称容易被误解为 `T_tcp_camera`，与场景一实际计算需要的 `T_camera_tcp` 相反。

后续配置和 L3 必须使用 [[CameraFromTcpExtrinsic]]：

```text
camera_from_left_tcp
camera_from_right_tcp
```

本文件仅保留为旧链接兼容，不得作为新 L2/L3 的目标数据定义。

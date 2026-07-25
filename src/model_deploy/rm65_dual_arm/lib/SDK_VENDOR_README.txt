# 睿尔曼 C/C++ SDK vendor 目录说明

本目录用于存放睿尔曼官方 C/C++ SDK 的运行时库文件。**这些文件不随仓库提交**
（受 SDK 厂商授权与二进制分发约束，且 .so 与目标架构/系统强相关），
开发者首次构建前必须手动从官方 SDK 包拷入。

## 需要放入的文件

从官方 RM_API2 / ros2_rm_robot 的 `rm_driver/lib/` 目录拷入以下文件
（x86_64 Linux 工作站用 linux_x86 版本）：

```
lib/
├── libRM_Service.so        -> libRM_Service.so.1.0.0   (soname 软链)
├── libRM_Service.so.1      -> libRM_Service.so.1.0.0
├── libRM_Service.so.1.0    -> libRM_Service.so.1.0.0
├── libRM_Service.so.1.0.0                             (实际库文件)
└── install_libs.sh                                    (本仓库提供，见下)
```

## 头文件

官方 SDK 头文件（`rm_define.h` / `rm_interface.h` / `rm_interface_global.h`
/ `rm_service.h` 等）放入：

```
include/rm65_dual_arm/
├── rm_define.h
├── rm_interface_global.h
├── rm_interface.h
└── rm_service.h
```

## 安装库到系统路径

头文件随包 include 即可，库文件需装到系统库路径供动态链接器找到：

```bash
sudo bash src/model_deploy/rm65_dual_arm/lib/install_libs.sh
```

该脚本把 libRM_Service.so* 拷到 /usr/local/lib/ 并执行 ldconfig。

## 版本依据

- 官方 ROS2 文档只背书 humble/foxy（Ubuntu 22.04/20.04）。
- 本仓库目标为 ROS2 Jazzy / Ubuntu 24.04，SDK 库版本 v4.3.7，
  Jazzy 兼容性需真机验证（见包 README"真机风险"章节）。
- 官方 SDK 不提供 find_package / pkg-config，只能手动 link。

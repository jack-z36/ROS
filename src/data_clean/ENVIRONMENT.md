# Data Clean — 环境依赖

## Conda 环境

- **环境名**: `data-clean`
- **路径**: `.conda-envs/data-clean/`
- **Python**: 3.12.13
- **激活方式**: `start_data_clean.sh` 自动激活，无需手动操作

### 核心依赖

| 包 | 版本 | 用途 |
|----|------|------|
| mcap | 1.3.1 (editable) | MCAP 文件格式读写 |
| mcap-ros2-support | 0.5.7 (editable) | ROS2 CDR 反序列化 |
| numpy | 2.4.4 | 数值计算 |
| scipy | 1.17.1 | 科学计算 |
| opencv-contrib-python-headless | 4.13.0 | 图像处理（无 GUI） |
| pytest | 9.0.3 | 测试框架 |
| robotic-arm | 1.1.5 | 机械臂运动学 |
| PyYAML | 6.0.3 | 配置文件解析 |
| lz4 | 4.4.5 | LZ4 压缩 |
| zstandard | 0.25.0 | Zstandard 压缩 |

### 系统依赖

| 依赖 | 说明 |
|------|------|
| ROS2 Jazzy | `/opt/ros/jazzy/setup.bash`（用于 mcap-ros2-support 的 CDR 解码） |

### 启动入口

```bash
./start_data_clean.sh              # Web UI
./start_data_clean.sh --cli        # 命令行模式
./start_data_clean.sh --dev        # 开发者验证菜单
```

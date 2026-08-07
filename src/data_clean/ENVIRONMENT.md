# Data Clean — 环境依赖

## Conda 环境

- **环境名**: `data-clean`
- **首选路径**: `/home/hit/.conda-envs/data-clean/`
- **旧路径兼容**: 工作树或 `/home/hit/ROS/src/data_clean/.conda-envs/data-clean/`
- **Python**: 3.12.13
- **使用方式**: `start_data_clean.sh` 优先发现 `/home/hit/.conda-envs` 下的环境，无需手动激活

### 核心依赖

| 包 | 版本 | 用途 |
|----|------|------|
| mcap | 1.3.1 | MCAP 文件格式读写 |
| mcap-ros2-support | 0.5.7 | ROS2 CDR 反序列化 |
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

### mcap / mcap-ros2-support 安装来源与陷阱

- **PyPI 不可达**：本机无法 `pip install` 拉 mcap（SSL EOF）。这两包是**从 forge venv 复制的官方 wheel 安装**，不是 editable、也不是 in-tree 源码：
  - 源：`/home/hit/forge/.venv/lib/python3.12/site-packages/` 下的 `mcap/`、`mcap_ros2/` 及对应 `*.dist-info`
  - 目标：`/home/hit/.conda-envs/data-clean/lib/python3.12/site-packages/`
- **不要使用 in-tree 第三方副本**：`src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap/` 是不完整 checkout，缺 `mcap/_chunk_builder.py`（官方 1.3.1 是纯 Python 文件），导入 `mcap.writer` 会抛 `ModuleNotFoundError: No module named 'mcap._chunk_builder'`。
- **`start_data_clean.sh` 已不再把 in-tree 副本注入 `PYTHONPATH`**（之前会遮蔽环境里的正常安装）。若重新生成该脚本，务必保留这一行为，否则 Web UI 启动会再次失败。
- **修复方式**：若 `mcap._chunk_builder` 报错，从 forge venv 复制完整 `mcap/`（含 `_chunk_builder.py`）进本环境；不要 `pip install -e` 指向 in-tree 副本。

### 启动入口

```bash
./start_data_clean.sh              # Web UI
./start_data_clean.sh --cli        # 命令行模式
./start_data_clean.sh --dev        # 开发者验证菜单
```

## 官方 LeRobot 0.5.2 导出环境

Web 生产任务不使用 Forge writer。最终 dataset 由独立 Python 3.12 环境中的仓库内
`src/model_deploy/third_party/lerobot` `0.5.2` 写出：

- 首选路径：`/home/hit/.conda-envs/lerobot-export`
- 旧路径兼容：`/home/hit/ROS/src/data_clean/.conda-envs/lerobot-export`
- 依赖锁：`config/lerobot_export.lock.json`
- 创建/验收：`runtime/create_lerobot_export_env.sh`
- 覆盖变量：`DATA_CLEAN_LEROBOT_PYTHON`

如需更换整组外部环境根目录，可设置 `DATA_CLEAN_ENV_ROOT`；显式的
`DATA_CLEAN_CONDA_ENV` 或 `DATA_CLEAN_LEROBOT_PYTHON` 优先级更高。

`start_data_clean.sh` 启动 Web 前会检查 Python、LeRobot 版本、核心依赖版本和仓库源码
指纹；不一致时拒绝启动生产 Web。官方导出进程使用 JSON 请求/响应边界，Forge 只在
导出后执行 inspect/quality 业务质量评估。

## user systemd

仓库提供 `systemd/data-clean-web.service`。安装并启动：

```bash
src/data_clean/systemd/install_user_service.sh
journalctl --user -u data-clean-web.service -f
```

该单元使用 `Restart=on-failure`、SIGTERM 优雅停止和 journald。Web 同时在
`<run_root>/runtime_sessions/` 记录 PID、boot ID、退出状态、内存与磁盘采样。
服务固定监听 `http://127.0.0.1:36959/`；直接运行脚本时仍默认自动选择空闲端口。

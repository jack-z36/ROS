# Web 生产交互模型

## 定位

普通 Web 入口面向批次 LeRobotDataset v3 构建，不是单文件调试器，也不是开发者单功能菜单。

用户选择一批 raw MCAP 后，系统为每个文件独立执行阶段二主链路，并将成功 episode 聚合到同一个 LeRobotDataset v3 数据集。

## 核心语义

- 普通 Web 固定走生产语义。
- 最终 LeRobotDataset v3 可输出到用户选择的本机父目录。
- cleaned、MCAP_A、aligned、bridge、日志、报告和 sidecar 留在受控目录。
- 单个 MCAP 失败不应阻断其他成功 episode 发布。
- 每个 Web job 都应保留配置快照，后续判断以 job 当时的 feature contract 为准。

## 配置中心

Web 配置中心面向生产配置，而不是临时调试参数。它应表达：

- 左右 `camera_from_tcp.translation_mm`。
- 左右 `work_frames.position_mm / rotation_euler_rad`。
- 场景二滤波生产默认参数。
- LeRobot v3 feature 段落配置。
- 夹爪标定状态和 gripper-only GoPro 向导入口。

## 详细内容

- Web UI 源码：`src/data_clean/ui/web_launcher.py`
- 生产配置 Runtime：`src/data_clean/runtime/production_config.py`
- Web job 配置快照：`src/data_clean/runtime/web_pipeline_config.py`
- 工程行为记录：`DOCS/03_工程/阶段二：数据清洗/阶段产出.md`

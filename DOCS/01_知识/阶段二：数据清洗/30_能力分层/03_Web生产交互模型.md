# Web 生产交互模型

## 定位

普通 Web 入口面向批次 LeRobotDataset v3 构建，不是单文件调试器，也不是开发者单功能菜单。

用户选择一批 raw MCAP 后，系统为每个文件独立执行阶段二主链路，并将成功 episode 聚合到同一个 LeRobotDataset v3 数据集。

## 核心语义

- 普通 Web 固定走生产语义。
- 最终 LeRobotDataset v3 可输出到用户选择的本机父目录。
- cleaned、MCAP_A、aligned、bridge、日志、报告和 sidecar 留在受控目录，不与最终 LeRobotDataset v3 输出目录混放。
- 单个 MCAP 失败不应阻断其他成功 episode 发布。
- 每个 Web job 都应保留配置快照，后续判断以 job 当时的 feature contract 为准。

## 产物目录边界

Web 生产入口需要区分“用户最终产物”和“阶段二中间产物”：

- 最终产物是可被训练阶段消费的 LeRobotDataset v3，输出到用户选择的 export 父目录。
- 中间产物包括 cleaned、MCAP_A、aligned、bridge、日志、报告和 sidecar，应进入受控的中间产物根目录。
- 中间产物根目录应可配置，以便把大体积临时文件放到容量更合适的磁盘，避免系统盘被阶段二批量生产写满。
- 中间产物目录策略不改变数据语义：它只改变文件落点，不改变 raw -> cleaned -> MCAP_A -> aligned -> bridge -> LeRobotDataset v3 的主链路。

## 健康审计交互边界

Web 可以提供 MCAP health audit 和 rejected 文件移动能力，但这类交互属于生产前资格判断，不等同于正式清洗 job 的 stage。

正式清洗 job 应消费已满足生产前提的输入文件，并继续保持“单文件失败不阻断其他成功 episode 发布”的批处理语义。

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

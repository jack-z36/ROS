# AGENTS.md 文档索引

本文件作为 `/home/hit/ROS` 工作区的文档目录索引使用。具体任务文档必须保存在 `/home/hit/ROS/DOCS` 下对应阶段和场景的位置中；后续某个场景产生的新文档，也必须继续加入该场景对应目录。

每次执行任务前，都必须阅读 `/home/hit/ROS/DOCS/public_rules.md`。

当一次任务无法明确归入某个阶段/场景，或属于跨阶段零散维护、仓库管理、公共文档体系整理时，执行记录必须追加到 `/home/hit/ROS/DOCS/总执行日志.md`。

当我提到现在处于某个阶段时，你必须根据这里的索引加载该阶段下的四个阶段级文档，然后才能执行任务。

当我提到现在处于某个阶段的某个场景时，你必须先加载该阶段的四个阶段级文档，再加载该场景下的五个固定文档，然后才能执行任务。

## 预读规则

当我问到跨阶段零散任务、公共文档体系维护、仓库管理或无法判断属于哪个阶段/场景的问题时，必须先阅读：

- `/home/hit/ROS/DOCS/总执行日志.md`

当我问到与 Git 状态、提交、推送、拉取、远端、账号、分支或仓库同步相关的问题时，必须先阅读：

- `/home/hit/ROS/DOCS/git操作约束.md`

当我问到与 `/home/hit/ROS/src/baton_mini_sdk_demo` 相关的问题时，必须先阅读：

- `/home/hit/ROS/src/baton_mini_sdk_demo/baton_mini_architecture.md`
- `/home/hit/ROS/src/baton_mini_sdk_demo/batonmini运行指南.md`

当我问到与 `/home/hit/ROS/src/gopro_camera_launch` 相关的问题时，必须先阅读：

- `/home/hit/ROS/src/gopro_camera_launch/ARCHITECTURE.md`
- `/home/hit/ROS/src/gopro_camera_launch/gopro节点运行操作指南.md`

当我问到与 `/home/hit/ROS/src/data_clean` 或 `start_data_clean.sh` 相关的问题时，必须先阅读阶段二的四个阶段级文档，再阅读阶段二场景一的五个固定文档。

## 工作流

目录：`/home/hit/ROS/DOCS/工作流`

当交互模式识别为"从零编写程序"时，必须加载以下工作流文档并按步骤执行：

- 从零编写程序：`/home/hit/ROS/DOCS/工作流/从零编写程序.md`

## 阶段一：数据采集

目录：`/home/hit/ROS/DOCS/阶段一：数据采集`

阶段级文档：

- 阶段目标描述：`/home/hit/ROS/DOCS/阶段一：数据采集/阶段目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段一：数据采集/背景信息.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段一：数据采集/当前进度.md`
- 阶段产出：`/home/hit/ROS/DOCS/阶段一：数据采集/阶段产出.md`

### 阶段一场景一：一个一个启动 4 个相机节点

目录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景一`

- 目标描述：`/home/hit/ROS/DOCS/阶段一：数据采集/场景一/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段一：数据采集/场景一/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段一：数据采集/场景一/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景一/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段一：数据采集/场景一/当前进度.md`

### 阶段一场景二：一键启动所有的相机 ROS 节点

目录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景二`

- 目标描述：`/home/hit/ROS/DOCS/阶段一：数据采集/场景二/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段一：数据采集/场景二/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段一：数据采集/场景二/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景二/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段一：数据采集/场景二/当前进度.md`

### 阶段一场景三：运行 Octopus 采集 8 个目标 topic 并输出 MCAP

目录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景三`

- 目标描述：`/home/hit/ROS/DOCS/阶段一：数据采集/场景三/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段一：数据采集/场景三/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段一：数据采集/场景三/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景三/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段一：数据采集/场景三/当前进度.md`

### 阶段一场景四：修改 Octopus UI 展示订阅 topic 与目标数据可视化

目录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景四`

- 目标描述：`/home/hit/ROS/DOCS/阶段一：数据采集/场景四/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段一：数据采集/场景四/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段一：数据采集/场景四/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景四/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段一：数据采集/场景四/当前进度.md`

### 阶段一场景五：硬件信息映射为稳定设备名称和 topic 名称

目录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景五`

- 目标描述：`/home/hit/ROS/DOCS/阶段一：数据采集/场景五/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段一：数据采集/场景五/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段一：数据采集/场景五/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段一：数据采集/场景五/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段一：数据采集/场景五/当前进度.md`

## 阶段二：数据清洗

目录：`/home/hit/ROS/DOCS/阶段二：数据清洗`

阶段级文档：

- 阶段目标描述：`/home/hit/ROS/DOCS/阶段二：数据清洗/阶段目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段二：数据清洗/背景信息.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段二：数据清洗/当前进度.md`
- 阶段产出：`/home/hit/ROS/DOCS/阶段二：数据清洗/阶段产出.md`

### 阶段二场景一：提取夹爪开合以及位姿转换

目录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景一`

- 目标描述：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景一/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景一/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景一/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景一/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景一/当前进度.md`

### 阶段二场景二：硬件数据可靠性验证（滤波、异常值处理与 IK 仿真）

目录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景二`

- 目标描述：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景二/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景二/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景二/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景二/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景二/当前进度.md`

### 阶段二场景三：MCAP 多 topic 时间轴对齐

目录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景三`

- 目标描述：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景三/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景三/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景三/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景三/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景三/当前进度.md`

### 阶段二场景四：构建标准 canonical dataset

目录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景四`

- 目标描述：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景四/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景四/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景四/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景四/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景四/当前进度.md`

### 阶段二场景五：模型训练格式导出器

目录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景五`

- 目标描述：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景五/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景五/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景五/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景五/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段二：数据清洗/场景五/当前进度.md`

## 阶段三：模型训练

目录：`/home/hit/ROS/DOCS/阶段三：模型训练`

当前仅创建阶段目录，尚未建立具体场景。

阶段级文档：

- 阶段目标描述：`/home/hit/ROS/DOCS/阶段三：模型训练/阶段目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段三：模型训练/背景信息.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段三：模型训练/当前进度.md`
- 阶段产出：`/home/hit/ROS/DOCS/阶段三：模型训练/阶段产出.md`

## 阶段四：模型部署

目录：`/home/hit/ROS/DOCS/阶段四：模型部署`

当前仅创建阶段目录，尚未建立具体场景。

阶段级文档：

- 阶段目标描述：`/home/hit/ROS/DOCS/阶段四：模型部署/阶段目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/阶段四：模型部署/背景信息.md`
- 当前进度：`/home/hit/ROS/DOCS/阶段四：模型部署/当前进度.md`
- 阶段产出：`/home/hit/ROS/DOCS/阶段四：模型部署/阶段产出.md`

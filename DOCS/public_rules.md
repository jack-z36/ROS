# 公共规则

本文件记录 `/home/hit/ROS` 项目的公共协作规则。它服务于当前总目标和五个任务场景，是所有场景共享的常驻规则文件。

## 一、项目最终目标

通过公司的数据采集平台程序 Octopus，实现 FASTUMI 数据采集，并将采集结果输出为 MCAP 文件。

Octopus 的架构索引文件为：

- `/home/hit/ROS/DOCS/Octopus_architecture.md`

涉及 Octopus 采集链路、ROS2 topic、MCAP 录制、配置文件、显示与录制边界时，必须优先阅读该架构文件，再继续分析或修改。

## 二、项目边界

本项目当前关注的是数据采集链路打通，不把目标扩展为重新设计 Octopus 或重构全部 ROS 节点。

核心边界如下：

- 数据来源：FASTUMI 相关 ROS2 节点输出的话题数据。
- 采集平台：公司的 Octopus 程序。
- 目标产物：可被后续处理、回放或验证的 `.mcap` 文件。
- 当前拆分场景：相机 ROS 节点的逐个启动、一键启动、Octopus 对 8 个目标 topic 的图形化采集与 MCAP 输出、Octopus UI 操作页和目标数据可视化改造、硬件信息到稳定设备名称和固定 topic 的映射，以及 MCAP 数据清洗脚本与交互式启动器。
- 关键验证：Octopus 能看到需要的 ROS2 topic，并能把选定 topic 正确录制进 MCAP。

## 三、当前任务场景

### 场景一：一个一个启动 4 个相机节点

目标是分别启动、观察、验证 4 个相机 ROS 节点，确认每个节点的启动命令、topic 输出、运行状态、问题现象和修复方式。

索引目录：

- `/home/hit/ROS/DOCS/场景一`

固定文档：

- 目标描述：`/home/hit/ROS/DOCS/场景一/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/场景一/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/场景一/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/场景一/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/场景一/当前进度.md`

### 场景二：一键启动所有的相机 ROS 节点

目标是将已经验证过的相机节点启动流程整合为一键启动方式，使所有目标相机 ROS 节点能够稳定、可重复地同时启动，并服务于 Octopus 采集。

索引目录：

- `/home/hit/ROS/DOCS/场景二`

固定文档：

- 目标描述：`/home/hit/ROS/DOCS/场景二/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/场景二/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/场景二/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/场景二/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/场景二/当前进度.md`

### 场景三：运行 Octopus 采集 8 个目标 topic 并输出 MCAP

目标是成功运行 Octopus 数据采集程序，订阅 2 个 Baton Mini 相机 topic、2 个 GoPro 相机 topic 和 4 个触觉传感器 topic，并能在图形化界面中开始与结束采集，最终输出可验证的 `.mcap` 文件。

索引目录：

- `/home/hit/ROS/DOCS/场景三`

固定文档：

- 目标描述：`/home/hit/ROS/DOCS/场景三/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/场景三/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/场景三/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/场景三/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/场景三/当前进度.md`

### 场景四：修改 Octopus UI 展示订阅 topic 与目标数据可视化

目标是在场景三 8 个目标 topic 和 MCAP 录制链路基础上，修改 Octopus UI：操作页面直接展示全部订阅 topic，主显示区改为左/右手 GoPro、左/右手位姿数据和左/右手触觉数据可视化。

索引目录：

- `/home/hit/ROS/DOCS/场景四`

固定文档：

- 目标描述：`/home/hit/ROS/DOCS/场景四/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/场景四/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/场景四/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/场景四/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/场景四/当前进度.md`

### 场景五：硬件信息映射为稳定设备名称和 topic 名称

目标是根据触觉传感器和 GoPro 采集卡的硬件信息识别真实设备，将其映射为固定逻辑名称，并保证无论插拔顺序或 USB 口如何变化，都输出规定 ROS2 topic 名称。

索引目录：

- `/home/hit/ROS/DOCS/场景五`

固定文档：

- 目标描述：`/home/hit/ROS/DOCS/场景五/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/场景五/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/场景五/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/场景五/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/场景五/当前进度.md`

### 场景六：MCAP 数据清洗脚本与交互式启动器

目标是将 Octopus 输出的 FASTUMI 原始 `.mcap` 文件，通过独立的 `data_clean` 离线清洗程序转换为清洗后 MCAP，并提供面向用户的交互式启动器选择清洗最近 1 个、最近 N 个或全部文件。

索引目录：

- `/home/hit/ROS/DOCS/场景六`

固定文档：

- 目标描述：`/home/hit/ROS/DOCS/场景六/目标描述.md`
- 背景信息：`/home/hit/ROS/DOCS/场景六/背景信息.md`
- 执行约束：`/home/hit/ROS/DOCS/场景六/执行约束.md`
- 执行记录：`/home/hit/ROS/DOCS/场景六/执行记录.md`
- 当前进度：`/home/hit/ROS/DOCS/场景六/当前进度.md`

## 四、DOCS 管理规则

`/home/hit/ROS/DOCS` 是本项目的文档中心。除已有代码包自带文档外，围绕本项目目标产生的新文档都必须放入该目录。

规则：

- 公共规则、总架构、跨场景信息放在 `/home/hit/ROS/DOCS` 根目录。
- 场景一产生的新文档必须放入 `/home/hit/ROS/DOCS/场景一`。
- 场景二产生的新文档必须放入 `/home/hit/ROS/DOCS/场景二`。
- 场景三产生的新文档必须放入 `/home/hit/ROS/DOCS/场景三`。
- 场景四产生的新文档必须放入 `/home/hit/ROS/DOCS/场景四`。
- 场景五产生的新文档必须放入 `/home/hit/ROS/DOCS/场景五`。
- 场景六产生的新文档必须放入 `/home/hit/ROS/DOCS/场景六`。
- 不把新的项目文档散落到 `/home/hit/ROS` 根目录、`src` 目录或临时目录。
- 新文档必须能被 `AGENTS.md` 或对应场景的固定文档索引到。
- 废弃但仍有参考价值的内容不直接删除，优先移动到对应场景目录下的归档文档或在执行记录中注明。

## 五、五类固定文档的职责

每个场景都固定维护以下五类文档。

### 目标描述

说明该场景最终要达成什么效果。

应记录：

- 场景的终极目标。
- 成功时用户能做什么。
- 与 Octopus 采集 FASTUMI 数据和 MCAP 输出的关系。

### 背景信息

说明完成该场景需要知道的上下文。

应记录：

- 涉及的 ROS2 包、launch 文件、脚本和配置文件。
- 相关设备、相机编号、topic 名称和数据类型。
- Octopus 侧需要关注的订阅、显示或录制配置。

### 执行约束

说明执行过程中哪些事情必须遵守限制。


### 执行记录

说明某时某刻做了什么，遇到了什么问题。

应记录：

- 具体日期时间。
- 执行的命令或操作。
- 观察到的输出、现象、错误和临时判断。
- 采取的修复动作和结果。

### 当前进度

说明现在推进到了哪一步。

应记录：

- 已完成事项。
- 正在处理的事项。
- 未完成事项。
- 下次继续时建议优先看的文件和优先执行的命令。

## 六、执行纪律

处理本项目问题时，默认遵守以下纪律：

- 先判断问题属于公共目标、场景一、场景二、场景三、场景四、场景五、场景六，还是 Octopus 架构本身。
- 涉及 Octopus 采集程序时，先阅读 `/home/hit/ROS/DOCS/Octopus_architecture.md`。
- 涉及 `/home/hit/ROS/src/gopro_camera_launch` 时，先阅读该包的架构和运行指南。
- 涉及 `/home/hit/ROS/src/baton_mini_sdk_demo` 时，先阅读该包的架构和运行指南。
- 涉及 `/home/hit/ROS/src/data_clean` 或 `start_data_clean.sh` 时，先阅读场景六五个固定文档。
- 修改代码或脚本前，先确认它服务的是逐个启动、批量启动，还是 Octopus 录制验证。
- 运行命令后，如结果会影响场景判断，需要更新对应场景的执行记录或当前进度。
- 当用户明确给出新的事实、约束或阶段性结论时，优先沉淀到对应场景文档。

## 七、AGENTS.md 维护规则

`/home/hit/ROS/AGENTS.md` 是项目入口索引文件，只放索引和强制阅读规则，不承载详细任务内容。

维护规则：

- 新增场景时，先在 `/home/hit/ROS/DOCS` 下创建对应场景目录。
- 每个新场景至少包含目标描述、背景信息、执行约束、执行记录、当前进度五类文档。
- `AGENTS.md` 中只添加场景名称、目录路径和固定文档路径。
- 详细内容写入 DOCS 下对应文档，不写入 `AGENTS.md`。

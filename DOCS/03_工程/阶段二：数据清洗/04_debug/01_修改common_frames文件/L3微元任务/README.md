# common_frames debug 微元任务索引

本目录存放 `01_修改common_frames文件` 的 debug active L3 微元任务。这里的 L3 是后续代码执行任务，不是继续完善计划文档的任务。

注意：

- `active/` 是本次 debug 微元任务的唯一待执行入口。
- `completed/` 是本次 debug 微元任务的唯一完成归档入口。
- 执行前不得把任务迁移到正式 `03_tasks/task/active/`；完成后也不得归档到正式 `03_tasks/task/completed/`。
- 本目录中的任务用于锁定 common frame 修正路线，执行时必须修改或完善 `src/data_clean` 既有代码、schema、测试、开发者入口或配置加载逻辑。
- 除当前 L3 任务文件自身的执行摘要外，执行端不得把主要工作变成修改 L2 功能文档、数据定义文档或规划说明。
- 执行端必须优先复用现有代码，并读取 `/home/hit/.agents/skills/tdd/SKILL.md`，按 `$tdd` 的 RED/GREEN/REFACTOR 垂直切片方式增加或修正测试。
- 测试数据源固定为 `/home/hit/下载/mcap`；该目录只读，不允许覆盖或清洗原始文件。
- 最终代码修改必须服务于 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/05_开发者验收交互文档.md` 中定义的 `./start_data_clean.sh --dev` 开发者交互。

## 任务 DAG

| 顺序 | 任务文件 | 目标 |
|---|---|---|
| 1 | `active/common_frames_debug_001_盘点common_frame影响面.md` | 在代码层建立 common frame 影响面清单和回归测试基线。 |
| 2 | `active/common_frames_debug_002_改造数据定义为arm_base_pose契约.md` | 在 `src/data_clean/schemas/` 落地左右 arm-base TCP pose 代码契约。 |
| 3 | `active/common_frames_debug_003_废弃位姿转换配置生成路线.md` | 废弃 `FrameAlignmentConfig/common_anchor` 配置生成主路线。 |
| 4 | `active/common_frames_debug_004_建立睿尔曼官方API环境自检.md` | 建立可导入、可调用 `Algo` 的睿尔曼 Python SDK 环境自检。 |
| 5 | `active/common_frames_debug_005_保留相机位姿到TCP位姿转换.md` | 保留并测试相机位姿到 TCP 位姿的第一段转换能力。 |
| 6 | `active/common_frames_debug_006_实现官方API生成arm_base_TCP位姿.md` | 用 `rm_algo_workframe2base()` 实现第二段 arm-base TCP pose 转换。 |
| 7 | `active/common_frames_debug_007_改造cleaned_MCAP输出arm_base_TCP_pose.md` | 让 cleaned MCAP 输出左右 arm-base TCP pose。 |
| 8 | `active/common_frames_debug_008_改造场景二滤波和MCAP_A输入语义.md` | 让场景二滤波与 MCAP_A 消费 arm-base TCP pose。 |
| 9 | `active/common_frames_debug_009_补充开发者验收和回归检查.md` | 补齐开发者入口、smoke test 和回归检查。 |

## 执行与归档

- 执行时直接读取 `active/<任务文件名>`。
- 完成时只更新当前任务文件自身的勾选项和执行摘要。
- 完成后将当前任务文件从 `active/` 移入 `completed/`。
- 不写 `DOCS/总执行日志.md`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/03_工程/阶段二：数据清洗/执行记录/`。

## 路线边界

- 当前主线：`raw Baton Mini -> TCP in camera -> TCP in left/right arm base -> filter -> MCAP_A -> 数据对齐 -> LeRobot v3`。
- 放弃主线：`common_frame -> robot_base -> IK -> MCAP_B -> 关节限制检查`。
- 旧 IK / MCAP_B / 关节限制 L3 已由用户另行处理，本目录不再生成存储方案文档，也不把这些路线作为代码执行目标。

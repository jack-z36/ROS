# data_clean 架构说明

本文档说明 `src/data_clean` 在阶段二数据清洗中的职责、分层、数据流、运行入口和关键模块映射。它面向没有上下文的后续 Codex：先读本文件，再按任务进入具体 runtime/service/schema 文件。

阶段二顶层文档入口：

- `DOCS/阶段二：数据清洗/阶段目标描述.md`
- `DOCS/阶段二：数据清洗/背景信息.md`
- `DOCS/阶段二：数据清洗/阶段产出.md`
- `DOCS/阶段二：数据清洗/当前进度.md`

## 1. 概述

`data_clean` 是阶段二的数据清洗与训练格式桥接代码包。它不是 ROS2 节点，而是 Python 离线处理工具集，由 `start_data_clean.sh` 统一设置 Python、ROS 环境和 `PYTHONPATH` 后启动。

当前真实主链路是：

```text
raw MCAP
  -> [场景一] cleaned MCAP
  -> [场景二] MCAP_A
  -> [场景三] aligned MCAP
  -> [标准 bridge] 04_forge_bridge/forge_ready.mcap
  -> [官方 LeRobot 0.5.2 writer] LeRobot v3 dataset
  -> [官方兼容门禁] loader / parquet / video / stats / ACT batch
  -> [非阻断业务评估] Forge inspect / quality
  -> [事务发布] dataset + sidecar
```

当前已验证样例产物位于：

```text
asset/阶段二：数据清洗/dev/full_flow_random_bimanual/
```

网页批次已验证：

- `5` 个 raw MCAP 聚合为 `5 episodes / 773 frames`，Forge quality 总分 `8.39/10`，`flagged=0`。
- 用户选择外部父目录后，已成功发布 `/home/hit/下载/lerobot/20260601_15`，包含 `1 episode / 273 frames`。

阶段二输出左右 arm-base 下的绝对 TCP 目标位姿；训练侧 LeRobot 框架按训练策略负责转换为差分或相对表示。正常 Web 新任务的最终训练格式固定由官方 LeRobot `0.5.2 / v3.0` 写出。

## 2. 分层原则

代码按单向依赖分层组织：

```text
Schemas -> Config/Repo -> Service -> Runtime -> UI
```

规则：

- `schemas/`：纯数据结构、枚举和契约，不能依赖业务实现。
- `config/`：配置解析和校验，供 service/runtime 使用。
- `repo/`：MCAP、Parquet、JSON、ROS2 CDR 等 I/O 适配。
- `service/`：可测试的业务算法与写出编排。
- `runtime/`：开发者检查、run 目录、日志、manifest、场景调度。
- `ui/`：网页入口、终端 dev menu、标定向导。

后层可以调用前层；前层不要反向依赖后层。

## 3. 入口

| 入口                   | 路径                               | 用途                                                                                 |
| ---------------------- | ---------------------------------- | ------------------------------------------------------------------------------------ |
| 统一脚本               | `start_data_clean.sh`            | 推荐入口，设置环境并分流到网页、CLI 或 dev menu。                                    |
| 正常网页 UI            | `ui/web_launcher.py`             | 本地 Web UI，看板、新建任务、目录浏览、运行进度和历史记录。                          |
| legacy CLI             | `runtime/mcap_clean_launcher.py` | 终端交互/脚本化清洗入口，支持 latest/all/dry-run/workers/calibrate。                 |
| dev menu               | `ui/dev_menu.py`                 | `./start_data_clean.sh --dev` 的开发者功能检验菜单。                               |
| 标定向导               | `ui/mcap_calibration_wizard.py`  | 辅助生成 `config/data_clean/data_clean_calibrated.yaml`。                          |
| 正常 Web 生产配置 Runtime | `runtime/production_config.py` | 读取、校验、原子保存生产配置，并检查夹爪、arm-base topic 与 RealMan SDK readiness。 |
| Web job snapshot Runtime | `runtime/web_pipeline_config.py` | 为任务生成各阶段适配器与可复现 job snapshot；旧 preset 逻辑仅保留历史兼容。 |

常用命令：

```bash
./start_data_clean.sh
./start_data_clean.sh --cli --latest 1
./start_data_clean.sh --cli --dry-run --all --workers auto
./start_data_clean.sh --cli --calibrate
./start_data_clean.sh --dev
DATA_CLEAN_RAW_JSON=1 ./start_data_clean.sh --cli --latest 1
```

配置优先级：

```text
--config / DATA_CLEAN_CONFIG
  > config/data_clean/data_clean_calibrated.yaml
  > config/data_clean/data_clean_smoke_test.yaml
```

正常网页任务直接读取正式生产配置，并为每次任务写出快照：

```text
data_clean_calibrated.yaml
  -> src/data_clean/runs/web_jobs/runs/<job_id>/config_snapshot.yaml
```

普通网页不再显示 preset、任务级算法覆盖或 bridge mode。历史 preset 文件不删除，但只作为兼容资产保留。

普通网页新建任务采用分层预检，避免破坏原先快速扫描体验：

- 扫描目录只做 `.mcap` 文件枚举，立即返回文件列表，状态为 `unchecked`。
- preview 做 summary 级快速审计，检查 MCAP summary 可读性、左右相机图像、左右 Baton pose、启用的触觉 topic 和 schema。
- create 做最终强审计，合并 Baton Mini 位姿采样审计，拦截位姿 topic 缺失、四元数异常和左右尺度疑似不一致。
- 缺陷文件按 `web_file_management.rejected_mcap_dir` 自动移动到中文原因目录，job run 目录写出 `precheck_report.json`。
- 批次正常收尾时，成功进入最终 dataset 的 raw MCAP 移动到 `web_file_management.completed_mcap_dir`，单文件清洗失败的 raw MCAP 移动到缺陷目录，输入目录只保留未处理数据。
- 创建任务前做中间产物空间估算：`keep_all` 按全批累计估算；`production_cleanup` 按并发 worker 峰值中间产物、聚合前必须暂存的 bridge/dataset 产物和 `safety_gb` 估算，并按空间收紧实际 worker。
- 默认 `production_cleanup` 策略会在发布事务提交后删除 cleaned/MCAP_A/aligned/forge_ready 等大型上游中间 MCAP，只保留最终 LeRobot dataset、摘要和必要报告。

## 4. 场景一：raw MCAP -> cleaned MCAP

场景一负责从 raw MCAP 生成 cleaned MCAP，核心能力包括：

- 读取 Octopus 录制的 raw MCAP。
- 校验输入 topic/schema。
- 从 GoPro 图像中检测 ArUco marker，生成左右夹爪宽度 `std_msgs/msg/Float32`。
- 处理 Baton Mini 到左右 arm-base TCP pose 的正式转换；旧 common payload 只保留兼容读取。
- 写出 cleaned MCAP，并保留处理报告。

关键模块：

| 模块                              | 职责                                                                    |
| --------------------------------- | ----------------------------------------------------------------------- |
| `config/mcap_process_config.py` | 兼容 facade；实际解析位于 `repo/config/mcap_process_config.py`。         |
| `repo/config/mcap_process_config.py` | 解析 batch、pose streams、gripper、`camera_from_tcp`、`work_frames` 和历史兼容配置。 |
| `service/mcap_io.py`            | 单文件清洗核心；两遍读取 MCAP，第一遍生成中间 payload，第二遍写出结果。 |
| `service/validator.py`          | 输入 topic/schema 与输出契约校验。                                      |
| `schemas/mcap_health_audit.py`  | Web 新建任务前健康审计的数据结构、状态和缺陷分类目录契约。             |
| `service/mcap_health_audit.py`  | 读取 raw MCAP summary，合并相机/位姿/触觉/schema 健康审计并移动缺陷 MCAP。 |
| `service/mcap_file_management.py` | Web 批次收尾后移动 raw MCAP：成功样本进入已完成清洗目录，失败样本进入缺陷目录。 |
| `service/gripper_width.py`      | ArUco 夹爪宽度提取、缺失帧插值和归一化。                                |
| `service/baton_pose_audit.py`   | Baton Mini 左右位姿 topic 采样、单位量级分类；普通 Web 新建任务通过 `service/mcap_health_audit.py` 复用其审计思想。 |
| `service/training_readiness.py` | 将 Forge quality、LeRobot stats、对齐、夹爪和 bridge feature schema 合成为面向训练前复查的可读摘要；按当前 LeRobot feature contract 判断 state/action 维度。 |
| `service/tcp_transform.py`      | 将每帧 Baton Mini 动态 pose 与 `camera_from_tcp.translation_mm` 组合为动态 TCP 中间位姿；旧 common-frame helper 仅保留兼容。 |
| `service/arm_base_transform.py` | arm-base pose 相关转换与契约支持。                                      |
| `ui/scene1_dev_checks.py`       | 场景一开发者检验项。                                                    |

典型输出：

```text
asset/阶段二：数据清洗/dev/mcap_cleaned/*.mcap
```

注意：

- 旧 common pose 只能服务 `format-only` 开发烟测。
- 正式生产需要 arm-base TCP pose、相机到 TCP 平移、work frame 标定和 RealMan SDK readiness。
- raw pose 保留/可追溯；正式主位姿固定为左右 arm-base TCP pose。

## 5. 场景二：cleaned MCAP -> MCAP_A

场景二目标是把 cleaned MCAP 中的主信号整理成更可靠的 MCAP_A，供场景三对齐使用。

已实现的 dev check 链路：

| 模块                                                      | 职责                                                           |
| --------------------------------------------------------- | -------------------------------------------------------------- |
| `runtime/scene2_signal_reliability.py`                  | 加载样本并检测位姿、夹爪、触觉的缺失、非法值、跳变和异常变化。 |
| `runtime/scene2_signal_repair.py`                       | 构建 repair run，对可修复异常做插值、copy/hold 等补全。        |
| `runtime/scene2_pose_filter.py`                         | 对 pose 序列做平滑和 guard 审计。                              |
| `runtime/scene2_tactile_filter.py`                      | 对 tactile 序列做滤波和差异审计。                              |
| `runtime/scene2_mcap_a_writer.py`                       | 串联场景二检验链路并写出 MCAP_A。                              |
| `service/detectors.py`                                  | 位姿/夹爪/触觉样本级异常检测。                                 |
| `service/repair_run.py`、`service/repair_compute.py`  | repair run 构建与修复值计算。                                  |
| `service/pose_filter.py`、`service/tactile_filter.py` | 可靠片段滤波与审计。                                           |
| `repo/mcap_a_writer.py`                                 | MCAP_A 写出。                                                  |

尚未完成：

- IK 求解器。
- 关节限制、速度/加速度限制检查。
- MuJoCo 仿真验证。
- 正式 robot constraint report。

## 6. 场景三：MCAP_A -> aligned MCAP

场景三负责把 MCAP_A 的多 topic 数据对齐到统一 step 时间轴，输出 aligned MCAP、alignment index 和 alignment report。

关键 runtime：

| 模块                                           | 职责                                              |
| ---------------------------------------------- | ------------------------------------------------- |
| `runtime/scene3_mcap_a_input_check.py`       | 盘点 MCAP_A topic、schema、时间范围和字段可用性。 |
| `runtime/scene3_step_timeline_check.py`      | 生成统一 step timeline。                          |
| `runtime/scene3_field_alignment_check.py`    | 运行多策略字段对齐检验。                          |
| `runtime/scene3_alignment_report_check.py`   | 生成对齐索引和报告。                              |
| `runtime/scene3_aligned_mcap_write_check.py` | 写出 aligned MCAP 与 sidecar。                    |
| `runtime/scene3_full_flow_check.py`          | 顺序运行场景三全流程。                            |

关键 service/repo：

| 模块                                   | 职责                                                            |
| -------------------------------------- | --------------------------------------------------------------- |
| `service/mcap_a_input_validator.py`  | MCAP_A 输入盘点与校验。                                         |
| `service/step_timeline_generator.py` | 基于目标频率和 baseline intersection 生成 step 时间轴。         |
| `service/field_aligner.py`           | 图像和夹爪最近邻对齐。                                          |
| `service/pose_field_aligner.py`      | pose position 插值、quaternion slerp 和 fallback nearest。      |
| `service/tactile_field_aligner.py`   | half-step 窗口聚合 tactile 矩阵为 mean/std/min/max。            |
| `service/alignment_report.py`        | 对齐报告数据生成。                                              |
| `service/aligned_mcap_writer.py`     | aligned MCAP 写出 staging 编排。                                |
| `repo/aligned_mcap_writer.py`        | aligned MCAP 底层写出。                                         |
| `repo/alignment_sidecar_writer.py`   | `alignment_index.parquet` 与 `alignment_report.json` 写出。 |

### 6.1 时间域规则

场景三必须谨慎选择时间域：

- 图像优先使用 ROS `header.stamp`。
- 触觉优先使用 ROS `header.stamp`。
- 位姿优先使用 MCAP `publish_time`，避免设备 header 时钟不同步造成跨设备错位。
- 缺失时回退 `log_time`。

相关实现：

- `repo/ros2_codec.py`
- `repo/mcap_topic_catalog.py`
- `runtime/scene3_full_flow_check.py`

### 6.2 aligned MCAP 语义 topic

当前 aligned MCAP 语义字段：

```text
/gopro_left/image_raw
/gopro_right/image_raw
/aligned/left_tcp_pose
/aligned/right_tcp_pose
/aligned/left_gripper_width
/aligned/right_gripper_width
/aligned/tactile_left_gripper_1
/aligned/tactile_left_gripper_2
/aligned/tactile_right_gripper_1
/aligned/tactile_right_gripper_2
```

pose 派生值写为 7 维：

```text
x, y, z, qx, qy, qz, qw
```

tactile 派生值写为 4 维：

```text
mean, std, min, max
```

`scene3_full_flow_check` 默认使用 formal pose source：`/left_arm_base_tcp_pose` 与 `/right_arm_base_tcp_pose`。未完成标定时，可显式使用 `pose_source_profile=format-only` 消费旧 common pose 做结构烟测。

## 7. 标准 bridge 与官方 LeRobot v3 导出

标准 bridge 不修改正式 aligned MCAP，而是写出单独目录：

```text
04_forge_bridge/
├── forge_ready.mcap
├── forge_topic_config.yaml
├── forge_bridge_schema.json
└── forge_bridge_report.json
```

关键模块：

| 模块                                   | 职责                                                                                                                            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `service/forge_bridge.py` | 消费 aligned MCAP，按固定生产契约拼接 16 维 state 与 16 维 `t+1 action`，写出标准 bridge MCAP。 |
| `repo/bridge_mcap_reader.py` | 按 timestamp 流式解码 bridge，每次只保留一帧的 state/action/双目图像。 |
| `service/lerobot_official_exporter.py` | 独立进程调用官方 `LeRobotDataset.create/add_frame/save_episode/finalize`，按 Web 文件顺序一文件一 episode。 |
| `service/lerobot_official_validator.py` | 用训练侧官方 loader 阻断检查 metadata、parquet dtype、索引、双目 H.264、stats 和 ACT delta-timestamp batch。 |
| `runtime/official_lerobot_export.py` | JSON 请求/响应适配与固定环境预检；生产路径不回退 Forge writer。 |
| `service/lerobot_act_acceptance.py` | CI/版本验收：真实 loader batch 经过 ACT processor 后执行一次前向与反向；不在每个生产任务中运行。 |

### 7.1 LeRobot 临时 step 语义

`observation.state` 固定 16 维：

```text
[0:7]   left_tcp_pose_t
[7:14]  right_tcp_pose_t
[14]    left_gripper_width_t
[15]    right_gripper_width_t
```

`action` 默认 16 维，固定使用下一帧 `t+1` 的绝对目标；左右 TCP pose 必选，夹爪段落可配置：

```text
[0:7]   left_tcp_pose_t+1
[7]     left_gripper_width_t+1
[8:15]  right_tcp_pose_t+1
[15]    right_gripper_width_t+1
```

最后一帧因没有 `t+1` action，会在 bridge 阶段丢弃。

时间戳不再做 parquet 后处理。官方 writer 自动按 `frame_index / 15` 生成 episode 内时间戳，并统一写出 episode metadata、stats、data/video 索引与 parquet dtype。

### 7.2 format-only 与 formal

- `format-only`：允许旧 common pose 做结构烟测，报告固定 `training_eligible=false`。
- `formal`：要求 arm-base pose source 与标定就绪；缺字段、非有限值、夹爪超出 `[0,1]`、pose 绝对值超过默认 `10m` 等会阻止导出。

Forge quality 分数只表示业务质量，不证明格式可训练；只有官方兼容门禁通过才能发布。

## 8. UI 与开发者检验

### 8.1 `web_launcher.py`

正常网页 UI：

- 默认监听 `127.0.0.1`。
- 提供任务看板、新建任务、目录浏览、文件勾选、启动确认、运行进度、历史记录和 JSON API。
- 正常用户语义是“批次 LeRobot v3 数据集构建”：用户勾选的多个 raw MCAP 最终聚合为一个 LeRobot v3 dataset。
- 输出父目录默认使用 `asset/阶段二：数据清洗/prod/exports/lerobot/`，但正常网页允许用户自由选择任意本机目录；preview/create 不做路径限制，也不显示路径风险提示。该行为是 `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md` 中仅针对最终 LeRobot dataset 的受控例外。
- 最终 dataset 写入 `<output_parent>/<dataset_name>/`，sidecar 和中间产物写入 `asset/阶段二：数据清洗/dev/debug/web_jobs/<dataset_name>_data_clean_sidecar/`。
- 当前调度真实主链路：场景一 cleaned MCAP、场景二 MCAP_A、场景三 aligned MCAP、标准 bridge、官方 LeRobot 聚合与阻断门禁、Forge 非阻断业务质量评估。
- 结果页提供三个视图：评测报告分数可视化、从最终 LeRobot v3 `observation.state` 读取的左右 TCP 3D 轨迹、逐文件状态；轨迹 API 为 `GET /api/jobs/{job_id}/trajectory`。
- 3D 轨迹使用固定右手坐标系工程视角，显示局部原点固定在画布左下角；局部原点取当前视图 `bounds.min`，不是物理坐标 `(0, 0, 0)`，原始坐标值不会被改写。单个 episode 按原始时间戳播放，全部 episode 仅做静态总览。普通 Web 使用左右 `arm_base` 数据，必须分屏或明确标注不同物理坐标系，不能暗示双手位于同一世界坐标；`format-only/common_frame` 叠加仅用于开发 smoke。
- 普通网页固定使用左右 arm-base pose 的生产链路，不向普通用户暴露 `format-only/formal`；开发 smoke 仍可显式使用 `format-only`。
- 单个 MCAP 失败不会阻止其他成功 bridge episodes 进入最终 dataset；至少一个 MCAP 成功时批次可发布为 `partial_failed`。
- 用户主动取消会持久化，在当前安全边界停止；有效 checkpoint 和未发布 staging 保留，重启后不会自动恢复。历史删除只删除任务记录，不删除真实产物。
- 独立配置中心展示左右夹爪标定状态、`camera_from_tcp.translation_mm`、`work_frames`、场景二 pose/tactile 滤波生产默认参数和 LeRobot v3 feature 段落。夹爪配置由 gripper-only GoPro 向导自动生成；人工平移输入明确标注 `mm`，机械臂 base 旋转使用 Euler `rad`。Parser 在进入 Runtime 前统一换算为位置 `m`，最终 cleaned MCAP 的 arm-base TCP 位置也保持 `m`。
- 每个 job 必须写出可复现 snapshot；生产配置缺失或 RealMan SDK 不可用时禁止启动。

Web UI 的批次处理模型：

```text
用户勾选 raw MCAP
  -> 每个文件独立执行 scene1 / scene2 / scene3 / bridge
  -> 单文件失败只记录错误，不中断其他文件
  -> 聚合所有成功 bridge episode
  -> 官方 LeRobot 0.5.2 写入一个 v3 dataset
  -> 官方兼容门禁
  -> Forge inspect / quality
  -> 同文件系统事务发布 dataset 与 sidecar
```

关键行为：

- SQLite 持久 worker 一次领取一个 job；job 内文件共享 worker 预算，最终视频聚合始终单 job 执行。
- 页面轮询任务状态；刷新或关闭浏览器不会取消任务。
- `data_clean.sqlite3` 是 job、文件、checkpoint、事件和发布事务的唯一权威；终态 JSON 只是 sidecar 快照。
- 每阶段采用 attempt 临时目录、产物 manifest 校验、原子 rename、checkpoint 提交；owner lease 与 heartbeat 支持服务重启恢复。
- 最终 dataset staging 与目标位于同一输出文件系统；overwrite 发布使用 `prepared -> old_backed_up -> new_installed -> committed` 事务恢复。
- Forge 低分或 flags 只形成质量警告，不阻止 dataset 发布。
- 官方兼容失败阻止发布；失败 staging/bridge 进入 job 诊断目录并保留 7 天。

Web JSON API：

| 方法       | 路径                                   | 用途                                            |
| ---------- | -------------------------------------- | ----------------------------------------------- |
| `GET`    | `/api/dashboard`                     | 看板、最近任务、默认设置和标定状态。            |
| `GET`    | `/api/history`                       | 历史任务摘要。                                  |
| `GET`    | `/api/production-config`             | 读取普通 Web 生产配置。                         |
| `POST`   | `/api/production-config/validate`    | 校验左右 arm-base 位姿配置、滤波生产默认参数和 LeRobot feature 白名单并返回字段错误。 |
| `POST`   | `/api/production-config`             | 原子保存正式生产配置；保存后影响后续任务，已运行任务保留自己的 snapshot。 |
| `GET`    | `/api/production-readiness`          | 检查夹爪、外参、topic 与 RealMan SDK。           |
| `GET`    | `/api/calibration/gripper/status`    | 获取夹爪向导状态。                              |
| `POST`   | `/api/calibration/gripper/open`      | 启动或复用 gripper-only GoPro 向导。             |
| `GET`    | `/api/filesystem?path=...`           | 浏览本机目录。                                  |
| `POST`   | `/api/filesystem/create-directory`   | 创建用户指定目录。                              |
| `POST`   | `/api/input-files/scan`              | 扫描输入目录当前层 `.mcap` 文件，不递归。     |
| `POST`   | `/api/baton-pose-audit/preview`      | 审计左右 Baton Mini 位姿 topic 数值和单位量级，只写报告不移动 MCAP。 |
| `POST`   | `/api/baton-pose-audit/start`        | 后台启动 Baton 位姿审计并返回进度任务 ID。       |
| `GET`    | `/api/baton-pose-audit/{audit_id}/status` | 轮询 Baton 位姿审计进度；完成后返回审计记录。 |
| `POST`   | `/api/baton-pose-audit/move`         | 根据审计结果确认后移动 MCAP 到 `normal`、`unit_mismatch` 或 `other_issue`。 |
| `POST`   | `/api/baton-pose-audit/{audit_id}/move/start` | 后台启动确认后的分类移动。                    |
| `GET`    | `/api/baton-pose-audit/{audit_id}/move/status` | 轮询分类移动进度；完成后返回移动记录。       |
| `GET`    | `/api/baton-pose-audit/{audit_id}`   | 读取 Baton 位姿审计记录。                       |
| `POST`   | `/api/jobs/preview`                  | 预览 dataset、sidecar、文件数、大小和同名冲突。 |
| `POST`   | `/api/jobs`                          | 创建批次数据集构建任务。                        |
| `GET`    | `/api/jobs/{job_id}`                 | 获取任务、阶段和逐文件状态。                    |
| `GET`    | `/api/jobs/{job_id}/trajectory`      | 读取或生成轨迹摘要。                            |
| `POST`   | `/api/jobs/{job_id}/cancel`          | 持久取消，在安全边界停止且不自动恢复。          |
| `POST`   | `/api/jobs/{job_id}/resume`          | 从仍有效的 checkpoint 手动恢复 failed job。     |
| `POST`   | `/api/jobs/{job_id}/retry-failed`    | 以失败 MCAP 创建新任务草稿。                    |
| `POST`   | `/api/jobs/{job_id}/open-visualizer` | 按需启动 Forge Web Viewer。                     |
| `DELETE` | `/api/history/{job_id}`              | 只删除网页历史摘要。                            |

结果页 sidecar 缓存：

| 文件                                    | 用途                                                                  |
| --------------------------------------- | --------------------------------------------------------------------- |
| `reports/forge_inspect.json`          | Forge inspect 原始报告。                                              |
| `reports/forge_quality.json`          | Forge quality 原始报告。                                              |
| `reports/forge_quality_flagged.json`  | flagged episode 列表。                                                |
| `reports/official_compatibility.json` | 官方 loader、dtype、索引、视频、stats 与 ACT batch 阻断门禁报告。     |
| `reports/quality_visual_summary.json` | 评测页总分、维度分、训练前技术体检、逐 episode 分数和 flags 缓存。   |
| `reports/training_readiness_summary.json` | PI0.5 / VLA 训练前技术体检摘要；包含 LeRobot feature contract fingerprint，契约变化后自动重算。 |
| `reports/trajectory_summary.json`     | 轨迹页 episode、时间戳、左右 TCP pose、bounds 和坐标系 profile 缓存。 |

轨迹 API 从最终 dataset 的 `data/chunk-*/file-*.parquet` 读取 `episode_index`、`frame_index`、`timestamp` 和 `observation.state`。它优先根据 job snapshot / LeRobot feature schema 查找左右 TCP pose offset，旧任务回退 32 维默认 offset。响应除原始轨迹样本外，还包含：

```text
coordinate_frame_profile    # common_frame_compat | dual_arm_base
coordinate_frames           # left/right 实际坐标系名称
hand_bounds                 # 左右轨迹独立 min/max/center
projection_hint             # right-handed + local_bounds_min
```

历史任务若已有旧版 `reports/trajectory_summary.json`，API 会从缓存样本补齐新版字段并写回 sidecar，不要求重新读取 parquet。训练前技术体检缓存若缺少或不匹配当前 contract fingerprint，会重新生成并写回 `quality_visual_summary.json`。

### 8.2 `dev_menu.py`

开发者菜单：

- 通过 `./start_data_clean.sh --dev` 进入。
- 场景一：位姿配置、位姿转换、夹爪提取、夹爪配置、输出契约、smoke test。
- 场景二：异常检测、数据补全、pose filter、tactile filter、MCAP_A writer。
- 场景三：MCAP_A 输入、step timeline、字段对齐、alignment report、aligned MCAP 写出、full flow。
- 标准 bridge：按生产契约生成 16 维 state 与 16 维 action。

Service 场景最终验收仍应由用户本人运行 dev menu 后确认；自动化测试只能证明局部实现正确。

## 9. 产物目录

阶段二真实数据产物默认位于：

```text
asset/阶段二：数据清洗/
```

常见 dev 产物：

| 目录/文件                                                                 | 含义                                                                                                                   |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `dev/mcap_cleaned/`                                                     | 场景一 cleaned MCAP。                                                                                                  |
| `dev/full_flow_random_bimanual/03_aligned/`                             | 已验证 aligned MCAP 样例。                                                                                             |
| `dev/full_flow_random_bimanual/04_forge_bridge/`                        | 已验证 Forge bridge 样例。                                                                                             |
| `dev/full_flow_random_bimanual/05_lerobot_v3_bimanual/`                 | 已验证双目 LeRobot v3 样例。                                                                                           |
| `dev/full_flow_random_bimanual/reports/05_quality_report_bimanual.json` | Forge quality 报告。                                                                                                   |
| `dev/debug/web_jobs/<dataset_name>_data_clean_sidecar/`                 | Web UI 批次 sidecar：`01_cleaned/`、`02_mcap_a/`、`03_aligned/`、`04_forge_bridge/`、`logs/`、`reports/`。 |

常见最终产物：

* [ ] 目录/文件含义`prod/exports/lerobot/<dataset_name>/`默认目录下的单个标准 LeRobot v3 dataset，不混入中间产物。`<用户选择的本机父目录>/<dataset_name>/`正常网页入口允许的最终 LeRobot dataset 受控例外。

网页批次 sidecar 始终留在：

```text
asset/阶段二：数据清洗/dev/debug/web_jobs/<dataset_name>_data_clean_sidecar/
```

自由选择目录只适用于最终 dataset。cleaned MCAP、MCAP_A、aligned MCAP、Forge bridge、报告、日志和缓存不得跟随 dataset 散落到外部目录。

## 10. 依赖

主要依赖：

- Python 3
- `mcap`
- `mcap_ros2`
- `numpy`
- `scipy`
- `opencv-python` 且包含 `cv2.aruco`
- `PyYAML`
- `pyarrow`
- ROS2 CDR 解码所需的本地 Python 环境
- 固定 LeRobot 0.5.2 环境，用于官方 v3 写出与格式门禁
- 外部 Forge 环境，仅用于 inspect/quality

`start_data_clean.sh` 会把以下目录加入 `PYTHONPATH`：

- `src/data_clean`
- `/home/hit/forge`（可用 `DATA_CLEAN_FORGE_SOURCE` 覆盖）
Forge venv 的 `site-packages` 不应全局前置到 `PYTHONPATH`，否则可能覆盖 data-clean 环境中的 OpenCV。官方 LeRobot writer 在独立进程和固定环境中运行。

## 11. 与上下游的关系

上游：

- 阶段一/Octopus 采集 raw MCAP。
- raw MCAP 应包含双目图像、双臂位姿、触觉和后续清洗需要的 topic。

下游：

- 当前生产下游是官方 LeRobot 0.5.2 / v3.0 dataset。
- 正式下游仍是阶段三模型训练，需要 canonical dataset 和正式 action 语义。

边界：

- `data_clean` 不启动 Octopus，不负责实时采集。
- `data_clean` 不修改原始 MCAP；所有处理写入独立产物目录。
- Forge writer 只保留为非生产对照工具。
- `format-only` 只用于开发 smoke，不是普通网页模式。
- 修改清洗算法、topic 契约、配置项、运行入口或导出语义时，必须同步更新本文件和阶段二顶层文档。

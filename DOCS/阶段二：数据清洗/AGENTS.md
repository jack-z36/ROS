# 阶段二 AGENTS 入口

本文件只负责阶段二的模式分流、接手读文档顺序和目录索引。不要把它当作完整上下文包；具体任务需要什么上下文，由工作流、场景文档或 L3 文件显式列出。

## 无上下文接手建议读取顺序

后续 Codex 如果完全没有上下文，先按以下顺序读取：

1. `DOCS/阶段二：数据清洗/阶段目标描述.md`
2. `DOCS/阶段二：数据清洗/背景信息.md`
3. `DOCS/阶段二：数据清洗/阶段产出.md`
4. `src/data_clean/data_clean_architecture.md`
5. 当前任务对应的场景目录，例如 `DOCS/阶段二：数据清洗/02_service/场景三/`

当前阶段真实主链路：

```text
raw pose (Baton Mini) → TCP in camera (tcp_transform.compute_tcp_in_camera)
                      → arm-base TCP pose (arm_base_transform.compute_arm_base_tcp_pose, per RM65 base)
                      → pose filter (validate_arm_base=True)
                      → cleaned MCAP (主位姿 topic: /left_arm_base_tcp_pose / /right_arm_base_tcp_pose,
                                      frame_id=left_arm_base / right_arm_base)
```

common_frame / 旧 robot_base 转换仅保留为历史兼容，**不再作为主链路**。

已验证样例产物位于：

```text
asset/阶段二：数据清洗/dev/full_flow_random_bimanual/
```

正常用户网页已经接入全链路批次构建：

```text
勾选 raw MCAP
  -> cleaned MCAP
  -> MCAP_A
  -> aligned MCAP
  -> Forge bridge
  -> 聚合为单个 LeRobot v3 dataset
  -> Forge inspect / quality
```

接手网页任务时注意：

- 最终 dataset 父目录允许用户自由选择任意本机目录，不做路径限制或风险提示。
- 该自由输出规则是 `约束文件/文件存放规范.md` 中的受控例外，不得重新加回 `asset/prod` 路径拦截。
- 中间产物、报告和日志仍固定写入 `asset/阶段二：数据清洗/dev/debug/web_jobs/<dataset_name>_data_clean_sidecar/`。
- 结果页包含评测报告、TCP 3D 轨迹和逐文件状态。
- 普通网页顶部提供独立“配置中心”：仅编辑左右 `camera_from_tcp.translation_mm` 与 `work_frames.position_mm / rotation_euler_rad`，夹爪配置通过 gripper-only GoPro 向导自动生成；人工配置使用 `mm/rad`，进入 Runtime 后位置统一换算为 `m`。普通任务固定走 arm-base 生产链路，不暴露 preset 或 `format-only/formal` 切换。
- TCP 3D 轨迹使用固定右手工程视角；显示局部原点是当前 bounds 的最小值，不是物理坐标 `(0, 0, 0)`。
- 历史 `format-only/common_frame` 轨迹只能作为开发烟测兼容；普通 Web 固定使用左右 arm-base 生产语义，左右轨迹必须分屏或明确标注为不同物理坐标系。

## 双机协作原则

阶段二采用双机分工：

- Win 主机：规划与文档生成，负责架构文档、L2 功能说明、L3 微元任务生成与整理。
- Ubuntu 主机：代码执行，负责执行单个 L3、修改代码和测试、更新该 L3 文件自身并归档。

写入边界见：

- `约束文件/双机协作写入边界.md`
- `约束文件/功能分支接力流程.md`

阶段二默认不在 `main` 上工作；Runtime MVP 使用 `runtime-mvp` 分支；Service 场景一到五分别使用 `service-s1`、`service-s2`、`service-s3`、`service-s4`、`service-s5` 分支。Ubuntu 禁止在 `main` 上执行 L3 或推送阶段二代码。

## 当前入口

用户和开发者入口：

```bash
./start_data_clean.sh          # 正常网页入口
./start_data_clean.sh --cli    # legacy 终端清洗入口
./start_data_clean.sh --dev    # 开发者功能检验菜单
```

关键代码入口：

- `start_data_clean.sh`
- `src/data_clean/ui/web_launcher.py`
- `src/data_clean/ui/dev_menu.py`
- `src/data_clean/data_clean_architecture.md`

## 模式入口

### Win 文档规划模式

触发信号：

- 阶段二 pipeline
- L1/L2/L3
- 功能模块拆解
- 功能模块说明文档
- 数据定义
- 微元任务生成

读取入口：

- `DOCS/工作流/阶段二开发范式.md`
- `约束文件/功能分支接力流程.md`
- `约束文件/L3功能组目录约束.md`
- `约束文件/L3现有实现盘点约束.md`
- `约束文件/L3调度元数据约束.md`
- `约束文件/开发者验收入口约束.md`

输出位置：

- L2 能力模块说明：对应 L1 或场景目录下的 `L2能力模块/`
- L3 微元任务：`03_tasks/task/active/<功能组>/`

开始规划前必须确认当前处于对应 Runtime 分支或 Service 场景分支；不得在 `main` 上生成阶段二 L2/L3。

Service 场景一到场景五的 L2/L3 设计必须说明它如何通过 `./start_data_clean.sh --dev` 的场景菜单、功能检验项或场景完整 smoke test 被最终人工验收。

### Ubuntu L3 执行模式

触发信号：

- 用户指定一个 `03_tasks/task/active/<功能组>/xxx.md` 文件并要求执行。

读取入口：

- 当前 L3 文件。
- 当前 L3 文件列出的必读任务文档、相关 L3、约束文档和代码文件。
- `约束文件/L3任务文件身份校验约束.md`
- `约束文件/L3调度元数据约束.md`
- `约束文件/功能分支接力流程.md`
- `约束文件/开发者验收入口约束.md`

输出位置：

- 代码和测试：由当前 L3 的“允许修改”决定。
- 当前 L3 文件：勾选成功标准并在末尾追加执行摘要。
- 归档：从 `03_tasks/task/active/<功能组>/` 移动到 `03_tasks/task/completed/<L1归档目录>/<功能组>/`；如果原 active 功能组目录为空，删除该空目录。

Ubuntu L3 执行模式禁止写入集中共享记录文件，包括 `执行记录/`、各级 `当前进度.md`、各级共享 `执行记录.md` 和 `DOCS/总执行日志.md`。

Ubuntu L3 执行前必须先校验用户指定路径、实际读取路径、文件名编号和正文 `L3 编号` 是否一致。若找不到用户指定文件，或编号/标题不一致，必须停止并汇报问题；禁止改读同目录下其他 L3。

Ubuntu L3 执行前必须确认当前分支是该 L3 所属 Runtime 分支或 Service 场景分支；如果当前分支是 `main` 或其他分支，必须停止并提示切换。

Service 场景 L3 的自动化验收只证明局部实现正确；完成一个场景的全部 L3 后，最终验收必须由用户本人运行 `./start_data_clean.sh --dev`，选择对应场景和功能检验项或场景完整 smoke test 后确认。

## 目录索引

- 架构与路线图：`00_架构与路线图/`
- Runtime MVP：`01_runtime_mvp/`
- Service：`02_service/`
- L3 任务池：`03_tasks/`
- 约束文件：`约束文件/`
- Win 端规划记录与历史执行记录：`执行记录/`
- 真实数据产物：`asset/阶段二：数据清洗/`

## 当前重点代码模块

- 场景一清洗与标定：`src/data_clean/service/mcap_io.py`、`src/data_clean/service/gripper_width.py`、`src/data_clean/ui/mcap_calibration_wizard.py`
- 场景二 MCAP_A：`src/data_clean/runtime/scene2_*`
- 场景三 aligned MCAP：`src/data_clean/runtime/scene3_full_flow_check.py`
- 临时 Forge bridge：`src/data_clean/service/forge_bridge.py`
- LeRobot v3 转换：`src/data_clean/runtime/forge_bridge_to_lerobot.py`
- 正常用户网页与批次编排：`src/data_clean/ui/web_launcher.py`

## L3 任务池

```text
03_tasks/
├── task/
│   ├── active/<功能组>/
│   └── completed/<L1归档目录>/<功能组>/
├── active/       # 历史兼容目录，不再写入新 L3
└── completed/    # 历史兼容目录，不再写入新 L3
```

功能组示例：

- `runtime-g1`
- `runtime-g2`
- `service-s1-g1`
- `service-s2-g1`

同一个 L2 功能模块拆出的 L3 必须放入同一个功能组。功能组序号必须与 `功能模块清单.md` 中的功能模块序号一致，禁止把同一场景的全部 L3 堆放到 `g1`。

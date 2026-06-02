# common_frames_debug_doc_update — Learnings

## 分支
- 目标分支：`生成lerobot数据集`
- 父提交：`73a10bf v1.0`（L3 002–009 + debug：common_frame 的工作都打包在这个 v1.0 commit 中）
- 10 个 commit 在 v1.0 之上，主要内容是场景三对齐（aligned MCAP）+ LeRobot v3 转换
- 已确认：L3 代码（`arm_base_transform.py` / `arm_base_pose.py` / `tcp_transform.py` 等）在 v1.0 已提交；切换到 `生成lerobot数据集` 后这些文件存在且与 HEAD 匹配

## 执行策略
- Wave 1 并行：A, B, D（互不共享文件路径）
- Wave 2 串行：C（依赖 B 中新增的 L2 数据定义文件）
- Wave 3 验证：E（多数为"不改"）

## 文档侧关键发现
- `DOCS/阶段二：数据清洗/AGENTS.md` 第 46 行已包含 "format-only 的旧 `common_frame` 轨迹可叠加；`formal` 的左右 `arm_base` 轨迹必须分屏同步播放" — 这是网页端配置项语义，**保留**不动。
- `场景一/目标描述.md` 仍写 "把左右 Baton Mini raw pose 转换到 common frame 下的相机 pose" — 这是 Batch B1 的核心目标。
- 场景一六件套场景目录实际包含 `当前进度.md` / `执行记录.md` / `docs/` — 这些不在计划的 Batch B 范围（计划未列入），**保持不动**。
- 场景一 L2 数据定义实际比计划多：`Scene1DevArtifact.md` / `Scene1DevCheckItem.md` / `Scene1DevConfigOverride.md` / `Scene1DevRunLog.md` / `Scene1DevRun.md` — 这些是 dev 菜单相关，与位姿框架无关，**保持不动**。
- 场景二 L2 数据定义实际比计划多很多（joint limit / signal repair / reliability / IK 等子项）— 计划内 C 项 7 个文件已覆盖主链路需要的部分，其余**保持不动**。

## 约束（来自 `02_service/AGENTS.md` 等）
- Win 端不写 `执行记录/` / `当前进度.md` / 共享 `执行记录.md` / `DOCS/总执行日志.md`
- 阶段二默认不在 main 工作；当前在 `生成lerobot数据集` 分支（用户已指定）
- L2 数据定义原子性；新文件遵循 Obsidian wikilink

## 2026-06-02 Batch A 执行记录

执行于分支 `生成lerobot数据集`（与 L3 v1.0 commit 一致）。

### 发现与观察
- A1 AGENTS.md: 原文件无 "raw pose → common frame → robot_base TCP pose" 文本，MCAP 层 pipeline（raw MCAP → cleaned MCAP → MCAP_A → aligned MCAP → bridge）与 plan 预期含位姿描述的版本不同。最终在 "当前真实主链路" 段替换为新的位姿链路，并保留 common_frame 降级标注。
- A2 阶段目标描述.md: 原行 "处理 common/arm-base 位姿相关语义" 已部分旧兼容；改为直接指定主位姿输出坐标系。
- A3 背景信息.md: 无独立 "数据链路" 小节；在 topic 世界段新增位姿链路文本。
- A4 阶段产出.md: `tcp_transform.py` 与 `arm_base_transform.py` 原本已在同一行；按要求拆分为两行，各自补充详细用途。
- A6 宏观蓝图.md: 场景一输出列补了 "（含 arm-base TCP pose + raw pose）"；旧 vs 新对比表第 2 行措辞更新。
- A7 实现路线图.md: 场景一 P0 目标列改为 "位姿转换到 arm-base"；输出列同步补了 arm-base 标注。
- A8 产物架构设计.md: cleaned MCAP 核心变化新增具体 topic 名与 frame_id 条目。
- 未触碰：当前进度.md、执行记录/、03_tasks/、01_runtime_mvp/、src/ 代码文件。

## Batch D 执行记录 (2026-06-02)

### D1 目标描述.md
- 行 9: `common frame 位姿语义` → `机械臂基坐标系（per RM65 base）下的 TCP pose 语义`
- 公共文件摘要层措辞，与场景一六件套 B1 不冲突。

### D2 背景信息.md
- 在 MCAP 层级主链路之后新增两行场景一/二 pose 链路描述：
  - 场景一：raw MCAP → TCP in camera → 机械臂基坐标系（per RM65 base）下的 TCP pose → cleaned MCAP
  - 场景二：cleaned MCAP → 位姿滤波器（arm_base_tcp_pose 校验）→ validated MCAP
- 文件原本无 common frame 提及，属于新增而非替换。

### D3 输出程序与文件.md
- 预期输出表场景一/二行各追加 `（主位姿: arm_base_tcp_pose）`
- 场景一：`cleaned MCAP（主位姿: arm_base_tcp_pose）、清洗报告、标定结果和转换参数`
- 场景二：`validated MCAP（主位姿: arm_base_tcp_pose）、异常报告、修复记录、机器人约束报告`

### 验证
- grep 复检 3 文件 `common frame` → 0 match（仅场景一/二/三子目录有，非 Batch D 范围）
- 分支确认：`生成lerobot数据集`
- 未调用 git commit

## Batch B 执行发现（2026-06-02）
- 场景一 L2能力模块 旧 `common frame位姿转换.md` 已成功删除，`arm-base 位姿转换.md` 创建完成；无其他文件引用旧 wikilink `[[common frame位姿转换]]`。
- 场景一 L2数据定义 新增 3 文件：`ArmBaseTcpPose.md` / `TcpInCamera.md` / `WorkFrameInBaseConfig.md`。
- 所有 deprecated 段使用统一格式：`> ⚠️ **Deprecated since 2026-06 debug-common-frames L3 001**。`。
- B3 模块 05 从 `common frame 位姿转换` 重命名为 `arm-base 位姿转换`；B3/B8/B9 dev 检验项名称同步更新。
- B15-B17 旧 `tcp_common` / `camera_common` 字段标记为"已弃用字段，保留读取兼容"。
- 未触及文件验证：dev 菜单 5 文件、夹爪 3 文件、`GripperWidthSample.md` / `GripperCalibrationConfig.md` / `TcpFromCameraExtrinsic.md` 均保持原样。
- grep 复检通过：arm-base/arm_base 出现 74 次（原 0），无残留 common frame 作为主链路措辞（deprecated 段中的历史引用保留）。

# 文档更新计划：反映 arm-base TCP pose 数据流

## TL;DR

> **Summary**: 阶段二数据清洗主链路已从 "raw pose → common_frame → robot_base TCP pose" 改为 "raw pose → TCP in camera → arm-base TCP pose (per RM65 base)"；本计划列出 `DOCS/阶段二：数据清洗/` 下所有需要同步更新的 `.md` 文档及具体改动内容。
> **Deliverables**: 一份按"阶段入口 → 架构路线图 → 服务场景 → L2 模块/数据 → debug 归档"分组的文件清单，每条含当前文本、推荐新文本/弃用标记、迁移理由。
> **Effort**: Short（纯文档编辑，无代码改动）
> **Parallel**: NO（单分支串行编辑，避免冲突）
> **Critical Path**: 阶段入口文档 → 02_service 场景一/二六件套 → L2 模块/数据定义 → 当前进度与产出

## Context

### Original Request

> "根据上次的代码修改内容，更新一下当前分支的 `@DOCS/阶段二：数据清洗/` 内部的md文档，确保这个文档的内容，能够正确的反映真实的数据清洗数据流（尤其是位姿转换，是转换到机械臂基坐标系而不是转换到common_frame）。现在，来计划一下，具体要修改哪些md文件？具体要修改哪些内容？完成计划之后，交给我审核"

### Interview Summary

- 用户已确认目标范围：仅 `DOCS/阶段二：数据清洗/` 内部 `.md` 文档，不涉及 `src/` 代码、不修改 L3 任务文件。
- 真实数据流（已由 L3 002–009 落地）：
  1. 场景一：`raw pose (Baton Mini) → TCP in camera (新增 tcp_transform.compute_tcp_in_camera) → arm-base TCP pose (新增 arm_base_transform.compute_arm_base_tcp_pose, 调 `Algo.rm_algo_workframe2base `) → pose filter (新增 `validate_arm_base=True `) → cleaned MCAP 写出 arm-base TCP pose + raw pose 保留`。
  2. 场景二：输入改为 arm-base TCP pose；IK / MCAP_B / joint-limit 检查不在主路径；`MCAP_A → 对齐 → LeRobot v3` 是后续方向。
- 用户要求先出计划文档供审核，再编辑。

### Metis Review（已识别风险）

- **分支归属**：`debug：common_frame` 不是 `约束文件/功能分支接力流程.md` 中列出的六个默认分支之一。文档编辑按 Win/Ubuntu 边界规范应落到 `service-s1`（场景一）、`service-s2`（场景二）；但当前 L3 已在 `debug：common_frame` 完成，用户期望"在当前分支"落地——**此点需用户在审核时明确**。
- **L2 约束**：`约束文件/L2能力模块与数据定义约束.md` 要求"每次编写、补全或重写 L2 能力模块说明文件之前，必须使用 `grill-me` 技能确认用户意图"——本计划对 L2 模块说明的"重写"属于该条款范畴；建议审核完成后，对 `场景一/L2能力模块/common frame位姿转换.md`（重命名为 arm-base 位姿转换）等使用 `grill-me` 单独确认。
- **Obsidian wikilink**：`L2能力模块/*.md` 中所有引用数据概念必须用 wikilink，引用未存在的 L2 数据定义文件要先建。
- **不要触碰**：`03_tasks/task/completed/**`、`04_debug/01_修改common_frames文件/L3微元任务/completed/**`（已归档的执行摘要，应保持原状作为历史证据）。
- **场景二 joint-limit / IK 模块**：原本在场景二功能模块清单中，正式产品演进中可能回归；本计划只标记"暂不在主路径"，不删除，避免未来需要重建时缺失上下文。

## Work Objectives

### Core Objective

让 `DOCS/阶段二：数据清洗/` 下的 `.md` 文档与代码实况（arm-base TCP pose 主位姿、IK/MCAP_B 暂离主路径）保持一致，读者（包括下一轮 L3 执行者）能直接从文档理解真实数据流。

### Deliverables

- 一份 `.omo/plans/common_frames_debug_doc_update.md`（本文件），列出每条改动。
- 审核通过后，落到 `DOCS/阶段二：数据清洗/` 内的具体 `.md` 编辑（不在本计划执行范围）。

### Definition of Done（计划层）

- [ ] 每条改动含"文件路径 / 当前文本摘要 / 推荐新文本或弃用标记 / 改动理由 / 优先级"。
- [ ] 区分"重写"、"标记 deprecated"、"微调措辞"三类。
- [ ] 指明"暂不修改"的文件以避免歧义。
- [ ] 明确分支归属待用户裁决。

### Must Have

- 阶段入口文档（AGENTS.md / 阶段目标描述.md / 背景信息.md / 阶段产出.md）能正确反映主链路。
- 00_架构与路线图 中场景一/二行不再写 "common_frame → robot_base"。
- 02_service 场景一/二 六件套中所有位姿概念统一为 arm-base TCP pose。
- L2 数据定义中标记已弃用的（`FrameAlignmentConfig` / `CommonFrameCameraPose` / `CommonFrameTcpPose` / `CommonToRobotBaseTransform` / `RobotBaseTcpPose`）有明确的弃用说明和替代品指向。
- 04_debug/01_修改common_frames文件/ 下的 5 份规划文档已经写好了新方向，本计划**只做最少措辞微调**（或不调）。

### Must NOT Have

- **不**修改 L3 任务文件（在 `L3微元任务/completed/` 或 `L3微元任务/active/`）。
- **不**修改 `01_runtime_mvp/`（与本次 debug 无关；`01_runtime_mvp` 分支未动）。
- **不**修改 `00_架构与路线图/架构设计约束.md`（通用架构约束，不涉及位姿框架细节）。
- **不**修改 L2 能力模块中 `夹爪开合配置生成.md` / `夹爪宽度提取.md` / `触觉滤波器.md`（与位姿框架无关）。
- **不**修改 L2 数据定义中 `GripperWidthSample.md` / `GripperCalibrationConfig.md` / `TcpFromCameraExtrinsic.md`（已 deprecated 且与位姿链解耦）。
- **不**删除任何"暂不在主路径"的模块说明（joint-limit / IK / MCAP_B / 异常值检测 / 数据补全）——只标记"未在当前主路径启用"，保留演进空间。
- **不**写入 `DOCS/总执行日志.md` / `执行记录/` / `当前进度.md` / 共享 `执行记录.md`（按双机边界，Win 不写）。
- **不**在没有用户确认前，把改动落到任何分支。

## Verification Strategy（计划审核维度）

- 用户逐条 review 后给"接受/拒绝/调整"反馈。
- 编辑执行完成后（不在本计划），用 grep 复检：
  - `DOCS/阶段二：数据清洗/02_service/场景一/**/*.md` 中不应再出现"common frame TCP pose"作为主输出。
  - `DOCS/阶段二：数据清洗/02_service/场景二/**/*.md` 中 pose 输入应为 arm-base TCP pose。
  - 已 deprecated 的 L2 数据定义文件首部应含 "⚠️ Deprecated" 或类似显式标记。

## Execution Strategy

### Parallel Execution Waves

**本计划是文档编辑清单，非实现计划**——执行编辑时按文件依赖关系串行即可（每文件内部自洽、无跨文件编辑冲突）。建议执行批次（审核通过后）：

- **Batch A（阶段入口与架构蓝图）**：先动高层，让读者从入口看就对。
- **Batch B（02_service 场景一六件套）**：主链路变更最集中。
- **Batch C（02_service 场景二六件套）**：从场景一接收 arm-base TCP pose；IK/MCAP_B/joint-limit 标注。
- **Batch D（L2 数据定义弃用与新增）**：标记旧、补充新。
- **Batch E（debug 内部规划文档 + 当前进度）**：收尾。

### 依赖矩阵

| Batch | 依赖                                        |
| ----- | ------------------------------------------- |
| A     | 无                                          |
| B     | A 完成后（场景一的目标/背景与阶段入口一致） |
| C     | B 完成后（场景二接收场景一输出）            |
| D     | B+C 完成后（数据定义对应场景链路）          |
| E     | A–D 完成后（基于真实落地的总结）           |

### Agent Dispatch Summary

- 本计划由 Win 端主会话直接编辑；不需要 subagent。
- 后续若需并发，可对 Batch A 内部文件并行（但简单起见推荐串行）。

## TODOs（按"文件分组"组织，每项即一处文档改动）

> 说明：以下每一条 `N.` 即一个编辑项。**实施前需用户确认分支归属**。

### Batch A：阶段入口与架构蓝图

#### A1. `DOCS/阶段二：数据清洗/AGENTS.md`

- **优先级**: High
- **当前文本**:
  - "阶段二数据清洗入口文件" 段落对"数据清洗主链路"的描述提到位姿转换。
- **改动类型**: 措辞微调
- **推荐改动**:
  - 找到"当前阶段真实主链路"或类似行（原句提到"raw pose → common frame → robot_base TCP pose → ..."的部分）替换为：
    > "当前阶段真实主链路：raw pose → TCP in camera → arm-base TCP pose (per RM65 base) → pose filter → cleaned MCAP。common_frame / 旧 robot_base 转换仅保留为历史兼容，**不再作为主链路**。"
    >
- **理由**: AGENTS.md 是阅读入口，链路图错了一切文档都误导。
- **不**修改: L1 索引、约束文件索引、目录列表。

#### A2. `DOCS/阶段二：数据清洗/阶段目标描述.md`

- **优先级**: High
- **改动类型**: 措辞微调
- **推荐改动**: 把"产出 cleaned MCAP"段中关于"主位姿输出在 common frame"的描述改为"主位姿输出在机械臂基坐标系（per RM65 base）"。
- **理由**: 阶段目标与实际产出对齐。

#### A3. `DOCS/阶段二：数据清洗/背景信息.md`

- **优先级**: Medium
- **改动类型**: 措辞微调
- **推荐改动**: "数据链路"小节里场景一的 chain 描述，由"raw → common → robot_base"改为"raw → tcp_in_camera → arm_base"。
- **理由**: 背景文档需与新数据流一致。

#### A4. `DOCS/阶段二：数据清洗/阶段产出.md`

- **优先级**: High
- **改动类型**: 行级更新
- **推荐改动**:
  - 代码资产表里 `tcp_transform.py` 行：补充"将相机坐标下 TCP 转换为机械臂基坐标系 TCP（arm-base）"。
  - 代码资产表里**新增**一行 `arm_base_transform.py`（封装 `Algo.rm_algo_workframe2base`），写明用途。
- **理由**: 阶段产出文档是"读者一眼看清代码结构"的入口，缺一行就看不到新模块。
- **不**改动: 其他表行；`mcap_io.py` 描述本身不变（已能写 arm-base payload）。

#### A5. `DOCS/阶段二：数据清洗/当前进度.md`

- **优先级**: Medium
- **改动类型**: 状态更新
- **推荐改动**: "当前真实状态"段落中关于 Forge bridge TCP 3D 轨迹或"cleaned MCAP 含 common-frame TCP pose"的描述改为"cleaned MCAP 含 arm-base TCP pose（左/右各一个 topic）+ raw pose 保留"。
- **注意**: 此文件按双机边界，**Win 主机可写**（在 02_service 同级，不在禁止列表）；但仍建议与用户在分支选择上对齐。
- **不**改动: 标题与目录结构。

#### A6. `DOCS/阶段二：数据清洗/00_架构与路线图/数据清洗pipeline宏观蓝图.md`

- **优先级**: High
- **改动类型**: 表格更新
- **推荐改动**:
  - 场景一行的"输出"列：`cleaned MCAP（含 common frame TCP pose + raw pose）` → `cleaned MCAP（含 arm-base TCP pose + raw pose）`。
  - 全局"新链路 vs 旧链路"对比表（如有）：将旧链路列的"common_frame → robot_base"改为"已弃用，仅历史兼容"。
- **理由**: 蓝图文档影响后续所有读者。

#### A7. `DOCS/阶段二：数据清洗/00_架构与路线图/阶段二实现路线图.md`

- **优先级**: Medium
- **改动类型**: 表格更新
- **推荐改动**: 场景一 P0 行的"主链路单元"列改为"位姿转换到 arm-base"；关联模块列去掉 `common frame位姿转换`、加入 `arm-base 位姿转换`。
- **不**改动: 阶段里程碑日期。

#### A8. `DOCS/阶段二：数据清洗/00_架构与路线图/阶段二产物架构设计.md`

- **优先级**: Medium
- **改动类型**: 段落更新
- **推荐改动**: "cleaned MCAP 契约"小节里关于主位姿 topic 名称与 frame_id 的描述改为"arm_base_tcp_pose, frame_id = `<hand>_arm_base_link` (per RM65 base)"。
- **不**改动: 总体章节结构。

#### A9. `DOCS/阶段二：数据清洗/00_架构与路线图/架构设计约束.md`

- **优先级**: None
- **改动**: **不改**。此文件是通用架构约束，不涉及具体位姿框架表述。

### Batch B：02_service 场景一六件套

#### B1. `DOCS/阶段二：数据清洗/02_service/场景一/目标描述.md`

- **优先级**: High
- **改动类型**: 重写位姿段
- **推荐改动**: 找到"将左右 Baton Mini raw pose 转换到 common frame 下的相机 pose / TCP pose"等表述，重写为：
  > "将左右 Baton Mini raw pose 转换为机械臂基坐标系下的 TCP pose（arm-base），并写入 cleaned MCAP；raw pose 保留为附加大字段。"
  >
- **理由**: 场景目标是阅读首要文件。

#### B2. `DOCS/阶段二：数据清洗/02_service/场景一/背景信息.md`

- **优先级**: High
- **改动类型**: 段落重写
- **推荐改动**: "数据链路"小节里场景一的链图由 "raw → 相机 pose → common frame → 转换到 robot_base" 改为 "raw → 相机 pose → TCP in camera → arm-base TCP pose"；补充"使用 `Algo.rm_algo_workframe2base` 完成转换"一句。
- **不**改动: 硬件介绍、夹爪部分。

#### B3. `DOCS/阶段二：数据清洗/02_service/场景一/功能模块清单.md`

- **优先级**: High
- **改动类型**: 表格行级
- **推荐改动**:
  - "接口稳定"段：去除对 `FrameAlignmentConfig.common_anchor: left` 的描述，改为"输出 `ArmBaseTcpPose`，frame_id = `<hand>_arm_base_link`"。
  - "开发检查项"表：把基于 `frame_alignment` 的检查改为 `arm-base 位姿转换（新链路，不再依赖 common_frame）`。
- **不**改动: 夹爪相关行。

#### B4. `DOCS/阶段二：数据清洗/02_service/场景一/输出程序与文件.md`

- **优先级**: High
- **改动类型**: 表格行级
- **推荐改动**: cleaned MCAP 输出表里的位姿 topic 行改为 `arm_base_tcp_pose`（frame_id=`<hand>_arm_base_link`），删除/置灰 `tcp_common` 行（保留为"历史字段，不推荐使用"）。
- **不**改动: raw pose 行（保留不变）。

#### B5. `DOCS/阶段二：数据清洗/02_service/场景一/执行约束.md`

- **优先级**: Low
- **改动**: **不改**（如需加一句"不要依赖 common_frame 配置项"，可微调；非必须）。

#### B6. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/common frame位姿转换.md` → **建议重命名为 `arm-base 位姿转换.md`**

- **优先级**: High
- **改动类型**: 文档重命名 + 内容重写（**需用 `grill-me` 与用户确认意图**）
- **推荐改动**:
  - 文件名: `common frame位姿转换.md` → `arm-base 位姿转换.md`。
  - 文档内容: 重写为基于 `Algo.rm_algo_workframe2base` 的转换链；引用新 L2 数据定义（`ArmBaseTcpPose` / `TcpInCamera` / `WorkFrameInArmBasePose`）。
  - 所有内部 wikilink 同步更新。
- **理由**: 主能力模块文档必须重写。
- **风险**: 文件重命名后，旧链接会断；需同步扫描引用 `common frame位姿转换` 的其他 L2 文档。
- **前提**: 用户在 `grill-me` 中确认重写意图。

#### B7. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`

- **优先级**: High
- **改动类型**: 标记 deprecated
- **推荐改动**: 在文档首部加弃用说明：
  > "⚠️ Deprecated since 2026-06 debug-common-frames L3 001。配置生成路线（基于 `FrameAlignmentConfig.common_anchor`）已废弃。替代品：见 [[arm-base 位姿转换]]；新配置由 `WorkFrameInBaseConfig` + `McapProcessConfig.work_frames_in_base` 直接提供。"
  > 配置示例保留为"历史参考"段，不删除。
  >
- **不**改动: 现有表格结构（仅头部加弃用段）。

#### B8. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/cleaned MCAP契约稳定.md`

- **优先级**: High
- **改动类型**: 段落更新
- **推荐改动**:
  - "契约不变量"段中关于"主位姿 topic" 的描述改为"主位姿 = `arm_base_tcp_pose`，frame_id = `<hand>_arm_base_link`；raw pose 保留为辅助字段；`tcp_common`/`camera_common` 字段保留为历史兼容，不推荐消费方依赖"。
  - 删除/置灰 "主位姿在 common frame" 的示例。

#### B9. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/基础校验与输出契约检查.md`

- **优先级**: Medium
- **改动类型**: 段落更新
- **推荐改动**: 把"以 `FrameAlignmentConfig` 为输入"的检查步骤改为"以 `WorkFrameInBaseConfig` + `McapProcessConfig` 为输入，检查 `arm-base` 输出是否齐备"。
- **不**改动: 校验器整体结构（仅替换输入引用）。

#### B10/B11. `夹爪开合配置生成.md` / `夹爪宽度提取.md`

- **优先级**: None
- **改动**: **不改**（与位姿框架无关）。

#### B12. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`

- **优先级**: High
- **改动类型**: 标记 deprecated
- **推荐改动**: 文档首部加弃用段，指向 `WorkFrameInBaseConfig.md`（如尚未存在则需在 B14 之后建）。
  > "⚠️ Deprecated. 该配置生成路线已废弃；新链路使用 [[WorkFrameInBaseConfig]] + [[McapProcessConfig.work_frames_in_base]]。"
  >

#### B13. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CommonFrameCameraPose.md`

- **优先级**: High
- **改动类型**: 标记 deprecated
- **推荐改动**: 文档首部加弃用段：
  > "⚠️ Deprecated. 当前主链路不再输出 common-frame 相机 pose；保留为历史字段，不推荐消费方依赖。"
  >

#### B14. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CommonFrameTcpPose.md`

- **优先级**: High
- **改动类型**: 标记 deprecated，**并新增 `ArmBaseTcpPose.md` / `TcpInCamera.md`**
- **推荐改动**:
  - 在本文件首部加弃用段，指向新文件：`[[ArmBaseTcpPose]]`。
  - **新增** `ArmBaseTcpPose.md`：描述 `frame_id` 语义（per RM65 base link）、坐标轴约定、单位（米/弧度）、`HandType` 字段。
  - **新增** `TcpInCamera.md`：描述中间产物（arm-base 转换前的 TCP in camera 位姿）。
  - 如 `WorkFrameInBaseConfig.md` 尚不存在，**新增**之。
- **前提**: 新增 L2 数据定义需符合 `约束文件/L2数据定义约束.md` 原子性原则；每文件单一数据概念。

#### B15. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CleanedMcap.md`

- **优先级**: High
- **改动类型**: 字段表重写
- **推荐改动**: 字段表里主位姿行改为 `arm_base_tcp_pose`（含 `frame_id`、`hand` 等子字段）；`tcp_common` / `camera_common` 标记为"已弃用字段，保留读取兼容"；raw pose 行不变。

#### B16. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1Config.md`

- **优先级**: High
- **改动类型**: 字段重写
- **推荐改动**: 配置字段表中删除 `frame_alignment` 节；新增 `work_frames_in_base` 节（指向 `WorkFrameInBaseConfig.md`）；新增 `output_arm_base_tcp_pose: bool` 字段说明。

#### B17. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1CleanReport.md`

- **优先级**: High
- **改动类型**: 字段重写
- **推荐改动**: 报告字段表中"主位姿产出数"等行指向 `arm_base_tcp_pose`；删除对 `tcp_common` 字段的统计指标（或标注为"历史字段统计"）。

#### B18. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CameraFromTcpExtrinsic.md`

- **优先级**: Low
- **改动**: 文档首部加一行"⚠️ Intermediate use only — 当前仅作为 TCP in camera 推导的中间量，不直接暴露给下游"。

#### B19/B20. `TcpFromCameraExtrinsic.md` / `GripperWidthSample.md` / `GripperCalibrationConfig.md`

- **优先级**: None
- **改动**: **不改**。

### Batch C：02_service 场景二六件套

#### C1. `DOCS/阶段二：数据清洗/02_service/场景二/目标描述.md`

- **优先级**: High
- **改动类型**: 措辞微调
- **推荐改动**: 找到"对 common-frame TCP pose 做滤波/校验后写入 MCAP_A"等表述改为"对 arm-base TCP pose 做滤波/校验后写入 MCAP_A；IK / MCAP_B / 关节限制检查模块**当前不作为主路径**，保留以备未来演进"。

#### C2. `DOCS/阶段二：数据清洗/02_service/场景二/背景信息.md`

- **优先级**: High
- **改动类型**: 段落更新
- **推荐改动**: "数据链路"段里场景二的输入由 `CommonFrameTcpPose` 改为 `ArmBaseTcpPose`；明确"下游 MCAP_A 的位姿 topic 是 arm-base"。

#### C3. `DOCS/阶段二：数据清洗/02_service/场景二/功能模块清单.md`

- **优先级**: High
- **改动类型**: 表格行级
- **推荐改动**:
  - 上游接口表：将 `CommonFrameTcpPose` 替换为 `ArmBaseTcpPose`；`FrameAlignmentConfig.common_anchor: left` 整行删除或改为"`ArmBaseTcpPose.frame_id` per RM65 base"。
  - 主链路模块表：`位姿滤波器` / `MCAP_A生成器` 行更新；`IK 求解与 MCAP_B 生成器` / `关节限制检查器` 行标注"未在当前主路径启用"。

#### C4. `DOCS/阶段二：数据清洗/02_service/场景二/输出程序与文件.md`

- **优先级**: High
- **改动类型**: 表格行级
- **推荐改动**: MCAP_A 输出表里位姿 topic 行改为 arm-base；说明帧 ID 来源；IK 产物（MCAP_B）行标注"当前不输出"。

#### C5. `DOCS/阶段二：数据清洗/02_service/场景二/执行约束.md`

- **优先级**: None
- **改动**: **不改**。

#### C6. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`

- **优先级**: High
- **改动类型**: 输入输出引用更新
- **推荐改动**: 输入从 `PoseFilterInputSequence`（基于 `CommonFrameTcpPose`）改为基于 `ArmBaseTcpPose` 的输入序列；同步引用 `[[ArmBaseTcpPose]]`。

#### C7. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`

- **优先级**: High
- **改动类型**: 字段表更新
- **推荐改动**: 写出 topic 名改为 `arm_base_tcp_pose`（frame_id per RM65 base）；telemetry summary 中 arm-base 字段替代 robot_base 字段；IK / MCAP_B 相关字段标注"未在当前主路径"。

#### C8. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`

- **优先级**: None
- **改动**: **不改**。

#### C9. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`

- **优先级**: Medium
- **改动类型**: 标注未启用
- **推荐改动**: 文档首部加："⚠️ 当前不在主路径；保留以备未来"。

#### C10. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`

- **优先级**: Medium
- **改动**: 同 C9。

#### C11. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`

- **优先级**: Medium
- **改动**: 同 C9。

#### C12. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`

- **优先级**: Medium
- **改动**: 文档首部加："⚠️ 当前不在主路径；MCAP_B 不输出。保留以备未来需要 IK 训练数据时回归。"

#### C13. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`

- **优先级**: High
- **改动类型**: 字段表更新
- **推荐改动**: pose topic 字段描述从 robot_base / common_frame 改为 arm-base；frame_id 字段指向 `[[ArmBaseTcpPose]]` 的约定。

#### C14. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterInputSequence.md`

- **优先级**: High
- **改动类型**: 输入样本类型更新
- **推荐改动**: 样本类型从 `CommonFrameTcpPose` 改为 `ArmBaseTcpPose`；前置 wikilink 同步。

#### C15. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteConfig.md`

- **优先级**: Medium
- **改动类型**: 字段表更新
- **推荐改动**: 配置字段中 `pose_topic` 默认值从 robot_base / common 改为 `arm_base_tcp_pose`；其他字段保留。

#### C16. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`

- **优先级**: Medium
- **改动类型**: 字段表更新
- **推荐改动**: telemetry 摘要字段中 arm-base 替代 robot_base。

#### C17. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/CommonToRobotBaseTransform.md`

- **优先级**: High
- **改动类型**: 标记 deprecated
- **推荐改动**: 首部加弃用段："⚠️ Deprecated. 当前主链路不再使用此转换；替代品：`[[arm-base 位姿转换]]` + `[[WorkFrameInArmBasePose]]`（由 `Algo.rm_algo_workframe2base` 完成）。"

#### C18. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/RobotBaseTcpPose.md`

- **优先级**: High
- **改动类型**: 标记 deprecated
- **推荐改动**: 首部加弃用段："⚠️ Deprecated. 替代品：`[[ArmBaseTcpPose]]`。注意：本文件原意指统一 robot base，**与当前 per-arm base 语义不同**；阅读旧文档时需特别小心此区别。"

### Batch D：02_service 公共文件

#### D1. `DOCS/阶段二：数据清洗/02_service/目标描述.md`

- **优先级**: Medium
- **改动类型**: 措辞微调
- **推荐改动**: 场景一行"把左右 Baton Mini raw pose 转换到 common frame 下的相机 pose"改为"转换到机械臂基坐标系（per RM65 base）下的 TCP pose"。

#### D2. `DOCS/阶段二：数据清洗/02_service/背景信息.md`

- **优先级**: Medium
- **改动**: 同 D1，对应场景一/场景二链路。

#### D3. `DOCS/阶段二：数据清洗/02_service/输出程序与文件.md`

- **优先级**: Medium
- **改动**: 场景一/二预期输出表里 pose 相关行更新为 arm-base。

### Batch E：debug 内部规划 + 当前进度

#### E1. `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/修改计划.md`

- **优先级**: Low
- **改动**: **不改**。此文档已与新方向一致，作为历史规划留存。

#### E2–E5. `01_删除位姿转换配置生成模块.md` / `02_使用官方函数生成基坐标系TCP位姿.md` / `03_场景二路线调整为MCAP_A到LeRobot_v3.md` / `04_数据定义文件修改方案.md` / `05_开发者验收交互文档.md`

- **优先级**: Low
- **改动**: **不改**（如个别措辞与新链路有出入，可在实施时微调，但原则上不动；这些是"规划过程留痕"）。

#### E6. `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/*.md`

- **优先级**: None
- **改动**: **不改**。已归档的执行摘要保持原样。

## Final Verification Wave（计划审核）

> 本计划为文档编辑清单，无代码改动，无需 4 个并行 review 代理。
> 计划审核流程（用户侧）：
>
> - 逐条 review Batch A–E 的编辑项。
> - 明确分支归属（见下方"分支归属决策"）。
> - 对需要 `grill-me` 的项（B6 / B14）单独确认意图后再实施。

### 分支归属决策（待用户确认）

- **默认建议**：按双机边界规范，Win 端文档编辑应落到对应 Service 场景分支（`service-s1` / `service-s2`），再由 Win 端合并到 `main`。
- **本次现状**：用户原始需求"更新一下当前分支"——当前分支是 `debug：common_frame`（非默认分支之一）。
- 默认把在"生成lerobot数据集"分支上进行文档改动

## Commit Strategy

- 建议每个 Batch 一次提交（提交信息形如 `docs(stage2/s1): 反映 arm-base TCP pose 数据流`）。
- 提交时机：每个 Batch 全部文件编辑完成、grep 复检通过后。
- 涉及重命名的 B6（`common frame位姿转换.md` → `arm-base 位姿转换.md`）需单独 commit 以便追踪。

## Success Criteria

- [ ] 计划文件本身被用户审核通过（或按反馈调整后通过）。
- [ ] 明确分支归属候选。
- [ ] B6 / B14 等高风险项（重命名、新增 L2 数据定义）经 `grill-me` 单独确认。
- [ ] 实施完成后，grep 复检通过：场景一/二文档中"主位姿"统一为 arm-base；deprecated 文件首部含显式弃用标记。

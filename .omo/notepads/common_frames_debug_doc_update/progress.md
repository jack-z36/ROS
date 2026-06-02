# common_frames_debug_doc_update — Progress

## Status
- Wave 1 (A, B, D): in_progress
- Wave 2 (C): pending (depends on B)
- Wave 3 (E): pending (mostly no-ops)

## Batch Items

### Batch A — 阶段入口与架构蓝图（6 文件）
- [ ] A1 `DOCS/阶段二：数据清洗/AGENTS.md` — 主链路措辞微调
- [ ] A2 `DOCS/阶段二：数据清洗/阶段目标描述.md` — 主位姿措辞微调
- [ ] A3 `DOCS/阶段二：数据清洗/背景信息.md` — 链路图更新
- [ ] A4 `DOCS/阶段二：数据清洗/阶段产出.md` — 代码资产表新增行
- [ ] A5 `DOCS/阶段二：数据清洗/当前进度.md` — **降级为不改**（双机边界：Win 不写当前进度.md）
- [ ] A6 `DOCS/阶段二：数据清洗/00_架构与路线图/数据清洗pipeline宏观蓝图.md` — 表格更新
- [ ] A7 `DOCS/阶段二：数据清洗/00_架构与路线图/阶段二实现路线图.md` — 表格更新
- [ ] A8 `DOCS/阶段二：数据清洗/00_架构与路线图/阶段二产物架构设计.md` — cleaned MCAP 契约

### Batch B — 02_service 场景一六件套 + L2（~14 文件）
- [ ] B1 场景一/目标描述.md — 重写位姿段
- [ ] B2 场景一/背景信息.md — 链路重写
- [ ] B3 场景一/功能模块清单.md — 接口表行级
- [ ] B4 场景一/输出程序与文件.md — 输出表行级
- [ ] B5 场景一/执行约束.md — **不改**（low）
- [ ] B6 场景一/L2能力模块/common frame位姿转换.md → 重命名为 arm-base 位姿转换.md
- [ ] B7 场景一/L2能力模块/位姿转换配置生成.md — deprecated 标记
- [ ] B8 场景一/L2能力模块/cleaned MCAP契约稳定.md — 段落更新
- [ ] B9 场景一/L2能力模块/基础校验与输出契约检查.md — 输入引用更新
- [ ] B12 场景一/L2数据定义/FrameAlignmentConfig.md — deprecated
- [ ] B13 场景一/L2数据定义/CommonFrameCameraPose.md — deprecated
- [ ] B14 场景一/L2数据定义/CommonFrameTcpPose.md — deprecated + 新增 ArmBaseTcpPose.md / TcpInCamera.md / WorkFrameInBaseConfig.md
- [ ] B15 场景一/L2数据定义/CleanedMcap.md — 字段表重写
- [ ] B16 场景一/L2数据定义/Scene1Config.md — 字段重写
- [ ] B17 场景一/L2数据定义/Scene1CleanReport.md — 字段重写
- [ ] B18 场景一/L2数据定义/CameraFromTcpExtrinsic.md — low（intermediate note）

### Batch C — 02_service 场景二六件套 + L2（~12 文件，依赖 B）
- [ ] C1 场景二/目标描述.md
- [ ] C2 场景二/背景信息.md
- [ ] C3 场景二/功能模块清单.md
- [ ] C4 场景二/输出程序与文件.md
- [ ] C6 场景二/L2能力模块/位姿滤波器.md
- [ ] C7 场景二/L2能力模块/MCAP_A生成器.md
- [ ] C9 场景二/L2能力模块/异常值检测器.md
- [ ] C10 场景二/L2能力模块/数据补全器.md
- [ ] C11 场景二/L2能力模块/关节限制检查器.md
- [ ] C12 场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md
- [ ] C13 场景二/L2数据定义/McapA.md
- [ ] C14 场景二/L2数据定义/PoseFilterInputSequence.md
- [ ] C15 场景二/L2数据定义/McapAWriteConfig.md
- [ ] C16 场景二/L2数据定义/McapAWriteSummary.md
- [ ] C17 场景二/L2数据定义/CommonToRobotBaseTransform.md — deprecated
- [ ] C18 场景二/L2数据定义/RobotBaseTcpPose.md — deprecated

### Batch D — 02_service 公共文件（3 文件）
- [ ] D1 02_service/目标描述.md
- [ ] D2 02_service/背景信息.md
- [ ] D3 02_service/输出程序与文件.md

### Batch E — debug 内部规划 + L3 归档
- [ ] E1-E6 — **不改**（debug 内部规划保持原状）

## 关键风险与降级
- A5 `当前进度.md`：按双机边界，Win 不写 `当前进度.md`。**降级为不改** A5。

## 2026-06-02 — Batch A completed

### Status
- [x] A1 `AGENTS.md` — 主链路替换为位姿级 pipeline，common_frame 降级标注
- [x] A2 `阶段目标描述.md` — cleaned MCAP 描述主位姿输出在 arm-base
- [x] A3 `背景信息.md` — topic 世界段新增位姿链路
- [x] A4 `阶段产出.md` — tcp_transform / arm_base_transform 拆为两行，各自补用途
- [x] A5 `当前进度.md` — **降级不改**（双机边界）
- [x] A6 `数据清洗pipeline宏观蓝图.md` — 场景一输出 + 对比表更新
- [x] A7 `阶段二实现路线图.md` — 场景一 P0 目标/输出列更新
- [x] A8 `阶段二产物架构设计.md` — cleaned MCAP 新增 topic/frame_id

### Verification
- 7 个目标文件全部 grep 确认含 arm-base/arm_base
- 未触碰禁止范围（当前进度.md、执行记录/、03_tasks/、01_runtime_mvp/、src/）

### Batch D — 02_service 公共文件（2026-06-02 ✅）
- [x] D1 02_service/目标描述.md — common frame → arm-base TCP pose
- [x] D2 02_service/背景信息.md — 场景一/二链路追加
- [x] D3 02_service/输出程序与文件.md — 预期输出表 arm_base_tcp_pose 主位姿标注

## Batch B Completion (2026-06-02)
- [x] B1 场景一/目标描述.md — 位姿段重写完成（arm-base 替代 common frame）
- [x] B2 场景一/背景信息.md — 数据链路图重写完成（raw → TCP in camera → arm-base TCP pose）
- [x] B3 场景一/功能模块清单.md — 接口表/dev检查项表行级更新完成（模块05重命名为 arm-base 位姿转换）
- [x] B4 场景一/输出程序与文件.md — 输出表行级更新完成（arm_base_tcp_pose 主位姿，旧字段标记为历史）
- [x] B6 场景一/L2能力模块/common frame位姿转换.md → arm-base 位姿转换.md 重命名+重写完成
- [x] B7 场景一/L2能力模块/位姿转换配置生成.md — deprecated 段添加完成
- [x] B8 场景一/L2能力模块/cleaned MCAP契约稳定.md — 段落更新完成（主位姿 = arm_base_tcp_pose）
- [x] B9 场景一/L2能力模块/基础校验与输出契约检查.md — 输入引用更新完成（WorkFrameInBaseConfig）
- [x] B12 场景一/L2数据定义/FrameAlignmentConfig.md — deprecated 段添加完成
- [x] B13 场景一/L2数据定义/CommonFrameCameraPose.md — deprecated 段添加完成
- [x] B14 场景一/L2数据定义/CommonFrameTcpPose.md — deprecated 段添加完成 + 新增 ArmBaseTcpPose.md / TcpInCamera.md / WorkFrameInBaseConfig.md
- [x] B15 场景一/L2数据定义/CleanedMcap.md — 字段表重写完成（arm_base_tcp_pose 主位姿）
- [x] B16 场景一/L2数据定义/Scene1Config.md — 字段重写完成（work_frames_in_base + output_arm_base_tcp_pose）
- [x] B17 场景一/L2数据定义/Scene1CleanReport.md — 字段重写完成（arm-base TCP pose 统计）
- [x] B18 场景一/L2数据定义/CameraFromTcpExtrinsic.md — intermediate note 添加完成
- [x] 验证: grep arm-base/arm_base 出现 74 次（原是 0），文件树完整，dev 菜单文件未被改动

## 2026-06-02 — 断链修复（common frame wikilink → arm-base）
- 发现：Batch B 重命名 `common frame 位姿转换.md` → `arm-base 位姿转换.md` 后，场景一 4 个文件仍引用旧 wikilink `[[common frame 位姿转换]]`，指向已删除文件。
- 修复：
  - `场景一/L2能力模块/位姿转换配置生成.md:73`
  - `场景一/L2数据定义/CommonFrameTcpPose.md:11`
  - `场景一/L2数据定义/CommonFrameCameraPose.md:11`
  - `场景一/L2数据定义/FrameAlignmentConfig.md:78`
- 操作：每条使用 Edit 工具精确字符串替换，未动整文件。
- 验证：
  - `grep "\[\[common frame 位姿转换\]\]" 场景一/` → 0 match ✅
  - `grep "\[\[arm-base 位姿转换\]\]" 场景一/` → 14 matches（含本批 4 处新增）✅
- 分支：`生成lerobot数据集` ✅
- git commit: 未调用

## Batch C Completion (2026-06-02)

### Status
- [x] C1 场景二/目标描述.md — arm-base TCP pose + IK/MCAP_B 不在主路径标注
- [x] C2 场景二/背景信息.md — 数据链路更新（ArmBaseTcpPose + MCAP_A pose topic arm-base）
- [x] C3 场景二/功能模块清单.md — 接口表/模块表 arm-base 更新 + IK/关节限制未启用标注
- [x] C4 场景二/输出程序与文件.md — 位姿 topic arm-base + IK 当前不输出
- [x] C5 场景二/执行约束.md — 计划标注不改
- [x] C6 场景二/L2能力模块/位姿滤波器.md — CommonFrameTcpPose → ArmBaseTcpPose 引用
- [x] C7 场景二/L2能力模块/MCAP_A生成器.md — IK 引用 arm-base 标注
- [x] C8 场景二/L2能力模块/触觉滤波器.md — 计划标注不改
- [x] C9 场景二/L2能力模块/异常值检测器.md — 首部 ⚠️ 未启用标注
- [x] C10 场景二/L2能力模块/数据补全器.md — 首部 ⚠️ 未启用标注
- [x] C11 场景二/L2能力模块/关节限制检查器.md — 首部 ⚠️ 未启用标注
- [x] C12 场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md — ✅ ⚠️ 未启用标注 + 断链修复
- [x] C13 场景二/L2数据定义/McapA.md — pose topic arm-base
- [x] C14 场景二/L2数据定义/PoseFilterInputSequence.md — CommonFrameTcpPose → ArmBaseTcpPose
- [x] C15 场景二/L2数据定义/McapAWriteConfig.md — pose_topic 默认值 arm_base_tcp_pose
- [x] C16 场景二/L2数据定义/McapAWriteSummary.md — arm-base 替代 robot_base
- [x] C17 场景二/L2数据定义/CommonToRobotBaseTransform.md — ⚠️ Deprecated 段
- [x] C18 场景二/L2数据定义/RobotBaseTcpPose.md — ⚠️ Deprecated 段

### 发现与观察
- C2 背景信息.md 原文使用 U+201C/U+201D 中文花引号，Edit 工具精确匹配需用同样字符；用 Python 作 fallback 处理。
- C15 McapAWriteConfig.md 原无 `pose_topic` 字段，按计划新增字段 + 默认值 `arm_base_tcp_pose`。
- C12 断链修复：`[[common frame 位姿转换]]` 替换为 `[[arm-base 位姿转换]]` 共 3 处（wikilink + 两处文档引用），均为 Batch B 重命名后的残留。
- IK 求解与 MCAP_B 生成器.md 文件名含空格和中文括号，grep 命令需要双引号包裹路径。

### Verification
- `grep "\[\[common frame 位姿转换\]\]" 场景二/` → 0 matches ✅
- arm-base/ArmBase/arm_base 总出现次数: 34 次（跨 16 个目标文件）✅
- 所有 deprecated 段使用统一格式 ✅
- 所有未启用标注使用 `⚠️ 当前不在主路径；保留以备未来。` ✅
- 分支：`生成lerobot数据集` ✅
- git commit: 未调用

## 最终完成状态

### 总体统计
- 修改 (M)：40 文件
- 删除 (D)：1 文件（`场景一/L2能力模块/common frame位姿转换.md` → 重命名为 `arm-base 位姿转换.md`）
- 新增 (??)：4 文件
  - `场景一/L2能力模块/arm-base 位姿转换.md`（B6 重命名目标）
  - `场景一/L2数据定义/ArmBaseTcpPose.md`（B14 新增）
  - `场景一/L2数据定义/TcpInCamera.md`（B14 新增）
  - `场景一/L2数据定义/WorkFrameInBaseConfig.md`（B14 新增）
- 总计：45 个文件路径变更，全部在 `DOCS/阶段二：数据清洗/` 范围内
- 总修改：193 行新增，273 行删除

### 范围验证
- ✅ src/ 代码未修改
- ✅ 04_debug/.../L3微元任务/completed/ L3 归档未修改
- ✅ 03_tasks/ 下任何 L3 任务文件未修改
- ✅ 01_runtime_mvp/ 未修改
- ✅ 任何 `执行记录.md` / `当前进度.md`（根）未修改（Win 不写边界遵守）
- ✅ AGENTS.md 受保护段（第 21-26、27-37、39-46 行）未破坏
- ✅ `00_架构与路线图/架构设计约束.md` 未修改
- ✅ 触觉滤波器 / 夹爪相关 L2 文件未修改

### 验证指标
- arm-base/arm_base 出现文件数：54
- ⚠️ Deprecated since 2026-06 标记文件数：7
- "未在当前主路径" / "当前不在主路径" 标记文件数：5
- 指向已删除 `common frame 位姿转换` 文件的断链：0

### 已知计划外（out-of-scope）残留引用
- `场景一/当前进度.md`（进度日志，Win 不写）— 4 处 common frame
- `场景一/执行记录.md`（执行日志，Win 不写）— N 处
- `场景一/执行约束.md`（约束规则，约束文件）— 4 处
- `场景一/docs/index.html`（HTML 可视化，plan 未列）— 5 处
- `场景二/执行约束.md`（约束规则）— 1 处
- 3 个 deprecated L2 数据定义文件保留 body 描述 — 设计意图
- `场景一/L2能力模块/位姿转换配置生成.md`（deprecated，保留 body）— 设计意图
- `arm-base 位姿转换.md:25` / `cleaned MCAP契约稳定.md:33` / `功能模块清单.md:99` — historical context，"接管了旧 common frame 转换链路"等

### 任务会话记录
- A 批：`ses_1798df4b7fferhorKnWJpReNHL`（2m 32s，7 文件）
- B 批：`ses_1798d25a7ffe0wgrp1QTZFW2jh`（3m 12s，~14 文件 + 4 新文件 + 1 删除）
- 断链修复：`ses_179867fe1ffecuWZk4L2bCm4R8`（26s，4 文件）
- C 批：`ses_17984c812ffeKhwMwZe3AMstLw`（3m 59s，~16 文件 + 1 断链修复）
- D 批：`ses_1798cd5c6ffe0X18EdbN0koHcU`（1m 6s，3 文件）

### Plan 执行完成
- [x] Batch A（7 项 + A5 降级）
- [x] Batch B（14 项 + 4 断链修复）
- [x] Batch C（16 项）
- [x] Batch D（3 项）
- [x] Batch E（不改项）
- 未调用 git commit（按计划）

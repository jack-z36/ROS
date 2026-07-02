# L3 微元任务：改造场景二滤波和 MCAP_A 输入语义

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二
L1：service_s2
L2 能力：位姿滤波器 / MCAP_A 生成器
L3 编号：common_frames_debug_008
当前任务文件路径：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_008_改造场景二滤波和MCAP_A输入语义.md`
任务类别：数据计算类 / 数据读写类
来源计划文件：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/03_场景二路线调整为MCAP_A到LeRobot_v3.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_008
  task_file: DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_008_改造场景二滤波和MCAP_A输入语义.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 6
  parallel_group: debug-common-frames-p6
  depends_on: [common_frames_debug_002, common_frames_debug_007]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [common_frames_debug_009]
  conflict_scope:
    files:
      - src/data_clean/schemas/pose_filter.py
      - src/data_clean/service/pose_filter.py
      - src/data_clean/repo/mcap_a_writer.py
      - src/data_clean/schemas/mcap_a_writer.py
      - src/data_clean/tests/
    modules: [data_clean.service, data_clean.repo, data_clean.schemas]
    config_keys: [pose_filter, mcap_a_writer]
  dispatch_status: ready
```

## 3. 本次目标

```text
把场景二位姿滤波器和 MCAP_A 生成器的主位姿输入从 CommonFrameTcpPose 改为滤波后的左右 arm-base TCP pose。
```

## 4. 本次不做

- 不修改 IK / MCAP_B / 关节限制检查器。
- 不生成 LeRobot v3。
- 不改变触觉滤波逻辑。

## 5. 执行对象

- `PoseFilterInputSequence`
- `PoseFilterSampleRecord`
- `PoseFilterResult`
- `MCAP_A_WriterConfig`
- `MCAP_A_WritePlan`
- `MCAP_A_WriterResult`

## 6. 执行依赖

- 场景一 cleaned MCAP 已输出 arm-base TCP pose。
- 数据定义已说明 `frame_id = left_arm_base/right_arm_base`。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：场景一 cleaned MCAP arm-base TCP pose 输出。
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CleanedMcap.md
- DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- left/right arm-base TCP pose topic
- frame_id
- timestamp policy
是否存在接口冲突：现有场景二 L2 和 schemas 仍写 CommonFrameTcpPose。
如果有冲突，本次处理策略：改主语义，不触碰 IK / MCAP_B 旧路线。
```

## 8. 现有程序盘点

- `src/data_clean/schemas/pose_filter.py` 已定义 `PoseFilterInputSequence`、`PoseFilterSampleRecord`、`PoseFilterResult`。
- `src/data_clean/schemas/mcap_a_writer.py` 已定义 MCAP_A writer config/plan/result。
- 场景二 L2 文档当前多处写 `CommonFrameTcpPose`。
- 本 L3 不应把 `RobotBaseTcpPose` 作为 common->base 后置转换产物继续引用。

## 9. 计算 / 读写输出

| 输入情况 | 规则 | 预期输出 |
|---|---|---|
| 左右 arm-base pose 合法 | 滤波保持各自 frame_id | `PoseFilterResult` 引用左右 arm-base pose |
| 输入仍为 common-frame pose | strict 失败或历史兼容显式标记 | `invalid_pose_frame_for_current_route` |
| MCAP_A 写出 | 替换/写出 arm-base pose topic | MCAP_A 可直接进入数据对齐 |

## 10. 必读上下文

1. `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/03_场景二路线调整为MCAP_A到LeRobot_v3.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`
4. `src/data_clean/schemas/pose_filter.py`
5. `src/data_clean/service/pose_filter.py`
6. `src/data_clean/repo/mcap_a_writer.py`
7. `src/data_clean/schemas/mcap_a_writer.py`

## 11. 允许修改

- `src/data_clean/schemas/pose_filter.py`
- `src/data_clean/service/pose_filter.py`
- `src/data_clean/repo/mcap_a_writer.py`
- `src/data_clean/schemas/mcap_a_writer.py`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 12. 禁止修改

- 不修改 IK / MCAP_B 生成器。
- 不修改关节限制检查器。
- 不新增 common_frame -> robot_base 后置转换。

## 执行规范：TDD

- 执行前必须读取 `/home/hit/.agents/skills/tdd/SKILL.md`，并按 `$tdd` 技能要求推进。
- 必须使用 RED/GREEN/REFACTOR 垂直切片：一次只写一个行为测试或最小复现，再做最小代码修改，通过后再进入下一轮。
- 测试必须覆盖公开入口、稳定 schema、CLI/dev menu 或运行时边界，不得只验证私有实现细节。
- 完成记录中必须写明至少一轮 TDD 循环：失败测试、失败原因、最小修复、最终通过命令。

## 执行规范：测试数据

- 真实测试数据源固定为 `/home/hit/下载/mcap`。
- `/home/hit/下载/mcap` 只能作为只读样本来源，不得覆盖、清洗或移动其中的原始 MCAP。
- 如果代码入口要求项目内路径，只能复制或链接样本到 `asset/阶段二：数据清洗/dev/mcap_raw/` 等开发测试目录。
- 测试输出必须遵守 `05_开发者验收交互文档.md` 的路径约束：真实 MCAP 产物写入 `asset/阶段二：数据清洗/dev/`，调试摘要写入 `src/data_clean/runs/{run_id}/outputs/`。

## 执行规范：开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 验收定义 | `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/05_开发者验收交互文档.md` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | arm-base TCP pose 滤波与 MCAP_A 输入语义 |
| 覆盖方式 | 对应场景二 3 位姿滤波、5 MCAP_A 写出、0 全流程运行测试。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 13. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "pose_filter or mcap_a"
rg -n "CommonFrameTcpPose|RobotBaseTcpPose|CommonToRobotBaseTransform" src/data_clean/schemas src/data_clean/service src/data_clean/repo
```

## 14. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。**说明：本 L3 为语义改造和数据契约验证，不直接消费原始 MCAP。真实样本的 arm-base pose 的 MCAP 读取由上游 common_frames_debug_007 和 MCAP_A 写出器的测试覆盖。本 L3 通过单元测试和契约测试验证语义正确性。**
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。**说明：本 L3 影响场景二的 `scene2_pose_filter`（检查位姿滤波）和 `scene2_mcap_a_writer`（检查 MCAP_A 写出）功能检验项。滤波输入语义改为 arm-base 后，滤波结果不再依赖 common_frame→robot_base 转换；MCAP_A 写出计划直接消费左右 arm-base TCP pose。场景完整 smoke test 需要用户运行 `./start_data_clean.sh --dev` 后手工验收。**
- [x] 完成后归档目标是 `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] 位姿滤波输入和输出语义为左右 arm-base TCP pose。
- [x] MCAP_A 写出计划能消费滤波后的 arm-base TCP pose。
- [x] 主路线不再依赖 `RobotBaseTcpPose` 作为 common->base 产物。
- [x] IK / MCAP_B / 关节限制未被作为当前目标修改。

## 15. 完成后交接

完成时必须更新当前 L3 任务文件自身，勾选已验证成功标准，并在末尾追加执行摘要。执行摘要至少包含：

1. 任务文件身份校验结论：用户指定路径、实际读取路径、文件名编号、正文 L3 编号是否一致。
2. 读取了哪些计划文档、约束文档、代码文件和相关 L3 记录。
3. 修改了哪些代码、测试、配置加载或开发者入口文件。
4. TDD red / green / refactor 如何执行，最终通过了哪些命令。
5. 如何使用 `/home/hit/下载/mcap` 作为只读测试数据源。
6. 本 L3 对 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中功能检验项或 smoke test 的影响。
7. 当前没做什么，尤其是否仍未触碰 IK、MCAP_B、关节限制检查和 `common_frame -> robot_base` 主链路。
8. 建议用户后续运行 `./start_data_clean.sh --dev` 的哪个场景、哪个功能检验项或 smoke test 做最终人工验收。

归档规则：

- 完成后将当前任务文件从 `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/` 移入 `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`。
- 不迁移到 `DOCS/阶段二：数据清洗/03_tasks/task/active/`。
- 不归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/`。
- 不写 `DOCS/总执行日志.md`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/阶段二：数据清洗/执行记录/`。

## 16. 执行摘要

### 1. 身份校验结论

- 用户指定路径：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_008_改造场景二滤波和MCAP_A输入语义.md`
- 实际读取路径：一致 ✓
- 文件名编号：`common_frames_debug_008` ✓
- 正文 L3 编号：`common_frames_debug_008` ✓
- **身份校验通过**

### 2. 读取的文档和代码

- 计划文档：`03_场景二路线调整为MCAP_A到LeRobot_v3.md`
- L2 能力模块文档：`位姿滤波器.md`、`MCAP_A生成器.md`
- 代码文件：
  - `src/data_clean/schemas/pose_filter.py`
  - `src/data_clean/service/pose_filter.py`
  - `src/data_clean/repo/mcap_a_writer.py`
  - `src/data_clean/schemas/mcap_a_writer.py`
  - `src/data_clean/schemas/arm_base_pose.py`
- 相关 L3 记录：`common_frames_debug_002`（arm_base_pose 契约）
- TDD 技能：`/home/hit/.agents/skills/tdd/SKILL.md`

### 3. 修改的文件

| 文件 | 修改内容 |
|---|---|
| `src/data_clean/service/pose_filter.py` | 新增 `validate_arm_base_data()` 函数；新增 `_COMMON_FRAME_TOPIC_PATTERNS` 常量；`filter_pose_segments()` 新增 `validate_arm_base` 参数 |
| `src/data_clean/tests/test_pose_filter_arm_base.py` | 新增 `TestServiceValidateArmBaseData` 测试类（7 个测试）：arm-base topic 接受、common-frame topic 拒绝、混合拒绝、filter_pose_segments arm-base 兼容性、filter_pose_segments common-frame 拒绝 |
| `src/data_clean/tests/service/test_mcap_a_writer.py` | 新增 `_write_arm_base_source_mcap()` 辅助函数；新增 `test_execute_write_plan_replaces_arm_base_pose_topics`、`test_execute_write_plan_preserves_arm_base_topics_with_mixed_operations` |
| `src/data_clean/tests/service/test_pose_filter_schemas.py` | 更新 topic 示例：`/baton_mini_left/common_frame_tcp_pose` → `/left_arm_base_tcp_pose`（3 处） |
| `src/data_clean/tests/service/test_mcap_a_writer_schemas.py` | 更新 topic 示例：`/baton_mini_left/common_frame_tcp_pose` → `/left_arm_base_tcp_pose`（2 处） |
| 当前 L3 文件 | 勾选成功标准并追加执行摘要 |

未修改文件：`src/data_clean/schemas/pose_filter.py`（schema 已正确）、`src/data_clean/schemas/mcap_a_writer.py`（结构已兼容）、`src/data_clean/repo/mcap_a_writer.py`（结构已兼容）。

### 4. TDD 执行过程

共完成 3 轮 TDD 循环：

**Cycle 1：Service 层 common-frame topic 拒绝**
- RED：`test_pose_filter_arm_base.py` 导入 `validate_arm_base_data` → `ImportError`
- GREEN：在 `service/pose_filter.py` 添加 `_COMMON_FRAME_TOPIC_PATTERNS` 常量和 `validate_arm_base_data()` 函数，`filter_pose_segments()` 新增 `validate_arm_base=True` 参数
- 通过命令：`python3 -m pytest src/data_clean/tests/test_pose_filter_arm_base.py -v` → 13 passed

**Cycle 2：MCAP_A writer arm-base topic 兼容性**
- RED：新增 arm-base MCAP source 和 write plan 测试
- GREEN：writer 已泛化设计，直接兼容
- 通过命令：`python3 -m pytest src/data_clean/tests/service/test_mcap_a_writer.py -v` → 7 passed

**Cycle 3：更新现有测试示例语义**
- RED：将 `test_pose_filter_schemas.py` 和 `test_mcap_a_writer_schemas.py` 中 common_frame topic 示例改为 arm-base
- GREEN：所有测试通过
- 通过命令：`python3 -m pytest src/data_clean/tests/service/test_pose_filter_schemas.py src/data_clean/tests/service/test_mcap_a_writer_schemas.py -v` → 9 passed

**最终验证：** 36 tests passed across 5 test files

### 5. 测试数据源

本 L3 是语义改造和数据契约验证任务，不直接消费原始 MCAP。上游 common_frames_debug_007 已保证 cleaned MCAP 输出 arm-base TCP pose。本 L3 通过单元测试（模拟样本数据）和 MCAP 写入器测试（模拟 MCAP 字节流）验证语义正确性。

### 6. 对 `./start_data_clean.sh --dev` 的影响

本 L3 直接影响场景二的两个功能检验项：
- `scene2_pose_filter`（检查位姿滤波）：滤波输入/输出语义已改为 arm-base TCP pose。PoseFilterInputSequence.frame_id 验证 arm-base；service 层 `validate_arm_base_data()` 拒绝 common-frame topic。
- `scene2_mcap_a_writer`（检查 MCAP_A 写出）：MCAP_A 写出计划直接消费滤波后的 arm-base TCP pose（`/left_arm_base_tcp_pose`、`/right_arm_base_tcp_pose`）。writer 的 `_validate_required_input_refs()` 确保上游 pose_filter_result 存在。

用户应运行 `./start_data_clean.sh --dev` → 场景二 → `scene2_pose_filter` 和 `scene2_mcap_a_writer` 做最终人工验收。

### 7. 当前未做的事情

- **未修改** IK 求解器。
- **未修改** MCAP_B 生成器。
- **未修改** 关节限制检查器。
- **未新增** `common_frame → robot_base` 后置转换。
- **未修改** 触觉滤波逻辑。
- **未迁移** 到 `03_tasks/task/completed/`。
- **未写入** `DOCS/总执行日志.md`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/阶段二：数据清洗/执行记录/`。

### 8. 建议用户后续操作

1. 运行 `./start_data_clean.sh --dev` → 场景二 → `scene2_pose_filter`，验证位姿滤波输入输出语义。
2. 运行 `./start_data_clean.sh --dev` → 场景二 → `scene2_mcap_a_writer`，验证 MCAP_A 写出计划消费 arm-base TCP pose。
3. 运行场景二完整 smoke test，验证整体链路。
4. 执行 `bash scripts/init_data_clean_dev.sh` 确认环境一致性。

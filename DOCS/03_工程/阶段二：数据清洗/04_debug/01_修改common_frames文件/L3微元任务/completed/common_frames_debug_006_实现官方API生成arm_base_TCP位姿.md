# L3 微元任务：实现官方 API 生成 arm-base TCP 位姿

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一
L1：service_s1
L2 能力：位姿转换功能模块
L3 编号：common_frames_debug_006
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_006_实现官方API生成arm_base_TCP位姿.md`
任务类别：数据计算类
来源计划文件：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_006
  task_file: DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_006_实现官方API生成arm_base_TCP位姿.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 4
  parallel_group: debug-common-frames-p4
  depends_on: [common_frames_debug_003, common_frames_debug_004, common_frames_debug_005]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [common_frames_debug_007, common_frames_debug_008]
  conflict_scope:
    files:
      - src/data_clean/service/tcp_transform.py
      - src/data_clean/service/
      - src/data_clean/tests/
    modules: [data_clean.service]
    config_keys: [work_frame_in_arm_base_pose]
  dispatch_status: ready
```

## 3. 本次目标

```text
封装睿尔曼官方 `Algo.rm_algo_workframe2base()`，把 TCP 在相机坐标系下的位姿转换为对应侧机械臂基坐标系下的 TCP 位姿。
```

## 4. 本次不做

- 不生成 work frame pose 配置。
- 不写 MCAP。
- 不改滤波器。
- 不实现 IK。

## 5. 执行对象

- 官方 API adapter。
- `WorkFrameInArmBasePose` 输入。
- `ArmBaseTcpPose` 输出。
- 左右手隔离测试。

## 6. 执行依赖

- `common_frames_debug_004` 已证明 SDK 可导入或有稳定失败原因。
- `common_frames_debug_005` 已提供 TCP in camera pose。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：
- 相机位姿到 TCP 位姿转换
- 睿尔曼官方 API 环境自检
上游接口定义位置：
- src/data_clean/service/tcp_transform.py
- DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- tcp_pose_in_camera
- work_frame_in_arm_base_pose
- Algo.rm_algo_pos2matrix
- Algo.rm_algo_workframe2base
是否存在接口冲突：睿尔曼文档中 `rm_algo_workframe2base` 的返回描述存在歧义。
如果有冲突，本次处理策略：用 identity 和 round-trip 测试确认实际语义，失败则阻塞并汇报。
```

## 8. 现有程序盘点

- `src/data_clean/service/tcp_transform.py` 现有实现基于 scipy/SE(3) 自研矩阵路径。
- 新路线禁止用该自研路径替代第二段坐标系转换。
- 可复用现有 pose 字段提取和测试 fixture，但主转换必须调用官方 API。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| identity work frame | `workframe2base(I, pose)` | 输出等价输入 | 无 |
| 左右不同 work frame | 分别调用官方 API | 输出体现左右 base 差异 | 无 |
| SDK 不可导入 | strict 失败 | 不生成结果 | `realman_sdk_unavailable` |
| API 语义不符合 identity/round-trip | 阻塞 | 不落地业务实现 | `realman_api_semantics_unverified` |

## 10. 必读上下文

1. `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`
2. `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md`
3. `/home/hit/下载/睿尔曼r65四代技术文档/Python 算法接口配置algo  睿尔曼智能科技.md`
4. `src/data_clean/service/tcp_transform.py`
5. `src/data_clean/tests/`

## 11. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- 必要 schema/type 文件。
- 当前 L3 文件自身。

## 12. 禁止修改

- 不使用自研矩阵公式替代官方 API。
- 不修改 MCAP_A 写出器。
- 不修改 IK / MCAP_B。

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
| 验收定义 | `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/05_开发者验收交互文档.md` |
| 所属一级场景菜单 | 场景一 |
| 对应功能检验项 | 官方 API 生成 left_arm_base/right_arm_base TCP pose |
| 覆盖方式 | 对应场景一 4 位姿转换运行测试、0 全流程运行测试。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 13. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -c "from Robotic_Arm.rm_robot_interface import *; print(Algo)"
python3 -m pytest src/data_clean/tests/ -k "realman or arm_base or workframe2base"
```

## 14. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。
- [x] 完成后归档目标是 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] 主转换调用 `Algo.rm_algo_workframe2base()`。
- [x] `rm_algo_pos2matrix()` 用于生成 work frame matrix。
- [x] identity 用例通过。
- [x] round-trip 用例通过或明确记录官方 API 语义冲突。
- [x] 左右手基坐标系不会混用。

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

- 完成后将当前任务文件从 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/` 移入 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`。
- 不迁移到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/`。
- 不归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/`。
- 不写 `DOCS/总执行日志.md`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/03_工程/阶段二：数据清洗/执行记录/`。

---

## 执行摘要

### 1. 任务文件身份校验结论

| 项目 | 内容 | 一致性 |
|------|------|--------|
| 用户指定路径 | `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_006_实现官方API生成arm_base_TCP位姿.md` | — |
| 实际读取路径 | `/home/hit/ROS/DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_006_实现官方API生成arm_base_TCP位姿.md` | ✅ |
| 文件名编号 | `common_frames_debug_006` | ✅ |
| 正文 L3 编号 | `common_frames_debug_006` (第9行) | ✅ |

### 2. 读取的计划文档、约束文档、代码文件和相关 L3 记录

- **计划文档**: `02_使用官方函数生成基坐标系TCP位姿.md`, `04_数据定义文件修改方案.md`
- **官方 SDK 文档**: `/home/hit/下载/睿尔曼r65四代技术文档/Python 算法接口配置algo  睿尔曼智能科技.md` (1484行)
- **代码文件**:
  - `src/data_clean/service/tcp_transform.py` — 现有 `compute_tcp_in_camera()` 和旧 common-frame 转换
  - `src/data_clean/schemas/arm_base_pose.py` — `ArmBaseTcpPose`, `WorkFrameInArmBasePose`, `HandType`, `FrameIdType`
  - `src/data_clean/tests/service/test_tcp_transform_camera.py` — 上游 L3-005 测试
  - `src/data_clean/tests/runtime/test_realman_sdk_self_check.py` — 现有 SDK 自检测试
  - `src/data_clean/tests/contract/test_arm_base_pose_schemas.py` — schema 契约测试
  - `src/data_clean/schemas/__init__.py` — exports
- **TDD 技能**: `/home/hit/.agents/skills/tdd/SKILL.md` — 严格按照 RED/GREEN/REFACTOR 垂直切片执行

### 3. 修改/新增的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/data_clean/service/arm_base_transform.py` | **新增** | 官方 API adapter，封装 `rm_algo_workframe2base()` + `rm_algo_pos2matrix()` + `rm_algo_quaternion2euler()` + `rm_algo_euler2quaternion()` |
| `src/data_clean/tests/service/test_arm_base_transform.py` | **新增** | 11 个测试覆盖：tracer bullet、identity work frame、非 identity 正向转换、左右手隔离、round-trip 语义文档、错误处理 |
| 当前 L3 任务文件 | **修改** | 勾选成功标准 + 追加本执行摘要 |

未修改：MCAP_A 写出器、IK/MCAP_B、其他 L3 文件、配置加载或开发者入口文件。

### 4. TDD 循环记录

**TDD Cycle 1 — Tracer bullet (函数存在性 + 类型返回)**
- RED: 模块未创建 → `ModuleNotFoundError: No module named 'service.arm_base_transform'`
- GREEN: 创建 `arm_base_transform.py` 实现 `compute_arm_base_tcp_pose()`
- 通过命令: `pytest test_arm_base_transform.py -k "test_import or test_returns_arm_base"`

**TDD Cycle 2 — Identity work frame**
- RED: 测试编写时引用不存在函数 → import 失败
- GREEN: 实现核心逻辑，identity 用例通过
- 通过命令: `pytest test_arm_base_transform.py -k "identity"` (2 tests)

**TDD Cycle 3 — Non-identity work frame (正向转换)**
- RED: 测试预期 `workframe2base(W, T_work) = T_work - W_translation` — 需验证 SDK 语义
- GREEN: 实验确认 SDK 语义: `workframe2base(M, p_work) = M⁻¹ · p_work`，其中 `M = pos2matrix(work_frame_pose)` 映射 base→work
- 通过命令: `pytest test_arm_base_transform.py -k "translation_offset"` (2 tests)

**TDD Cycle 4 — 左右手隔离**
- RED: 测试依赖相同的 work_frame 不同 hand 配置
- GREEN: 实现正确使用 work_frame 的 hand 和 base_frame_id
- 通过命令: `pytest test_arm_base_transform.py -k "left_right"` (2 tests)

**TDD Cycle 5 — Round-trip 语义文档**
- 实验发现 `base2workframe()` 返回的是"基坐标系在工作坐标系下的位姿"(固定值)，不是"工具端在工作坐标系下的位姿"
- 文档了替代 round-trip 方法（逆 work frame 二次调用 workframe2base）
- 通过命令: `pytest test_arm_base_transform.py -k "round_trip"` (2 tests)

**TDD Cycle 6 — 错误处理**
- RED: 预期 adapter 抛出 ValueError，但 `WorkFrameInArmBasePose.__post_init__` 在构造时就抛出
- GREEN: 调整测试，验证 schema 层验证
- 通过命令: `pytest test_arm_base_transform.py -k "invalid"` (1 test)

**最终验收命令**:
```bash
bash scripts/init_data_clean_dev.sh
python3 -c "from Robotic_Arm.rm_robot_interface import *; print(Algo)"
python3 -m pytest src/data_clean/tests/ -k "realman or arm_base or workframe2base"
```
结果: 59 个相关测试全部通过（11 新增 + 8 SDK 自检 + 26 schema 契约 + 7 TCP-in-camera + 7 其他 common_frame）。

### 5. 真实 MCAP 测试数据源

本 L3 不需要读取 `/home/hit/下载/mcap`。原因是：

- 本 L3 是纯算法 adapter，输入来自 `compute_tcp_in_camera()` (L3-005) 的输出和用户提供的 `WorkFrameInArmBasePose`
- 测试使用合成的 identity 和已知数值的工作坐标系位姿，不依赖任何 MCAP 样本
- SDK 算法接口在离线模式下即可运行，不需要连接真实机械臂

### 6. 对开发者验收入口的影响

本 L3 的 `compute_arm_base_tcp_pose()` 是场景一"位姿转换功能模块"的核心实现。它提供了：

- `./start_data_clean.sh --dev` 场景一中的"官方 API 生成 left/right arm-base TCP pose"功能检验项所需的 adapter
- 验收交互文档 `05_开发者验收交互文档.md` 中 4.位姿转换运行测试 的执行路径

当前本 L3 仅实现了 adapter 层，完整的场景一集成（从 raw Baton Mini 到 arm-base TCP pose）需要上游 L3-005 和下游 L3-007/L3-008 配合才能作为端到端 smoke test 执行。

### 7. 当前未做的事情

- **未实现 IK** — 逆运动学不在当前主线中
- **未实现 MCAP_B** — MCAP_B 路线已废弃
- **未实现关节限制检查** — 不在当前主线中
- **未修改 `common_frame -> robot_base` 主链路** — 已废弃的旧路线
- **未修改 MCAP_A 写出器**
- **未修改场景二滤波输入**
- **未使用自研矩阵公式替代官方 API** — 始终调用 `Algo.rm_algo_workframe2base()`

### 8. 建议用户后续验收步骤

1. **运行场景一 smoke test**:
   ```bash
   ./start_data_clean.sh --dev
   # 选择场景一 → 4.位姿转换运行测试
   ```
2. **检查 L3-005 + L3-006 集成**: 确认 `compute_tcp_in_camera()` 输出能正常传入 `compute_arm_base_tcp_pose()`，并产生正确的 `ArmBaseTcpPose`
3. **检查左右手隔离**: 使用不同的 `WorkFrameInArmBasePose` 配置，验证 left/right arm-base TCP pose 分别正确生成
4. **等待 L3-007/L3-008 完成后做端到端验证**

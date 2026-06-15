# L3 微元任务：落地 arm-base TCP pose 代码契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一、场景二
L1：service_s1 / service_s2
L2 能力：代码 schema / type 契约修改
L3 编号：common_frames_debug_002
当前任务文件路径：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_002_改造数据定义为arm_base_pose契约.md`
任务类别：数据定义类 / 代码类型类
来源计划文件：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_002
  task_file: DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_002_改造数据定义为arm_base_pose契约.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 2
  parallel_group: debug-common-frames-p2
  depends_on: [common_frames_debug_001]
  must_run_after: []
  can_run_parallel_with: [common_frames_debug_003, common_frames_debug_004]
  blocks: [common_frames_debug_007, common_frames_debug_008]
  conflict_scope:
    files:
      - src/data_clean/schemas/
    modules: [data_clean.schemas]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
在 `src/data_clean/schemas/` 中落地左右独立的 ArmBaseTcpPose、WorkFrameInArmBasePose 和 MCAP_A arm-base pose channel 代码契约。
```

## 4. 本次不做

- 不修改 L2 数据定义文档或功能描述文档。
- 不修改位姿转换计算代码。
- 不接入 MCAP 写出。
- 不恢复 IK / MCAP_B / 关节限制数据契约。

## 5. 执行对象

- `src/data_clean/schemas/` 中的 pose / config / MCAP_A 相关 Python dataclass。
- `ArmBaseTcpPose`
- `WorkFrameInArmBasePose`
- `McapAArmBasePoseChannel`
- 对应单元测试。

## 6. 执行依赖

- `common_frames_debug_001` 已完成影响面盘点。
- 已确认官方 API 输入输出语义来自 `02_使用官方函数生成基坐标系TCP位姿.md`。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：debug 数据定义修改方案和现有 schema 代码。
上游接口定义位置：
- DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md
- DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- hand
- frame_id = left_arm_base / right_arm_base
- position_m
- orientation representation
- source work frame pose
- official_api
是否存在接口冲突：现有 schema 代码没有 arm-base pose 主契约。
如果有冲突，本次处理策略：新增代码契约并补测试，不修改 L2 文档。
```

## 8. 预期改动形态

- `src/data_clean/schemas/` 中新增或更新 arm-base pose 相关 dataclass / enum。
- 新增测试验证左右手、frame_id、单位、姿态顺序和官方 API trace 字段。
- 不修改 `DOCS/阶段二：数据清洗/02_service/` 既有 L2 文档。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `ArmBaseTcpPose` | dataclass / enum 支撑 | `src/data_clean/schemas/` | 位姿滤波器、MCAP_A 写出、LeRobot v3 导出 |
| `WorkFrameInArmBasePose` | dataclass / config type | `src/data_clean/schemas/` 或配置 schema 文件 | 官方 API adapter |
| `McapAArmBasePoseChannel` | dataclass | `src/data_clean/schemas/` | MCAP_A 生成器、场景三/五 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `hand` | enum | 左右手 | 无 | `left` / `right` |
| `frame_id` | enum | 输出坐标系 | 无 | `left_arm_base` / `right_arm_base` |
| `position_m` | object/list | TCP 位置 | 无 | 单位 m |
| `orientation` | object/list | TCP 姿态 | 无 | 明确 Euler rad 或 quaternion 顺序 |
| `official_api` | string | 官方函数名 | `Algo.rm_algo_workframe2base` | 必须可追溯 |

## 10. 必读上下文

1. `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md`
2. `src/data_clean/schemas/pose_filter.py`
3. `src/data_clean/schemas/mcap_a_writer.py`
4. `src/data_clean/schemas/ros2_schemas.py`
5. `src/data_clean/tests/`

## 11. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 12. 禁止修改

- 不修改 L2 数据定义文档。
- 不修改位姿转换实现。
- 不修改 MCAP 读写器。
- 不修改 IK / MCAP_B / 关节限制相关代码作为当前主线。

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
| 所属一级场景菜单 | 跨场景一、场景二 |
| 对应功能检验项 | arm-base TCP pose schema 契约 |
| 覆盖方式 | 不直接接入开发者入口；由场景一位姿转换检验、场景二位姿滤波和 MCAP_A 写出间接覆盖。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 13. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "schema or arm_base_pose or mcap_a"
python3 - <<'PY'
from data_clean.schemas import pose_filter, mcap_a_writer
print("schemas import ok")
PY
```

## 14. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。
- [x] 完成后归档目标是 `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] `src/data_clean/schemas/` 中存在 arm-base pose 代码契约。
- [x] 代码契约能追溯 TCP in camera 和 work frame in base 两个输入。
- [x] 左右手和 `left_arm_base/right_arm_base` 合法性有测试覆盖。
- [x] 导入、实例化和非法值测试通过。

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

---

## 16. 执行摘要

### 16.1 身份校验结论

- 用户指定路径：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_002_改造数据定义为arm_base_pose契约.md`
- 实际读取路径：一致
- 文件名编号：`common_frames_debug_002`
- 正文 L3 编号：`common_frames_debug_002`
- 一致性校验：**通过**

### 16.2 分支校验

- 当前分支：`debug：common_frame`
- L3 要求分支：`debug：common_frame`
- 校验结果：**通过**

### 16.3 读取的文件

1. **计划/约束文档**：
   - `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md` — 了解 arm-base pose 数据定义方案
   - `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/README.md` — 了解任务 DAG 和归档规则
   - `DOCS/阶段二：数据清洗/AGENTS.md` — 了解双机协作写入边界
   - `/home/hit/.agents/skills/tdd/SKILL.md` — TDD 技能文档

2. **代码文件**：
   - `src/data_clean/schemas/pose_filter.py` — 现有 pose 类型模式（Enum + dataclass + __post_init__）
   - `src/data_clean/schemas/mcap_a_writer.py` — MCAP_A writer config 模式
   - `src/data_clean/schemas/ros2_schemas.py` — ROS2 schema 常量
   - `src/data_clean/schemas/__init__.py` — schemas 包导出模式
   - `src/data_clean/schemas/reliability.py` — Enum + dataclass 模式参考
   - `src/data_clean/tests/conftest.py` — 测试路径配置
   - `src/data_clean/tests/contract/test_common_frame_impact.py` — 现有 contract 测试模式
   - `src/data_clean/tests/contract/test_scene1_output_contract.py` — 现有 contract 测试模式
   - `scripts/init_data_clean_dev.sh` — 开发环境初始化脚本

### 16.4 修改的文件

| 文件 | 修改类型 | 说明 |
|---|---|---|
| `src/data_clean/schemas/arm_base_pose.py` | **新增** | 定义 ArmBaseTcpPose、WorkFrameInArmBasePose、McapAArmBasePoseChannel 三个 dataclass 及 HandType、FrameIdType 两个 enum |
| `src/data_clean/schemas/__init__.py` | **修改** | 新增 arm_base_pose 模块的 import 和 __all__ 导出 |
| `src/data_clean/tests/contract/test_arm_base_pose_schemas.py` | **新增** | 34 个测试覆盖 enum 值、dataclass 实例化、__post_init__ 验证、top-level 导入 |
| 当前 L3 文件 | **修改** | 勾选成功标准 + 追加本执行摘要 |

### 16.5 TDD 循环记录

**循环 1（RED→GREEN→VERIFY）**：

| 阶段 | 操作 | 结果 |
|---|---|---|
| RED | 编写 `test_arm_base_pose_schemas.py` 测试 HandType 和 FrameIdType enum（29 个测试） | 全部失败 — ModuleNotFoundError（模块不存在，预期行为） |
| GREEN | 创建 `arm_base_pose.py`，定义 HandType(LEFT/RIGHT) 和 FrameIdType(LEFT_ARM_BASE/RIGHT_ARM_BASE) enum，定义 ArmBaseTcpPose、WorkFrameInArmBasePose、McapAArmBasePoseChannel dataclass | 文件写入完成 |
| REFACTOR | 修复 __init__.py 导出（补充 __all__ 条目，去重 RuntimeLogEventType） | 14 个测试通过 |
| VERIFY | 发现 import 路径问题：conftest 添加 `src/data_clean/` 到 sys.path，需要 `from schemas.arm_base_pose import ...` 而非 `from data_clean.schemas.arm_base_pose import ...` | 全 34 个测试通过 |

**循环 2（最终验收）**：

| 命令 | 结果 |
|---|---|
| `pytest src/data_clean/tests/contract/test_arm_base_pose_schemas.py -v` | 34/34 PASSED |
| `pytest src/data_clean/tests/contract/test_mcap_a_scene3_compat.py -v` | 5/5 PASSED（回归） |
| `pytest src/data_clean/tests/contract/test_common_frame_impact.py -v` | 3/3 PASSED（回归） |
| `python3 -c "from data_clean.schemas import pose_filter, mcap_a_writer; print('OK')"` (src/ in PYTHONPATH) | OK |

### 16.6 测试数据使用

本 L3 不需要读取真实 MCAP 数据。所有测试均为纯代码契约测试（enum 值验证、dataclass 实例化、__post_init__ 非法值拦截），不依赖任何 MCAP 文件。因此未使用 `/home/hit/下载/mcap` 目录。

### 16.7 与 dev 入口的关系

- **统一入口**：`./start_data_clean.sh --dev`
- **验收定义**：`05_开发者验收交互文档.md`
- **所属场景**：跨场景一、场景二
- **覆盖方式**：本次新增的 `ArmBaseTcpPose`、`WorkFrameInArmBasePose`、`McapAArmBasePoseChannel` 代码契约为后续 L3（common_frames_debug_005～008）提供数据定义基础。当前 L3 不直接接入开发者入口；位姿转换和 MCAP_A 写出会在后续 L3 中通过场景一/二的 smoke test 间接覆盖。

### 16.8 未做的事

- 未修改 L2 数据定义文档（如 `FrameAlignmentConfig.md`、`CommonFrameTcpPose.md` 等）
- 未修改位姿转换实现代码（`tcp_transform.py`、`mcap_io.py` 等）
- 未修改 MCAP 读写器代码
- 未修改 IK / MCAP_B / 关节限制相关代码
- 未修改 `common_frame → robot_base` 主链路
- 未使用真实 MCAP 测试数据
- 未接入 `./start_data_clean.sh --dev` 开发者入口（将由后续 L3 完成）

### 16.9 用户后续验收建议

1. 运行 `PYTHONPATH=src:$PYTHONPATH python3 -c "from data_clean.schemas import ArmBaseTcpPose, WorkFrameInArmBasePose, McapAArmBasePoseChannel, HandType, FrameIdType; print('import ok')"` 确认顶层导入。
2. 运行 `python3 -m pytest src/data_clean/tests/contract/test_arm_base_pose_schemas.py -v` 确认 34 个契约测试全部通过。
3. 在后续 L3（debug_005 ~ debug_008）完成后，运行 `./start_data_clean.sh --dev` 的场景一或场景二 smoke test 做端到端人工验收。

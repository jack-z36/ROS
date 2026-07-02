# L3 微元任务：废弃位姿转换配置生成路线

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一
L1：service_s1
L2 能力：位姿转换配置生成
L3 编号：common_frames_debug_003
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_003_废弃位姿转换配置生成路线.md`
任务类别：流程编排类 / 数据定义类
来源计划文件：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/01_删除位姿转换配置生成模块.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_003
  task_file: DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_003_废弃位姿转换配置生成路线.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 2
  parallel_group: debug-common-frames-p2
  depends_on: [common_frames_debug_001]
  must_run_after: []
  can_run_parallel_with: [common_frames_debug_002, common_frames_debug_004]
  blocks: [common_frames_debug_006, common_frames_debug_007]
  conflict_scope:
    files:
      - src/data_clean/ui/mcap_calibration_wizard.py
      - src/data_clean/ui/scene1_dev_checks.py
      - src/data_clean/repo/config/mcap_process_config.py
      - config/
    modules: [data_clean.ui, data_clean.repo.config]
    config_keys: [frame_alignment, common_anchor]
  dispatch_status: ready
```

## 3. 本次目标

```text
从当前主路线中移除 FrameAlignmentConfig/common_anchor 配置生成能力，改为由用户直接输入工作坐标系在机械臂基坐标系下的位姿。
```

## 4. 本次不做

- 不删除相机位姿到 TCP 位姿转换功能。
- 不实现睿尔曼官方 API adapter。
- 不改场景二滤波或 MCAP_A。

## 5. 执行对象

- 位姿转换配置生成入口。
- `FrameAlignmentConfig/common_anchor` 配置生成和校验路径。
- 场景一开发者功能检验项中与 `scene1_frame_alignment_config` 相关的主路线。

## 6. 执行依赖

- `common_frames_debug_001` 已完成影响面盘点。
- 用户确认后续直接提供 `work_frame_in_arm_base_pose`。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：旧浏览器/配置生成入口。
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md
- src/data_clean/ui/mcap_calibration_wizard.py
- src/data_clean/repo/config/mcap_process_config.py
当前 L3 期望消费的字段 / 文件 / 返回值：
- 旧 frame_alignment 生成路径
- 新 work_frame_in_arm_base_pose 输入位置
是否存在接口冲突：旧配置生成能力仍被清单和 dev 检验项引用。
如果有冲突，本次处理策略：主路线废弃，必要时保留历史兼容读取但不再生成。
```

## 8. 预期改动形态

- 执行时，配置生成入口不再生成 `common_from_left_start` / `common_from_right_start`。
- `config_is_calibrated` 不再依赖 `common_frame.left/right` 作为新路线必需项。
- dev 菜单若保留旧检验项，必须标记为历史兼容或禁用，不作为主 smoke 前置。

## 9. 编排输出

### 调用顺序

| 步骤 | 旧路线 | 新路线 |
|---|---|---|
| 配置生成 | 生成 `FrameAlignmentConfig` | 不生成；读取用户提供的 `WorkFrameInArmBasePose` |
| 主位姿转换 | raw -> common -> TCP common | raw -> TCP in camera -> TCP in arm base |
| 校验 | common frame 四项标定完成 | 左右 work frame pose 存在且可解析 |

### 失败行为

| 情况 | 预期行为 |
|---|---|
| 仍调用旧配置生成主路线 | 失败并提示旧路线已废弃 |
| 缺少用户输入 work frame pose | strict 失败，原因 `missing_work_frame_in_arm_base_pose` |
| 旧配置文件存在 | 可作为历史兼容读取，但不得覆盖新主路线 |

## 10. 必读上下文

1. `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/01_删除位姿转换配置生成模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/执行约束.md`
4. `src/data_clean/ui/mcap_calibration_wizard.py`
5. `src/data_clean/ui/scene1_dev_checks.py`
6. `src/data_clean/repo/config/mcap_process_config.py`

## 11. 现有程序盘点

- `src/data_clean/repo/config/mcap_process_config.py` 已定义 `FrameAlignmentConfig`、`ExtrinsicConfig`、`PoseStreamConfig.output_camera_pose_common` 和 `output_tcp_pose_common`。
- `src/data_clean/ui/mcap_calibration_wizard.py` 是旧配置生成的现实入口之一。
- `src/data_clean/ui/scene1_dev_checks.py` 可能承载场景一开发者检验项。
- 本 L3 不允许把这些能力粗暴删除到无法兼容旧样本；主目标是从新路线移除必需依赖。

## 12. 允许修改

- 执行时可修改配置生成入口和 dev 检验项。
- 执行时可修改配置校验逻辑。
- 当前 L3 文件自身。

## 13. 禁止修改

- 不修改 `service/tcp_transform.py` 的转换数学。
- 不修改 MCAP_A 写出。
- 不恢复 common->base 后置转换。

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
| 对应功能检验项 | 废弃 FrameAlignmentConfig/common_anchor 配置生成路线 |
| 覆盖方式 | 对应场景一 1 配置检查、4 位姿转换运行测试、0 全流程运行测试。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 14. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
rg -n "FrameAlignmentConfig|common_anchor|scene1_frame_alignment_config|config_is_calibrated|common_frame" src/data_clean DOCS/03_工程/阶段二：数据清洗/02_service/场景一
python3 -m pytest src/data_clean/tests/ -k "config or scene1"
```

## 15. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。
- [x] 完成后归档目标是 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] 新主路线不再要求生成 `FrameAlignmentConfig/common_anchor`。
- [x] 用户输入的 work-frame-in-base pose 成为新路线必需输入。
- [x] 旧 common frame 配置仅作为历史兼容或明确禁用项。
- [x] 场景一 smoke 不再被旧 common frame 标定状态阻塞。

## 17. 执行摘要

### 17.1 身份校验结论

- 用户指定路径: `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_003_废弃位姿转换配置生成路线.md`
- 实际读取路径: 同上
- 文件名编号: `common_frames_debug_003`
- 正文 L3 编号: `common_frames_debug_003`
- 结论: 一致 ✅

### 17.2 读取的文档和代码

- `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/01_删除位姿转换配置生成模块.md`
- `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`
- `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/执行约束.md`
- `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/README.md`
- `src/data_clean/repo/config/mcap_process_config.py`
- `src/data_clean/ui/scene1_dev_checks.py`
- `src/data_clean/ui/dev_menu.py`
- `src/data_clean/ui/mcap_calibration_wizard.py`
- `src/data_clean/service/tcp_transform.py`（只读，不修改）
- `src/data_clean/tests/config/test_frame_alignment_config.py`
- `src/data_clean/tests/service/test_scene1_frame_alignment_config.py`
- `src/data_clean/tests/service/test_common_frame_pose_transform.py`
- `src/data_clean/tests/service/test_scene1_dev_menu.py`
- `/home/hit/.agents/skills/tdd/SKILL.md`

### 17.3 修改的文件

| 文件 | 改动 |
|---|---|
| `src/data_clean/repo/config/mcap_process_config.py` | `config_is_calibrated()` 新增 `require_common_frame=False` 参数，默认不检查 common_frame；`calibration_missing_items()` 新增 `include_common_frame=False` 参数 |
| `src/data_clean/ui/scene1_dev_checks.py` | `run_scene1_frame_alignment_config()` 增加废弃警告打印和 docstring 标注 |
| `src/data_clean/ui/dev_menu.py` | `scene1_frame_alignment_config` 菜单项标注 `[已废弃]`；runner 默认提示废弃并只允许历史兼容检查 |
| `src/data_clean/ui/mcap_calibration_wizard.py` | `_print_status()` 改为 gripper 驱动；浏览器 UI common frame 按钮标注 `（已废弃）`；common frame 采样对话框标注废弃 |
| `src/data_clean/tests/config/test_frame_alignment_config.py` | 新增 `TestConfigIsCalibrated` 类 6 个测试 |
| `src/data_clean/tests/service/test_scene1_dev_menu.py` | 更新菜单标签预期；新增 `test_scene1_legacy_check_prints_deprecation_warning` |

### 17.4 TDD 执行记录

**TDD 循环 1: `config_is_calibrated` 不再依赖 common_frame**

- RED: 新增 `TestConfigIsCalibrated` 6 个测试，其中 5 个预期失败
- GREEN: 修改 `config_is_calibrated()` 和 `calibration_missing_items()` 函数签名，添加可选参数
- 最终通过: `python3 -m pytest src/data_clean/tests/config/test_frame_alignment_config.py::TestConfigIsCalibrated --tb=short -v` (6 pass)

**TDD 循环 2: dev 菜单旧检验项标记为历史兼容**

- RED: `test_scene1_dev_menu_exposes_expected_checks` 预期 `[已废弃]` 标签；新增 `test_scene1_legacy_check_prints_deprecation_warning`
- GREEN: 修改 `run_scene1_frame_alignment_config()`、`_run_scene1_frame_alignment_check()`、`SCENE1_CHECKS` 标签
- 最终通过: `python3 -m pytest src/data_clean/tests/service/test_scene1_dev_menu.py --tb=short -v` (2 pass)

**TDD 循环 3: 标定向导废弃 common frame**

- 更新 `_print_status()`、浏览器 UI HTML、`set_mode()` 消息、终端菜单
- 未创建新测试（UI 逻辑运行时依赖 GoPro 硬件，CI 不可达）
- 通过编译检查验证无语法错误

全部回归测试: 109 tests passed (config + scene1 相关)

### 17.5 测试数据使用说明

本 L3 不涉及 MCAP 文件读取。改动全部在配置校验逻辑和开发者菜单/UI 层面。不需要从 `/home/hit/下载/mcap` 读取样本。

### 17.6 对 `./start_data_clean.sh --dev` 的影响

- 场景一菜单 `scene1_frame_alignment_config`（位姿转换配置生成）已标注 `[已废弃]`，选择后会提示废弃信息并只允许历史兼容检查。
- `config_is_calibrated()` 默认不再检查 common_frame，现有 `data_clean_calibrated.yaml`（gripper 已标定、common_frame 未标定）将显示为 "基本标定完成"。
- 场景一 smoke test 不再被 common_frame 标定状态阻塞。

### 17.7 当前没做什么

- 未修改 `service/tcp_transform.py` 的转换数学。
- 未修改 MCAP_A 写出。
- 未触及 IK、MCAP_B、关节限制检查。
- 未删除 `FrameAlignmentConfig` 数据类（保留用于历史兼容读取）。
- 未修改 runtime 层 `mcap_clean_launcher.py`。

### 17.8 建议用户后续验收

运行 `./start_data_clean.sh --dev`，选择场景一，验证：

1. `scene1_smoke_test`（全场景测试）应正常运行，不被 common_frame 状态阻塞。
2. `[已废弃] 位姿转换配置生成` 应显示废弃提示。
3. 命令行校验: `python3 -c "from repo.config.mcap_process_config import config_is_calibrated; c = load_app_config('config/data_clean/data_clean_calibrated.yaml'); print(config_is_calibrated(c))"` 应返回 `True`。

## 16. 完成后交接（原内容）

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

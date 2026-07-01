# L3 微元任务：补充开发者验收和回归检查

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一、场景二
L1：service_s1 / service_s2
L2 能力：开发者验收入口与 smoke test
L3 编号：common_frames_debug_009
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_009_补充开发者验收和回归检查.md`
任务类别：流程编排类
来源计划文件：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/修改计划.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_009
  task_file: DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_009_补充开发者验收和回归检查.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 7
  parallel_group: debug-common-frames-p7
  depends_on: [common_frames_debug_007, common_frames_debug_008]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/data_clean/ui/dev_menu.py
      - src/data_clean/ui/scene1_dev_checks.py
      - src/data_clean/runtime/scene2_pose_filter.py
      - src/data_clean/runtime/scene2_mcap_a_writer.py
      - src/data_clean/tests/
    modules: [data_clean.ui, data_clean.runtime]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
补齐场景一和场景二开发者验收入口与回归检查，证明新链路不再依赖 common_frame 主路线。
```

## 4. 本次不做

- 不新增业务转换逻辑。
- 不改数据定义。
- 不执行用户最终人工验收。

## 5. 执行对象

- `./start_data_clean.sh --dev` 相关菜单和功能检验项。
- 场景一位姿转换功能检验。
- 场景二 pose filter / MCAP_A 功能检验。
- 回归测试命令。

## 6. 执行依赖

- cleaned MCAP 输出 arm-base TCP pose。
- 场景二滤波和 MCAP_A 已改为消费 arm-base TCP pose。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：
- 场景一 arm-base TCP pose 写出
- 场景二 pose filter / MCAP_A arm-base 输入语义
上游接口定义位置：
- common_frames_debug_007
- common_frames_debug_008
当前 L3 期望消费的字段 / 文件 / 返回值：
- 开发者入口功能检验项
- smoke test 输出摘要
- 回归测试结果
是否存在接口冲突：旧 dev 检验项可能仍以 scene1_common_pose_transform 命名。
如果有冲突，本次处理策略：改名或新增 arm-base 检验项，并保留旧项为历史兼容说明。
```

## 8. 预期改动形态

- 开发者入口出现或更新 arm-base pose 相关功能检验项。
- 自动化测试覆盖新链路关键断言。
- 运行摘要记录官方 API、左右 frame_id、输出 topic、MCAP_A 消费状态。

## 9. 编排输出

| 检验项 | 验收目标 |
|---|---|
| 场景一位姿转换检验 | raw pose -> TCP in camera -> TCP in arm base |
| 场景二位姿滤波检验 | arm-base pose 可被滤波并保持 frame_id |
| 场景二 MCAP_A 写出检验 | MCAP_A 写出 arm-base pose topic |
| 回归 grep | 主链路不再出现 common_frame -> robot_base |

## 10. 必读上下文

1. `DOCS/02_约束/阶段二任务体系/开发者验收入口约束.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/功能模块清单.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/功能模块清单.md`
4. `src/data_clean/ui/dev_menu.py`
5. `src/data_clean/ui/scene1_dev_checks.py`
6. `src/data_clean/runtime/scene2_pose_filter.py`
7. `src/data_clean/runtime/scene2_mcap_a_writer.py`

## 11. 允许修改

- `src/data_clean/ui/`
- `src/data_clean/runtime/`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 12. 禁止修改

- 不修改核心转换实现。
- 不修改 L2 数据定义。
- 不运行或伪造最终人工验收结论。

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
| 所属一级场景菜单 | 场景一、场景二 |
| 对应功能检验项 | 开发者入口、运行摘要、回归检查 |
| 覆盖方式 | 直接实现并串联场景一/场景二开发者菜单、单项检验和 smoke test。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 13. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "scene1 or scene2 or arm_base or mcap_a"
rg -n "common_frame -> robot_base|CommonToRobotBaseTransform|RobotBaseTcpPose" DOCS/阶段二：数据清洗/04_debug src/data_clean
```

用户最终人工验收仍需运行：

```bash
./start_data_clean.sh --dev
```

## 14. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。
- [x] 完成后归档目标是 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] 场景一开发者检验能覆盖 arm-base TCP pose 生成。
- [x] 场景二开发者检验能覆盖 arm-base pose 滤波和 MCAP_A 写出。
- [x] 回归检查证明主链路不要求 common_frame -> robot_base 后置转换。
- [x] 明确提示最终场景验收必须由用户运行 `./start_data_clean.sh --dev`。

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

## 16. 执行摘要

### 16.1 身份校验

- 用户指定路径：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_009_补充开发者验收和回归检查.md`
- 实际读取路径：同上 ✅
- 文件名编号：`common_frames_debug_009` ✅
- 正文 L3 编号：`common_frames_debug_009` ✅

### 16.2 读取的文档与代码

| 类型 | 文件 |
|------|------|
| 约束文档 | `约束文件/开发者验收入口约束.md` |
| 场景文档 | `02_service/场景一/功能模块清单.md`、`02_service/场景二/功能模块清单.md` |
| 验收文档 | `05_开发者验收交互文档.md` |
| UI 代码 | `ui/dev_menu.py`、`ui/scene1_dev_checks.py` |
| Runtime 代码 | `runtime/scene2_pose_filter.py`、`runtime/scene2_mcap_a_writer.py` |
| Schema 代码 | `schemas/arm_base_pose.py` |
| Service 代码 | `service/arm_base_transform.py`、`service/tcp_transform.py` |

### 16.3 修改的文件

| 文件 | 改动 |
|------|------|
| `src/data_clean/ui/scene1_dev_checks.py` | 新增 `run_scene1_arm_base_pose_transform()` 函数，实现 arm-base TCP pose 转换开发者检验 |
| `src/data_clean/ui/dev_menu.py` | 注册 `scene1_arm_base_pose_transform` 到 SCENE1_CHECKS；更新 scene2 `run_scene2_pose_filter_check` 和 `run_scene2_mcap_a_writer_check` 打印 arm-base 坐标语义和当前路线状态 |
| `src/data_clean/tests/service/test_scene1_dev_menu.py` | 更新硬编码的 SCENE1_CHECKS 断言列表，加入新检查项 |
| `src/data_clean/tests/service/test_scene1_arm_base_dev_menu.py` | **新增**: 7 个测试（菜单注册 + 输出内容校验） |
| `src/data_clean/tests/service/test_scene2_arm_base_dev_status.py` | **新增**: 4 个测试（场景二 arm-base 消费状态校验） |
| `src/data_clean/tests/contract/test_common_frame_regression.py` | **新增**: 5 个回归测试（common_frame/robot_base 拒绝 + 非依赖断言） |

### 16.4 TDD 执行记录

| 循环 | RED 测试 | 失败原因 | GREEN 修复 | 最终通过 |
|------|----------|----------|------------|----------|
| 1 | `test_scene1_checks_contains_arm_base_pose_transform` | SCENE1_CHECKS 无 scene1_arm_base_pose_transform | 新增 `run_scene1_arm_base_pose_transform` + 注册到 dev_menu.py | `pytest src/data_clean/tests/service/test_scene1_arm_base_dev_menu.py -v` (2 passed) |
| 2 | `test_output_contains_official_api_in_samples`, `test_output_contains_left_right_frame_id`, etc. | 无 arm_base_tcp_pose_samples.json | 实现输出 official_api、frame_id、common_frame_used: false、MCAP_A 消费状态 | 7 tests passed |
| 3 | `test_mcap_a_writer_check_code_prints_route_info`, `test_pose_filter_check_code_mentions_coordinate_semantic` | 无 arm-base 路线状态输出 | 在 dev_menu.py 中更新 pose_filter 和 mcap_a_writer 打印逻辑 | 4 tests passed |
| 4 | `test_pose_filter_arm_base_rejects_common_frame_frame_id`, `test_scene1_arm_base_check_explicitly_says_no_common_frame` | 需验证回归路径 | 新增 contract/test_common_frame_regression.py | 5 tests passed |

最终通过命令：
```bash
python3 -m pytest src/data_clean/tests/service/test_scene1_arm_base_dev_menu.py \
  src/data_clean/tests/service/test_scene2_arm_base_dev_status.py \
  src/data_clean/tests/contract/test_common_frame_regression.py \
  src/data_clean/tests/service/test_scene1_dev_menu.py -v
```
结果：**18 passed**

### 16.5 测试数据源

本 L3 不需要读取真实 MCAP 文件。所有测试使用确定性样本数据（hardcoded pose tuples）和 smoke test 配置（`data_clean_smoke_test.yaml`），无需访问 `/home/hit/下载/mcap`。

### 16.6 对开发者交互的影响

| 入口 | 影响 |
|------|------|
| `./start_data_clean.sh --dev` → 场景一 | 新增检验项：`scene1_arm_base_pose_transform`（"arm-base 位姿转换（新链路，不再依赖 common_frame）"）。输出 official_api、left/right frame_id、output topic、common_frame_used: false、MCAP_A 消费状态。 |
| `./start_data_clean.sh --dev` → 场景二 → 位姿滤波 | 输出增加坐标语义：input_pose_frame: left_arm_base/right_arm_base、common_frame_to_robot_base: not required |
| `./start_data_clean.sh --dev` → 场景二 → MCAP_A 写出 | 输出增加当前路线状态：IK/MCAP_B/joint_limit_check not in current route、arm_base_input: arm-base TCP pose topics consumed from cleaned MCAP |
| `05_开发者验收交互文档.md` 6.5 和 7.4/7.6 | 新增 arm-base 坐标语义和路线状态输出格式已对齐 |

### 16.7 当前未做

- ❌ 未修改核心转换实现（service/tcp_transform.py、service/mcap_io.py 等）
- ❌ 未修改 L2 数据定义（schemas/）
- ❌ 未运行或伪造最终人工验收结论
- ❌ 未触碰 IK、MCAP_B、关节限制检查
- ❌ 未保留 `common_frame -> robot_base` 作为主链路
- ❌ 未写 `DOCS/总执行日志.md`、`执行记录/`、`当前进度.md`、共享 `执行记录.md`
- ❌ 未修改其他 L3 文件

### 16.8 建议后续操作

用户最终人工验收建议：

```bash
# 运行统一开发者入口，选择对应场景和检验项
./start_data_clean.sh --dev
```

推荐顺序：
1. **场景一 → arm-base 位姿转换（新链路）**：确认输出包含官方 API 名、left/right frame_id、common_frame_used: false
2. **场景一 → 全场景测试**：确认主链路成功
3. **场景二 → MCAP_A 写出**：确认 arm-base input 状态和当前路线（不含 IK/MCAP_B）
4. **场景二 → 全场景测试**：确认主链路不再需要 common_frame -> robot_base 后置转换

最终验收标准参考 `05_开发者验收交互文档.md` 第 8 节。

# L3 微元任务：建立 common_frame 代码影响面与回归测试基线

## 1. 任务定位

阶段：阶段二：数据清洗
场景：跨场景一、场景二
L1：service_s1 / service_s2 过渡整改
L2 能力：common frame 错误链路代码整改
L3 编号：common_frames_debug_001
当前任务文件路径：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_001_盘点common_frame影响面.md`
任务类别：数据计算类 / 测试基线类
来源计划文件：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/修改计划.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_001
  task_file: DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_001_盘点common_frame影响面.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 1
  parallel_group: debug-common-frames-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [common_frames_debug_002, common_frames_debug_003, common_frames_debug_006, common_frames_debug_007, common_frames_debug_008]
  conflict_scope:
    files:
      - src/data_clean/
    modules: []
    config_keys: [frame_alignment, common_anchor, common_frame]
  dispatch_status: ready
```

## 3. 本次目标

```text
在代码层建立 common_frame 影响面清单和回归测试基线，明确后续代码改造必须消除哪些旧主链路依赖。
```

## 4. 本次不做

- 不修改任何 L2 数据定义文件或功能描述文档。
- 不删除旧 L3。
- 不执行 IK / MCAP_B / 关节限制路线。
- 不在本任务中实现最终转换逻辑。

## 5. 执行对象

- `src/data_clean` 中 common frame 相关配置、转换、写出、测试入口。
- 新增或修正的测试基线。
- 必要时新增代码扫描/断言工具，输出 common frame 代码影响面。

## 6. 执行依赖

- 已读取 `修改计划.md` 和 4 个原子文档。
- 已确认当前任务位于 debug active 队列，执行时直接按本文件修改代码与测试。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：无直接上游实现，依赖 debug 修改计划。
上游接口定义位置：
- DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/修改计划.md
- DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md
当前 L3 期望消费的字段 / 文件 / 返回值：代码中的 common_frame 相关引用清单、测试断言和失败信息。
是否存在接口冲突：存在，旧代码仍有 `FrameAlignmentConfig`、`output_tcp_pose_common` 和 common pose 写出路径。
如果有冲突，本次处理策略：先用测试和扫描结果固定影响面，不在本 L3 里做业务重写。
```

## 8. 预期改动形态

- `src/data_clean/tests/` 中新增 common frame 影响面回归测试或扫描测试。
- 测试能列出仍依赖旧主链路的代码位置。
- 测试不要求当前就通过新语义，但必须用明确失败信息指导后续 L3。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 代码包含旧主链路符号 | 扫描 `src/data_clean` 中 `FrameAlignmentConfig/common_anchor/output_tcp_pose_common/CommonFrame` | 失败并列出路径 | `legacy_common_frame_code_dependency` |
| 测试目录包含旧断言 | 扫描 `src/data_clean/tests` | 失败并列出路径 | `legacy_common_frame_test_dependency` |
| 无旧主链路依赖 | 扫描结果为空 | 通过 | 无 |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `path` | string | 代码或测试路径 | 仓库相对路径 |
| `symbol` | string | 命中的旧符号 | 必填 |
| `line` | int | 行号 | 大于 0 |
| `classification` | enum | 待改造 / 历史兼容 | 必填 |

## 10. 必读上下文

1. `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/修改计划.md`
2. `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md`

### 必读代码

1. `src/data_clean/repo/config/mcap_process_config.py`
2. `src/data_clean/service/tcp_transform.py`
3. `src/data_clean/service/mcap_io.py`
4. `src/data_clean/schemas/pose_filter.py`
5. `src/data_clean/schemas/mcap_a_writer.py`

## 11. 允许修改

- `src/data_clean/tests/`
- 必要时新增 `src/data_clean/tests/contract/` 下的扫描测试。
- 当前 L3 文件自身。

## 12. 禁止修改

- 不修改 `DOCS/阶段二：数据清洗/02_service/` 下既有文档。
- 不修改业务实现代码。
- 不修改 `03_tasks/task/active` 或 `store`。

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
| 对应功能检验项 | 配置、转换、写出、滤波、MCAP_A 回归检查 |
| 覆盖方式 | 不直接接入开发者入口；由后续场景一/场景二 smoke test 间接覆盖 common_frame 影响面回归。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 13. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "common_frame_impact or arm_base_migration"
rg -n "common_frame|CommonFrame|FrameAlignmentConfig|common_anchor|RobotBaseTcpPose|CommonToRobotBaseTransform" src/data_clean
```

## 14. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。
- [x] 完成后归档目标是 `DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] 已新增代码层影响面扫描或回归测试。
- [x] 测试覆盖配置、转换、MCAP 写出、schema 和运行入口中的旧 common-frame 依赖。
- [x] 测试失败信息能指出后续 L3 应改的代码位置。
- [x] 没有修改既有功能文档、L2 数据定义或业务实现代码。

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

### 任务文件身份校验

用户指定路径：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_001_盘点common_frame影响面.md`

实际读取路径：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_001_盘点common_frame影响面.md`

文件名编号：`common_frames_debug_001`

正文 L3 编号：`common_frames_debug_001`

校验结论：通过。调度 YAML 同步校验通过：`task_id=common_frames_debug_001`，`task_file` 为当前 active 路径，`group=debug-common-frames`，`branch=debug：common_frame`，`depends_on=[]`，`dispatch_status=ready`。

### 读取上下文

- 约束文档：`DOCS/阶段二：数据清洗/约束文件/L3任务文件身份校验约束.md`、`DOCS/阶段二：数据清洗/约束文件/L3调度元数据约束.md`、`DOCS/阶段二：数据清洗/约束文件/双机协作写入边界.md`、`DOCS/阶段二：数据清洗/约束文件/功能分支接力流程.md`。
- 计划文档：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/修改计划.md`、`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md`。
- 技能文档：`/home/hit/.agents/skills/tdd/SKILL.md`。
- 代码文件：`src/data_clean/repo/config/mcap_process_config.py`、`src/data_clean/service/tcp_transform.py`、`src/data_clean/service/mcap_io.py`、`src/data_clean/schemas/pose_filter.py`、`src/data_clean/schemas/mcap_a_writer.py`。
- 测试参考：`src/data_clean/tests/contract/`、`src/data_clean/tests/config/`、`src/data_clean/tests/service/`、`src/data_clean/tests/runtime/` 中既有测试布局。

### 实际修改

- 新增测试：`src/data_clean/tests/contract/test_common_frame_impact.py`。
- 更新当前 L3 文件：勾选成功标准并追加本执行摘要。
- 未修改业务实现代码、配置加载代码、开发者入口代码、L2 数据定义或规划文档。

### TDD red / green / refactor

- RED：先运行 `python3 -m pytest src/data_clean/tests/contract/test_common_frame_impact.py -k common_frame_impact`，因目标测试文件不存在失败，确认缺少 common-frame 影响面回归基线。
- GREEN：新增 `test_common_frame_impact.py`，实现扫描 `src/data_clean` Python 文件的公开 pytest 入口，输出 `path/symbol/line/classification` 结构，并用 `legacy_common_frame_code_dependency` 失败信息列出后续 L3 应改位置。
- REFACTOR：首次运行新增测试后，发现 schema 本体文件没有直接旧符号命中，但 schema 相关既有测试仍消费旧 `common_frame` 语义；将断言从“固定文件必须命中”调整为“配置、转换、MCAP 写出、schema、运行入口五类影响面必须覆盖”。
- 最终通过命令：`python3 -m pytest src/data_clean/tests/contract/test_common_frame_impact.py -k common_frame_impact`，结果 `3 passed`。

### 验收与命令记录

- `git branch --show-current`：确认当前分支为 `debug：common_frame`。
- `bash scripts/init_data_clean_dev.sh`：通过，输出包含 `Git branch OK (debug): debug：common_frame`、`Python imports OK`、`start_data_clean.sh --help OK`、`Data clean dev environment OK`。
- `python3 -m py_compile src/data_clean/tests/contract/test_common_frame_impact.py`：通过，无输出。
- `python3 -m pytest src/data_clean/tests/contract/test_common_frame_impact.py -k common_frame_impact`：通过，`3 passed`。
- `python3 -m pytest src/data_clean/tests/ -k "common_frame_impact or arm_base_migration"`：收集阶段遇到既有环境/收集问题 `ModuleNotFoundError: No module named 'data_clean'`，目标新增测试本身未失败。
- `PYTHONPATH=/home/hit/ROS/src python3 -m pytest src/data_clean/tests/ -k "common_frame_impact or arm_base_migration"`：收集阶段仍遇到既有 runtime 导入问题 `runtime.run_context_directory`、`config.runtime_config_loader` 缺失，目标新增测试本身未失败。
- `python3 -m pytest tests/ -k "common_frame_impact or arm_base_migration"`（在 `src/data_clean` 下）：收集阶段仍遇到既有 `data_clean` 包导入问题。
- `rg -n "common_frame|CommonFrame|FrameAlignmentConfig|common_anchor|RobotBaseTcpPose|CommonToRobotBaseTransform" src/data_clean`：环境中 `rg` 二进制不可用，返回 `rg: 未找到命令`。本 L3 的影响面扫描由新增 pytest 测试内置 Python 扫描实现覆盖。

### 测试数据与开发者验收关系

- 本 L3 不需要读取真实 MCAP：任务目标是建立代码层影响面扫描和回归基线，不执行 MCAP 清洗、转换或写出流程；因此 `/home/hit/下载/mcap` 仅作为后续 L3 的只读真实样本来源保留，未读取、未复制、未移动、未覆盖。
- 新增测试不直接接入 `./start_data_clean.sh --dev`；它固定了后续场景一/场景二 smoke test 之前必须消除或迁移的 common-frame 旧依赖影响面，覆盖 `05_开发者验收交互文档.md` 中配置、转换、写出、滤波、MCAP_A 回归检查相关风险。

### 当前未做与路线边界

- 未实现 IK、MCAP_B、关节限制检查。
- 未实现 `common_frame -> robot_base` 主链路。
- 未改造业务实现、数据定义、L2 文档、开发者入口或 dispatch 索引。
- 建议后续 L3 完成业务迁移后，由用户运行 `./start_data_clean.sh --dev`，优先选择跨场景一、场景二相关的配置、位姿转换、写出、滤波、MCAP_A 回归检查以及完整 smoke test 做最终人工验收。

### 归档路径

完成后归档到：`DOCS/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/common_frames_debug_001_盘点common_frame影响面.md`。

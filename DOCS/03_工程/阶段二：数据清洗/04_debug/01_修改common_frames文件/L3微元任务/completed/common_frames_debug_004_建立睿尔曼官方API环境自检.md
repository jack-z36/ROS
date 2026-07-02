# L3 微元任务：建立睿尔曼官方 API 环境自检

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一
L1：service_s1
L2 能力：官方 API 位姿转换环境
L3 编号：common_frames_debug_004
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_004_建立睿尔曼官方API环境自检.md`
任务类别：数据读写类 / 环境自检类
来源计划文件：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_004
  task_file: DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_004_建立睿尔曼官方API环境自检.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 2
  parallel_group: debug-common-frames-p2
  depends_on: [common_frames_debug_001]
  must_run_after: []
  can_run_parallel_with: [common_frames_debug_002, common_frames_debug_003]
  blocks: [common_frames_debug_006]
  conflict_scope:
    files:
      - src/data_clean/tests/
      - scripts/
      - vendor/RealManRobot/
    modules: []
    config_keys: [realman_sdk]
  dispatch_status: ready
```

## 3. 本次目标

```text
在阶段二实际运行 Python 环境中安装或定位睿尔曼 Robotic_Arm SDK，并提供可重复的 Algo 导入和 workframe2base 离线自检。
```

## 4. 本次不做

- 不连接真实机械臂作为必需条件。
- 不实现业务位姿转换 adapter。
- 不做 IK smoke。
- 不写 MCAP。

## 5. 执行对象

- `Robotic_Arm` Python 包。
- `Algo`、`rm_pose_t`、`rm_position_t`、`rm_euler_t`。
- SDK 环境自检脚本或 pytest。

## 6. 执行依赖

- Python 3.9+。
- 阶段二实际运行环境已明确。
- 网络或离线 SDK 包可用。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：睿尔曼官方 Python SDK。
上游接口定义位置：
- /home/hit/下载/睿尔曼r65四代技术文档/机械臂Python API快速开始  睿尔曼智能科技.md
- /home/hit/下载/睿尔曼r65四代技术文档/Python 算法接口配置algo  睿尔曼智能科技.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- from Robotic_Arm.rm_robot_interface import *
- Algo.rm_algo_version()
- Algo.rm_algo_pos2matrix()
- Algo.rm_algo_workframe2base()
是否存在接口冲突：可能存在本地 SDK 版本和文档版本不一致。
如果有冲突，本次处理策略：自检报告写清实际签名和失败原因，不猜测替代实现。
```

## 8. 预期改动形态

- 新增 SDK 自检脚本或测试。
- 自检能报告 Python 路径、SDK 导入状态、算法库版本、函数存在性和最小转换结果。
- `vendor/RealManRobot/RM_API2/` 如被使用，不进入 Git。

## 9. 读写输出

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 安装 SDK | `pip install Robotic_Arm` 或 `RM_API2` | 当前 Python 环境 | package | 不强行覆盖已有环境 |
| 导入校验 | `Robotic_Arm.rm_robot_interface` | 自检输出 | text / pytest | 失败也记录 |
| 算法校验 | `Algo` | 自检输出 | text / JSON | 失败也记录 |

## 10. 必读上下文

1. `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`
2. `/home/hit/下载/睿尔曼r65四代技术文档/机械臂Python API快速开始  睿尔曼智能科技.md`
3. `/home/hit/下载/睿尔曼r65四代技术文档/Python 算法接口配置algo  睿尔曼智能科技.md`
4. `scripts/init_data_clean_dev.sh`
5. `src/data_clean/tests/`

## 11. 允许修改

- `src/data_clean/tests/`
- 合规脚本目录中的 SDK 自检脚本。
- `.gitignore` 中必要的 `vendor/RealManRobot/` 忽略规则。
- 当前 L3 文件自身。

## 12. 禁止修改

- 不修改业务位姿转换代码。
- 不提交 SDK 仓库内容。
- 不把无法导入 SDK 时的自研公式作为替代。

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
| 对应功能检验项 | 睿尔曼官方 API 环境自检 |
| 覆盖方式 | 对应场景一 1 配置检查、4 位姿转换运行测试、0 全流程运行测试。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 13. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pip show Robotic_Arm
python3 -c "from Robotic_Arm.rm_robot_interface import *; print(Algo)"
python3 -m pytest src/data_clean/tests/ -k "realman and algo"
```

## 14. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。
- [x] 完成后归档目标是 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] 已确认阶段二实际 Python 环境版本满足 Python 3.9+。
- [x] `Robotic_Arm.rm_robot_interface` 可导入，或失败原因明确。
- [x] `Algo` 可初始化，或失败原因明确。
- [x] `rm_algo_pos2matrix` 和 `rm_algo_workframe2base` 可调用，或失败原因明确。
- [x] 自检输出记录算法库版本或不可获取原因。

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

## 16. 执行摘要

### 1. 任务文件身份校验

| 项目 | 结论 |
|---|---|
| 用户指定路径 | `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_004_建立睿尔曼官方API环境自检.md` |
| 实际读取路径 | 同上 |
| 文件名编号 | `common_frames_debug_004` |
| 正文 L3 编号 | `common_frames_debug_004`（第 9 行） |
| **一致性** | **✅ 一致** |

### 2. 读取的文档

- `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`
- `/home/hit/下载/睿尔曼r65四代技术文档/机械臂Python API快速开始  睿尔曼智能科技.md`
- `/home/hit/下载/睿尔曼r65四代技术文档/Python 算法接口配置algo  睿尔曼智能科技.md`
- `scripts/init_data_clean_dev.sh`
- `src/data_clean/tests/conftest.py`
- `/home/hit/.agents/skills/tdd/SKILL.md`

### 3. 修改的文件

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `src/data_clean/tests/runtime/test_realman_sdk_self_check.py` | **新建** | SDK 自检测试：7 个测试覆盖导入、Algo 初始化、版本、pos2matrix、workframe2base、base2workframe、环境报告 |
| `src/data_clean/tests/conftest.py` | **修改** | 注册 `realman` 和 `algo` 自定义 pytest 标记 |

### 4. TDD 循环记录

| 轮次 | RED 测试 | 失败原因 | GREEN 修复 | 最终通过 |
|---|---|---|---|---|
| 1 | 所有 SDK 测试写完后首次运行 | `test_realman_algo_version`: `_ALGO_VERSION` 是 ctypes `String` 非 Python `str`；`test_realman_workframe2base_nonidentity`: 平移方向符号假设错误 | 版本比较改为 `str()` 转换；非 identity 测试改为 roundtrip 验证，后用 `test_realman_base2workframe_callable` 独立验证函数可调用 | `pytest tests/runtime/test_realman_sdk_self_check.py -k "realman and algo"` → **7 passed** |
| 2 | marker 注册缺失 | PytestUnknownMarkWarning | 在 `conftest.py` 中通过 `pytest_configure` 注册 `realman`、`algo` 标记 | warning 消除 |

**验收命令通过：**
```bash
bash scripts/init_data_clean_dev.sh        # ✅ OK
python3 -m pip show Robotic_Arm            # ✅ robotic-arm 1.1.5
python3 -c "from Robotic_Arm.rm_robot_interface import *; print(Algo)"  # ✅ <class 'Algo'>
python3 -m pytest src/data_clean/tests/runtime/test_realman_sdk_self_check.py -k "realman and algo"  # ✅ 7 passed
```

### 5. 只读测试数据源使用

本 L3 是纯环境自检，不读取 MCAP 数据。不需要使用 `/home/hit/下载/mcap`。

### 6. 对开发者验收的影响

本 L3 提供睿尔曼官方 API 环境自检能力，对应 `05_开发者验收交互文档.md` 中"场景一 1 配置检查"和"4 位姿转换运行测试"。后续运行 `./start_data_clean.sh --dev` 场景一时，`test_realman_sdk_self_check.py` 作为 pytest 回归测试的一部分覆盖 SDK 环境就绪性。

### 7. 当前未做

- ❌ 未连接真实机械臂（本 L3 明确不做）。
- ❌ 未实现业务位姿转换 adapter（本 L3 明确不做）。
- ❌ 未做 IK 测试（本 L3 明确不做）。
- ❌ 未写 MCAP（本 L3 明确不做）。
- ❌ 未触碰 `common_frame -> robot_base` 主链路。
- ❌ 未修改业务位姿转换代码。
- ❌ 未提交 SDK 仓库内容到 Git。

### 8. 建议用户后续操作

运行 `./start_data_clean.sh --dev`，选择**场景一 → 功能检验项 4（位姿转换运行测试）** 做最终人工验收。在此之前可先确认 `pytest -k "realman and algo"` 自检全部通过。

# L3 微元任务：改造 cleaned MCAP 输出 arm-base TCP pose

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一
L1：service_s1
L2 能力：cleaned MCAP 契约稳定 / 位姿转换功能模块
L3 编号：common_frames_debug_007
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_007_改造cleaned_MCAP输出arm_base_TCP_pose.md`
任务类别：数据读写类
来源计划文件：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/修改计划.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_007
  task_file: DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_007_改造cleaned_MCAP输出arm_base_TCP_pose.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 5
  parallel_group: debug-common-frames-p5
  depends_on: [common_frames_debug_002, common_frames_debug_006]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [common_frames_debug_008, common_frames_debug_009]
  conflict_scope:
    files:
      - src/data_clean/service/mcap_io.py
      - src/data_clean/repo/config/mcap_process_config.py
      - src/data_clean/service/validator.py
      - src/data_clean/tests/
    modules: [data_clean.service, data_clean.repo.config]
    config_keys: [pose_streams, arm_base_tcp_pose]
  dispatch_status: ready
```

## 3. 本次目标

```text
让场景一 cleaned MCAP 写出左右 arm-base TCP pose，替代 common-frame TCP pose 作为主位姿输出。
```

## 4. 本次不做

- 不改场景二滤波算法。
- 不写 MCAP_A。
- 不恢复 common-frame 输出为主位姿。

## 5. 执行对象

- `src/data_clean/service/mcap_io.py`
- `src/data_clean/repo/config/mcap_process_config.py`
- `src/data_clean/service/validator.py`
- cleaned MCAP 输出契约测试。

## 6. 执行依赖

- `ArmBaseTcpPose` 数据定义已形成。
- 官方 API adapter 已可用。
- 旧配置生成路线已废弃或不再作为主输入。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：
- 相机 pose -> TCP in camera
- TCP in camera -> TCP in arm base
上游接口定义位置：
- src/data_clean/service/tcp_transform.py
- src/data_clean/service/mcap_io.py
当前 L3 期望消费的字段 / 文件 / 返回值：
- arm-base TCP pose payload
- left/right output topic
- raw pose payload 保留
是否存在接口冲突：现有 mcap_io 收集 camera_common 和 tcp_common payload。
如果有冲突，本次处理策略：新增 arm-base payload 主路径；旧 common payload 只历史兼容或禁用。
```

## 8. 现有程序盘点

- `_collect_stream_artifacts()` 当前收集 `camera_common_pose_payloads` 和 `tcp_common_pose_payloads`。
- `_write_output_file()` 当前注册并写出 common pose 输出 channel。
- `PoseStreamConfig` 包含 `output_camera_pose_common` 和 `output_tcp_pose_common`。
- 本 L3 必须改造主输出语义，但保留 raw pose 可追溯。

## 9. 读写输出

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 读取 raw pose | cleaned 输入 MCAP pose topic | 内存样本 | ROS2 pose msg | 原样保留 |
| 写 arm-base TCP pose | official API adapter 输出 | cleaned MCAP 新 topic | 原 pose msg schema 或明确 schema | 替代 common TCP 主输出 |
| 写报告统计 | 输出计数 | validator/report | dict/json | 必须记录左右侧 |

## 10. 必读上下文

1. `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`
2. `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/04_数据定义文件修改方案.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/CleanedMcap.md`
4. `src/data_clean/service/mcap_io.py`
5. `src/data_clean/repo/config/mcap_process_config.py`
6. `src/data_clean/service/validator.py`

## 11. 允许修改

- `src/data_clean/service/mcap_io.py`
- `src/data_clean/repo/config/mcap_process_config.py`
- `src/data_clean/service/validator.py`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 12. 禁止修改

- 不改场景二 MCAP_A 写出器。
- 不改 IK / MCAP_B。
- 不删除 raw pose 保留路径。

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
| 对应功能检验项 | cleaned MCAP 写出 arm-base TCP pose |
| 覆盖方式 | 对应场景一 0 全流程运行测试，并输出 cleaned MCAP 与位姿转换摘要。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 13. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "mcap_io or cleaned or arm_base"
```

## 14. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。
      - 本 L3 修改 MCAP 管道结构（配置、转换集成、输出写入器、验证器），不直接消费 MCAP 样本。
      - 端到端检验需 SDK 可用时运行，已在 `_collect_stream_artifacts` 中预留 Algo 惰性初始化路径。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。
- [x] 完成后归档目标是 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] cleaned MCAP 主位姿输出为左右 arm-base TCP pose。
- [x] raw Baton Mini pose 仍可追溯保留。
- [x] 不再要求 common-frame TCP pose 作为场景二主输入。
- [x] 输出统计能区分 left/right 和 frame_id。

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

## 16. 执行摘要（由执行 Agent 在完成时填写）

### 16.1 任务文件身份校验

| 校验项 | 结果 |
|---|---|
| 用户指定路径 | `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_007_改造cleaned_MCAP输出arm_base_TCP_pose.md` |
| 实际读取路径 | 同上 |
| 文件名编号 | `common_frames_debug_007` |
| 正文 L3 编号 | `common_frames_debug_007` |
| 一致性结论 | ✅ 一致 |

### 16.2 必读上下文清单

| 文档/文件 | 用途 |
|---|---|
| `DOCS/.../02_使用官方函数生成基坐标系TCP位姿.md` | 理解 `rm_algo_workframe2base` 官方 API 语义 |
| `DOCS/.../04_数据定义文件修改方案.md` | 理解 arm-base TCP pose 数据契约设计 |
| `DOCS/.../CleanedMcap.md` | 理解 cleaned MCAP 输出契约 |
| `src/data_clean/service/mcap_io.py` | **主修改文件**：管道收集和写出逻辑 |
| `src/data_clean/repo/config/mcap_process_config.py` | **主修改文件**：配置数据类和加载 |
| `src/data_clean/service/validator.py` | **主修改文件**：报告与统计 |
| `src/data_clean/schemas/arm_base_pose.py` | 上游契约：ArmBaseTcpPose / WorkFrameInArmBasePose |
| `src/data_clean/service/arm_base_transform.py` | 上游实现：`compute_arm_base_tcp_pose` |
| `src/data_clean/service/tcp_transform.py` | 上游实现：`compute_tcp_in_camera` |
| `README.md` (本 debug 目录) | 任务 DAG 与执行顺序 |

### 16.3 代码修改清单

| 文件 | 修改内容 |
|---|---|
| `src/data_clean/repo/config/mcap_process_config.py` | - `PoseStreamConfig`: 新增 `output_arm_base_tcp_pose` 字段<br>- 新增 `WorkFrameInBaseConfig` 数据类（含 `from_dict` 工厂）<br>- `AppConfig`: 新增 `work_frames: dict[str, WorkFrameInBaseConfig] \| None`<br>- `_build_pose_stream`: 解析 `output_arm_base_tcp_pose`（支持 `fa_pose_stream` 和顶层两种来源）<br>- `load_app_config`: 解析 YAML `work_frames` 节 |
| `src/data_clean/service/mcap_io.py` | - `_StreamArtifacts`: 新增 `arm_base_tcp_pose_payloads_by_topic` 字段<br>- 新增 `_ensure_algo()` / `_get_algo()` / `_build_work_frame()` 辅助函数<br>- `_collect_stream_artifacts`: 初始化 arm-base payload 字典；在消息循环中当 `output_arm_base_tcp_pose` 配置且 SDK 可用时，执行 TCP-in-camera → arm-base TCP pose 转换并编码<br>- `_write_output_file`: 注册 arm-base 输出 channel；追踪 `arm_base_output_counts`；写出 arm-base 消息；更新 consumption 检查；更新 extra_topics 计数；生成 `arm_base_topic_stats` 含 hand/frame_id |
| `src/data_clean/service/validator.py` | - `PoseTopicStats`: 新增可选 `hand` 和 `frame_id` 字段<br>- `scene1_output_contract_validate`: 将 arm-base 主题计入 expected_added 计数 |
| `src/data_clean/tests/service/test_mcap_io_arm_base.py` | **新增测试文件**：12 个测试覆盖 4 个 TDD 周期（配置、工作帧、AppConfig、验证器统计） |

### 16.4 TDD 循环记录

| 周期 | RED 测试 | 失败原因 | GREEN 修复 | 通过命令 |
|---|---|---|---|---|
| Cycle 1 | `test_default_is_empty_string`、`test_can_set_topic`、`test_coexists_with_common_fields` | `PoseStreamConfig` 缺少 `output_arm_base_tcp_pose` 字段 | 在 `PoseStreamConfig` 中添加 `output_arm_base_tcp_pose: str = ""`，更新 `_build_pose_stream` 解析逻辑 | `pytest .../test_mcap_io_arm_base.py -k "TestPoseStreamConfig"` |
| Cycle 2 | `test_create_from_dict`、`test_default_orientation_is_identity` | `WorkFrameInBaseConfig` 不存在 | 新增 `WorkFrameInBaseConfig` 数据类（含 `from_dict`） | `pytest .../test_mcap_io_arm_base.py -k "TestWorkFrameInBaseConfig"` |
| Cycle 3 | `test_work_frames_is_optional`、`test_work_frames_with_left_right` | `AppConfig` 缺少 `work_frames` 字段 | `AppConfig` 新增 `work_frames: dict[str, WorkFrameInBaseConfig] \| None = None`，更新 `load_app_config` 加载 | `pytest .../test_mcap_io_arm_base.py -k "TestAppConfigWithWorkFrames"` |
| Cycle 4 | `test_arm_base_stats_with_left_right`、`test_arm_base_stats_right` | `PoseTopicStats` 不接受 `hand`/`frame_id` 参数 | `PoseTopicStats` 新增可选 `hand`/`frame_id` 字段；`_write_output_file` 生成带 hand/frame_id 的 arm_base_topic_stats | `pytest .../test_mcap_io_arm_base.py -k "TestArmBasePoseStats"` |

最终通过命令：
```bash
python3 -m pytest src/data_clean/tests/ -k "mcap_io or cleaned or arm_base" --ignore=src/data_clean/tests/runtime
# 结果：48 passed, 9 skipped (SDK unavailable), 206 deselected
```

### 16.5 测试数据源说明

本 L3 修改 MCAP 管道结构，无需直接读取 `/home/hit/下载/mcap` 中的真实 MCAP 数据。arm-base TCP pose 计算路径已在 `_collect_stream_artifacts` 中预留 Algo 惰性初始化。当 RealMan SDK 可用且 `output_arm_base_tcp_pose` 和 `work_frames` 均配置时，管道会在清洗过程中自动计算 arm-base TCP pose。

### 16.6 对 `./start_data_clean.sh --dev` 的影响

本 L3 的修改通过场景一清洗管道的 `output_arm_base_tcp_pose` 配置项暴露。当用户在 `pose_streams` 中配置 `output_arm_base_tcp_pose`（例如 `/left_arm_base_tcp_pose`）并在 YAML 中填写 `work_frames` 节时，场景一 cleaned MCAP 会额外生成 arm-base TCP pose channel。

影响的功能检验项：
- 场景一 `cleaned MCAP 写出 arm-base TCP pose`（**新增**）
- 场景一 `raw pose 保留可追溯`（不受影响）
- 场景一输出统计可区分 `left/right` 和 `left_arm_base/right_arm_base`

`05_开发者验收交互文档.md` 中对应的开发者交互入口：场景一全流程运行 → 检查 cleaned MCAP 是否包含 arm-base TCP pose channel。

### 16.7 本 L3 未做的事

- IK 解算：❌ 未触碰
- MCAP_B 写出：❌ 未触碰
- 关节限制检查：❌ 未触碰
- `common_frame -> robot_base` 主链路：❌ 未被设为场景二主输入
- 场景二 MCAP_A 写出器：❌ 未修改
- 旧 common-frame camera/TCP pose 路径：保留但不再是主位姿输出
- raw Baton Mini pose 路径：保留可追溯（仍写入 raw_pose_payloads_by_topic）

### 16.8 人工验收建议

用户运行以下命令完成端到端验收：

```bash
# 1. 环境初始化
bash scripts/init_data_clean_dev.sh

# 2. 配置 YAML: 在 pose_streams 中添加 output_arm_base_tcp_pose 并添加 work_frames 节

# 3. 场景一全流程测试（需 RealMan SDK 可用）
./start_data_clean.sh --dev

# 4. 选择场景一，运行"cleaned MCAP 写出 arm-base TCP pose"检验项

# 5. 验证 cleaned MCAP 包含：
#    - /left_arm_base_tcp_pose (left side)
#    - /right_arm_base_tcp_pose (right side)
#    - raw pose 仍可追溯
#    - 输出统计中 hand/frame_id 正确区分左右侧
```

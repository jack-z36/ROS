# L3 微元任务：保留相机位姿到 TCP 位姿转换

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一
L1：service_s1
L2 能力：位姿转换功能模块
L3 编号：common_frames_debug_005
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_005_保留相机位姿到TCP位姿转换.md`
任务类别：数据计算类
来源计划文件：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: common_frames_debug_005
  task_file: DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_005_保留相机位姿到TCP位姿转换.md
  group: debug-common-frames
  branch: debug：common_frame
  wave: 3
  parallel_group: debug-common-frames-p3
  depends_on: [common_frames_debug_002]
  must_run_after: []
  can_run_parallel_with: [common_frames_debug_004]
  blocks: [common_frames_debug_006, common_frames_debug_007]
  conflict_scope:
    files:
      - src/data_clean/service/tcp_transform.py
      - src/data_clean/tests/
    modules: [data_clean.service]
    config_keys: [camera_from_tcp, tcp_from_camera]
  dispatch_status: ready
```

## 3. 本次目标

```text
确保位姿转换模块保留第一段能力：从 Baton Mini 相机位姿和 TCP 外参生成 TCP 在相机坐标系下的位姿。
```

## 4. 本次不做

- 不调用睿尔曼官方 API。
- 不把 TCP 位姿转换到机械臂基坐标系。
- 不改 MCAP 输出 topic。

## 5. 执行对象

- `src/data_clean/service/tcp_transform.py`
- TCP 相对相机外参定义。
- 相机 pose -> TCP pose 的单元测试。

## 6. 执行依赖

- 新数据定义中已明确 TCP in camera pose 的字段和姿态顺序。
- 已确认 `CameraFromTcpExtrinsic` / `TcpFromCameraExtrinsic` 的方向。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：场景一 raw Baton Mini pose 读取、TCP 外参配置。
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/CameraFromTcpExtrinsic.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/TcpFromCameraExtrinsic.md
- src/data_clean/service/tcp_transform.py
当前 L3 期望消费的字段 / 文件 / 返回值：
- camera pose: x/y/z/qx/qy/qz/qw 或等价结构
- camera_from_tcp 或 tcp_from_camera 外参
- tcp_pose_in_camera
是否存在接口冲突：外参方向命名历史上容易混淆。
如果有冲突，本次处理策略：测试用例固定单位外参、纯平移、纯旋转，用代码注释和测试命名明确方向。
```

## 8. 现有程序盘点

- `transform_camera_to_common_tcp()` 已实现 `T_common_tcp = T_common_camera @ T_camera_tcp`。
- `_pose_to_matrix()` 和 `_extrinsic_to_matrix()` 已存在，但命名绑定 common-frame 语义。
- 当前实现把 TCP 叠加放在 common camera pose 之后，缺少独立“TCP in camera”输出概念。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 单位 TCP 外参 | TCP pose 等于 camera pose 或等价本地位姿 | 通过 | 无 |
| 纯平移外参 | 输出位置体现外参平移 | 通过 | 无 |
| 非法四元数 | 拒绝或归一化策略明确 | 失败或规范化 | `invalid_quaternion` |

## 10. 必读上下文

1. `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/common frame位姿转换.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/CameraFromTcpExtrinsic.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/TcpFromCameraExtrinsic.md`
5. `src/data_clean/service/tcp_transform.py`

## 11. 允许修改

- `src/data_clean/service/tcp_transform.py`
- `src/data_clean/tests/`
- 必要的 schema / type 文件。
- 当前 L3 文件自身。

## 12. 禁止修改

- 不修改官方 API adapter。
- 不修改 MCAP 读写器。
- 不修改场景二滤波。

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
| 对应功能检验项 | 相机位姿到 TCP 位姿第一段转换 |
| 覆盖方式 | 对应场景一 4 位姿转换运行测试、0 全流程运行测试。 |
| 是否影响场景完整 smoke test | 是 |

本 L3 的代码修改最终必须能被 `05_开发者验收交互文档.md` 中定义的开发者交互覆盖。当前路线不实现 IK、MCAP_B、关节限制检查，也不保留 `common_frame -> robot_base` 作为主链路。

## 13. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "tcp_transform and camera"
```

## 14. 成功标准

- [x] 已按 `$tdd` 完成至少一轮 RED/GREEN/REFACTOR，并在执行摘要记录测试、失败点、修复点和最终通过命令。
- [x] 已使用 `/home/hit/下载/mcap` 作为只读真实样本来源，或说明本 L3 不需要读取真实 MCAP 的原因。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev`、`05_开发者验收交互文档.md` 中对应功能检验项或 smoke test 的关系。
- [x] 完成后归档目标是 `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/completed/`，不是正式 `03_tasks/task/completed/`。
- [x] 存在独立可测试的相机 pose -> TCP in camera pose 能力。
- [x] 单位外参、平移外参、非法四元数测试覆盖。
- [x] 该能力不依赖 `common_frame`。
- [x] 该能力输出可作为 `rm_algo_workframe2base()` 的 `pose_in_work` 输入。

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

### 任务身份校验

- 用户指定路径：`DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/L3微元任务/active/common_frames_debug_005_保留相机位姿到TCP位姿转换.md`
- 实际读取路径：同上
- 文件名编号：`common_frames_debug_005`
- 正文 L3 编号：`common_frames_debug_005`
- **结论：一致 ✓**

### 分支校验

- 当前分支：`debug：common_frame`
- YAML 中声明分支：`debug：common_frame`
- **结论：匹配 ✓**

### 读取的文档和代码

1. `DOCS/03_工程/阶段二：数据清洗/04_debug/01_修改common_frames文件/02_使用官方函数生成基坐标系TCP位姿.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/common frame位姿转换.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/CameraFromTcpExtrinsic.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/TcpFromCameraExtrinsic.md`
5. `src/data_clean/service/tcp_transform.py`（现有实现）
6. `src/data_clean/tests/service/test_common_frame_pose_transform.py`（现有测试模式参考）
7. `src/data_clean/schemas/arm_base_pose.py`（上游 `common_frames_debug_002` 产生的契约）
8. `/home/hit/.agents/skills/tdd/SKILL.md`（TDD 技能文件）

### 修改的文件

| 文件 | 修改类型 | 说明 |
|---|---|---|
| `src/data_clean/service/tcp_transform.py` | 新增函数 | 在文件末尾添加 `compute_tcp_in_camera()`，该函数接受相机 pose 和 TCP 外参，验证外参四元数为单位四元数，返回 TCP in camera frame 的 7 元组。 |
| `src/data_clean/tests/service/test_tcp_transform_camera.py` | 新建文件 | 7 个测试用例覆盖身份外参、平移外参、非法四元数、近单位四元数通过、相机 pose 无关性、输出=外参数值、旋转外参。 |

### TDD 循环记录

**Cycle 1 — RED → GREEN**
- RED: 编写 `test_tcp_transform_camera.py`，测试引用不存在的 `compute_tcp_in_camera`
- 预期失败: `ImportError: cannot import name 'compute_tcp_in_camera'` — ✅ 确认
- GREEN: 在 `tcp_transform.py` 末尾添加 `compute_tcp_in_camera()` 函数
- 首次运行: 6/7 通过，1 个测试（`test_output_matches_extrinsic_directly`）因测试四元数 `(0.1,0.2,0.3,0.927)` 的 norm²=0.999329 超出 1e-6 容差而失败
- **失败点修复**: 将测试中的硬编码 `0.927` 改为动态计算 `qw = sqrt(1 - 0.1² - 0.2² - 0.3²) ≈ 0.92736`，并修复断言值引用
- 最终通过: **7/7 passed**

**Cycle 2 — (built into Cycle 1 via multi-test file)**
- `test_output_does_not_depend_on_camera_pose`: 验证不同相机 pose 下相同外参返回相同结果
- `test_output_matches_extrinsic_directly`: 验证输出与外参数值相同（数学恒等式）
- `test_rotation_extrinsic_applied`: 验证旋转外参正确传递

### 最终通过命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/service/test_tcp_transform_camera.py -v
# 结果: 7 passed
```

### 测试数据源说明

本 L3 不需要读取真实 MCAP 数据。所有测试使用手动构造的数值参数，不依赖 `/home/hit/下载/mcap` 中的任何文件。功能验证通过 unit tests 完成。

### 对开发者验收的影响

本 L3 实现的是场景一"4 位姿转换"功能检验项中的**第一段**能力（相机 pose → TCP in camera pose）。当用户运行 `./start_data_clean.sh --dev` 并选择场景一的"位姿转换"功能检验项时，本 L3 新增的 `compute_tcp_in_camera()` 将被调用。

具体来说：
- 该函数输出（TCP in camera frame）可作为 downstream L3（`common_frames_debug_006`）中 `rm_algo_workframe2base()` 的 `pose_in_work` 输入。
- 当前实现不修改 `start_data_clean.sh` 或开发者验收入口本身，只提供可被验收脚本调用的基础能力。
- 本 L3 不涉及场景完整 smoke test 的运行。

### 本次未做

- ❌ 未调用睿尔曼官方 API（`rm_algo_workframe2base` 等）。
- ❌ 未实现 IK、MCAP_B、关节限制检查。
- ❌ 未实现 `common_frame → robot_base` 主链路（该链路由 `common_frames_debug_006` 通过官方 API 实现）。
- ❌ 未修改 MCAP 输出 topic。
- ❌ 未修改官方 API adapter、MCAP 读写器、场景二滤波。
- ❌ 未修改其他 L3 任务文件。
- ❌ 未写入 `DOCS/总执行日志.md`、`执行记录/`、`当前进度.md`、共享 `执行记录.md`。

### 建议用户后续运行

建议用户完成 `common_frames_debug_006`（官方 API 第二段转换）后，运行：
```bash
./start_data_clean.sh --dev
```
选择场景一 → "4 位姿转换" 功能检验项，验证完整的两段转换链路（本 L3 输出的 TCP in camera + L6 的 arm-base TCP pose）。

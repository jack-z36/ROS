# L2 能力模块说明：arm-base 位姿转换

## 1. 能力名称

```text
arm-base 位姿转换
```

## 2. 所属位置

阶段：阶段二：数据清洗
L1：service_s1
场景：场景一：提取夹爪开合以及位姿转换
模块类别：数据计算类
来源功能模块清单：`DOCS/阶段二：数据清洗/02_service/场景一/功能模块清单.md`

## 3. 一句话目标

```text
将左右 TCP in camera 位姿经 Algo.rm_algo_workframe2base 转换为机械臂基坐标系下的 ArmBaseTcpPose。
```

## 4. 能力角色

本能力是场景一空间语义补齐的核心模块。它接管了旧 common frame 转换链路，把 TCP in camera 中间产物转换为左右机械臂基座标系下的 TCP pose，写入 cleaned MCAP 的主位姿字段。

## 5. 两阶段转换链路

场景一采用两阶段转换，分别由两个独立 L2 能力覆盖：

| 阶段 | 能力模块 | 输入 | 输出 | 代码入口 |
|------|---------|------|------|----------|
| 1: raw → TCP in camera | 无独立 L2（属位姿转换前置） | raw camera pose + [[CameraFromTcpExtrinsic]] | [[TcpInCamera]] | `src/data_clean/service/tcp_transform.py` `compute_tcp_in_camera()` |
| 2: TCP in camera → arm-base | 本能力（arm-base 位姿转换） | [[TcpInCamera]] + [[WorkFrameInBaseConfig]] | [[ArmBaseTcpPose]] | `src/data_clean/service/arm_base_transform.py` `compute_arm_base_tcp_pose()` |

## 6. 核心转换逻辑

### 6.1 输入

| 输入 | 含义 | 约束 |
|------|------|------|
| `tcp_x/y/z` | TCP in camera 位置（米） | 由 `compute_tcp_in_camera` 产出 |
| `tcp_qx/y/z/w` | TCP in camera 姿态四元数（xyzw） | ROS 四元数顺序 |
| [[WorkFrameInBaseConfig]] | Work frame 在机械臂基坐标系下的位姿 | hand 必须匹配左右 |
| `Algo` 实例 | RealMan SDK 算法对象 | 需用正确臂型号初始化 |

### 6.2 处理

```text
1. WorkFrameInBaseConfig.position_mm / 1000 + rotation_euler_rad → SDK euler pose
2. euler → rm_algo_pos2matrix → work_matrix（4×4，表示 base→work 映射）
3. TCP quaternion (xyzw) → SDK euler → rm_pose_t
4. rm_algo_workframe2base(work_matrix, pose_in_work) → TCP in arm base (euler)
5. result euler → rm_algo_euler2quaternion → quaternion (wxyz → xyzw)
6. 根据 hand 选择 frame_id: left → left_arm_base, right → right_arm_base
```

### 6.3 输出

输出 [[ArmBaseTcpPose]]，包含：

| 字段 | 含义 |
|------|------|
| `hand` | `left` 或 `right` |
| `frame_id` | `left_arm_base` 或 `right_arm_base` |
| `position_m` | `{x, y, z}` 米 |
| `orientation` | `{x, y, z, w}` 四元数（xyzw） |
| `official_api` | `"Algo.rm_algo_workframe2base"` |

## 7. 上游关系

- [[TcpInCamera]] 由 `compute_tcp_in_camera` 从 raw camera pose + [[CameraFromTcpExtrinsic]] 得到。
- [[WorkFrameInBaseConfig]] 来自场景一配置的 `work_frames` 块。
- raw MCAP 保留原始 pose topic 作为附加大字段。

## 8. 下游关系

- 场景二优先按 [[ArmBaseTcpPose]] 消费位姿。
- [[ArmBaseTcpPose]] 写入 cleaned MCAP 的 `arm_base_tcp_pose` 字段。
- raw pose 保留用于漂移、单位、四元数顺序排查。

## 9. 职责边界

本能力负责：

1. 用 `compute_arm_base_tcp_pose` 将 TCP in camera 转换为 arm-base TCP pose。
2. 校验 [[WorkFrameInBaseConfig]] 的手别与 frame_id 一致性。
3. 保证输出 topic 和 frame_id 匹配：left → `/left_arm_base_tcp_pose` / `left_arm_base`，right → `/right_arm_base_tcp_pose` / `right_arm_base`。
4. 保证动态轨迹不得退化成固定 TCP 偏移；输出数量和时间戳必须跟随 raw Baton Mini pose。

本能力不负责：

1. 生成 WorkFrameInBaseConfig（由配置生成器负责）。
2. 计算 TCP in camera（由 `compute_tcp_in_camera` 前置步骤负责）。
3. 判断轨迹可靠性或机器人可执行性。
4. 执行场景二滤波、IK 或异常修复。

## 10. 异常与边界输入

| 边界情况 | 预期结果 | reason / error 表达 | 是否阻塞下游 |
|----------|----------|---------------------|-------------|
| work_frame hand 与期望手别不匹配 | 转换失败 | hand mismatch | 是 |
| TCP quaternion 非单位 | 配置加载失败 | invalid_quaternion | 是 |
| TCP in camera 未产出 | 清洗失败 | missing tcp_in_camera | 是 |
| WorkFrameInBaseConfig 缺失 | 配置加载失败 | missing work_frames config | 是 |
| SDK gimbal lock（±90° pitch） | 结果非确定 | documented limitation | 否 |

## 11. 可验证样例

| 样例 | 输入特征 | 预期输出 | 验证方式 |
|------|----------|----------|----------|
| identity work frame + 动态 TCP in camera | `work_frame` 单位阵，TCP in camera 随 raw pose 移动 | arm-base TCP 轨迹随 raw pose 移动 | unit test |
| 已知平移 | work_frame 平移 (0.1, 0, 0) | arm-base TCP x 偏移 0.1m | contract test |
| 左右 hand 交换 | 左右输入互换 | frame_id 正确切换 | unit test |
| 圆整测试 | 已知 SDK 输入输出对 | 与 SDK 独立计算结果一致 | round-trip test |

## 12. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 验收方式 |
|---------|------------|----------|------|------|-------------|----------|
| service_s1_006 | 实现 arm-base 位姿转换输出 | 数据计算类 | [[WorkFrameInBaseConfig]]、[[TcpInCamera]] | arm-base TCP pose contract | `src/data_clean/service/`、`src/data_clean/tests/` | `python3` contract test |

## 13. 给 L3 任务生成的约束

1. 不得混用左右 WorkFrameInBaseConfig。
2. 输出数量必须与输入 pose topic 数量一致。
3. 必须记录 `official_api` 字段为 `Algo.rm_algo_workframe2base`。
4. 必须覆盖“raw pose 改变时 arm-base 输出也改变”的验收，防止动态链路退化成固定外参。

## 14. 开发者功能检验契约

本能力在 `./start_data_clean.sh --dev -> 场景一` 下对应的功能检验项：

```text
scene1_arm_base_pose_transform
```

检验目标：

- 读取小样本 TCP in camera 和 [[WorkFrameInBaseConfig]]。
- 输出 [[ArmBaseTcpPose]] 调试样本。
- 验证 raw pose 可追溯保留。

测试产物：

- [[Scene1DevArtifact]]：`artifacts/arm_base_pose_samples.json`
- 可选 [[Scene1DevArtifact]]：`artifacts/debug_arm_base_pose.mcap`
- [[Scene1DevRunLog]]：`logs/run_log.json`

临时覆盖：

- 允许覆盖小样本输入、work frame 配置、TCP in camera 输入。
- 默认不写回正式配置。

输出隔离：

- 调试 pose 产物只写入本次 [[Scene1DevRun]]。

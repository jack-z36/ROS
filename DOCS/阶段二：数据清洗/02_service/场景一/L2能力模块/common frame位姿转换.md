# L2 能力模块说明：common frame 位姿转换

## 1. 能力名称

```text
common frame 位姿转换
```

## 2. 所属位置

阶段：阶段二：数据清洗
L1：service_s1
场景：场景一：提取夹爪开合以及位姿转换
模块类别：数据计算类
来源功能模块清单：`DOCS/阶段二：数据清洗/02_service/场景一/功能模块清单.md`

## 3. 一句话目标

```text
将左右 Baton Mini start frame 下的 raw pose 转换为 common frame 下的 camera pose 和 TCP pose。
```

## 4. 能力角色

本能力是场景一空间语义补齐模块。它把左右局部坐标系下的 raw pose 统一到 [[FrameAlignmentConfig]] 定义的 common frame，并输出 [[CommonFrameCameraPose]] 与 [[CommonFrameTcpPose]]。

## 5. 上游关系

- raw MCAP 必须包含左右 Baton Mini pose topic。
- [[Scene1Config]] 必须包含 [[FrameAlignmentConfig]]。
- [[FrameAlignmentConfig]] 默认 `common_anchor: left`。

## 6. 下游关系

- 场景二优先按 [[CommonFrameTcpPose]] 消费位姿。
- [[CommonFrameCameraPose]] 用于调试、TCP 外参复算和后续定位问题排查。
- raw pose 必须保留，用于排查漂移、单位、四元数顺序和跳变。

## 7. 上游接口对齐检查

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
|---|---|---|---|---|
| raw MCAP | `/baton_mini_left/fast_odom`、`/baton_mini_right/fast_odom` | 读取 raw pose | 已对齐 | 保留 raw pose 追溯 |
| 位姿转换配置生成 | [[FrameAlignmentConfig]] | 提供 `common_from_*_start` 和 `camera_from_*_tcp` | 待改造 | service_s1_004/005 |
| [[CleanedMcap]] | camera/TCP common pose 输出 | 写出统一坐标系位姿 | 待落地 | service_s1_006 |

## 8. 职责边界

本能力负责：

1. 计算 common frame 下的左右相机 pose。
2. 叠加 [[TcpFromCameraExtrinsic]] 得到左右 TCP pose。
3. 保留 raw pose 或提供可追溯 raw pose 备份策略。

本能力不负责：

1. 生成底座外参。
2. 判断轨迹可靠性或机器人可执行性。
3. 执行场景二滤波、IK 或异常修复。

## 9. 计算职责

| 计算项 | 输入 | 输出 | 影响下游 |
|---|---|---|---|
| anchor 选择 | `common_anchor` | common frame 定义 | 决定左右外参方向 |
| camera common pose | `T_start_camera(t)`、`common_from_*_start` | [[CommonFrameCameraPose]] | 场景二位姿输入和调试 |
| TCP common pose | [[CommonFrameCameraPose]]、[[CameraFromTcpExtrinsic]] | [[CommonFrameTcpPose]] | IK 前置输入 |
| raw pose 保留 | 输入 pose topic | raw pose 追溯 | 漂移和单位排查 |

## 10. 计算规则

当 `common_anchor: left`：

| hand | 计算 |
|---|---|
| left camera | `T_common_left_camera(t) = T_left_start_left_camera(t)` |
| right camera | `T_common_right_camera(t) = T_common_right_start * T_right_start_right_camera(t)` |
| left TCP | `T_common_left_tcp(t) = T_common_left_camera(t) * T_left_camera_tcp` |
| right TCP | `T_common_right_tcp(t) = T_common_right_camera(t) * T_right_camera_tcp` |

字段命名使用 `camera_from_left_tcp`、`camera_from_right_tcp`，表示 `T_camera_tcp`。

## 11. 异常与边界输入

| 边界情况 | 预期结果 | reason / error 表达 | 是否阻塞下游 |
|---|---|---|---|
| pose topic 缺失 | 清洗失败 | missing configured pose topic | 是 |
| pose schema 不支持 | 清洗失败 | unsupported pose message type | 是 |
| frame_alignment 缺失 | 配置加载失败 | missing frame_alignment | 是 |
| quaternion 非单位 | 配置加载失败 | must be a unit quaternion | 是 |
| TCP 外参占位 | 允许运行但进入报告 | identity_placeholder | 否 |

## 12. 可验证样例

| 样例 | 输入特征 | 预期输出 | 验证方式 |
|---|---|---|---|
| 左侧 anchor | 左 raw identity | 左 common camera 接近 identity | contract test |
| 右侧静止 | 右 raw identity | 右 common camera 接近 `common_from_right_start` | contract test |
| TCP 单位占位 | `camera_from_tcp` identity | TCP pose 等于 camera pose | unit test |
| raw 保留 | 输入有 fast_odom | cleaned 中可追溯 raw pose | contract test |

## 13. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 验收方式 |
|---|---|---|---|---|---|---|
| service_s1_006 | 实现 common frame 位姿转换输出 | 数据计算类 | [[FrameAlignmentConfig]]、现有 pose converter | raw/camera/TCP pose contract | `src/data_clean/service/`、`src/data_clean/tests/` | `python3` contract test |

## 14. 给 L3 任务生成的约束

1. 不得继续把 raw pose 不可追溯地替换为 common pose。
2. 不得混用 `camera_from_tcp` 和已废弃的 `tcp_from_camera`。
3. 输出数量必须与输入 pose topic 数量一致。

## 15. 开发者功能检验契约

本能力在 `./start_data_clean.sh --dev -> 场景一` 下对应的功能检验项：

```text
scene1_common_pose_transform
```

检验目标：

- 读取小样本 raw pose 和 [[FrameAlignmentConfig]]。
- 输出 [[CommonFrameCameraPose]] 和 [[CommonFrameTcpPose]] 调试样本。
- 验证 raw pose 可追溯保留。

测试产物：

- [[Scene1DevArtifact]]：`artifacts/common_pose_samples.json`
- 可选 [[Scene1DevArtifact]]：`artifacts/debug_common_pose.mcap`
- [[Scene1DevRunLog]]：`logs/run_log.json`

临时覆盖：

- 允许覆盖小样本输入、frame alignment 配置、camera 到 TCP 外参。
- 默认不写回正式配置。

输出隔离：

- 调试 pose 产物只写入本次 [[Scene1DevRun]]。

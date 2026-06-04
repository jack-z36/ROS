# L2 能力模块说明：cleaned MCAP 契约稳定

## 1. 能力名称

```text
cleaned MCAP 契约稳定
```

## 2. 所属位置

阶段：阶段二：数据清洗
L1：service_s1
场景：场景一：提取夹爪开合以及位姿转换
模块类别：数据定义类
来源功能模块清单：`DOCS/阶段二：数据清洗/02_service/场景一/功能模块清单.md`

## 3. 一句话目标

```text
稳定场景一对场景二公开的 CleanedMcap、Scene1Config 和 Scene1CleanReport 契约。
```

## 4. 能力角色

本能力把场景一从“已有脚本和局部实现”收敛成阶段二 Service 的稳定接口。它只定义契约和任务边界，不直接改源码。

## 5. 当前修正

本轮已把早先的“v1 替换原 pose payload”调整为：

```text
raw pose 必须保留或可追溯；
左右 arm-base TCP pose 是正式主位姿 topic；
gripper-only 浏览器向导和普通 Web 配置中心是场景一正式配置入口。
```

## 6. 上游关系

- raw MCAP 来自阶段一采集。
- [[GripperCalibrationConfig]] 来自已有浏览器 GoPro 标定程序。
- [[FrameAlignmentConfig]] 来自位姿转换配置生成模块（已废弃，保留历史兼容）。新链路使用 `camera_from_tcp` + [[WorkFrameInBaseConfig]] + `work_frames`。
- [[ArmBaseTcpPose]] 由 arm-base 位姿转换模块生成。

## 7. 下游关系

- 场景二读取 [[CleanedMcap]]、[[Scene1Config]]、[[Scene1CleanReport]]。
- 场景二优先消费 [[ArmBaseTcpPose]]，并可用 raw pose 做追溯。旧 `tcp_common` / `camera_common` 字段保留为历史兼容。

## 8. 数据定义职责

| 数据定义 | 职责 |
|---|---|
| [[CleanedMcap]] | cleaned MCAP 的 topic、payload 和追溯契约 |
| [[Scene1Config]] | 场景一配置总契约 |
| [[Scene1CleanReport]] | 清洗摘要和失败原因契约 |
| [[GripperCalibrationConfig]] | 夹爪开合标定配置 |
| [[FrameAlignmentConfig]] | common frame 和 pose 输出配置（已废弃，保留历史兼容） |
| [[ArmBaseTcpPose]] | arm-base TCP pose（主位姿字段） |
| [[TcpInCamera]] | TCP in camera 中间位姿 |
| [[WorkFrameInBaseConfig]] | work frame in base 配置 |
| [[CameraFromTcpExtrinsic]] | camera 到 TCP 外参 |
| [[CommonFrameCameraPose]] | common frame 下相机位姿（已废弃，保留历史兼容） |
| [[CommonFrameTcpPose]] | common frame 下 TCP 位姿（已废弃，保留历史兼容） |
| [[GripperWidthSample]] | 归一化夹爪宽度样本 |

## 9. 契约不变量

| 项 | 不变量 |
|---|---|
| 默认 cleaned 输出目录 | `asset/阶段二：数据清洗/dev/mcap_cleaned` |
| raw pose | 必须保留或可追溯 |
| 主位姿 topic | `/left_arm_base_tcp_pose`、`/right_arm_base_tcp_pose`，frame_id = `left_arm_base` / `right_arm_base` |
| 历史兼容字段 | `tcp_common` / `camera_common` 保留为历史兼容，不推荐消费方依赖 |
| gripper width | `std_msgs/msg/Float32`，归一化 `[0, 1]` |
| pose 数量 | raw/arm-base TCP 数量必须一致 |
| gripper 数量 | gripper 消息数等于对应 image 帧数 |

## 10. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 主要输出 |
|---|---|---|---|
| service_s1_001 | 稳定 cleaned MCAP 接口契约 | 数据定义类 | L2 数据定义和场景二契约同步 |
| service_s1_002 | 对接浏览器夹爪配置生成 | 工具对接类 | [[GripperCalibrationConfig]] 生成 |
| service_s1_003 | 实现夹爪宽度提取输出契约 | 数据计算类 | [[GripperWidthSample]] 输出 |
| service_s1_004 | 落地 frame_alignment 配置契约（已废弃） | 配置类 | [[FrameAlignmentConfig]] 加载（历史兼容） |
| service_s1_005 | 改造位姿转换配置生成器（已废弃） | 工具对接类 | `frame_alignment` 配置写出（历史兼容） |
| service_s1_006 | 实现 arm-base 位姿转换输出 | 数据计算类 | [[ArmBaseTcpPose]] 输出 |
| service_s1_007 | 补齐场景一输出契约校验 | 数据计算类 | validator 和 report contract |

## 11. 给 L3 任务生成的约束

1. 代码类 L3 必须使用 `$tdd`。
2. 不得在文档中宣称代码已完成尚未执行的改造。
3. 每个 L3 完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/service-s1-g1/`。

## 12. 开发者功能检验契约

本能力在 `./start_data_clean.sh --dev -> 场景一` 下对应的功能检验项：

```text
scene1_contract_preview
```

检验目标：

- 读取生产 [[Scene1Config]]。
- 检查 [[CleanedMcap]]、[[Scene1CleanReport]] 和场景一数据定义是否齐全。
- 生成场景一契约摘要，供开发者确认当前 cleaned MCAP 接口是否满足下游场景二消费。

测试产物：

- [[Scene1DevArtifact]]：`artifacts/contract_summary.json`
- [[Scene1DevArtifact]]：`artifacts/contract_summary.md`
- [[Scene1DevRunLog]]：`logs/run_log.json`

临时覆盖：

- 允许临时覆盖配置路径。
- 默认不写回正式配置。

输出隔离：

- 所有产物写入本次 [[Scene1DevRun]]，不得写入正式 cleaned/canonical 输出目录。

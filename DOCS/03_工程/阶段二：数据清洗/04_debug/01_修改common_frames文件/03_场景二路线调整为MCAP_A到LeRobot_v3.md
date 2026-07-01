# 03 场景二路线调整为 MCAP_A 到 LeRobot v3

## 问题定位

旧场景二后半段继续规划了：

```text
MCAP_A
-> common_frame 到 robot_base 转换
-> IK 求解
-> MCAP_B
-> 关节限制检查
```

用户已决定放弃这部分路线。当前不再围绕 IK、MCAP_B、关节限制检查继续改造。

## 新路线

后续主线改为：

```text
MCAP_A
-> 数据对齐
-> LeRobot v3 数据格式导出
```

因此当前 common_frames 修正计划只需要保证：

- MCAP_A 中的主位姿语义正确。
- 左右 TCP pose 已经分别处于对应机械臂基坐标系。
- MCAP_A 后续可直接进入数据对齐与 LeRobot v3 导出。

## 暂不修改的内容

以下内容暂不作为当前修改目标：

- IK 求解与 MCAP_B 生成器。
- `common_frame -> robot_base` 坐标转换 L3。
- RM65 SDK IK 适配器。
- MCAP_B 写出。
- 关节限制检查器。
- workspace 检查。
- SDK 限位函数自检。

这些内容可以保留在历史任务或存储目录中，但不得作为当前主线继续执行。

## 后续需要重新规划的方向

后续应围绕 LeRobot v3 重新规划：

1. MCAP_A 中哪些 topic 进入 observation。
2. MCAP_A 中哪些字段进入 action。
3. 左右机械臂基坐标系下 TCP pose 如何映射为 LeRobot v3 action。
4. gripper width、图像、触觉与 TCP pose 如何按时间对齐。
5. episode / frame / timestamp / metadata 如何生成。
6. 导出产物如何验收。

## 验收标准

后续完成新路线规划后，应满足：

- 当前计划不再要求实现 IK / MCAP_B / 关节限制。
- 新 L2 / L3 不再依赖 `RobotBaseTcpPose` 作为 common->base 后置转换产物。
- MCAP_A 可作为数据对齐和 LeRobot v3 导出的直接输入。
- LeRobot v3 导出路线有独立功能模块说明和 L3 任务。

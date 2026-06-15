# Octopus 采集模型

Octopus 是阶段一的显示与录制平台。它把 ROS2 topic 呈现给用户，并将选定 topic 录制为 MCAP。

## 三类关注点

- Display：让用户看到实时 topic。
- Recording：把选定 topic 写入 MCAP。
- Config：维护 topic、显示和录制配置。

显示链路和录制链路必须区分。UI 能看到 topic 只说明显示链路可用，不自动证明 MCAP 录制结果正确。

## 相关知识

更完整的 Octopus 架构知识由旧 `DOCS/Octopus_architecture.md` 迁移后沉淀。当前执行或维护 Octopus 时，应按根 `AGENTS.md` 路由读取对应知识和工程入口。

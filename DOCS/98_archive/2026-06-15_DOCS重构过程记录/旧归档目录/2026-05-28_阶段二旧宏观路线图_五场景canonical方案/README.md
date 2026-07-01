# 归档说明：阶段二旧宏观路线图（五场景 canonical 方案）

## 归档时间

2026-05-28

## 归档来源

本目录复制自：

```text
DOCS/阶段二：数据清洗/00_架构与路线图/
```

## 归档目的

本快照用于保留阶段二旧版宏观路线图，方便后续复盘“以 canonical dataset 为阶段二标准产物，再导出训练格式”的设计思路。

旧方案主链路为：

```text
raw MCAP
  -> cleaned MCAP
  -> validated MCAP
  -> aligned MCAP
  -> canonical_dataset_mcap/
  -> exports/
```

## 被替换原因

阶段二最终目标已经调整为直接产出 `LeRobotDataset v3`，用于 LeRobot 框架中的 ACT 模型训练。新方案不再把 `canonical_dataset_mcap/` 作为阶段二主产物，也不再把 IK、关节限位和 MuJoCo 仿真标注作为 `validated MCAP` 的 P0 主线。

## 当前有效文档

后续阶段二宏观设计以当前目录中的新版文件为准：

```text
DOCS/阶段二：数据清洗/00_架构与路线图/数据清洗pipeline宏观蓝图.md
DOCS/阶段二：数据清洗/00_架构与路线图/阶段二产物架构设计.md
DOCS/阶段二：数据清洗/00_架构与路线图/阶段二实现路线图.md
```

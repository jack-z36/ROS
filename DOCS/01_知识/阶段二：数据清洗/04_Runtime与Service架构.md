# Runtime 与 Service 架构

阶段二代码可按职责理解为：

```text
Schemas -> Config -> Repo -> Service -> Runtime -> UI
```

## Runtime

Runtime 负责流程编排和生命周期：入口、配置快照、run 目录、日志、manifest、场景调度和开发者检查。

## Service

Service 负责业务处理能力：数据清洗、变换、检测、滤波、对齐、桥接和报告生成。

## 工程边界

具体模块清单、功能模块说明、L2/L3 任务和当前进度属于工程文档，不写入本知识页。

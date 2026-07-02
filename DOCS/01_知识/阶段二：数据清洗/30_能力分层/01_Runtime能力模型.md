# Runtime 能力模型

## 定位

Runtime 负责流程编排和运行生命周期，不直接定义业务算法本身。

阶段二可以按以下分层理解：

```text
Schemas -> Config -> Repo -> Service -> Runtime -> UI
```

Runtime 位于 Service 之上，负责把配置、输入、Service 调用、产物目录、日志和错误摘要组织成一次可追溯运行。

## 核心能力

Runtime 主要承载：

- 入口分流和场景调度。
- 配置预检查和配置快照。
- 输入产物预检查。
- run 目录创建和产物索引。
- 结构化日志、manifest、错误摘要。
- 开发者检查和 Web job 编排。

## 对文档生成的影响

生成 Runtime 相关 L2/L3 时，应优先定义运行上下文、配置来源、输入输出路径、日志、manifest 和失败语义。不要把具体清洗、滤波、对齐算法写进 Runtime 概念里。

## 详细内容

- 源码架构：`src/data_clean/data_clean_architecture.md`
- Runtime 源码目录：`src/data_clean/runtime/`
- Runtime 数据类型：`src/data_clean/schemas/runtime_context.py`、`src/data_clean/schemas/runtime_results.py`

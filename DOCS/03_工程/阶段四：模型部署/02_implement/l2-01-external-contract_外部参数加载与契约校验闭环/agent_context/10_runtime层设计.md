# runtime 层 — L2-01 外部参数加载与契约校验闭环

> `l2_id`：`l2-01-external-contract`

本 L2 不在该层新增源码产物。

**原因**：`runtime/` 层负责时间、线程、队列、状态机、调度（如 shared buffer、inference worker、control loop、chunk smoother）。本 L2 只在程序**启动阶段**被同步调用一次（`load_deploy_config`），不参与稳态 tick 调度，不管理线程/队列/状态机。运行时调度属 L2-07（ControlLoop）范围。

**验收如何确认**：
- 本 L2 完成时不产生任何 `runtime/*.py` 文件。
- `load_deploy_config` 是同步无并发的编排函数（归 `config/`），不创建 timer/thread/queue。

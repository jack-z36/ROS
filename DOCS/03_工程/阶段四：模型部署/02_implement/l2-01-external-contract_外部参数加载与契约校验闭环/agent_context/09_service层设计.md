# service 层 — L2-01 外部参数加载与契约校验闭环

> `l2_id`：`l2-01-external-contract`

本 L2 不在该层新增源码产物。

**原因**：`service/` 层负责 RAM 内业务计算、转换、校验（如 observation collector、batch builder、safety guard、action adapter）。本 L2 的职责是外部参数加载与契约校验，其计算（类型化校验、contract 校验）归 `config/` 层，资源读取归 `repo/` 层，数据规格归 `types/` 层。本 L2 不做 observation/batch/safety/action 之类的 RAM 内业务计算——那些分别属 L2-02/L2-03/L2-05/L2-06 范围。

**验收如何确认**：
- L2-01 的所有校验逻辑（类型化校验器、contract 元数据校验）落在 `config/schema.py`，由 `config/` 层单测覆盖。
- 本 L2 完成时不产生任何 `service/*.py` 文件（验收时 `find src/model_deploy/act/service -name '*.py'` 应无 L2-01 产物）。

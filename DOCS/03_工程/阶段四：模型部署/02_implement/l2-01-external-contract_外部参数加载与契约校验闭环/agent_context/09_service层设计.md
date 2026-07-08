# service 层设计：L2-01

## 1. 本 L2 不在该层新增源码产物

原因：

- `service/` 层负责 RAM 内业务计算、转换、校验，例如 observation collector、batch builder、safety guard、action adapter。
- L2-01 的类型化配置校验归 `config/`，外部文件读取归 `repo/`，数据规格归 `types/`。
- 本 L2 不做 observation、batch、safety、action adapter 等业务计算。

## 2. 与去除平滑处理的关系

第一版没有独立 action smoothing service。本 L2 不创建 smoother、chunk blender、RTC aligner 或 smoothstep service。

## 3. 验收如何确认

- L2-01 不产生 `src/model_deploy/act/service/*.py` 产物。
- `rg` 检查 L2-01 设计和后续任务中不存在作为当前能力的 smoother/blender/RTC aligner。

## 4. 边界继承声明

本文件边界来自当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

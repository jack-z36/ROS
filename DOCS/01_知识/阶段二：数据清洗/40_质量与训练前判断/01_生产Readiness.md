# 生产 Readiness

## 定位

生产 readiness 判断的是当前配置和环境是否具备生成正式 LeRobotDataset v3 的前提。它不是 Forge quality 分数，也不是单个 smoke test 成功。

## 关键前提

生产 readiness 至少涉及：

- 左右夹爪标定完成。
- 左右 `camera_from_tcp` 外参存在。
- 左右 `work_frames` 由用户确认。
- 左右 arm-base TCP pose topic 可输出。
- RealMan SDK Algo 可用。
- Web job 使用正式生产配置并写出配置快照。

## 与 format-only 的区别

开发 smoke 可以用兼容路径验证结构和格式，但不能据此得出正式训练可用结论。

正式生产链路必须以 arm-base pose 和生产配置为基础。若 bridge 或任务标记为非 formal，应在训练前体检中视为阻断或复查项。

## 详细内容

- 生产配置检查：`src/data_clean/runtime/production_config.py`
- Web job 配置：`src/data_clean/runtime/web_pipeline_config.py`
- 当前状态：`DOCS/03_工程/阶段二：数据清洗/当前进度.md`

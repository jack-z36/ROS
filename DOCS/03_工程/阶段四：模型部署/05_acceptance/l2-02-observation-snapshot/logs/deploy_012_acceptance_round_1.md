# deploy_012 验收结论 — Round 1

结论：**PASS_LOCAL**

检查项逐条结果：

- [x] `observation_collector.py` 存在于 `src/model_deploy/act/service/observation_collector.py`。
- [x] `ObservationCollector` class 实现 `__init__`、`update_image`、`update_tcp_pose`、`update_gripper_state`、`missing_fields`、`stale_fields`、`snapshot`、`freshness_result`。
- [x] Thread safety: 使用 `threading.RLock` 保护缓存（reentrant 避免 snapshot() 内嵌套调用 missing_fields/stale_fields 死锁）。
- [x] `update_image` 更新 `_images` dict 和时间戳。
- [x] `update_tcp_pose` 按 side 和 position/orientation 写入 `_values` 和 stamps。
- [x] `update_gripper_state` 按 side 写入 `_values` 和 stamps。
- [x] `missing_fields()` 在 lock 下对比 required_image_keys + required_state_fields。
- [x] `stale_fields(now, max_age_s)` 返回超龄字段列表。
- [x] `snapshot(max_age_s)` 在 lock 下完成齐全性/新鲜度检查，构造 ObservationState 并调用 state_codec 生成 16D encoded_state，返回 ObservationSnapshot 或 None。
- [x] `_default_state_codec` 产生 16D float32 向量。
- [x] 无 ROS 依赖（service 层纯 RAM 计算）。
- [x] pytest 全部通过（13/13），无 skip。
- [x] 产物路径与 L3 声明一致。
- [x] 未修改 types/observation.py、config/、repo/、runtime/、ui/、pi05/ 等越界文件。

反馈说明：

部署环境已安装 Python 3.12.3、pytest 7.4.4、numpy，验收命令通过。修复了一处 RLock 问题（snapshot() 内嵌套持锁调用 missing_fields()/stale_fields() 导致非重入锁死锁，改用 RLock）。

验收命令：
```bash
python3 -m pytest src/model_deploy/act/tests/service/test_observation_collector.py -v
# 13 passed in 0.15s
```

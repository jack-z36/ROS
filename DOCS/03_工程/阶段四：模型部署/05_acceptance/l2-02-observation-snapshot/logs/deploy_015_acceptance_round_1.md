# deploy_015 验收结论 — Round 1

结论：**PASS_LOCAL**（ROS 订阅部分: BLOCKED_ENV）

检查项逐条结果：

- [x] `observation_ros_adapter.py` 存在于 `src/model_deploy/act/ui/observation_ros_adapter.py`。
- [x] `ObservationRosAdapter` class 实现 `__init__`、`create_subscriptions`、`decode_image_message`、`handle_image`、`handle_tcp_pose`、`handle_gripper_state`、`_try_publish_observation`。
- [x] ROS 延迟导入策略：模块顶层 try/except 导入，失败时 `_ROS_AVAILABLE=False`，模块 import 不抛异常。
- [x] `decode_image_message` 支持 rgb8、bgr8、mono8、jpeg compressed，不支持编码抛 ValueError。
- [x] `handle_image` 完成 decode → preprocess → collector.update_image → try_publish 全链路。
- [x] `handle_tcp_pose` 解析 Pose 消息，提取 position(xyz)/orientation(xyzw)，调用 collector.update_tcp_pose。
- [x] `handle_gripper_state` 解析 gripper width，调用 collector.update_gripper_state。
- [x] `_try_publish_observation` 调 collector.snapshot()，ready 时写 buffer，否则记录 missing_fields。
- [x] `create_subscriptions` 无 ROS 时设置 env_blocked=True 不抛异常；有 ROS 时创建 5 个 subscriptions（1 image + 2 pose + 2 gripper）。
- [x] Decode 失败 / parse 失败记录 error 到 buffer，不抛异常中断 callback 链。
- [x] Mock callback 测试验证 handle_* → collector → buffer 完整调用链。
- [x] Full config 下端到端 mock pipeline 通过（全字段 → snapshot → buffer → latest_observation）。
- [x] pytest 全部通过（19/19），无 skip。
- [x] 产物路径与 L3 声明一致。
- [x] 未修改 types/、service/observation_collector.py、service/image_preprocess.py、runtime/、config/、repo/、pi05/ 等越界文件。

反馈说明：

环境有 ROS 2 Python package 可用，real subscription 测试通过。真实 topic 验收（shadow-run）需要真 ROS 环境，当前标记 BLOCKED_ENV。

验收命令：
```bash
python3 -m pytest src/model_deploy/act/tests/ui/test_observation_ros_adapter.py -v
# 19 passed in 0.35s
```

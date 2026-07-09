# 验收卡片：deploy_015 ROS 适配器 ObservationRosAdapter

> [!info] 归属
> - 所属 L2：`l2-02-observation-snapshot`
> - L3 编号：`deploy_015`
> - 验收模式：`direct-local`（主）、`env-blocked`（辅助——真实 ROS subscription）
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_015` |
| 验收模式 | `direct-local` |
## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_015_ROS适配器ObservationRosAdapter.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/ui/observation_ros_adapter.py`、`src/model_deploy/act/tests/ui/test_observation_ros_adapter.py`、执行摘要、pytest 输出 |

## 2. 验收模式

- 主模式 `direct-local`：mock callback、decode、import 测试当前环境可直接运行。
- 辅助模式 `env-blocked`：真实 ROS subscription 需要 ROS 环境，当前标记 env-blocked。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/ui/test_observation_ros_adapter.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `observation_ros_adapter.py` 存在于 `src/model_deploy/act/ui/observation_ros_adapter.py`。
- [ ] `ObservationRosAdapter` class 存在，含 `__init__`、`create_subscriptions`、`decode_image_message`、`handle_image`、`handle_tcp_pose`、`handle_gripper_state`、`try_publish_observation` 方法。
- [ ] `decode_image_message(msg)` 处理 Image/CompressedImage → RGB numpy array。
- [ ] `handle_image` → decode → preprocess → collector.update_image → try_publish。
- [ ] `handle_tcp_pose` → 解析 position/orientation → collector.update_tcp_pose → try_publish。
- [ ] `handle_gripper_state` → 解析 width → collector.update_gripper_state → try_publish。
- [ ] `try_publish_observation`：ready 时 buffer.set_observation 被调用返回 True；missing 时 buffer.record_missing_fields 被调用返回 False。
- [ ] 无 ROS 环境时 `import act.ui.observation_ros_adapter` 不抛异常（延迟 import 策略）。
- [ ] 无 ROS 环境时 types/service/runtime 层 import 不触发 ROS 依赖。
- [ ] 无 ROS 时 `create_subscriptions` 记录 env-blocked 不抛异常。
- [ ] ui 层不实现核心 snapshot 业务规则（齐全性/新鲜度检查属 service 层）。
- [ ] ui 层不调用模型推理、不发布硬件命令。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 types/、service/、runtime/ 或 pi05/。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- 无 ROS 环境时 import ui 模块即报错（未延迟 import）。
- ui 层实现了核心 snapshot 业务规则。
- callback 中调用了模型推理或硬件命令。
- decode 失败静默通过（未记录 warning/diagnostics）。
- 修改了禁止修改的文件。
- pytest 失败或有未解释的 skip。

### BLOCKED_ENV

- 缺少 Python3 或 pytest，无法运行测试。
- 真实 ROS topic 订阅验收 → `BLOCKED_ENV`（当前无 ROS 环境，可解释）。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 影响 L2 Gate | 是 |
| 对应场景 | S5 无 ROS 环境可 import |
| 贡献 | ROS message 解码和转换、collector 更新编排、buffer 写入编排；无 ROS 环境 import 不失败 |
| 仍需后续 L3 | deploy_006 端到端集成验证；真实 ROS 订阅验收（env-blocked，等待 ROS 环境） |

## 6. 验收结论写入位置

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/deploy_015_acceptance_round_<n>.md
```

结论格式：

```text
结论：PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV / DEFER_TO_L2_GATE
检查项逐条结果：
- ...
blocked 项说明：
- adapter.real_subscription: 当前无 ROS 环境，真实 topic 订阅验收 BLOCKED_ENV
反馈说明：
```

# deploy_044 验收反馈 — 第 1 轮（acceptance_mode: direct-local）

- 验收 Agent：只读，未修改任何 source/tests/dispatch/cards/task/Git。
- 结论：**PASS_LOCAL**
- 辅助：`BLOCKED_ENV`（无 ROS graph / rclpy 不可用）、`BLOCKED_HARDWARE_EXPECTED`（无真机/急停/授权）。两者均为 dry-run-only 的预期阻塞，不阻断 `PASS_LOCAL`。

## 1. 必跑命令与真实输出

```text
$ PYTHONPATH=src python3 -m pytest \
    src/model_deploy/act/tests/ui/test_action_publisher.py \
    src/model_deploy/act/tests/ui/test_action_publisher_messages.py -v
# => 34 passed in 0.09s

$ PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/ui/ -q
# => 52 passed, 1 skipped in 0.24s
# 说明：1 skipped 来自 ui 目录下其余（ROS 观测适配）用例，因 rclpy 缺失而 skip，
#       与 deploy_044 无关，记为 aux BLOCKED_ENV。

$ PYTHONPATH=src python3 -c "from model_deploy.act.ui.action_publisher import ActionPublisher; print('IMPORT OK')"
# => IMPORT OK

$ grep -nE "create_subscription|create_timer|RuntimeConfig\.mode|publishes_command_topics|\.accepted|MoveIt|IK|TF|Modbus|serial|RM65" src/model_deploy/act/ui/action_publisher.py
# => NO FORBIDDEN TOKENS (GOOD) —— 边界扫描通过（G16）。
```

Python 3.12.3 / pytest 7.4.4 均可用，非 `BLOCKED_ENV`。

## 2. 场景 G09–G17 核对（门控发布闭环）

| 场景 | 要求 | 结果 | 证据 |
|---|---|---|---|
| G09 | constructor 恰好 6 publisher、0 subscription/timer/metrics | PASS | `test_exactly_six_publishers`：6 标签精确匹配；`/act/metrics` 未创建；`test_no_subscription_timer_api_needed`：FakeNode 无 subscription/timer API |
| G10 | REJECTED/OBSERVED/BLOCKED 三路，command=0 | PASS | `test_safety_rejected_is_rejected`(REJECTED/cmd=0)、`test_cli_disabled_is_observed`(OBSERVED/cmd=0/reason=COMMAND_OUTPUT_DISABLED)、`test_cli_enabled_permit_denied_is_blocked`(BLOCKED/cmd=0/reason=ESTOP_NOT_READY)；`_decide_command_publish_three_ways` 单测通过 |
| G11 | CLI=on+permit=on 进 command；policy 失败→cmd=0 | PASS | `test_cli_enabled_permit_allowed_publishes_four_commands`(PUBLISHED/count=4/plan=True)；`test_policy_publish_failure_stops_all_commands`(FAILED/cmd=0) |
| G12 | 首路失败停止剩余，真实 PARTIAL count | PASS | `test_first_command_failure_stops_remaining`(left_arm 成功1/right_arm 失败→停止/grippers=0/count=1/PARTIAL)；`test_all_commands_fail_first_is_failed`(count=0/FAILED) |
| G13 | 夹爪每侧独立，仅成功后更新 cache，skip 非失败 | PASS | `test_initial_publish_sets_cache`、`test_deadband_skip_is_not_a_failure`(skip 仍 PUBLISHED/count=2/cache 不更新)、`test_gripper_republish_after_deadband_updates_cache`、`test_failed_gripper_does_not_update_cache` |
| G14/G15 | status 在 C6 后构造，unknown=null，last result 一致 | PASS | `test_status_json_unknown_null_and_last_result_match`(driver_accepted/hardware_reached=None；`_last_result is res`)；`test_status_not_published_before_return` |
| G16 | 无 mode/accepted/subscription/timer/TF/IK/SDK/retry 越界 | PASS | grep 扫描无禁用 token；代码中无 `RuntimeConfig`/`.accepted`/`publishes_command_topics` 消费 |
| G17 | status best-effort 失败 → status_published=False | PASS | `test_status_publish_failure_is_best_effort`(outcome=PUBLISHED/cmd=4/status_published=False) |

## 3. 关键不变量：双门控（CLI 总开关 + CommandPermit 动态许可）

静态核对 `ActionPublisher.publish` 调用链（`action_publisher.py:602`）：

- **默认（CLI 未开启 `command_output_enabled=False`）**：`allow_command=False`，进入 `if not allow_command` 分支直接返回 OBSERVED，`command_count=0`。4 路 command topic **完全不写**；仅 `policy_action`（步骤 4 无条件写出）+ `status`（finalize best-effort）写入。✅ 符合「4 command 永不被写，只写 policy_action + command/status」。
- **CLI=on + permit=off**：`allow_command=False`，`outcome=BLOCKED`，`reason_code=permit.reason_code`，command 不写。✅
- **CLI=on + permit=on**：进入 command 循环，4 路全成功=PUBLISHED/count=4；policy 失败→command=0/FAILED；任一 command 首路失败→`break`，保留真实 count 与 PARTIAL，无伪造事务回滚。✅
- **无真实 ROS publisher 依赖**：`node.create_publisher` 注入式，rclpy 懒加载，缺 ROS 仍可导入/单测。✅
- **无越界消费**：无 `RuntimeConfig.mode` / `.accepted` / `publishes_command_topics`。✅
- **无部分写违规**：policy 在门控判断前写出；policy 失败时立即返回且未写任何 command。✅

## 4. 跨 L3 检查：deploy_043 测试文件最小改动

执行子代理声明对 `test_action_publisher_messages.py`（deploy_043 测试）做了「最小一处过时断言」改动。

核对结果（静态 + 全量单测）：

- 改动确为**最小单行**：`test_module_importable`（`test_action_publisher_messages.py:125-131`）新增 `assert hasattr(ap, "ActionPublisher")`，并附注释说明「deploy_044 extends this same module」。其余 13 个 deploy_043 用例（G07 五消息构造 / G08 失败不留 partial / 无 publisher 调用）**完整未触碰**。
- 该断言仅反映「`ActionPublisher` 现属于 `ui` 模块」这一事实翻转，未改动 deploy_043 的 B2/C8/C12-C14 行为或契约；`build_ros_messages` 的 5 消息 / 无 status / 失败不构造 partial bundle / 不调用 publish 等证据测试全部仍为原始实现并通过。
- deploy_043 全部 13 个用例在本轮 `34 passed` 中通过，无行为偏移。

**结论：未越界进入 deploy_043 范围，不计入 FAIL_LOCAL。**

## 5. 失败检查（FAIL_LOCAL 触发项）

无。所有必需本地检查均通过真实输出；无双门控泄漏、无失败事实伪造、无状态提前更新、pytest/扫描全部通过。

## 6. 修复请求（Fix Requests）

无。

## 7. 后续 / 主 Agent 动作

- `PASS_LOCAL`：主 Agent 应将 L3 任务文件
  `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_044_ActionPublisher门控发布闭环.md`
  移动到
  `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-05-action-publisher/`。
- 真机/ROS 观察阻塞（BLOCKED_ENV / BLOCKED_HARDWARE_EXPECTED）由 deploy_045 汇总，不在本卡范围。

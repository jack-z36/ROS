# 验收卡片：deploy_012 观测收集器 ObservationCollector

> [!info] 归属
> - 所属 L2：`l2-02-observation-snapshot`
> - L3 编号：`deploy_012`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_012` |
| 验收模式 | `direct-local` |
## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_012_观测收集器ObservationCollector.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/service/observation_collector.py`、`src/model_deploy/act/tests/service/test_observation_collector.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit / mock 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_observation_collector.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `observation_collector.py` 存在于 `src/model_deploy/act/service/observation_collector.py`。
- [ ] `ObservationCollector` class 存在，含 `__init__`、`update_image`、`update_tcp_pose`、`update_gripper_state`、`missing_fields`、`stale_fields`、`snapshot` 方法。
- [ ] `update_image(name, image)` 更新缓存和 stamp，unknown key 可拒绝或记录。
- [ ] `update_tcp_pose(side, position, orientation)` 更新 pose 缓存和 stamp。
- [ ] `update_gripper_state(side, width)` 更新 gripper 缓存和 stamp。
- [ ] `missing_fields()` 返回缺字段名列表。
- [ ] `stale_fields(now, max_age_s)` 返回过期字段名列表。
- [ ] `snapshot(max_age_s)` 在全字段 fresh 时返回 ObservationSnapshot（encoded_state.shape == (16,)）。
- [ ] `snapshot(max_age_s)` 在缺字段时返回 None。
- [ ] `snapshot(max_age_s)` 在字段过期时返回 None。
- [ ] 线程安全：使用 threading.Lock 保护共享缓存。
- [ ] 无 ROS import，service 层在无 ROS 环境下可 import 和单测。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 types/observation.py、config/、repo/、runtime/、ui/ 或 pi05/。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- collector 放在 runtime/ 或 ui/ 目录而非 service/。
- service 层 import 了 ROS packages。
- 照搬 Pi0.5 26D state 编码。
- 修改了禁止修改的文件（types/observation.py 等）。
- pytest 失败或有未解释的 skip。

### BLOCKED_ENV

- 缺少 Python3 或 pytest，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 影响 L2 Gate | 是 |
| 对应场景 | S1 Mock 全字段 snapshot 组装、S2 缺字段 / 过期拒绝 |
| 贡献 | 实现 L2-02 的核心业务逻辑——字段汇聚和 snapshot 构造 |
| 仍需后续 L3 | deploy_004 buffer 存储、deploy_005 ROS 订阅、deploy_006 端到端集成验证 |

## 6. 验收结论写入位置

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/deploy_012_acceptance_round_<n>.md
```

结论格式：

```text
结论：PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV / DEFER_TO_L2_GATE
检查项逐条结果：
- ...
反馈说明：
```

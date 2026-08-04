# 验收卡片：deploy_014 观测缓冲区 ObservationBuffer

> [!info] 归属
> - 所属 L2：`l2-02-observation-snapshot`
> - L3 编号：`deploy_014`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_014` |
| 验收模式 | `direct-local` |
## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_014_观测缓冲区ObservationBuffer.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/runtime/observation_buffer.py`、`src/model_deploy/act/tests/runtime/test_observation_buffer.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit / mock 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/runtime/test_observation_buffer.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `observation_buffer.py` 存在于 `src/model_deploy/act/runtime/observation_buffer.py`。
- [ ] `ObservationMetrics` dataclass 存在，字段含 observation_ready_count、replaced_observation_count、stale_observation_count、last_missing_fields、last_error、updated_at_s。
- [ ] `ObservationBuffer` class 存在，含 `set_observation`、`latest_observation`、`record_missing_fields`、`metrics_snapshot` 方法。
- [ ] `set_observation(observation)` 覆盖 latest observation，更新 counters。
- [ ] 连续写入 A 再写 B，`latest_observation()` 返回 B（覆盖语义，非队列）。
- [ ] buffer 为空时 `latest_observation()` 返回 None。
- [ ] `latest_observation(max_age_s)` 中超过 max_age_s 返回 None，stale counter 递增。
- [ ] `record_missing_fields(fields)` 更新 diagnostics。
- [ ] `metrics_snapshot()` 返回 metrics dict 副本。
- [ ] 线程安全：使用 threading.Lock 保护共享状态。
- [ ] 无 ROS import，runtime 层在无 ROS 环境下可 import 和单测。
- [ ] 未保存 request queue、chunk queue 或 ControlLoop 状态。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 types/、service/、ui/ 或 pi05/。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- latest_observation 返回旧 snapshot 而非最新（未覆盖）。
- max_age_s 不生效，超龄仍返回旧 snapshot。
- buffer 保存了历史队列（非 latest-only 语义）。
- buffer 中包含 request queue、chunk queue 或 ControlLoop cursor。
- runtime 层 import 了 ROS 或 service 层实现。
- 修改了禁止修改的文件。
- pytest 失败或有未解释的 skip。

### BLOCKED_ENV

- 缺少 Python3 或 pytest，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 影响 L2 Gate | 是 |
| 对应场景 | S1 Mock 全字段 snapshot 组装、S2 缺字段/过期拒绝、S4 Latest-only buffer 语义 |
| 贡献 | latest-only observation 保存、max_age 读取 gate、observation counters |
| 仍需后续 L3 | deploy_005 ROS adapter 写入路径、deploy_006 端到端集成验证 |

## 6. 验收结论写入位置

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/deploy_014_acceptance_round_<n>.md
```

结论格式：

```text
结论：PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV / DEFER_TO_L2_GATE
检查项逐条结果：
- ...
反馈说明：
```

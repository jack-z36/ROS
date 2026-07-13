# 验收卡片：deploy_042 Topic 候选载荷生成

> [!info] 归属
> - 所属 L2：`l2-05-action-publisher`
> - 对应 L3：`deploy_042`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读。

| L3 编号 | `deploy_042` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_042_Topic候选载荷生成.md` |
| 允许查看 | `service/action_output_adapter.py`、service 导出、局部测试、执行摘要/pytest |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/service/test_action_output_adapter.py -v
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] C9 仅接受 PASS/ADJUSTED + `ActionSpec`；REJECTED/action=None/shape/finite/爪域错误稳定失败。
- [ ] C10 保持 TCP7=xyz+xyzw 与单一非空 frame，无 TF/per-arm 假 frame。
- [ ] C11 严格 `0/0.5/1 -> 0/50/100`，越域失败，不 clip/猜尺度。
- [ ] B1 一次性返回完整 C4，任一失败无部分 payload。
- [ ] 文件无 ROS、permit、mode、publisher、runtime 或可变跨调用状态。

### FAIL_LOCAL

- 任一语义不符、pytest 失败，或 B1 吞入 ROS/硬件/安全投影职责。

### BLOCKED_ENV

- Python3/pytest/numpy 缺失导致命令不能运行；本 L3 不允许因无 ROS 而 BLOCKED。

## 4. L2 Gate 贡献

| 场景 | G04-G06 |
|---|---|
| 贡献 | B1/C9-C11 纯 RAM 16D -> C4 |
| 未完成影响 | deploy_044 不得启动，deploy_045 无法闭环 |


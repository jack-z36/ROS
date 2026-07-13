# 验收卡片：deploy_044 ActionPublisher 门控发布闭环

> [!info] 归属
> - 所属 L2：`l2-05-action-publisher`
> - 对应 L3：`deploy_044`
> - 验收模式：`direct-local`
> - 辅助模式：`env-blocked` / `hardware-blocked`
> - 验收轮次上限：3
> - 验收 Agent 只读。`hardware-blocked` 不能写成真机通过。

| L3 编号 | `deploy_044` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_044_ActionPublisher门控发布闭环.md` |
| 允许查看 | `ui/action_publisher.py`、UI 导出、B2/B3 测试、fake publisher 记录、执行摘要 |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/ui/test_action_publisher_messages.py \
  src/model_deploy/act/tests/ui/test_action_publisher.py -v
```

```bash
! rg -n "create_subscription|create_timer|RuntimeConfig\.mode|publishes_command_topics|\.accepted|MoveIt|IK|TF|Modbus|serial|RM65" \
  src/model_deploy/act/ui/action_publisher.py
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] constructor 创建恰好 6 publisher，0 subscription/timer/metrics publisher。
- [ ] REJECTED 不发 policy/command；CLI=False 为 OBSERVED；CLI=True+permit=False 为 BLOCKED，command 皆为 0。
- [ ] CLI=True+permit=True 才进入 command；policy 失败后 command=0。
- [ ] command 首个失败后停止剩余，C6 保留真实 count 与 PARTIAL，不伪造事务回滚。
- [ ] 夹爪 deadband/间隔每侧独立，仅成功 publish 后更新 cache，skip 不算失败。
- [ ] status 在最终 C6 后构造，unknown=null；last result 与返回 result 一致。
- [ ] 无 runtime/mode/accepted/TF/IK/SDK/fallback/retry 越界。

### FAIL_LOCAL

- 任一双门控泄漏、失败事实伪造、状态提前更新、pytest/扫描失败。

### BLOCKED

- 缺 ROS graph 记 `BLOCKED_ENV`；缺硬件/授权/急停记 `BLOCKED_HARDWARE_EXPECTED`。
- 本卡只认可 fake publisher local PASS，不允许因硬件缺失跳过 required 单测。

## 4. L2 Gate 贡献

| 场景 | G09-G17 |
|---|---|
| 贡献 | A1/B3/C15-C21 门控、外部写出、partial 事实与 status |
| 未完成影响 | deploy_045 不得启动，L2 Gate 无法运行 |


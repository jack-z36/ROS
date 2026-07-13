# 验收卡片：deploy_043 ROS 候选消息打包

> [!info] 归属
> - 所属 L2：`l2-05-action-publisher`
> - 对应 L3：`deploy_043`
> - 验收模式：`direct-local`
> - 辅助模式：`env-blocked`
> - 验收轮次上限：3
> - 验收 Agent 只读。

| L3 编号 | `deploy_043` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_043_ROS候选消息打包.md` |
| 允许查看 | `ui/action_publisher.py` 的 B2/C8/C12-C14、message 测试、执行摘要 |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/ui/test_action_publisher_messages.py -v
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] C12 产出 16D `Float32MultiArray`；C13 正确设置 frame/stamp/xyz/xyzw；C14 仅接受 `0..100`。
- [ ] C8 恰好包含 policy、两臂、两爪五个消息，不含 status。
- [ ] B2 任一 builder 失败时不返回部分 C8。
- [ ] B2 不读 CLI/permit/deadband，不调用 publisher，无任何外部副作用。
- [ ] 无 ROS graph 环境仍可 import 并用 mock message class 完成 required 测试。

### FAIL_LOCAL

- status 被提前构造、任一 publish 发生、消息字段/单位错误，或 required mock 测试失败。

### BLOCKED_ENV

- 真实 ROS message package 不可用可作辅助 BLOCKED，但不得代替 required local mock PASS。

## 4. L2 Gate 贡献

| 场景 | G07-G08 |
|---|---|
| 贡献 | B2/C8/C12-C14 无副作用五消息 bundle |
| 未完成影响 | deploy_044 不得启动 |


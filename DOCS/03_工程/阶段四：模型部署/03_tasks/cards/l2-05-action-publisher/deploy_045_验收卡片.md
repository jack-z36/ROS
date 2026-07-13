# 验收卡片：deploy_045 L2 Gate 集成测试与验收脚本

> [!info] 归属
> - 所属 L2：`l2-05-action-publisher`
> - 对应 L3：`deploy_045`
> - 验收模式：`direct-local`
> - 辅助模式：`env-blocked` / `hardware-blocked`
> - 验收轮次上限：3
> - 验收 Agent 只读。`hardware-blocked` 不能写成真机通过。

| L3 编号 | `deploy_045` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_045_L2Gate集成测试与验收脚本.md` |
| 允许查看 | Gate 集成测试、`l2_05_verify.sh`、验收结果/日志、执行摘要 |

## 2. 必跑命令

```bash
bash src/model_deploy/act/scripts/l2_05_verify.sh --case local
```

```bash
bash src/model_deploy/act/scripts/l2_05_verify.sh --case command-disabled
bash src/model_deploy/act/scripts/l2_05_verify.sh --case permit-blocked
bash src/model_deploy/act/scripts/l2_05_verify.sh --case topic-payloads
bash src/model_deploy/act/scripts/l2_05_verify.sh --case ros-message-bundle
bash src/model_deploy/act/scripts/l2_05_verify.sh --case command-enabled-mock
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] G01-G17 皆有可执行覆盖，local/mock 无 FAIL，required 项无 BLOCKED。
- [ ] 脚本按 types/config/repo/service/runtime/ui/boundary 分组输出。
- [ ] FAIL 行包含文件 -> class -> B/C 微元 -> pytest node -> error 完整链。
- [ ] 退出码：全 required PASS/仅预期 BLOCKED=0；required FAIL=1；参数/自检错误=2。
- [ ] G16 确认无 L2-05 repo/runtime 产物，无 subscription/timer/mode/accepted/TF/IK/SDK。
- [ ] 默认不存在 command-enabled real-robot 执行命令。

### FAIL_LOCAL

- 任一 required 场景缺失/失败，输出格式/退出码错误，或把 BLOCKED 伪装 PASS。

### BLOCKED

- G18 无 ROS 2：`BLOCKED_ENV`，需记录缺失命令/依赖。
- G19 无 driver/机器人/人工授权/急停：`BLOCKED_HARDWARE_EXPECTED`。
- 两者不阻止 required local Gate，但不得写成真机 PASS。

## 4. L2 Gate 贡献

| 场景 | G01-G19 |
|---|---|
| 贡献 | 统一 local/mock Gate 与 ROS/硬件阻断登记 |
| 未完成影响 | 不允许启动 L2 整体验收或人类签字 |


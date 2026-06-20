# L3 验收卡片：deploy_020 rm65_driver_node（状态发布 + 命令执行）

## 任务身份

| 字段 | 内容 |
|---|---|
| L3 编号 | `deploy_020` |
| L3 文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_020_rm65_driver_node.md` |
| 所属 L2 | `l2-05-hardware` |
| 验收卡片 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_020_验收卡片.md` |
| 对应 L2 运行场景 | `[S5]` |
| 验收模式 | `static-review` |
| 辅助模式 | `[hardware-blocked]` |
| 本地验收是否必须 | `false` |
| 最多迭代轮次 | `3` |
| 反馈目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs` |

## 验收 agent 权限

- 只评审、不改源码、不改测试、不移动任务文件、不提交 Git。
- 可以读取本卡片、对应 L3 文件、执行摘要、相关 diff、L3 声明的必读上下文和允许读取的代码。
- 可以运行本卡片允许的本地命令。
- 发现问题时输出可操作反馈，交回执行 agent 修复。

## 验收目标

确认执行 agent 是否完成 `rm65_driver_node（状态发布 + 命令执行）` 的唯一目标，并在 Ubuntu 22.04 无外联硬件条件下给出可验证结论。

## 验收模式说明

主模式：`static-review`。辅助模式：`[hardware-blocked]`。

验收重点：S5 driver 节点代码边界可评审，RM65 实机 blocked。

## 本地验收命令

本 L3 不强制独立运行命令。验收 agent 必须执行静态评审：读取执行摘要、检查 diff、确认允许/禁止修改边界、确认接口和回滚说明。

## 静态评审清单

- [ ] 任务文件身份、dispatch task_id、验收卡片 task_id 一致。
- [ ] 执行摘要存在，且列出修改文件、实际命令、结果和未验证项。
- [ ] 修改范围不超出 L3 的允许修改边界。
- [ ] 禁止修改项没有被触碰；如触碰必须判定 FAIL_LOCAL。
- [ ] 当前代码路径仍使用 src/model_deploy/pi05/...。
- [ ] 无硬件项没有被写成真机通过。
- [ ] 真实硬件验收项保持 blocked，且写明解除条件。

## 输出结论

验收 agent 必须输出以下结论之一：`PASS_LOCAL / FAIL_LOCAL / BLOCKED_HARDWARE_EXPECTED`。

反馈文件路径格式：

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs/deploy_020_acceptance_round_<n>.md
```

反馈内容必须包含：

1. 验收轮次。
2. 读取的文件。
3. 执行的命令或静态检查项。
4. 观察到的通过 / 失败现象。
5. 未验证项。
6. 最终结论。
7. 如果失败，列出交给执行 agent 的回修项。

## 下游 / 硬件说明

- `downstream-l2` 项只说明当前 L3 不能单独证明完整运行闭环，不能跳过评估。
- `hardware-blocked` 项在无硬件环境下只能记录 blocked 和解除条件，不能写成真机通过。
- `env-blocked` 项必须记录缺少的 ROS、bundle、SDK 或依赖。

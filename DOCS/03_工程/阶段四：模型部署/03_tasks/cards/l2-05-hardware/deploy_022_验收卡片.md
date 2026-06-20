# L3 验收卡片：deploy_022 新 launch + shadow-run 全链路验证

## 任务身份

| 字段 | 内容 |
|---|---|
| L3 编号 | `deploy_022` |
| L3 文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_022_launch与shadow_run全链路.md` |
| 所属 L2 | `l2-05-hardware` |
| 验收卡片 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_022_验收卡片.md` |
| 对应 L2 运行场景 | `[S1, S2, S3, S4]` |
| 验收模式 | `direct-local` |
| 辅助模式 | `[env-blocked]` |
| 本地验收是否必须 | `true` |
| 最多迭代轮次 | `3` |
| 反馈目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs` |

## 验收 agent 权限

- 只评审、不改源码、不改测试、不移动任务文件、不提交 Git。
- 可以读取本卡片、对应 L3 文件、执行摘要、相关 diff、L3 声明的必读上下文和允许读取的代码。
- 可以运行本卡片允许的本地命令。
- 发现问题时输出可操作反馈，交回执行 agent 修复。

## 验收目标

确认执行 agent 是否完成 `新 launch + shadow-run 全链路验证` 的唯一目标，并在 Ubuntu 22.04 无外联硬件条件下给出可验证结论。

## 验收模式说明

主模式：`direct-local`。辅助模式：`[env-blocked]`。

验收重点：S1/S2/S3/S4 launch / shadow-run；缺 ROS 时 BLOCKED_ENV。

## 本地验收命令

验收 agent 必须优先执行 L3 文件中记录的自动化验收命令。当前卡片抽取到的命令如下：

```bash
# launch 语法检查
python3 -c "
import ast
path = 'src/model_deploy/pi05/deploy/launch/pi05_rm65_deploy.launch.py'
src = open(path, encoding='utf-8').read()
ast.parse(src)
for node in ['command_bridge_sender_node','rm65_driver_node','elephant_gripper_node','Pi05VlaDeployNode']:
    assert node in src, f'{node} not in launch'
assert 'shadow' in src.lower(), 'default mode should mention shadow'
print('deploy_022 launch验收通过')
"
# shadow-run 实际执行（需硬件环境或 stub）
# ros2 launch deploy pi05_rm65_deploy.launch.py mode:=shadow-run
```

如果 Ubuntu 22.04 当前缺少 ROS、bundle 或 Python 依赖，结论写 `BLOCKED_ENV`，并记录缺失项；不得把环境缺失写成通过。

## 静态评审清单

- [ ] 任务文件身份、dispatch task_id、验收卡片 task_id 一致。
- [ ] 执行摘要存在，且列出修改文件、实际命令、结果和未验证项。
- [ ] 修改范围不超出 L3 的允许修改边界。
- [ ] 禁止修改项没有被触碰；如触碰必须判定 FAIL_LOCAL。
- [ ] 当前代码路径仍使用 src/model_deploy/pi05/...。
- [ ] 无硬件项没有被写成真机通过。

## 输出结论

验收 agent 必须输出以下结论之一：`PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV`。

反馈文件路径格式：

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs/deploy_022_acceptance_round_<n>.md
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

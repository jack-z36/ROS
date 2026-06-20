# L3 验收卡片：deploy_003 action_codec 维度校验跟随

## 任务身份

| 字段 | 内容 |
|---|---|
| L3 编号 | `deploy_003` |
| L3 文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_003_action_codec维度校验跟随.md` |
| 所属 L2 | `l2-01-types` |
| 验收卡片 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_003_验收卡片.md` |
| 对应 L2 运行场景 | `[S3]` |
| 验收模式 | `direct-local` |
| 辅助模式 | `[]` |
| 本地验收是否必须 | `true` |
| 最多迭代轮次 | `3` |
| 反馈目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs` |

## 验收 agent 权限

- 只评审、不改源码、不改测试、不移动任务文件、不提交 Git。
- 可以读取本卡片、对应 L3 文件、执行摘要、相关 diff、L3 声明的必读上下文和允许读取的代码。
- 可以运行本卡片允许的本地命令。
- 发现问题时输出可操作反馈，交回执行 agent 修复。

## 验收目标

确认执行 agent 是否完成 `action_codec 维度校验跟随` 的唯一目标，并在 Ubuntu 22.04 无外联硬件条件下给出可验证结论。

## 验收模式说明

主模式：`direct-local`。辅助模式：`[]`。

验收重点：S3 action codec 非法输入拒绝。

## 本地验收命令

验收 agent 必须优先执行 L3 文件中记录的自动化验收命令。当前卡片抽取到的命令如下：

```bash
python3 -c "
import ast
path = 'src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py'
src = open(path, encoding='utf-8').read()
ast.parse(src)  # 语法正确
# 确认无硬编码 14（在逻辑中）
import re
# 找数字 14 的出现，排除注释和 docstring 中的描述性 14-D（后者应已改成 16-D）
logic_14 = [l for l in src.splitlines() if re.search(r'[^-_\w]14[^-\w]', l) and not l.strip().startswith('#') and not l.strip().startswith('\"\"\"')]
assert not logic_14, f'发现可能的硬编码14: {logic_14}'
# 确认 ACTION_DIM 仍被引用
assert 'ACTION_DIM' in src
print('deploy_003 验收通过: 无硬编码14, ACTION_DIM引用保留')
"
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

验收 agent 必须输出以下结论之一：`PASS_LOCAL / FAIL_LOCAL`。

反馈文件路径格式：

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/deploy_003_acceptance_round_<n>.md
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

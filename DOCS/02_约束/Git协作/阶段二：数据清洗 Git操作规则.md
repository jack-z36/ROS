# 阶段二：数据清洗 Git 操作规则

## 适用范围

- 阶段：阶段二：数据清洗
- 任务模式：阶段二 Runtime MVP、Service 场景分支、Win/Ubuntu 接力执行 L3
- 适用对象：阶段二工程文档、Runtime / Service 代码、阶段二 L2/L3 任务文件
- 不适用对象：阶段四模型部署、`model_deploy` 集成分支、阶段四 L2 分支

使用本文件前，必须先读取：

```text
DOCS/02_约束/Git协作/Git操作规则.md
```

本文件只描述阶段二数据清洗的分支模型和同步流程；远端、账号、提交前检查、`pull --ff-only`、禁止强推等全局底线以 `Git操作规则.md` 为准。

## 阶段二分支模型

`main` 只保存稳定完成结果，不作为 Win 或 Ubuntu 的日常工作台。

阶段二默认分支：

| 任务线 / 场景 | 默认分支 |
|---|---|
| Runtime MVP | `runtime-mvp` |
| Service 场景一 | `service-s1` |
| Service 场景二 | `service-s2` |
| Service 场景三 | `service-s3` |
| Service 场景四 | `service-s4` |
| Service 场景五 | `service-s5` |

## 主机分工

- Win 主机负责创建和推进阶段二 Runtime 分支或 Service 场景分支上的架构文档、L2、L3。
- Ubuntu 主机只在对应 Runtime 分支或 Service 场景分支上执行 L3、修改代码和测试、更新当前 L3 文件并归档。
- Ubuntu 主机禁止直接提交或推送 `main`。
- 阶段二 Runtime 分支或 Service 场景分支合并回 `main` 只由 Win 主机执行。
- Win 和 Ubuntu 如果在同一个 Runtime 分支或 Service 场景分支接力，开始工作前必须先 `git pull --ff-only`；遇到分叉或冲突时停止，不自动 merge/rebase。

## 固定操作流程

Win 开始 Runtime MVP 分支：

```powershell
git switch main
git pull --ff-only
git switch -c runtime-mvp
```

Win 写完阶段二规划文档、L2 或 L3 后：

```powershell
git add -A
git status
git commit -m "docs(runtime): plan <模块名> 北京时间 YYYY-MM-DD HH:MM"
git push -u origin runtime-mvp
```

Ubuntu 执行 Runtime MVP L3 前：

```bash
git fetch origin
git switch runtime-mvp || git switch -c runtime-mvp origin/runtime-mvp
git pull --ff-only
```

Ubuntu 完成单个 L3 后：

```bash
git add -A
git status
git commit -m "feat(runtime): complete <L3任务名> 北京时间 YYYY-MM-DD HH:MM"
git push
```

Win 将 Runtime MVP 分支合并到 `main`：

```powershell
git switch main
git pull --ff-only
git merge --no-ff runtime-mvp -m "merge(runtime): integrate Runtime MVP 北京时间 YYYY-MM-DD HH:MM"
git push origin main
```

Service 场景分支同理，将 `runtime-mvp` 替换为对应 `service-sX` 分支。

## 阻断条件

出现以下任一情况时，停止阶段二同步并向用户报告：

- 当前分支不是正在执行的 Runtime 或 Service 场景分支。
- Ubuntu 主机准备直接提交或推送 `main`。
- `git pull --ff-only` 失败。
- 远端分叉、合并冲突或出现非预期工作区变更。
- 准备提交的内容超出当前阶段二 L3 或场景分支允许范围。
- 需要改写历史、强推或删除远端分支。

## 与阶段四规则的边界

阶段二规则不得用于阶段四模型部署。阶段四的 `model_deploy` 集成分支、`model_deploy-l2-xx-*` 分支、L2 Gate 自动同步、`--no-ff` 合入 `model_deploy`，全部以：

```text
DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md
```

为准。

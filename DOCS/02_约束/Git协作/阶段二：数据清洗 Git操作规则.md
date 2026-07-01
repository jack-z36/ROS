# 阶段二：数据清洗 Git 操作规则

## 适用范围

- 阶段：阶段二：数据清洗
- 任务模式：阶段二规划、L2/L3 生成、L3 执行、Runtime / Service 代码维护
- 适用对象：`data_clean` 二级长期分支及其三级功能分支
- 不适用对象：阶段一数据采集、阶段四模型部署、`main` 稳定分支合并流程

使用本文件前，必须先读取：

```text
DOCS/02_约束/Git协作/Git操作规则.md
```

本文件只描述阶段二数据清洗的分支和同步流程；远端、账号、提交前检查、`pull --ff-only`、禁止强推等全局底线以 `Git操作规则.md` 为准。

## 阶段二分支模型

- 二级长期分支：`data_clean`
- 三级功能分支：从 `data_clean` 创建，命名为 `feat/data_clean/<topic>`、`fix/data_clean/<topic>`、`docs/data_clean/<topic>`、`chore/data_clean/<topic>` 或 `spike/data_clean/<topic>`。
- 阶段二不再使用固定的 `runtime-mvp`、`service-s1`、`service-s2`、`service-s3`、`service-s4`、`service-s5` 长期分支。
- `main` 只保存稳定里程碑，不作为 Win 文档规划或 Ubuntu L3 执行的日常工作台。

## 主机分工

- Win 主机负责在 `data_clean` 或其三级文档 / 功能分支上推进阶段二架构文档、L2、L3。
- Ubuntu 主机只在当前 L3 对应的 `data_clean` 三级功能分支上执行 L3、修改代码和测试、更新当前 L3 文件并归档。
- Ubuntu 主机禁止直接提交或推送 `main`。
- 阶段二稳定里程碑完成后，`data_clean` 合入 `main`。
- Win 和 Ubuntu 如果在同一三级分支接力，开始工作前必须先 `git pull --ff-only`；遇到分叉或冲突时停止，不自动 rebase 或强推。

## 固定操作流程

开始阶段二功能：

```bash
git fetch origin
git switch data_clean || git switch -c data_clean origin/data_clean
git pull --ff-only
git switch -c feat/data_clean/<topic>
```

完成阶段二功能后合入 `data_clean`：

```bash
git switch data_clean
git pull --ff-only
git merge --no-ff feat/data_clean/<topic> -m "merge(data_clean): integrate <topic> 北京时间 YYYY-MM-DD HH:MM"
git push origin data_clean
git branch -d feat/data_clean/<topic>
git push origin --delete feat/data_clean/<topic>
```

阶段二稳定里程碑合入 `main`：

```bash
git switch main
git pull --ff-only
git merge --no-ff data_clean -m "merge(data_clean): integrate stable milestone 北京时间 YYYY-MM-DD HH:MM"
git push origin main
```

## 阻断条件

出现以下任一情况时，停止阶段二同步并向用户报告：

- 当前分支不是 `data_clean` 或从 `data_clean` 创建的当前任务三级分支。
- Ubuntu 主机准备直接提交或推送 `main`。
- `git pull --ff-only` 失败。
- 远端分叉、合并冲突或出现非预期工作区变更。
- 准备提交的内容超出当前阶段二 L3 或功能分支允许范围。
- 需要改写历史、强推或删除二级长期分支。

## 与阶段四规则的边界

阶段二规则不得用于阶段四模型部署。阶段四的 `model_deploy` 二级长期分支和 `feat/model_deploy/<topic>` 等三级功能分支，以：

```text
DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md
```

为准。

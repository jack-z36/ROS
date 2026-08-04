# 阶段四：模型部署 Git 操作规则

## 适用范围

- 阶段：阶段四：模型部署
- 任务模式：阶段四 L2 / L3 执行、模型部署代码和工程文档协作
- 适用对象：`model_deploy` 二级长期分支、阶段四三级功能分支、`src/model_deploy/act/` 和阶段四工程文档
- 不适用对象：阶段二数据清洗分支、`main` 稳定分支合并流程

使用本文件前，必须先读取：

```text
DOCS/02_约束/Git协作/Git操作规则.md
```

## Ralph / OpenCode 加载要求

当任务属于阶段四 Ralph / OpenCode 循环工程时，OpenCode 主 Agent 必须在读取状态摘要、选择目标 L2、检查分支或派发 L3 前加载本文件。不得等到准备提交时才读取 Git 规则。

加载链路固定为：

```text
ralph_stage4_prompt.md
→ DOCS/02_约束/上下文加载/08_循环工程加载规则.md
→ DOCS/02_约束/Git协作/Git操作规则.md
→ DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md
→ DOCS/02_约束/循环工程/behaviors/11_Git原子提交行为.md
```

主 Agent 输出当前循环状态摘要时，必须同时说明当前分支、目标三级分支、remote 名称和 remote URL 是否满足本文件要求。

## 分支模型

- 二级长期分支：`model_deploy`
- 三级功能分支：从 `model_deploy` 创建，命名为 `feat/model_deploy/<topic>`、`fix/model_deploy/<topic>`、`docs/model_deploy/<topic>`、`chore/model_deploy/<topic>` 或 `spike/model_deploy/<topic>`。
- L2 / L3 工作如果需要独立分支，统一落在三级功能分支命名下，例如 `feat/model_deploy/l2-03-assembly`。
- 三级分支合入 `model_deploy` 后删除；不再长期保留旧的 `model_deploy-l2-xx-*` 分支。

普通单个 L3 执行 sub-agent 不得提交或推送。Ralph / OpenCode 循环工程中，主 Agent 在单个 L3 验收进入可提交终态后，必须在当前三级功能分支进行 L3 原子提交并尝试小包 push；同一功能分支的 required L3 全部通过 Gate 后，才允许合入 `model_deploy`。

## 功能分支开工流程

从 `model_deploy` 创建新三级功能分支：

```bash
git fetch origin
git switch model_deploy
git pull --ff-only
git switch -c feat/model_deploy/<topic>
```

如果远端已经存在对应三级功能分支：

```bash
git fetch origin
git switch feat/model_deploy/<topic> || git switch -c feat/model_deploy/<topic> origin/feat/model_deploy/<topic>
git pull --ff-only
```

## 多 Agent 并行工作树

阶段四存在两种典型并行场景：Ralph / OpenCode 循环工程主 Agent 在 `model_deploy` 上持续调度 L2/L3，同时用户或另一个 Agent 需要在三级功能分支上开发代码或设计文档。此时**不得**在主工作目录内用 `git switch` 切换分支，必须使用工作树。

具体规则见全局 `DOCS/02_约束/Git协作/Git操作规则.md` 的「工作树」节。以下为阶段四专属约定。

### 触发时机

OpenCode 主 Agent 或用户在以下情况必须使用 worktree：

- 主工作目录已检出 `model_deploy` 且工作区存在 Ralph / OpenCode 循环工程的活跃改动（状态摘要、dispatch、任务文件等）。
- 需要同时在 `model_deploy` 和某个三级功能分支上工作。
- 用户明确要求"在其他目录继续开发某个 L2/L3"。

### 阶段四工作树命名

阶段四的工作树目录统一命名为：

```text
worktrees/<l2-id 或简短用途描述>
```

示例：

```text
worktrees/l2-01-external-contract  → feat/model_deploy/l2-01-external-contract-design
worktrees/l2-03-act-inference      → feat/model_deploy/l2-03-act-inference
```

### 加载链更新

OpenCode 主 Agent 在`00_status/current_loop_snapshot.md` 的输出中，必须说明当前所在工作树路径、检出分支，以及是否存在其他活跃工作树。格式：

```text
当前工作树：/home/hit/ROS/worktrees/l2-01-external-contract
检出分支：feat/model_deploy/l2-01-external-contract-design
其他活跃工作树：/home/hit/ROS (model_deploy)
```

### Gate 合入后清理

三级功能分支合入 `model_deploy` 并确认远端同步后，应删除对应工作树：

```bash
# 回到主工作目录
cd /home/hit/ROS
# 删除工作树（必须先确保工作树内无未提交改动）
git worktree remove worktrees/<l2-id>
```

合入 `model_deploy` 本身在任一工作树或主工作目录中均可执行——优先在主工作目录执行，除非主工作目录被 Ralph / OpenCode 循环工程占用且有未完成状态无法中断。

## L3 原子提交流程

Ralph / OpenCode 循环工程中，当单个 L3 验收结论为 `PASS_LOCAL`、`DEFER_TO_GATE`、`BLOCKED_ENV` 或 `BLOCKED_HARDWARE_EXPECTED`，且相关证据已登记后，主 Agent 可以执行 L3 原子提交。

如果验收结论为 `PASS_LOCAL`，提交前必须先把对应 L3 任务文件从 `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/<new-l2>/` 移动到 `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/<new-l2>/`，并把该归档移动纳入同一个 L3 原子提交。其他可提交终态不是“验收任务执行通过”，默认不触发该归档。

```bash
git status --short --branch
git branch --show-current
git remote -v
git add <当前L3允许提交的文件清单>
git status --short
git commit -m "feat(model_deploy): <deploy_id> <summary> 北京时间 YYYY-MM-DD HH:MM"
git push -u origin feat/model_deploy/<topic>
```

提交前必须确认当前分支是该 L3 所属三级功能分支。禁止 `git add -A`、`git commit --amend`、force push、rebase 或跨功能分支混合提交。

如果本地 commit 成功但 push 因网络失败，必须记录到 `DOCS/03_工程/阶段四：模型部署/00_status/git_sync_status.md`，将该 L3 标为 `pending_push`，并用 docs-only 小提交持久化记录；不得 amend 已有 L3 commit。

## Gate 后合入流程

当且仅当所属功能 Gate 通过 **且 人类验收签字通过** 后，AI 可以自动执行以下同步流程。

人类验收关卡规则见 `DOCS/02_约束/工作流/阶段四开发工作流/attachments/人类验收关卡规则.md`。合入前必须检查 `05_acceptance/<l2>/验收结果.md` 的「人类验收」段：未填写或勾选「不通过」时，停止合入并向用户报告。

```bash
git status --short --branch
git push -u origin feat/model_deploy/<topic>
git switch model_deploy
git pull --ff-only
git merge --no-ff feat/model_deploy/<topic> -m "merge(model_deploy): integrate <topic> 北京时间 YYYY-MM-DD HH:MM"
git push origin model_deploy
git branch -d feat/model_deploy/<topic>
git push origin --delete feat/model_deploy/<topic>
```

## 阻断条件

出现以下任一情况时，停止自动同步并向用户报告：

- 功能 Gate 未通过，或对应验收结果未记录通过结论。
- 人类验收未签字、勾选「不通过」或缺少用户名/日期（见人类验收关卡规则）。
- 当前分支不是对应三级功能分支，或该分支不是从 `model_deploy` 开出。
- `model_deploy` 远端领先、本地分叉或 `pull --ff-only` 失败。
- `git merge --no-ff` 产生冲突。
- 工作区包含本功能之外的非预期变更。
- 待提交内容包含超大文件、缓存、私有配置、环境目录或未归档解释的运行产物。
- 真机相关任务缺少风险确认、急停准备或人工验收记录。

## 阶段四提交范围

允许提交：

- `src/model_deploy/act/` 下本 L3 明确允许的源码、配置、launch、脚本或测试。
- 当前 L2 对应的 `DOCS/03_工程/阶段四：模型部署/02_implement/<new-l2>/` 设计文档。
- 当前 L2 对应的 `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/<new-l2>/` 任务文件。
- 当前 L2 对应的 `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/<new-l2>/` 已通过 L3 任务归档文件。
- 当前 L2 对应的 `DOCS/03_工程/阶段四：模型部署/03_tasks/task/dispatch/<new-l2>.yaml` dispatch。
- 当前 L2 对应的 `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/<new-l2>/` 验收卡片。
- 当前 L2 对应的 `DOCS/03_工程/阶段四：模型部署/05_acceptance/<new-l2>/` 验收结果、脚本和日志。
- `DOCS/02_约束/` 下本次明确要求维护的约束、模板或工作流文件。

禁止提交：

- `src/model_deploy/pi05/`、`DOCS/03_工程/阶段四：模型部署/pi05_old/` 或其他 Pi0.5 历史源码作为 L3 修改落点；Pi0.5 只能作为只读参考。
- `DOCS/03_工程/阶段四：模型部署/02_implement/归档/`、`03_tasks/归档/_legacy_layer_based_act/`、`05_acceptance/_legacy_layer_based_act/` 下的旧 layer-based ACT 产物，除非当前任务明确是文档归档、迁移或降权维护。
- ROS 构建产物：`build/`、`install/`、`log/`
- Python 缓存和测试缓存：`__pycache__/`、`*.pyc`、`.pytest_cache/`
- 本地环境、私有配置、下载缓存、模型权重和大型数据产物
- 未经说明的第三方源码改动，尤其是 `src/model_deploy/third_party/`

## Gate 与 Git 同步关系

Gate 是阶段四自动同步的前置条件。每个功能分支的验收结果必须记录：

- required L3 完成情况。
- 执行过的运行命令或人工验收项。
- 测试输入：mock 数据、配置、ROS topic、shadow-run 或 real-robot 条件。
- 观察点：stdout、日志、topic、生成文件、metrics 或机器人行为。
- 通过现象：明确写出看到什么输出、日志、shape、状态或人工现象才算 OK。
- 失败现象与排查入口。
- 脚本和日志路径。
- 未验证项。
- 是否通过 Gate。
- 是否允许自动同步。
- 自动同步结果。

未通过 Gate 的三级功能分支不得合入 `model_deploy`。L3 原子提交只允许在所属三级功能分支上进行，且必须有对应 L3 验收终态和证据记录。

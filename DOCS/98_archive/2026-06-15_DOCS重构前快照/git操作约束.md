# Git 操作约束

本文件记录 `.` 工作区的 Git 同步习惯与强制操作流程。每次涉及 Git 状态、提交、推送、拉取、远端、账号、分支、合并或同步时，必须先阅读本文件。

## 一、触发条件

- 只有当用户明确提出“同步”“提交”“推送”“拉取”“远端”“分支”“合并”“Git 状态”等 Git 相关需求时，才执行 Git 写操作。
- 用户没有明确要求 Git 操作时，不主动提交、推送、改远端、改分支或合并。
- 用户明确要求“提交”时，默认含义是：提交当前分支，并推送到当前分支对应的远端跟踪分支；不得把 `origin/main` 当作默认目标。
- “同步”默认含义是：检查当前分支状态，按当前分支生成提交，并推送到当前分支对应远端；阶段二开发中默认同步当前 Runtime 分支或 Service 场景分支。

## 二、仓库与账号

- 默认 GitHub 账号：`jack-z36`。
- 默认远端仓库：`https://github.com/jack-z36/ROS.git`。
- 默认远端名：`origin`。
- 稳定分支：`main`。
- 阶段二工作分支：Runtime MVP 使用一个长期分支；Service 按场景分别使用长期分支。
- GitHub 仓库必须保持 `private`，除非用户明确要求改为公开。

阶段二默认分支：

| 任务线 / 场景 | 默认分支 |
|---|---|
| Runtime MVP | `runtime-mvp` |
| Service 场景一 | `service-s1` |
| Service 场景二 | `service-s2` |
| Service 场景三 | `service-s3` |
| Service 场景四 | `service-s4` |
| Service 场景五 | `service-s5` |

## 三、阶段二分支策略

- `main` 只保存稳定完成结果，不作为 Win 或 Ubuntu 的日常工作台。
- Win 主机负责创建和推进阶段二 Runtime 分支或 Service 场景分支上的架构文档、L2、L3。
- Ubuntu 主机只在对应 Runtime 分支或 Service 场景分支上执行 L3、修改代码和测试、更新当前 L3 文件并归档。
- Ubuntu 主机禁止直接提交或推送 `main`。
- 阶段二 Runtime 分支或 Service 场景分支合并回 `main` 只由 Win 主机执行。
- Win 和 Ubuntu 如果在同一个 Runtime 分支或 Service 场景分支接力，开始工作前必须先 `git pull --ff-only`；遇到分叉或冲突时停止，不自动 merge/rebase。

## 四、固定操作流程

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
git commit -m "docs(runtime): plan <模块名>"
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
git commit -m "feat(runtime): complete <L3任务名>"
git push
```

Win 将 Runtime MVP 分支合并到 `main`：

```powershell
git switch main
git pull --ff-only
git fetch origin
git merge --no-ff runtime-mvp
git push
```

Service 场景一到五使用同样流程，把分支名分别替换为 `service-s1`、`service-s2`、`service-s3`、`service-s4`、`service-s5`。提交信息前缀按场景使用 `docs(service-s1): ...` / `feat(service-s1): ...`，其他场景依次替换为 `service-s2` 到 `service-s5`。

## 五、提交策略

- 默认尽量少提交：按一个稳定文档批次、一个 L3 完成结果或一次明确同步需求提交。
- 阶段二 Win 文档规划提交默认使用 `docs(runtime): plan <模块名>` 或 `docs(service-sN): plan <模块名>`。
- 阶段二 Ubuntu L3 执行提交默认使用 `feat(runtime): complete <L3任务名>` 或 `feat(service-sN): complete <L3任务名>`。
- 每次提交并推送到远端时，提交信息末尾必须注明本次提交的北京时间（格式：`北京时间 YYYY-MM-DD HH:MM`），除非用户明确指定提交信息不可改。
- 提交前需要给出摘要确认，至少包括：
  - 当前分支与远端跟踪分支。
  - 变更范围摘要。
  - 是否存在风险点。
  - 拟使用的提交信息。
- 低风险且用户已经明确要求同步时，可以在摘要后继续执行提交和推送。

## 六、严格检查

提交或推送前必须检查：

- `git status --short --branch`
- 当前远端是否为 `origin`，并指向 `https://github.com/jack-z36/ROS.git`
- 当前 Git 用户是否为 `jack-z36 <jack-z36@users.noreply.github.com>`
- 当前分支是否符合当前任务：
  - 阶段二 Win 文档规划：对应 Runtime 分支或 Service 场景分支。
  - 阶段二 Ubuntu L3 执行：当前 L3 所属 Runtime 分支或 Service 场景分支。
  - 阶段二合并：Win 主机在 `main` 上执行 `merge --no-ff`。
- 暂存区和工作区变更是否符合本次任务。
- 是否存在新增嵌套 `.git` 仓库或子模块指针。
- 是否存在超过 GitHub 普通限制的大文件风险。
- `.gitignore` 是否覆盖本地生成物、缓存、数据文件和私有配置。

## 七、忽略规则

敏感文件、生成文件和本地环境文件主要通过 `.gitignore` 控制。

默认不提交以下类型内容：

- ROS 构建产物：`build/`、`install/`、`log/`
- 本地 Python 或 conda 环境：`.conda-envs/`、`.conda-home/`、`.miniconda3/`
- 下载缓存和生成数据：`.downloads/`、`mcap_cleaned/`、`*.mcap`
- 依赖缓存：`src/data_collection/VTLA_octopus-master/.deps/`
- 本地 IDE 或私有配置：`src/.obsidian/`、`src/data_collection/gopro_camera_launch/.idea/`、`.claude/settings.local.json`

如果同步前发现应该忽略但未被忽略的文件，默认先更新 `.gitignore`，从暂存区移除对应文件，再继续同步。

## 八、远端变化处理

- 所有拉取默认使用 `git pull --ff-only`。
- 推送前如果发现远端领先、本地与远端分叉、需要合并或可能冲突，不自动 `merge`、`rebase` 或强推。
- 遇到上述情况时，先停止 Git 写操作，说明当前分支关系、风险和建议命令，等待用户明确确认。
- 禁止使用 `git push --force` 或会改写远端历史的操作，除非用户明确要求并确认风险。

## 九、完成后验证

同步完成后必须确认：

- `git status --short --branch` 显示当前分支与对应远端跟踪分支对齐。
- 最近一次提交符合本次同步目标。
- GitHub 仓库仍为 `PRIVATE`。
- 工作区没有意外未提交变更；如有，说明原因和路径。

阶段二合并到 `main` 完成后，还必须确认：

- `main` 已包含目标 Runtime 分支或 Service 场景分支的最新提交。
- `main` 已推送到 `origin/main`。
- 后续 Win/Ubuntu 继续工作时重新回到对应 Runtime 分支或 Service 场景分支，不在 `main` 上继续开发。


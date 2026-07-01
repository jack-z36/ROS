# Git 操作约束

本文件记录 `.` 工作区的 Git 分支、提交、同步、合并、删除与归档规则。每次涉及 Git 状态、提交、推送、拉取、远端、账号、分支、合并或同步时，必须先阅读本文件。

## 一、触发条件

- 只有当用户明确提出“同步”“提交”“推送”“拉取”“远端”“分支”“合并”“Git 状态”“删除分支”或类似 Git 相关需求时，才执行 Git 写操作。
- 用户没有明确要求 Git 操作时，不主动提交、推送、改远端、改分支、合并或删除分支。
- 用户明确要求“提交”时，默认含义是：提交当前分支，并推送到当前分支对应的远端跟踪分支；不得把 `origin/main` 当作默认目标。
- “同步”默认含义是：检查当前分支状态，按当前分支生成提交，并推送到当前分支对应远端。

## 二、仓库与账号

- 默认 GitHub 账号：`jack-z36`。
- 默认远端仓库：`https://github.com/jack-z36/ROS.git`。
- 默认远端名：`origin`。
- GitHub 仓库必须保持 `private`，除非用户明确要求改为公开。

Git 用户必须是：

```bash
jack-z36 <jack-z36@users.noreply.github.com>
```

## 三、分支层级

本仓库采用“一级稳定主干 + 二级长期集成分支 + 三级短功能分支”的模型，吸收 GitHub Flow / Trunk-based 的短生命周期功能分支做法，同时保留本项目需要的阶段级长期集成线。

### 一级稳定主干

| 分支 | 用途 |
|---|---|
| `main` | 稳定主干，只接收已经验收的二级分支里程碑结果；不作为日常开发分支。 |

### 二级长期集成分支

| 分支 | 用途 |
|---|---|
| `data_collection` | 阶段一 / 数据采集长期集成分支。 |
| `data_clean` | 阶段二 / 数据清洗长期集成分支。 |
| `model_deploy` | 阶段四 / 模型部署长期集成分支。 |
| `docs_maintaining` | 文档体系长期维护分支，只维护 `DOCS/` 及必要索引文件，例如 `AGENTS.md`、`CLAUDE.md`。 |

二级长期分支不得删除。二级分支达到阶段稳定里程碑后，通过明确的合并流程进入 `main`。

### 三级短功能分支

三级分支必须从目标二级长期分支创建，功能完成并合入对应二级分支后删除。

命名格式：

```text
feat/<area>/<topic>
fix/<area>/<topic>
docs/<area>/<topic>
chore/<area>/<topic>
spike/<area>/<topic>
```

示例：

- `feat/data_clean/lerobot-timestamp-rebase`
- `fix/data_collection/gopro-device-path`
- `docs/maintaining/git-policy`
- `feat/model_deploy/gripper-runtime`

命名约束：

- 使用小写 ASCII、数字、`-`、`_` 和 `/`。
- 禁止中文分支名、空格、全角符号和临时编号式命名。
- `spike/` 只用于实验；若实验要落地，必须整理成 `feat/` 或 `fix/` 分支再合入。

## 四、固定工作流

### 开始数据采集功能

```bash
git fetch origin
git switch data_collection || git switch -c data_collection origin/data_collection
git pull --ff-only
git switch -c feat/data_collection/<topic>
```

### 开始数据清洗功能

```bash
git fetch origin
git switch data_clean || git switch -c data_clean origin/data_clean
git pull --ff-only
git switch -c feat/data_clean/<topic>
```

### 开始模型部署功能

```bash
git fetch origin
git switch model_deploy || git switch -c model_deploy origin/model_deploy
git pull --ff-only
git switch -c feat/model_deploy/<topic>
```

### 开始文档体系维护

```bash
git fetch origin
git switch docs_maintaining || git switch -c docs_maintaining origin/docs_maintaining
git pull --ff-only
git switch -c docs/maintaining/<topic>
```

### 三级分支合入二级分支

优先通过 GitHub PR、review 和检查合入。若用户明确要求由本地维护者合并，流程如下：

```bash
git switch <level2-branch>
git pull --ff-only
git merge --no-ff <level3-branch>
git push
git branch -d <level3-branch>
git push origin --delete <level3-branch>
```

### 文档分支同步到其他二级分支

`docs_maintaining` 每次维护完成后，由维护者本地 merge 到 `data_collection`、`data_clean`、`model_deploy`，不删除 `docs_maintaining`：

```bash
git switch docs_maintaining
git pull --ff-only

git switch data_collection
git pull --ff-only
git merge --no-ff docs_maintaining
git push

git switch data_clean
git pull --ff-only
git merge --no-ff docs_maintaining
git push

git switch model_deploy
git pull --ff-only
git merge --no-ff docs_maintaining
git push
```

文档维护达到稳定批次后，再把 `docs_maintaining` 合入 `main`。

### 二级分支合入 main

二级分支只在阶段稳定里程碑完成后合入 `main`：

```bash
git switch main
git pull --ff-only
git fetch origin
git merge --no-ff <level2-branch>
git push
```

## 五、提交策略

- 默认尽量少提交：按一个稳定文档批次、一个功能完成结果、一个 L3 完成结果或一次明确同步需求提交。
- 提交信息使用简洁前缀：
  - `feat(data_clean): ...`
  - `fix(data_collection): ...`
  - `docs(maintaining): ...`
  - `feat(model_deploy): ...`
  - `chore(repo): ...`
- 每次提交并推送到远端时，提交信息末尾必须注明本次提交的北京时间（格式：`北京时间 YYYY-MM-DD HH:MM`），除非用户明确指定提交信息不可改。
- 提交前需要给出摘要确认，至少包括：
  - 当前分支与远端跟踪分支。
  - 变更范围摘要。
  - 是否存在风险点。
  - 拟使用的提交信息。
- 低风险且用户已经明确要求同步或执行既定整理方案时，可以在摘要后继续执行提交和推送。

## 六、严格检查

提交、推送、合并或删除分支前必须检查：

- `git status --short --branch`
- 当前远端是否为 `origin`，并指向 `https://github.com/jack-z36/ROS.git`
- 当前 Git 用户是否为 `jack-z36 <jack-z36@users.noreply.github.com>`
- 当前分支是否符合当前任务：
  - 阶段一数据采集：`data_collection` 或其三级分支。
  - 阶段二数据清洗：`data_clean` 或其三级分支。
  - 阶段四模型部署：`model_deploy` 或其三级分支。
  - 文档体系维护：`docs_maintaining` 或其三级分支。
  - 稳定里程碑合并：在 `main` 上合入二级分支。
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
- 运行产物和 Agent 临时状态：`.omo/`、`.ralph/`

如果同步前发现应该忽略但未被忽略的文件，默认先更新 `.gitignore`，从暂存区移除对应文件，再继续同步。

## 八、远端变化处理

- 所有拉取默认使用 `git pull --ff-only`。
- 推送前如果发现远端领先、本地与远端分叉、需要合并或可能冲突，不自动 `merge`、`rebase` 或强推。
- 遇到上述情况时，先停止 Git 写操作，说明当前分支关系、风险和建议命令，等待用户明确确认。
- 禁止使用 `git push --force` 或会改写远端历史的操作。

## 九、分支删除与归档

- 禁止删除 `main`、`data_collection`、`data_clean`、`model_deploy`、`docs_maintaining`。
- 三级分支合入对应二级分支并确认远端同步后，应删除本地和远端三级分支。
- 删除未合入或历史分支前，必须先创建可恢复归档：

```bash
git tag -a archive/YYYYMMDD/<branch-slug> <branch> -m "Archive <branch> before cleanup YYYY-MM-DD"
git push origin archive/YYYYMMDD/<branch-slug>
```

- 对 stash 也按需创建 archive tag 或 bundle，避免本地清理后丢失。
- 删除远端分支前必须确认远端没有仍在使用的 PR 或协作者依赖。

## 十、完成后验证

同步、合并或删除完成后必须确认：

- `git status --short --branch` 显示当前分支与对应远端跟踪分支对齐。
- 最近一次提交符合本次同步目标。
- GitHub 仓库仍为 `PRIVATE`。
- 工作区没有意外未提交变更；如有，说明原因和路径。
- 远端长期分支至少包含：`main`、`data_collection`、`data_clean`、`model_deploy`、`docs_maintaining`。


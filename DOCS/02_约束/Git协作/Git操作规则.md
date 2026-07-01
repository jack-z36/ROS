# Git 操作规则

## 适用范围

- 阶段：全局
- 任务模式：Git 状态、提交、推送、拉取、远端、分支、合并、删除或同步
- 适用对象：仓库根目录 `.` 工作区
- 不适用对象：阶段专属提交范围细则

本文件承载全局 Git 底线规则、三层分支模型和阶段规则路由。阶段二、阶段四等具体提交范围和验收条件必须放在各自阶段专属文件中。

## 分支层级

本仓库采用“一级稳定主干 + 二级长期集成分支 + 三级短功能分支”的模型。

| 层级 | 分支 | 用途 |
|---|---|---|
| 一级 | `main` | 稳定主干，只接收已经验收的二级分支里程碑结果；不作为日常开发分支。 |
| 二级 | `data_collection` | 阶段一 / 数据采集长期集成分支。 |
| 二级 | `data_clean` | 阶段二 / 数据清洗长期集成分支。 |
| 二级 | `model_deploy` | 阶段四 / 模型部署长期集成分支。 |
| 二级 | `docs_maintaining` | 文档体系长期维护分支，只维护 `DOCS/` 及必要索引文件，例如 `AGENTS.md`、`CLAUDE.md`。 |

二级长期分支不得删除。二级分支达到阶段稳定里程碑后，通过明确合并流程进入 `main`。

## 三级分支命名

三级分支必须从目标二级长期分支创建，功能完成并合入对应二级分支后删除。

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

## 通用强制规则

1. 只有用户明确提出 Git 写操作，或当前任务文件/阶段规则明确授权自动同步时，才允许提交、推送、创建分支、切换分支、合并或删除分支。
2. 所有拉取默认使用 `git pull --ff-only`。
3. 遇到远端领先、本地分叉、冲突、非预期工作区变更或需要改写历史时，立即停止，不自动 rebase 或 force push。
4. 禁止使用 `git push --force` 或其他改写远端历史的操作。
5. 提交前必须检查：
   - `git status --short --branch`
   - 当前远端是否为 `origin`
   - 当前远端 URL 是否为 `https://github.com/jack-z36/ROS.git`
   - 当前 Git 用户是否为 `jack-z36 <jack-z36@users.noreply.github.com>`
   - 工作区和暂存区是否只包含本次任务允许的变更
   - 是否存在新增嵌套 `.git` 仓库、超大文件、缓存、私有配置或应忽略产物
6. 提交信息末尾必须注明北京时间，格式为 `北京时间 YYYY-MM-DD HH:MM`，除非用户明确指定提交信息不可改。

## 固定工作流

从二级分支创建三级分支：

```bash
git fetch origin
git switch <level2-branch> || git switch -c <level2-branch> origin/<level2-branch>
git pull --ff-only
git switch -c <type>/<area>/<topic>
```

三级分支合入二级分支：

```bash
git switch <level2-branch>
git pull --ff-only
git merge --no-ff <type>/<area>/<topic>
git push
git branch -d <type>/<area>/<topic>
git push origin --delete <type>/<area>/<topic>
```

`docs_maintaining` 同步到其他二级分支：

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

二级分支达到阶段稳定里程碑后合入 `main`：

```bash
git switch main
git pull --ff-only
git fetch origin
git merge --no-ff <level2-branch>
git push
```

## 阶段规则入口

| 阶段 | 必读规则 |
|---|---|
| 阶段二：数据清洗 | `DOCS/02_约束/Git协作/阶段二：数据清洗 Git操作规则.md` |
| 阶段四：模型部署 | `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md` |

执行阶段任务时，必须先读取本文件，再读取对应阶段专属 Git 规则。阶段专属文件只定义本阶段的提交范围、同步和验收策略，不得重复或降低本文件的全局底线。

## 分支删除与归档

- 禁止删除 `main`、`data_collection`、`data_clean`、`model_deploy`、`docs_maintaining`。
- 三级分支合入对应二级分支并确认远端同步后，应删除本地和远端三级分支。
- 删除未合入或历史分支前，必须先创建可恢复归档：

```bash
git tag -a archive/YYYYMMDD/<branch-slug> <branch> -m "Archive <branch> before cleanup YYYY-MM-DD"
git push origin archive/YYYYMMDD/<branch-slug>
```

- 对 stash 也按需创建 archive tag 或 bundle，避免本地清理后丢失。

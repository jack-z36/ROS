# 阶段四：模型部署 Git 操作规则

## 适用范围

- 阶段：阶段四：模型部署
- 任务模式：阶段四 L2 / L3 执行、L2 Gate 后同步、模型部署代码和工程文档协作
- 适用对象：`model_deploy` 集成分支、阶段四 L2 分支、`src/model_deploy/pi05/` 和阶段四工程文档
- 不适用对象：阶段二数据清洗分支、`main` 稳定分支合并流程

使用本文件前，必须先读取：

```text
DOCS/02_约束/Git协作/Git操作规则.md
```

## 分支模型

阶段四 `model_deploy` L3 执行采用 L2 分支制。

- 集成分支：`model_deploy`
- L2 分支命名：`model_deploy-l2-xx-*`
- L2 分支示例：
  - `model_deploy-l2-01-types`
  - `model_deploy-l2-02-config`
  - `model_deploy-l2-03-assembly`
  - `model_deploy-l2-04-publish`
  - `model_deploy-l2-05-hardware`

单个 L3 完成后不默认提交推送。同一 L2 的 required L3 全部通过 L2 Gate 后，才允许进行 L2 批量同步。

## L2 开工流程

从集成分支创建新 L2 分支：

```powershell
git fetch origin
git switch model_deploy
git pull --ff-only
git switch -c model_deploy-l2-xx-*
```

如果远端已经存在对应 L2 分支：

```powershell
git fetch origin
git switch model_deploy-l2-xx-* || git switch -c model_deploy-l2-xx-* origin/model_deploy-l2-xx-*
git pull --ff-only
```

## L2 自动同步流程

当且仅当所属 L2 Gate 通过后，AI 可以自动执行以下同步流程：

```powershell
git status --short --branch
git add -A
git status --short
git commit -m "feat(model_deploy): complete L2-xx <name> 北京时间 YYYY-MM-DD HH:MM"
git push -u origin model_deploy-l2-xx-*
git switch model_deploy
git pull --ff-only
git merge --no-ff model_deploy-l2-xx-* -m "merge(model_deploy): integrate L2-xx <name> 北京时间 YYYY-MM-DD HH:MM"
git push origin model_deploy
```

L2 分支推送后保留远端分支，不自动删除。

## 阻断条件

出现以下任一情况时，停止自动同步并向用户报告：

- L2 Gate 未通过，或 `05_acceptance/<l2>/验收结果.md` 未记录通过结论。
- 当前分支不是对应 L2 分支，或 L2 分支不是从 `model_deploy` 开出。
- `model_deploy` 远端领先、本地分叉或 `pull --ff-only` 失败。
- `git merge --no-ff` 产生冲突。
- 工作区包含本 L2 之外的非预期变更。
- 待提交内容包含超大文件、缓存、私有配置、环境目录或未归档解释的运行产物。
- 真机相关 L2 缺少风险确认、急停准备或人工验收记录。

## 阶段四提交范围

允许提交：

- `src/model_deploy/pi05/` 下本 L2 明确允许的源码、配置、脚本或测试。
- `DOCS/03_工程/阶段四：模型部署/` 下本 L2 的任务文件、验收结果和工程记录。
- `DOCS/02_约束/` 下本次明确要求维护的约束、模板或工作流文件。

禁止提交：

- ROS 构建产物：`build/`、`install/`、`log/`
- Python 缓存和测试缓存：`__pycache__/`、`*.pyc`、`.pytest_cache/`
- 本地环境、私有配置、下载缓存、模型权重和大型数据产物
- 未经说明的第三方源码改动，尤其是 `src/model_deploy/third_party/`

## L2 Gate 与 Git 同步关系

L2 Gate 是阶段四自动同步的前置条件。每个 L2 的 `05_acceptance/<l2>/验收结果.md` 必须记录：

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

未通过 Gate 的 L2 不得提交、推送或合入 `model_deploy`。

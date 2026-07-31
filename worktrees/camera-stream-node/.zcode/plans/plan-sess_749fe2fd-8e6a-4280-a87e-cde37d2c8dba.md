# 修订计划：阶段四 Git 规则 + 两个 docs skill 放开分支限制

## 你的四条要求
1. 删除 squash 合入方式，三级→二级**只保留 `merge --no-ff`**
2. 合入后先归档再删（worktree 移 `worktrees/archive/`，分支打 archive tag 后删）
3. 合并前自动用 subagent 跑两个 docs skill
4. **这两个 skill 可以在任何分支上运行**（放开分支限制，不是加 mode 开关）

---

## 文件 1：`skills/update-knowledge-from-commits/SKILL.md`（放开分支限制）

**核心问题**：当前把「sync 到长期分支 + 推送」写成强制默认，等于隐含限定在 `docs_maintaining` 跑。

### 1.1 frontmatter description（第 3 行）
去掉「then sync the docs update from docs_maintaining ... when Git preflight is clean」的强制语气，改为「可在任意分支运行；默认只创建本地 commit，跨分支 sync 由调用方显式要求时才执行」。

### 1.2 Default Behavior 末尾（第 34 行）
```
原：After successful knowledge updates, create a local commit, then sync that docs update across long-lived project branches according to Git操作规则.md.
改：After successful knowledge updates, create a local commit on the current branch. 本 skill 可在任意分支（含 feat/*/fix/* 等三级功能分支）运行。
    跨分支 sync 仅当调用方显式要求（如 prompt 指定 sync=true）时才执行；默认不 sync、不推送。
```

### 1.3 Preflight 第 5-6 项（第 42-49 行）
把「Before branch sync, also verify ...」的校验改为「仅当将执行 sync 时才校验」，并去掉「local branch tips are not behind upstreams」这条对单分支场景无意义的前置。

### 1.4 Branch Sync 节（118-154 行）开头加守卫
```
本节为可选流程，仅当调用方显式要求跨分支同步时执行。
若在三级功能分支上跑且未要求 sync，跳过本节，直接进入 Output（sync 结果记为 skipped）。
```

---

## 文件 2：`skills/update-routes-from-commits/SKILL.md`（放开分支限制）

`update-routes` 本来就「只本地 commit、不推送」，分支限制弱，主要是补明确授权。

### 2.1 Default Behavior 末尾（第 34 行）
```
原：After successful route updates, create a local commit. Do not push.
改：After successful route updates, create a local commit on the current branch. Do not push.
    本 skill 可在任意分支（含 feat/*/fix/* 等三级功能分支）运行；产出 commit 由调用方随后续 merge 带入目标分支。
```

---

## 文件 3：`DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 3.1 重写「Gate 后合入流程」节（132-147 行）为 5 步
- **第1步 文档预维护**：在当前三级功能分支依次用 subagent 跑 update-knowledge、update-routes（两者现可在任意分支跑，默认只产本地 docs commit、不 sync/不推送）。
- **第2步** `git push -u origin feat/model_deploy/<topic>`
- **第3步** `merge --no-ff` 进 model_deploy（message 带北京日期）——**明确写入唯一允许的合入方式，禁止 squash/rebase/amend 压扁合入**。
- **第4步** 归档（见 3.2）
- **第5步** 推送归档 tag

### 3.2 新增「合入后归档流程」节
```
(1) 归档 worktree：mkdir -p worktrees/archive/ && mv worktrees/<用途> worktrees/archive/<用途>-<YYYYMMDD>
(2) 归档分支：git tag -a archive/<YYYYMMDD>/<slug> <分支> -m "..." && git push origin archive/<...>
(3) 删分支：git branch -d <分支> && git push origin --delete <分支>
```
注明：worktrees/archive/ 已被 .gitignore 覆盖；归档 tag 永久保留；这是阶段四对全局归档规则的收紧。

### 3.3 「阻断条件」节补充
- 文档预维护 subagent 跑完后工作树有非 docs 的预期外变更 → 停。
- 归档 tag 创建/推送失败 → 停止删分支。

---

## 文件 4：`skills/stage4-git-integrator/SKILL.md`（联动）
- Workflow 2 / Gate Merge：把合入后的 `branch -d` + `push --delete` 改为先归档（tag + 移 worktree）再删。
- Preflight 增补：合入前应在功能分支先跑两个 docs skill subagent。

## 不改
- 全局 `Git操作规则.md`（阶段四收紧即可）。
- 改完不立即提交，先给你确认；这批变更最终作为一个 docs commit。

## 待定（实现时定）
归档 worktree 物理目录保留多久：默认永久（archive tag 是唯一恢复依据，物理目录可手动删）。
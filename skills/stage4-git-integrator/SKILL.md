---
name: stage4-git-integrator
description: Perform checked Stage 4 model_deploy Git submission and merge workflows in this ROS repository. Use when making L3 atomic commits, pushing Stage 4 feature branches, merging into model_deploy and downstream L2 branches, or cleaning up worktrees after integration. This skill must not bypass Gate, human signature, branch, or allowed-path checks.
---

# Stage4 Git Integrator

## Purpose

Use this skill for Stage 4 `model_deploy` Git operations after L3 acceptance or L2 human acceptance.

It covers three workflows:

1. **Clean Commit** — commit L3 changes on the current feature branch, archive completed tasks, remove stale files, and guarantee a clean `git status` afterward.
2. **Downstream Merge** — merge the current feature branch into `model_deploy`, then propagate the merge into every downstream L2 branch (l2-03 through l2-06), handling worktree conflicts and pushing all branches.
3. **L3 Atomic Commit** — a single-L3 commit after acceptance (legacy, now subsumed by Clean Commit).

Do not use this skill to implement code, generate L3 files, or judge L2 design quality.

## Required Context

Read these before any Git operation:

1. `AGENTS.md`
2. `DOCS/02_约束/上下文加载/07_Git同步加载规则.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
6. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/人类验收关卡规则.md`
7. Target L3 task, dispatch, acceptance card, L2 Gate report, or `05_acceptance/<l2>/验收结果.md` depending on the requested operation.

## Preflight

Always run:

```bash
python3 skills/stage4-git-integrator/scripts/check_stage4_git_ready.py --l2 <l2_id> --mode <clean-commit|merge>
```

Then inspect:

```bash
git status --short --branch
git branch --show-current
git remote -v
```

Stop if:

- current branch is not the expected Stage 4 feature branch;
- worktree contains unrelated changes;
- L2 Gate is missing or not passed when merging;
- human acceptance is missing, unsigned, or not passed when merging;
- real-robot risk notes are missing for hardware work;
- requested files exceed the allowed Stage 4 paths;
- merge or pull requires rebase, force push, amend, or conflict resolution.

## L2 Ordering and Downstream Branches

Stage 4 L2 dispatch follows a fixed pipeline order. Each L2 builds on the previous one:

| Index | L2 ID | Feature Branch |
|---|---|---|
| 0 | `model_deploy` | `model_deploy` (integration trunk) |
| 1 | `l2-01-external-contract` | `feat/model_deploy/l2-01-external-contract-design` |
| 2 | `l2-02-observation-snapshot` | `feat/model_deploy/l2-02-observation-snapshot` |
| 3 | `l2-03-act-inference` | `feat/model_deploy/l2-03-act-inference` |
| 4 | `l2-04-safety-guard` | `feat/model_deploy/l2-04-safety-guard` |
| 5 | `l2-05-action-publisher` | `feat/model_deploy/l2-05-action-publisher` |
| 6 | `l2-06-control-loop` | `feat/model_deploy/l2-06-control-loop` |

**Downstream branches** of a given L2 are all L2 branches with a higher index. For example, downstream of l2-02 are l2-03, l2-04, l2-05, l2-06.

Each downstream branch lives in its own git worktree at:

```text
worktrees/<l2-id>/
```

Example: `worktrees/l2-03-act-inference/` is the worktree for `feat/model_deploy/l2-03-act-inference`.

The main worktree at `/home/hit/ROS` holds `model_deploy`.

## Workflow 1: Clean Commit

Clean Commit handles the full commit lifecycle for one or more L3s: archive, stage, commit, push, and post-commit cleanup.

### Step 1: Archive Completed Tasks

If the L3 conclusion is `PASS_LOCAL`, the main Agent must move the matching active L3 task file into `03_tasks/completed/<l2_id>/` **before** committing.

```bash
# Create completed/ directory if missing
mkdir -p "DOCS/03_工程/阶段四：模型部署/03_tasks/completed/<l2_id>/"

# Move each PASS_LOCAL task
mv "DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/<l2_id>/<deploy_id>_*.md" \
   "DOCS/03_工程/阶段四：模型部署/03_tasks/completed/<l2_id>/"
```

After archiving, **remove any remaining stale files** that conflicts between worktrees could leave behind. During a downstream-sync merge, `completed/` files may be restored from the index even though `active/` has a newer copy on disk. Always:

- `git restore` any `completed/` files that show as `D` (deleted) — these were tracked and need to stay.
- `rm` any `active/` files — they were moved to `completed/` and committed; if a merge restores them, they are stale.

```bash
# Restore deleted tracked files in completed/
git restore "DOCS/03_工程/阶段四：模型部署/03_tasks/completed/<l2_id>/"

# Remove stale active/ files (already archived in a prior commit)
rm -f "DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/<l2_id>/"*
```

### Step 2: Stage Only Allowed Files

Stage only the current L2 scope. Never use `git add -A`.

Allowed paths:

- `src/model_deploy/act/` — only files modified or created by the current L2/L3 tasks
- `DOCS/03_工程/阶段四：模型部署/02_implement/<l2_id>*/` — L2 design documents
- `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/<l2_id>/` — active L3 task files
- `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/<l2_id>/` — archived completed L3 files
- `DOCS/03_工程/阶段四：模型部署/03_tasks/task/dispatch/<l2_id>.yaml` — dispatch index
- `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/<l2_id>/` — acceptance cards
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2_id>/` — acceptance evidence/logs
- `DOCS/02_约束/` — only files explicitly required by the task
- `skills/` — skill files explicitly modified
- `.gitignore` — if modified for legitimate reasons

Verify after staging:

```bash
git status --short
```

Only files matching the allowed paths should appear staged (`A`/`M`/`D`). Unstaged modifications (` M`) and untracked files (`??`) that belong to other L2s must remain out of the commit.

### Step 3: Commit

Commit message format:

```text
feat(model_deploy): <summary> 北京时间 YYYY-MM-DD HH:MM
```

For cleanup/sync commits:

```text
chore(model_deploy): <summary> 北京时间 YYYY-MM-DD HH:MM
```

Commit message must include the Beijing timestamp. Do not amend, rebase, or force-push.

### Step 4: Push and Verify

```bash
git push

# Verify clean
git status --short --branch
```

After the push, `git status` must be empty (no modified, staged, or untracked files that belong to this L2). Untracked files like `.zcode/plans/` are permitted if `.gitignore` covers them.

## Workflow 2: Downstream Merge

After completing an L2 (all L3s passed, Gate passed, human acceptance signed), propagate the changes to `model_deploy` and all downstream L2 branches.

### Step 1: Ensure Current Branch is Pushed and Clean

```bash
git push
git status --short --branch  # must be clean
```

### Step 2: Merge into model_deploy

The main worktree at `/home/hit/ROS` holds `model_deploy`. Use `git -C` to operate on it:

```bash
git -C /home/hit/ROS pull --ff-only
git -C /home/hit/ROS merge --no-ff <current-feature-branch> \
  -m "merge(model_deploy): integrate <l2_id> 北京时间 YYYY-MM-DD HH:MM"
git -C /home/hit/ROS push origin model_deploy
```

If the main worktree has unrelated changes, stop and report — do not force.

### Step 3: Identify Downstream Branches

Use the script to list downstream branches:

```bash
python3 skills/stage4-git-integrator/scripts/list_downstream.py --l2 <l2_id>
```

For each downstream branch, locate its worktree at `worktrees/<l2-id>/`.

### Step 4: Merge into Each Downstream Branch

For each downstream worktree:

```bash
# Pull first (may need --set-upstream on first push)
git -C worktrees/<downstream-id> merge --no-ff model_deploy \
  -m "merge(model_deploy): sync <source-l2> into <downstream-id> 北京时间 YYYY-MM-DD HH:MM"
```

**Worktree conflict handling**: A downstream worktree may have untracked files that the merge would overwrite. Common causes:

- `html要求.md` — remove
- `.zcode/plans/` — covered by `.gitignore` (if not, add it)
- Stale `active/` task files — remove

After each merge, check `git status` in the downstream worktree. If the merge introduced modified tracked files or restored stale files, handle them:

- Modified tracked files that belong to the downstream L2: commit them locally as a `chore` commit.
- Deleted files in `completed/`: `git restore` them.
- Stale files in `active/`: `rm` them.

### Step 5: Commit Any Merge Artifacts in Downstream Branches

If a downstream branch has merge-related modifications:

```bash
git -C worktrees/<downstream-id> add <files>
git -C worktrees/<downstream-id> commit -m "chore(model_deploy): sync <source-l2> merge artifacts into <downstream-id> 北京时间 ..."
```

### Step 6: Push All Branches

```bash
git push                                                           # current branch
for downstream in <list>; do
  git -C worktrees/$downstream push origin feat/model_deploy/$downstream
done
```

### Step 7: Verify All Branches Clean

```bash
for wt in /home/hit/ROS worktrees/*; do
  git -C "$wt" status --short --branch
done
```

Every worktree must show empty status (no modified/staged files). Untracked `.zcode/` files are acceptable if covered by `.gitignore`.

### Common Downstream Merge Errors and Resolutions

| Error | Cause | Resolution |
|---|---|---|
| `fatal: 'model_deploy' is already used by worktree` | Current worktree has `model_deploy` checked out; cannot switch in the same worktree | Use `git -C /home/hit/ROS` to operate in the main worktree |
| `error: untracked working tree files would be overwritten` | Downstream worktree has untracked file that merge would create | `rm` the untracked file in the downstream worktree |
| `fatal: no upstream branch` | Downstream branch was never pushed with `--set-upstream` | Use `git push --set-upstream origin <branch>` |
| Modified files after merge | Merge resolved conflicts or auto-merged changes | Commit them as a `chore` commit in the downstream worktree |
| TLS handshake failure on push | Transient network issue | Retry push once; if persistent, record in git_sync_status.md |

### Full Downstream Merge Example (l2-02 → all)

```bash
# 1. Ensure clean and pushed
git push
git status --short --branch

# 2. Merge into model_deploy
git -C /home/hit/ROS pull --ff-only
git -C /home/hit/ROS merge --no-ff feat/model_deploy/l2-02-observation-snapshot \
  -m "merge(model_deploy): integrate l2-02-observation-snapshot 北京时间 2026-07-09 08:49"
git -C /home/hit/ROS push origin model_deploy

# 3. Merge into downstream (l2-03, l2-04, l2-05, l2-06)
for l2 in l2-03-act-inference l2-04-safety-guard l2-05-action-publisher l2-06-control-loop; do
  # Handle untracked conflicts
  rm -f "worktrees/$l2/html要求.md" 2>/dev/null
  git -C "worktrees/$l2" merge --no-ff model_deploy \
    -m "merge(model_deploy): sync l2-02 into $l2 北京时间 2026-07-09 08:49"
done

# 4. Push all
for l2 in l2-03-act-inference l2-04-safety-guard l2-05-action-publisher l2-06-control-loop; do
  git -C "worktrees/$l2" push origin "feat/model_deploy/$l2"
done

# 5. Verify all clean
for wt in /home/hit/ROS worktrees/l2-*; do
  echo "=== $(basename $wt) ===" && git -C "$wt" status --short
done
```

## Workflow 3: L3 Atomic Commit (Legacy)

Allowed after one L3 reaches a committable state according to the Stage 4 Git rules.

If the conclusion is `PASS_LOCAL`, the main Agent must archive the matching active L3 task into `03_tasks/completed/<l2_id>/` before the commit.

Commit only the current L3 scope:

- allowed source/test paths under `src/model_deploy/act/`;
- matching L2 design docs;
- matching task/card/dispatch/acceptance evidence;
- required status or git sync record.

Never use `git add -A`. Prefer Workflow 1 (Clean Commit) which properly handles archive moves, stale-file cleanup, and post-commit verification.

## Gate Merge

Allowed only after:

- all required L3 tasks are complete or explicitly blocked in an accepted way;
- L2 Gate passed;
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2_id>/验收结果.md` contains a passed human signature;
- Stage 4 Git rules allow automatic merge.

Use the exact merge flow from `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`.

## Scripts

- `scripts/check_stage4_git_ready.py` — preflight check: branch, worktree state, human acceptance.
- `scripts/list_downstream.py` — list downstream L2 branches and their worktree paths.

## Handoff

End with:

- operation mode;
- current branch and target branches;
- files staged/committed/merged;
- command results;
- any blocked condition;
- whether push or merge remains pending.
- final `git status` output for every affected branch.

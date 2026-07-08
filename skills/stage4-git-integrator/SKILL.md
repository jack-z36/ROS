---
name: stage4-git-integrator
description: Perform checked Stage 4 model_deploy Git submission and merge workflows in this ROS repository. Use when making an L3 atomic commit, pushing a Stage 4 feature branch, checking L2 Gate and human acceptance before merge, merging a feature branch into `model_deploy`, or deleting the integrated feature branch. This skill must not bypass Gate, human signature, branch, or allowed-path checks.
---

# Stage4 Git Integrator

## Purpose

Use this skill for Stage 4 `model_deploy` Git operations after L3 acceptance or L2 human acceptance.

It covers:

- L3 atomic commit on the current Stage 4 feature branch;
- feature branch push;
- Gate-after-human-acceptance merge into `model_deploy`;
- local and remote feature branch deletion after successful merge.

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
python3 skills/stage4-git-integrator/scripts/check_stage4_git_ready.py --l2 <l2_id> --mode <l3-commit|merge>
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

## L3 Atomic Commit

Allowed after one L3 reaches a committable state according to the Stage 4 Git rules.

If the conclusion is `PASS_LOCAL`, the main Agent must archive the matching active L3 task into `03_tasks/completed/<l2_id>/` before the commit.

Commit only the current L3 scope:

- allowed source/test paths under `src/model_deploy/act/`;
- matching L2 design docs;
- matching task/card/dispatch/acceptance evidence;
- required status or git sync record.

Never use `git add -A`.

## Gate Merge

Allowed only after:

- all required L3 tasks are complete or explicitly blocked in an accepted way;
- L2 Gate passed;
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2_id>/验收结果.md` contains a passed human signature;
- Stage 4 Git rules allow automatic merge.

Use the exact merge flow from `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`.

## Handoff

End with:

- operation mode;
- current branch and target branch;
- files staged/committed/merged;
- command results;
- any blocked condition;
- whether push or merge remains pending.

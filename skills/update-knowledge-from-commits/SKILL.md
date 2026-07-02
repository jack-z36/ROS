---
name: update-knowledge-from-commits
description: Analyze Git commits in this ROS project and update stable DOCS/01_知识 knowledge documents. Use when the user asks to update the knowledge base from commits, refresh knowledge docs after development, derive knowledge changes from the latest commit, or maintain stage knowledge from Git history. By default, analyze the latest non-maintenance commit, update knowledge docs when stable semantics changed, create a local docs(knowledge) commit, then sync the docs update from docs_maintaining to the repository's long-lived branches when Git preflight is clean.
---

# Update Knowledge From Commits

## Purpose

Use this skill to update stable project knowledge from Git history.

Knowledge documents in `DOCS/01_知识/` contain durable understanding: what the project is, what the data means, why the design works, and what downstream phases need to know. They must not become execution logs, task status, debug notes, or commit summaries.

## Default Behavior

If the user does not provide a commit range, analyze the latest non-maintenance commit:

```text
<target_commit>^..<target_commit>
```

Skip maintenance commits while searching backward from `HEAD`. Treat a commit as maintenance when its subject starts with either:

- `docs(knowledge): update from commit`
- `docs(routes): update from commit`

Also skip commits whose subject contains:

- `auto knowledge update`
- `auto route update`

If the user provides an explicit commit range, use that range instead.

After successful knowledge updates, create a local commit, then sync that docs update across long-lived project branches according to `DOCS/02_约束/Git协作/Git操作规则.md`.

## Preflight

1. Read `AGENTS.md`.
2. Read the relevant loading rules from `DOCS/02_约束/上下文加载/`.
3. Read `DOCS/02_约束/文档体系/文档分类与目录规范.md`.
4. Check `git status --short --branch`.
5. Stop if the working tree has unrelated uncommitted changes.
   - Allowed pre-existing changes are only files under `skills/update-knowledge-from-commits/` when the user is editing this skill itself.
   - For normal skill use, require a clean working tree before editing knowledge docs.
6. Before branch sync, also verify:
   - remote is `origin`
   - remote URL is `https://github.com/jack-z36/ROS.git`
   - Git user is `jack-z36 <jack-z36@users.noreply.github.com>`
   - local branch tips are not behind their configured upstreams

## Commit Inspection

Inspect the selected range with:

```text
git log --oneline --decorate <range>
git diff --stat <range>
git diff --name-status <range>
git diff <range> -- <targeted paths>
```

Load relevant stage knowledge under `DOCS/01_知识/` before deciding where to write.

## Stable Knowledge Gate

Only update knowledge documents when the commit changes at least one stable semantic fact:

- stage objective or phase boundary
- main data flow or artifact contract
- data concept, schema meaning, coordinate frame, time domain, or unit boundary
- Runtime, Service, Web, quality, or production-readiness boundary at a conceptual level
- relationship between stages, such as Stage 2 output consumed by Stage 3 training
- historical boundary that prevents future agents from reviving a wrong route

Do not write these into `DOCS/01_知识/`:

- execution records
- current progress only
- L2/L3 task status
- dispatch metadata
- temporary debug notes
- isolated tests
- local refactors that do not change project semantics
- implementation details already covered by engineering docs or source references

## Allowed Edits

This skill may edit only:

- `DOCS/01_知识/**`
- `DOCS/语义迁移审计表.md`, only when the update includes semantic migration or document restructuring

If any other file would need changes, stop and report the required follow-up instead of editing it.

## Execution Flow

1. Print a short execution summary:
   - selected commit or range
   - affected stage(s)
   - target knowledge files
   - whether a local commit and branch sync will be created
2. Update the relevant knowledge docs.
3. Verify:
   - referenced `DOCS/...` and `src/...` paths exist
   - no execution records, debug logs, or task status were written into `DOCS/01_知识/`
   - modified paths are within the allowed edit set
4. If no knowledge update is needed, do not edit and do not commit.
5. If files changed, commit locally:

```text
docs(knowledge): update from commit <short_sha>

北京时间 YYYY-MM-DD HH:MM
```

Use the selected target commit short SHA. For an explicit multi-commit range, use the range end short SHA.

## Branch Sync

After creating the local `docs(knowledge)` commit, sync the resulting docs update from `docs_maintaining` to long-lived project branches.

Target branches:

- `data_collection`
- `data_clean`
- `model_deploy`
- `main`

Do not automatically sync to:

- `backup/*`
- `feat/*`
- `fix/*`
- `docs/*`
- `chore/*`
- `spike/*`
- branches without an `origin/*` upstream

Sync procedure:

1. Ensure the knowledge commit exists on `docs_maintaining`.
2. For each target branch, run `git fetch origin`, switch to the branch, and run `git pull --ff-only`.
3. Merge `docs_maintaining` with `git merge --no-ff docs_maintaining`.
4. If there is no effective change because the branch already contains the docs update, do not create an empty merge commit.
5. Push each successfully updated target branch to `origin`.
6. Return to `docs_maintaining` and push it to `origin`.

Stop and report without resolving automatically if any branch has:

- remote divergence or non-fast-forward pull failure
- merge conflict
- dirty worktree unrelated to the sync
- missing target branch or missing upstream
- required push rejection

## Output

After completion, report:

- analyzed commit range
- updated knowledge files
- excluded changes and why
- local commit SHA, or `no commit created`
- branch sync results for `docs_maintaining`, `data_collection`, `data_clean`, `model_deploy`, and `main`
- any remaining worktree changes

## Project Conventions

- Read and write Markdown as UTF-8.
- Keep `DOCS/01_知识/` stable and concise.
- Use relative paths in proposed references.
- Do not read `DOCS/98_archive/` or `DOCS/99_learning/` unless the user explicitly asks for historical or learning material.
- When updating knowledge from an old route, mark the old route as historical instead of silently deleting context that prevents regression.

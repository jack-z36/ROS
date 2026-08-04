---
name: update-routes-from-commits
description: Analyze Git commits in this ROS project and update route files, loading rules, and INDEX.md files according to DOCS/02_约束/文档体系 constraints. Use when the user asks to refresh routing, maintain AGENTS.md, update context loading rules, repair INDEX links after commits, or synchronize route files from the latest commit. By default, analyze the latest non-maintenance commit, update route files when routing changed, and create a local docs(routes) commit; do not push.
---

# Update Routes From Commits

## Purpose

Use this skill to keep routing files synchronized with repository structure changes.

Routing files tell agents what to read next. They must not become project encyclopedias, progress logs, execution records, or implementation manuals.

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

After successful route updates, create a local commit on the current branch. Do not push.

本 skill 可在任意分支上运行，包括 `feat/*`、`fix/*` 等三级功能分支——不限定于 `docs_maintaining`。产出 commit 留在当前分支，由调用方随后续 `merge --no-ff` 带入目标分支。

## Required Rules

Before editing, read:

- `AGENTS.md`
- `DOCS/02_约束/文档体系/INDEX.md`
- `DOCS/02_约束/文档体系/路由文档纯度规范.md`
- `DOCS/02_约束/文档体系/AGENTS维护规则.md`
- `DOCS/02_约束/文档体系/文档分类与目录规范.md`
- `DOCS/02_约束/上下文加载/01_文档体系维护加载规则.md`

If semantic migration is involved, also read `DOCS/02_约束/文档体系/语义微元迁移规范.md` and maintain `DOCS/语义迁移审计表.md`.

## Preflight

1. Check `git status --short --branch`.
2. Stop if the working tree has unrelated uncommitted changes.
   - Allowed pre-existing changes are only files under `skills/update-routes-from-commits/` when the user is editing this skill itself.
   - For normal skill use, require a clean working tree before editing routes.
3. Inspect the selected range:

```text
git log --oneline --decorate <range>
git diff --stat <range>
git diff --name-status <range>
git diff <range> -- <targeted paths>
```

## Route File Scope

This skill may edit only:

- `AGENTS.md`
- `DOCS/02_约束/上下文加载/**`
- `DOCS/**/INDEX.md`
- `DOCS/语义迁移审计表.md`, only when route maintenance includes semantic migration

If any other file would need changes, stop and report the required follow-up instead of editing it.

## Route Roles

Use role-specific purity gates before editing.

### Global Route: `AGENTS.md`

Allowed content:

- task type name
- one-sentence trigger
- loading-rule path
- default forbidden read zones

Forbidden content:

- project knowledge
- current progress
- rules body
- implementation details
- commands or debug conclusions

### Context Loading Rules

Allowed content:

- scope
- trigger signals
- context loading order
- required entries
- forbidden default reads
- blocking conditions
- output requirements

Forbidden content:

- large knowledge summaries
- implementation walkthroughs
- execution logs
- task status

### `INDEX.md`

Allowed content:

- this directory's route purpose
- entries in the same topic or directory
- read conditions
- forbidden/default-not-read notes
- short boundary notes needed to choose the next file

Forbidden content:

- engineering progress
- debug records
- full rule bodies duplicated from target files
- business knowledge that belongs in `DOCS/01_知识/`
- implementation details that belong in `DOCS/03_工程/` or source docs

## Route Impact Gate

Update routes only when the commit changes at least one routing fact:

- new, moved, renamed, or deleted loading rule
- new, moved, renamed, or deleted constraint/workflow/rule file
- new task type or loading entry
- directory structure change that breaks an existing `INDEX.md`
- old path replaced by a new canonical path
- rule entry exists but its index no longer points to it

Do not update routes for ordinary source changes, tests, execution records, or knowledge-only content unless an existing route entry becomes stale.

## Execution Flow

1. Print a short execution summary:
   - selected commit or range
   - detected route impact
   - route files to edit
   - whether a local commit will be created
2. Update route files within the allowed edit set.
3. Verify:
   - all referenced `DOCS/...` paths exist
   - `AGENTS.md` obeys `AGENTS维护规则.md`
   - route files do not contain project knowledge, progress, debug records, or implementation details
   - modified paths are within the allowed edit set
4. If no route update is needed, do not edit and do not commit.
5. If files changed, commit locally:

```text
docs(routes): update from commit <short_sha>

北京时间 YYYY-MM-DD HH:MM
```

Use the selected target commit short SHA. For an explicit multi-commit range, use the range end short SHA.

## Output

After completion, report:

- analyzed commit range
- updated route files
- route impacts handled
- excluded changes and why
- local commit SHA, or `no commit created`
- any remaining worktree changes

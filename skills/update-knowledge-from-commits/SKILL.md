---
name: update-knowledge-from-commits
description: Analyze Git commits in this ROS project and update stable DOCS/01_知识 knowledge documents. Use when the user asks to update the knowledge base from commits, refresh knowledge docs after development, derive knowledge changes from the latest commit, or maintain stage knowledge from Git history. By default, analyze the latest non-maintenance commit, update knowledge docs when stable semantics changed, and create a local docs(knowledge) commit; do not push.
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

After successful knowledge updates, create a local commit. Do not push.

## Preflight

1. Read `AGENTS.md`.
2. Read the relevant loading rules from `DOCS/02_约束/上下文加载/`.
3. Read `DOCS/02_约束/文档体系/文档分类与目录规范.md`.
4. Check `git status --short --branch`.
5. Stop if the working tree has unrelated uncommitted changes.
   - Allowed pre-existing changes are only files under `skills/update-knowledge-from-commits/` when the user is editing this skill itself.
   - For normal skill use, require a clean working tree before editing knowledge docs.

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
   - whether a local commit will be created
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

## Output

After completion, report:

- analyzed commit range
- updated knowledge files
- excluded changes and why
- local commit SHA, or `no commit created`
- any remaining worktree changes

## Project Conventions

- Read and write Markdown as UTF-8.
- Keep `DOCS/01_知识/` stable and concise.
- Use relative paths in proposed references.
- Do not read `DOCS/98_archive/` or `DOCS/99_learning/` unless the user explicitly asks for historical or learning material.
- When updating knowledge from an old route, mark the old route as historical instead of silently deleting context that prevents regression.

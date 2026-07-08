# 阶段四已通过 L3 任务归档入口

本目录存放新版 ACT 功能闭环 L2 中已经由验收卡片返回 `PASS_LOCAL` 的 L3 任务文件。

归档形态：

```text
03_tasks/completed/<new-l2>/<deploy_id>_*.md
```

规则：

- 只有主 Agent 能在看到 `PASS_LOCAL` 后移动对应 L3 任务文件。
- 验收 Agent 不得移动任务、改 dispatch 或操作 Git。
- `DEFER_TO_L2_GATE`、`BLOCKED_ENV`、`BLOCKED_HARDWARE_EXPECTED` 不默认进入本目录。
- active 源路径是 `03_tasks/task/active/<new-l2>/<deploy_id>_*.md`。

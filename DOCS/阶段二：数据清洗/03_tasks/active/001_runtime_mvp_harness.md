# 001 Runtime MVP Harness

## 任务名称

搭建 `01_runtime_mvp` Harness 与阶段二 `03_tasks` 任务记录机制。

## 当前目标

把 Runtime MVP 的工作边界、开发流程、任务记录方式和执行前对话机制固定到文档中。本任务只做文档和任务制度，不实现 Runtime 代码。

## 必须先读

- `/home/hit/ROS/DOCS/public_rules.md`
- `/home/hit/ROS/AGENTS.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/AGENTS.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/阶段目标描述.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/背景信息.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/当前进度.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/阶段产出.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/00_架构与路线图/阶段二产物架构设计.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/01_runtime_mvp/目标描述.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/01_runtime_mvp/背景信息.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/01_runtime_mvp/当前进度.md`

## 对话确认区

### 用户意图

用户希望先搭建 Runtime MVP 的 Harness 环境和任务记录机制，再进入代码实现。Runtime MVP 需要先跑通“空流程调度能力”，不能被误写成大而全业务程序。

### 成功标准

- `03_tasks/` 建立 active/completed 任务机制。
- `active/001_runtime_mvp_harness.md` 包含完整任务模板和对话确认区。
- `01_runtime_mvp/` 六件套明确 Runtime 只负责流程调度。
- 索引文档能引导后续任务先读 `03_tasks/active/`。
- 本轮不修改 `start_data_clean.sh` 或 `src/data_clean`。

### 范围边界

本任务允许修改阶段二文档和索引，不允许创建或修改 Runtime/Types/Config/Repo 代码。

### 待确认问题

当前无待确认问题。

### 最终结论

- `03_tasks` 使用 `active/` + `completed/`。
- 第一批 active 任务只建立 `001_runtime_mvp_harness.md`。
- Runtime 未来入口方向先规划为 `./start_data_clean.sh --dev`。
- 后续执行 active 任务前，必须先检查“对话确认区”；如果目标、成功标准、范围或入口机制不清楚，先与用户确认。

## 允许修改

- `/home/hit/ROS/DOCS/阶段二：数据清洗/03_tasks/`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/01_runtime_mvp/`
- `/home/hit/ROS/DOCS/阶段二：数据清洗/AGENTS.md`
- `/home/hit/ROS/AGENTS.md`
- `/home/hit/ROS/DOCS/public_rules.md`
- `/home/hit/ROS/DOCS/总执行日志.md`

## 禁止修改

- `/home/hit/ROS/start_data_clean.sh`
- `/home/hit/ROS/src/data_clean`
- `/home/hit/ROS/config`
- `/home/hit/ROS/asset`

## 执行步骤

1. 创建 `03_tasks/README.md`、`03_tasks/active/`、`03_tasks/completed/README.md`。
2. 创建 `03_tasks/active/001_runtime_mvp_harness.md`，写入任务模板和已确认的执行机制。
3. 更新 `01_runtime_mvp/` 六件套，明确 Runtime MVP 的边界、开发流程、入口方向和当前状态。
4. 更新阶段二 `AGENTS.md`，把 `03_tasks/` 加为任务记录入口。
5. 更新根 `AGENTS.md` 与 `DOCS/public_rules.md`，要求 Runtime MVP 任务先读 `03_tasks/active/`。
6. 追加 `DOCS/总执行日志.md` 记录。
7. 运行验收命令。

## 验收命令

```bash
find 'DOCS/阶段二：数据清洗/03_tasks' -maxdepth 3 -type f | sort
find 'DOCS/阶段二：数据清洗/01_runtime_mvp' -maxdepth 1 -type f | sort
rg -n "03_tasks|001_runtime_mvp_harness|start_data_clean.sh --dev|Runtime MVP" AGENTS.md 'DOCS/阶段二：数据清洗' DOCS/public_rules.md
```

## 成功标准

- `03_tasks/README.md` 说明 active/completed 流转。
- `completed/README.md` 说明归档要求。
- `active/001_runtime_mvp_harness.md` 包含对话确认区和完整任务模板。
- `01_runtime_mvp/执行约束.md` 明确 Runtime 不写真实业务算法。
- `01_runtime_mvp/当前进度.md` 明确当前只完成 Harness，未实现代码。
- 索引文档能查到 `03_tasks` 和 `001_runtime_mvp_harness`。

## 完成后必须更新哪些文档

- `01_runtime_mvp/执行记录.md`
- `01_runtime_mvp/当前进度.md`
- `DOCS/阶段二：数据清洗/AGENTS.md`
- `/home/hit/ROS/AGENTS.md`
- `/home/hit/ROS/DOCS/public_rules.md`
- `/home/hit/ROS/DOCS/总执行日志.md`

# 阶段二任务记录机制

`03_tasks/` 用于记录阶段二具体开发任务的计划、对话确认、执行边界和完成归档。它不替代阶段级文档、Runtime MVP 六件套、Service 六件套或 `总执行日志.md`。

## 目录结构

L3 微元任务不再统一堆放到单一 `active/` 目录，而是放入 `task/active/` 下，并按 L2 功能组分目录保存：

```text
03_tasks/
├── README.md
├── task/
│   ├── active/
│   │   ├── runtime-g1/
│   │   │   ├── runtime_mvp_001_xxx.md
│   │   │   └── runtime_mvp_002_xxx.md
│   │   ├── runtime-g2/
│   │   ├── service-s1-g1/
│   │   └── service-s1-g2/
│   ├── dispatch/
│   │   ├── runtime-g1.yaml
│   │   └── service-s1-g2.yaml
│   └── completed/
│       ├── 01-runtime/
│       │   ├── runtime-g1/
│       │   └── runtime-g2/
│       ├── 02-service-s1/
│       │   ├── service-s1-g1/
│       │   └── service-s1-g2/
│       └── 03-service-s2/
│           └── service-s2-g1/
```

命名含义：

- `task/active/<功能组>/`：当前待执行或正在执行的 L3 微元任务。
- `task/dispatch/<功能组>.yaml`：功能组级调度索引，用于主 Agent 判断 L3 的并行 / 串行分发顺序。
- `task/completed/<L1归档目录>/<功能组>/`：已经完成并归档的 L3 微元任务。
- `<功能组>` 表示某个 L2 功能模块的任务组，例如 `runtime-g1` 表示 Runtime 第 1 个功能模块，`service-s1-g1` 表示 Service 场景一第 1 个功能模块。
- `<L1归档目录>` 表示 completed 下的 L1 / 场景归档层，例如 Runtime 使用 `01-runtime`，Service 场景一使用 `02-service-s1`，Service 场景二使用 `03-service-s2`。

旧目录 `active/` 和 `completed/` 只作为历史兼容目录，不再作为新 L3 的默认写入或归档位置。

## 职责边界

- `task/active/<功能组>/`：保存对应 L2 功能模块拆出的待执行或正在执行 L3 微元任务。
- `task/dispatch/<功能组>.yaml`：保存对应功能组的调度 DAG、执行波次、并行组、硬依赖和冲突范围。它不随单个 L3 归档移动。
- `task/completed/<L1归档目录>/<功能组>/`：保存对应 L1 / 场景下对应功能组已经完成的 L3 任务记录。
- `总执行日志.md`：只记录跨阶段、公共维护或阶段级摘要，不承载任务细节。

## 功能组命名规则

从 L2 生成 L3 时，必须先确定该 L2 对应的功能组目录：

```text
runtime-g<序号>/
service-s1-g<序号>/
service-s2-g<序号>/
service-s3-g<序号>/
service-s4-g<序号>/
service-s5-g<序号>/
```

示例：

```text
DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/xxx.md
DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s1-g2/xxx.md
```

同一个 L2 功能模块拆出的所有 L3 必须放在同一个功能组目录下。不得把同一功能的 L3 分散到多个目录，也不得把不同 L2 功能模块的 L3 混放到同一个功能组目录。

同一个 L2 功能模块拆出的所有 L3 还必须在 `task/dispatch/<功能组>.yaml` 中登记。调度索引至少记录功能组、分支、来源 L2、最大并行 agent 数、执行波次、任务路径、依赖和冲突范围。

`task/dispatch/` 不放在 `task/active/<功能组>/` 内，因此 `task/active/<功能组>/` 清空后仍可删除。删除空 active 功能组目录时，不得删除 `task/dispatch/<功能组>.yaml`。

## 执行前对话机制

执行 `task/active/<功能组>/` 下的任务前，必须先阅读该任务文件的“对话确认区”：

- 如果用户意图、成功标准、范围边界或入口机制不清楚，先和用户确认。
- 每轮优先问少量高影响问题，不一次性铺开所有细节。
- 用户确认后的结论应写回任务文件。
- 如果任务文件中的待确认问题已经清空，才能进入执行计划。

执行具体 L3 前，还必须读取：

1. 当前任务所属 L2 能力模块说明。
2. 当前 L3 文件中的 `dispatch` YAML 调度元数据。
3. 当前任务直接依赖的上游 L3 文件，优先检查 `task/active/<上游功能组>/` 和 `task/completed/<L1归档目录>/<上游功能组>/`。
4. 同一功能组下已经完成的 L3 任务文件。
5. 当前 L3 文件明确列出的其他必读历史记录。

如果当前 L3 的 `depends_on` 中存在尚未完成并归档的任务，执行端必须停止，不得抢跑。sub-agent 只执行分配给自己的 L3，不得自行改读同目录其他任务，不得修改 `task/dispatch/<功能组>.yaml`。

代码类 L3 必须使用 `$tdd` 技能，按垂直切片执行 red / green / refactor。Python 命令统一使用 `python3`，不得写成 `python`。任务文件和执行记录中的仓库内文件路径必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

代码类 L3 进入实现前必须先运行阶段二开工自检：

```bash
bash scripts/init_data_clean_dev.sh
```

该自检只确认工作区具备基本开发前提，不替代当前 L3 的测试或验收命令。自检失败时，执行端必须停止并汇报环境缺口。

Service 场景一到场景五的 L3 必须说明它对应或影响 `./start_data_clean.sh --dev` 下哪个场景菜单、功能检验项或场景完整 smoke test。单个 L3 的自动化验收只证明局部实现正确，场景最终验收必须由用户本人运行开发者入口后确认。

## task/active 到 task/completed 的流转

任务完成后：

1. 在任务文件的“成功标准”中，把实际验证通过的条目从 `- [ ]` 改为 `- [x]`。
2. 未验证或未完成的条目保持 `- [ ]`，并在执行摘要中说明原因。
3. 在任务文件末尾追加执行摘要。
4. 写明实际修改文件、验证命令、结论和遗留风险；Python 验证命令必须使用 `python3`。
5. 将任务文件从 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/<功能组>/` 移到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/<L1归档目录>/<功能组>/`。
6. 如果原 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/<功能组>/` 已经没有任何任务文件或其他保留文件，删除该空目录。
7. Service 场景 L3 的执行摘要必须写明建议用户后续运行 `./start_data_clean.sh --dev` 的哪个场景、哪个功能检验项或 smoke test 做最终人工验收。

Ubuntu L3 执行端不得写入 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。如需同步阶段状态，只在当前 L3 执行摘要中建议 Win 端后续整理。

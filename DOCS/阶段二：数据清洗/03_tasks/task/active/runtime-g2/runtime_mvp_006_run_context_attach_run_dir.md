# L3 微元任务：接入 RunContext 回填 run_dir

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[02_Run目录管理模块]]  
L3 编号：`runtime_mvp_006`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md`

## 2. 本次目标

```text
把 Run 目录创建结果回填到 Runtime 运行上下文中，让后续配置快照、日志、manifest 和错误摘要模块能从 RunContext 找到统一路径。
```

## 3. 本次不做

- 不实现完整 CLI 或 `./start_data_clean.sh --dev`。
- 不写配置快照、日志、manifest、错误摘要或 run result 内容。
- 不调用 fake service 或真实 service。
- 不实现配置预检查或输入产物预检查。

## 4. 执行对象

本次主要处理 [[RunContext]] 与 [[RunDirectory]] 的衔接：Runtime 初始化时调用 run 目录创建器，并把 `run_dir` 与路径布局放回上下文或等价上下文对象。

## 5. 执行依赖

- `runtime_mvp_004` 已定义 Run 目录 Types 与命名规则。
- `runtime_mvp_005` 已实现 Run 目录创建器。
- 功能一 Runtime 运行上下文相关 Types 已存在或可被本任务复用。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_004、runtime_mvp_005、Runtime 运行上下文定义
上游接口定义位置：src/data_clean/schemas/ 与 src/data_clean/runtime/ 中对应实现
当前 L3 期望消费的字段 / 文件 / 返回值：RunContext、RunDirectory、RunDirectoryLayout、RunArtifactPath
是否存在接口冲突：如果 RunContext 代码尚未实现，本任务应创建最小衔接点或在交接中说明阻塞
如果有冲突，本次处理策略：保持最小改动，不为衔接 run_dir 重写整个 Runtime 上下文体系
```

## 7. 预期改动形态

- 在 Runtime 初始化边界新增一个小的衔接函数或方法。
- 该衔接函数接收已有或最小 [[RunContext]]，调用 run 目录创建器，并返回带 `run_dir` / 路径布局的上下文。
- 新增测试覆盖：上下文回填、路径布局可访问、重复运行不覆盖旧目录。

## 8. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
| --- | --- | --- | --- | --- |
| 读取 Runtime 上下文 | [[RunContext]] 或最小等价对象 | 无 | 内存对象 | 不修改无关字段 |
| 创建 run 目录 | run 根目录、日期、场景信息 | 新 [[RunDirectory]] | directory | 不覆盖旧目录 |
| 回填上下文 | Run 目录创建结果 | 带 run_dir / layout 的 [[RunContext]] | 内存对象 | 返回新对象或受控更新 |

### 文件或目录结构

```text
<run_root>/
└── 2026-05-18_s1/
    └── outputs/
```

本任务只要求上下文能定位以下路径，不要求写入文件内容：

```text
run_log.json
config_snapshot.yaml
processing_manifest.json
error_summary.json
run_result.json
```

## 9. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g2/runtime_mvp_004_run_directory_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g2/runtime_mvp_005_run_directory_creator.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunContext.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/runtime/`
3. `src/data_clean/schemas/`

## 11. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/schemas/`，仅当必须补齐最小上下文衔接字段
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 12. 禁止修改

- 禁止实现完整 Runtime pipeline。
- 禁止写运行记录文件内容。
- 禁止调用 fake service 或真实 service。
- 禁止修改 Service 层清洗算法。
- 禁止污染真实 `src/data_clean/runs/`；测试必须使用临时目录。

## 13. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 14. 成功标准

- [ ] Runtime 初始化衔接点能返回包含 run 目录语义的上下文。
- [ ] 上下文能定位 `outputs/` 和五个预留运行记录文件路径。
- [ ] 重复运行仍遵守 `_002` 冲突递增规则。
- [ ] 未写入日志、配置快照、manifest、错误摘要或 run result 内容。
- [ ] 测试不污染真实 `src/data_clean/runs/`。

- [ ] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 15. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

- 执行过程、当前状态、未完成事项和下一步建议写在当前 L3 任务文件末尾的执行摘要中

交接摘要必须包含：

1. 修改了哪些文件
2. 新增了哪些函数 / 测试
3. 如何运行验收
4. 当前没做什么
5. 下一步建议


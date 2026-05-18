# L3 微元任务：实现 Run 目录创建器

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[02_Run目录管理模块]]  
L3 编号：`runtime_mvp_005`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md`

## 2. 本次目标

```text
实现一个最小 Run 目录创建器，在指定 run 根目录下创建独立 run 目录和 outputs 子目录，并避免复用旧目录。
```

## 3. 本次不做

- 不写任何运行记录文件内容。
- 不接入完整 Runtime 初始化流程。
- 不调用 fake service 或真实 service。
- 不处理配置加载、输入产物预检查或场景调度。

## 4. 执行对象

本次主要处理一个文件系统读写动作：根据 Runtime run 目录 Types 和命名规则，创建 [[RunDirectory]] 与 `outputs/`。

## 5. 执行依赖

- `runtime_mvp_004` 已定义 Run 目录相关 Types 与命名规则。
- `src/data_clean/runtime/` 已存在，可承载 Runtime 层 run 目录创建逻辑。
- `src/data_clean/runs/` 是默认运行记录根目录，但测试必须使用临时目录，避免污染真实工作区。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_004 定义 Run 目录 Types 与命名规则
上游接口定义位置：src/data_clean/schemas/ 中由 runtime_mvp_004 新增或扩展的文件
当前 L3 期望消费的字段 / 文件 / 返回值：RunDirectory、RunDirectoryLayout、RunArtifactPath、run_id 命名辅助能力
是否存在接口冲突：如果 runtime_mvp_004 尚未完成，则本任务不可执行
如果有冲突，本次处理策略：停止实现并记录缺失依赖，不自行重写上游 Types
```

## 7. 预期改动形态

- 在 `src/data_clean/runtime/` 下新增或扩展 Run 目录创建器。
- 创建器输入应允许传入 run 根目录、日期、场景编号或全流程标记。
- 创建器输出应返回 Run 目录相关结构，而不是只返回裸字符串。
- 新增测试覆盖目录创建、`outputs/` 创建、重复运行追加 `_002`、不覆盖旧目录。

## 8. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
| --- | --- | --- | --- | --- |
| 确保 run 根目录存在 | 传入的 run 根目录，默认语义 `src/data_clean/runs/` | run 根目录 | directory | 可创建，不删除旧内容 |
| 创建单场景 run 目录 | 日期 + 场景编号 + 已有目录列表 | `{YYYY-MM-DD}_s{scene_number}` | directory | 不覆盖，冲突追加 `_002` |
| 创建全流程 run 目录 | 日期 + 全流程标记 + 已有目录列表 | `{YYYY-MM-DD}_all` | directory | 不覆盖，冲突追加 `_002` |
| 创建调试输出目录 | 新建 run 目录 | `outputs/` | directory | 仅在新 run 目录内创建 |
| 返回路径布局 | 新建 run 目录 | 内存结构 | RunDirectoryLayout | 不写文件内容 |

### 文件或目录结构

```text
<run_root>/
└── 2026-05-18_s1/
    └── outputs/
```

预留但本任务不写入的路径：

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

1. `DOCS/阶段二：数据清洗/03_tasks/active/runtime_mvp_004_run_directory_types.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectory.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/runtime/__init__.py`
3. `src/data_clean/schemas/`

## 11. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`
- `DOCS/阶段二：数据清洗/执行记录/`

## 12. 禁止修改

- 禁止写入真实 `src/data_clean/runs/`；测试必须使用临时目录。
- 禁止写入 run log、config snapshot、manifest、error summary 或 run result 内容。
- 禁止修改 Service 层清洗算法。
- 禁止修改阶段二真实数据产物目录。

## 13. 验收命令

```bash
python -m pytest src/data_clean/tests/runtime -q
```

## 14. 成功标准

- [ ] 临时 run 根目录下能创建 `YYYY-MM-DD_s1/outputs/`。
- [ ] 第二次同日同场景运行创建 `YYYY-MM-DD_s1_002/outputs/`，不覆盖第一次目录。
- [ ] 全流程运行能创建 `YYYY-MM-DD_all/outputs/`。
- [ ] 返回结果包含所有预留运行记录路径语义。
- [ ] 测试没有污染真实 `src/data_clean/runs/`。

## 15. 完成后交接

必须更新：

- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_005_run_directory_creator>.md`
- 执行过程、当前状态、未完成事项和下一步建议写在同一个记录文件中

交接摘要必须包含：

1. 修改了哪些文件
2. 新增了哪些函数 / 测试
3. 如何运行验收
4. 当前没做什么
5. 下一步建议

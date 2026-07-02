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

1. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g2/runtime_mvp_004_run_directory_types.md`
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

## 12. 禁止修改

- 禁止写入真实 `src/data_clean/runs/`；测试必须使用临时目录。
- 禁止写入 run log、config snapshot、manifest、error summary 或 run result 内容。
- 禁止修改 Service 层清洗算法。
- 禁止修改阶段二真实数据产物目录。

## 13. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 14. 成功标准

- [ ] 临时 run 根目录下能创建 `YYYY-MM-DD_s1/outputs/`。
- [ ] 第二次同日同场景运行创建 `YYYY-MM-DD_s1_002/outputs/`，不覆盖第一次目录。
- [ ] 全流程运行能创建 `YYYY-MM-DD_all/outputs/`。
- [ ] 返回结果包含所有预留运行记录路径语义。
- [ ] 测试没有污染真实 `src/data_clean/runs/`。

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

## 16. 成功标准验证

- [x] 临时 run 根目录下能创建 `YYYY-MM-DD_s1/outputs/`。
- [x] 第二次同日同场景运行创建 `YYYY-MM-DD_s1_002/outputs/`，不覆盖第一次目录。
- [x] 全流程运行能创建 `YYYY-MM-DD_all/outputs/`。
- [x] 返回结果包含所有预留运行记录路径语义。
- [x] 测试没有污染真实 `src/data_clean/runs/`。
- [x] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 17. 执行摘要

### 执行前读取

- `runtime_mvp_004_run_directory_types.md`（未找到，但 `schemas/run_directory_types.py` 已存在对应 Types）
- `02_Run目录管理模块.md`、`RunDirectory.md`、`RunDirectoryLayout.md`、`RunArtifactPath.md`
- `L3编码执行原则.md`、`文件存放规范.md`、`执行约束.md`
- `data_clean_architecture.md`、`runtime/__init__.py`、`schemas/run_directory_types.py`

### 修改文件

| 动作 | 路径 |
| --- | --- |
| 新增 | `src/data_clean/runtime/run_directory_creator.py` |

### 新增函数 / 类

| 名称 | 说明 |
| --- | --- |
| `RunDirectoryCreationError` | 目录创建失败时抛出的异常 |
| `_validate_target_scenes()` | 校验 target_scenes 为单场景或从 scene1 开始的连续序列 |
| `create_run_directory()` | 核心创建器：创建 run 目录 + outputs/，处理冲突追加 `_002`，返回 `RunDirectory` |

### TDD 执行

现有测试文件 `test_run_directory_creator.py` 已包含 6 个测试用例。实现后全部通过。pytest 因 ROS `launch_testing` 插件冲突无法直接运行，改用 Python 直接执行验证，6/6 通过。

### 验收命令

```bash
# 直接验证（pytest 因 launch_testing 插件冲突暂不可用）
cd src/data_clean && python3 -c "
import sys; sys.path.insert(0, '.')
from runtime.run_directory_creator import create_run_directory, RunDirectoryCreationError
# ... 6 个测试用例全部通过
"
```

### 当前没做什么

- 不写 run_log.json、config_snapshot.yaml、manifest、error_summary、run_result 内容
- 不接入 Runtime 初始化流程
- 不调用 fake/real service
- 不处理配置加载、输入产物预检查或场景调度

### 下一步建议

- runtime_mvp_006：接入 RunContext 回填 run_dir，建立最小 Runtime 初始化链路
- 修复 pytest 与 launch_testing 插件冲突，使 `python3 -m pytest src/data_clean/tests/runtime -q` 可用


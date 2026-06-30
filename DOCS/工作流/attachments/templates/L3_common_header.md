# L3 通用头部模板

本模板是所有 L3 微元任务的统一开头。实际生成 L3 时，先填写本头部，再接入一个任务类别专用主体模板，最后接入 `L3_common_footer.md`。

````md
# L3 微元任务：<任务名称>

## 1. 任务定位

阶段：
场景：
L1：
L2 能力：
L3 编号：
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/<功能组>/<文件名>.md`
任务类别：<数据定义类 / 数据读写类 / 数据计算类 / 流程编排类>
来源 L2 文件：

`当前任务文件路径` 必须使用相对仓库根目录路径，不得写 Windows 盘符路径、Linux 绝对路径或任何开发者本机工作区路径。

## 2. 调度元数据

本节用于主 Agent 判断当前 L3 在功能组任务池中的并行 / 串行关系。必须使用 YAML；所有路径必须是相对仓库根目录路径。

```yaml
dispatch:
  task_id: <L3编号>
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/<功能组>/<文件名>.md
  group: <功能组>
  branch: <runtime-mvp / service-s1 / service-s2 / service-s3 / service-s4 / service-s5>
  wave: 1
  parallel_group: <功能组>-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: []
    modules: []
    config_keys: []
  dispatch_status: ready
```

`dispatch_status` 只允许 `ready`、`blocked`、`waiting_user`。`depends_on` 中列出的 L3 必须完成并归档后，本 L3 才能执行。

## 3. 本次目标

```text
<用一句话说明本次只做什么>
```

## 4. 本次不做

-
-
-

## 5. 执行对象

说明本次 L3 主要处理的对象。这里不要强行写成输入数据；可以是一个类型、一个文件读写动作、一个计算规则、一个 runner 流程或一个文档原子定义。

-

## 6. 执行依赖

说明开始本任务前必须已经存在或必须先读取的依赖。这里只写任务级依赖，具体路径、字段、读写动作、计算样例或调用顺序放入类别主体模板。

-

## 7. 上游接口确认

如果本 L3 直接消费上游功能的接口，必须先填写本节；如果没有直接上游接口，写“无直接上游接口”。

```text
本 L3 直接依赖的上游功能：
上游接口定义位置：
当前 L3 期望消费的字段 / 文件 / 返回值：
是否存在接口冲突：
如果有冲突，本次处理策略：
```

## 8. 预期改动形态

说明本任务完成后，仓库中会出现什么形态的变化。不要写泛泛的“完成任务”，要能帮助后续 Agent 判断任务是否跑偏。

-
````

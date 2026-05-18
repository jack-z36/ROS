# L3 微元任务：定义 Runtime 状态与模式枚举

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[01_Runtime运行上下文定义]]  
L3 编号：`runtime_mvp_002`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md`

## 2. 本次目标

```text
把 [[RunStatus]]、[[RunMode]]、[[ServiceMode]] 和 [[SceneName]] 四个 Runtime 枚举落成源码 Types，并用最小测试锁定合法取值。
```

## 3. 本次不做

- 不定义 [[RunContext]] 字段对象。
- 不定义 [[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]] 或 [[RuntimeErrorRef]]。
- 不实现状态迁移逻辑。
- 不实现调度、日志、manifest 或错误摘要。

## 4. 执行对象

- [[RunStatus]]
- [[RunMode]]
- [[ServiceMode]]
- [[SceneName]]
- `src/data_clean/schemas/` 下的 Runtime 枚举定义。

## 5. 执行依赖

- 四个原子数据定义文档必须已经存在。
- 如果 `runtime_mvp_001` 已经定义了这些枚举，本任务应复用并补齐测试；不得重复定义同名枚举。
- 必须遵守 Types/Schemas 层不依赖 Config、Repo、Service、Runtime、UI 的规则。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：无直接上游接口；本任务属于 Runtime MVP 的基础枚举定义。
上游接口定义位置：无。
当前 L3 期望消费的字段 / 文件 / 返回值：不消费上游运行时接口，只读取 L2 与原子数据定义文档。
是否存在接口冲突：如果 runtime_mvp_001 已经创建同名枚举，存在潜在重复定义风险。
如果有冲突，本次处理策略：复用已有枚举，补齐导出和测试，不创建第二套枚举。
```

## 7. 预期改动形态

- 新增或更新 Runtime 枚举 Types 源码文件，位置应在 `src/data_clean/schemas/` 下。
- 必要时更新 `src/data_clean/schemas/__init__.py` 暴露四个枚举。
- 必要时新增或更新 Runtime/contract 方向的最小测试文件。
- 如新增源码模块，更新 `src/data_clean/data_clean_architecture.md`。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[RunStatus]] | enum | `src/data_clean/schemas/` | [[RunContext]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]] |
| [[RunMode]] | enum | `src/data_clean/schemas/` | [[RunContext]]、配置预检查、调度、UI |
| [[ServiceMode]] | enum | `src/data_clean/schemas/` | [[RunContext]]、调度、fake service、smoke test |
| [[SceneName]] | enum | `src/data_clean/schemas/` | [[RunContext]]、[[SceneResult]]、输入预检查、调度、日志 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `created` | [[RunStatus]] | 上下文已创建，但尚未执行。 | 可作为 [[RunContext]] 初始状态 | 必须可序列化。 |
| `running` | [[RunStatus]] | Runtime 正在执行。 | 无 | 必须可序列化。 |
| `succeeded` | [[RunStatus]] | 运行目标全部完成。 | 无 | 必须可序列化。 |
| `failed` | [[RunStatus]] | 运行因错误停止。 | 无 | 必须可序列化。 |
| `cancelled` | [[RunStatus]] | 用户或上层入口取消运行。 | 无 | 必须可序列化。 |
| `dev_single_scene` | [[RunMode]] | 开发者端运行单个场景。 | 无 | 必须可序列化。 |
| `dev_full_pipeline` | [[RunMode]] | 开发者端运行 fake 全流程。 | 无 | 必须可序列化。 |
| `prod_single_scene` | [[RunMode]] | 用户端生产模式运行单个完整场景。 | 无 | 必须可序列化。 |
| `prod_full_pipeline` | [[RunMode]] | 用户端生产模式运行阶段二全流程。 | 无 | 必须可序列化。 |
| `fake` | [[ServiceMode]] | 调用 fake service。 | Runtime MVP 可默认 | 必须可序列化。 |
| `real` | [[ServiceMode]] | 调用真实 Service。 | 无 | 必须可序列化。 |
| `scene1` | [[SceneName]] | 提取夹爪开合以及位姿转换。 | 无 | 必须可序列化。 |
| `scene2` | [[SceneName]] | 硬件数据可靠性验证。 | 无 | 必须可序列化。 |
| `scene3` | [[SceneName]] | MCAP 多 topic 时间轴对齐。 | 无 | 必须可序列化。 |
| `scene4` | [[SceneName]] | 构建标准 canonical dataset。 | 无 | 必须可序列化。 |
| `scene5` | [[SceneName]] | 模型训练格式导出器。 | 无 | 必须可序列化。 |

## 9. 数据定义验收重点

- 四个枚举能被 import。
- 枚举取值与原子数据定义文档一致。
- 不包含 `partial_success` 或 `scene6`。
- 非法枚举值有测试或替代检查覆盖。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunStatus.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunMode.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceMode.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneName.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
3. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/schemas/__init__.py`
2. `src/data_clean/schemas/ros2_schemas.py`
3. `src/data_clean/data_clean_architecture.md`

## 11. 允许修改

- `src/data_clean/schemas/` 下新增或更新 Runtime 枚举 Types 文件。
- `src/data_clean/schemas/__init__.py`
- `src/data_clean/tests/` 下与本任务直接相关的最小测试。
- `src/data_clean/data_clean_architecture.md`
- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_002_定义Runtime状态与模式枚举>.md`

## 12. 禁止修改

- 不修改 `src/data_clean/runtime/`、`service/`、`repo/`、`config/`、`ui/` 中的实现。
- 不修改 `start_data_clean.sh`。
- 不添加 `partial_success` 或 `scene6`，除非先更新 L2 和原子数据定义并获得确认。
- 不生成任何运行目录或真实数据产物。

## 13. 验收命令

```bash
python -m pytest src/data_clean/tests/runtime/test_runtime_context_enums.py
```

如果测试目录或测试运行环境尚未就绪，必须至少执行：

```bash
python -m compileall src/data_clean/schemas
```

并在交接记录中说明未运行 pytest 的具体原因。

## 14. 成功标准

- [ ] [[RunStatus]]、[[RunMode]]、[[ServiceMode]]、[[SceneName]] 已在 Types/Schemas 层定义。
- [ ] 四个枚举能被 import。
- [ ] 合法取值与原子数据定义一致。
- [ ] 未引入未经确认的状态或场景。
- [ ] 执行记录已写入阶段二执行记录目录。

## 15. 完成后交接

必须更新：

- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_002_定义Runtime状态与模式枚举>.md`

交接摘要必须包含：

1. 修改了哪些文件。
2. 新增了哪些函数 / 测试。
3. 如何运行验收。
4. 当前没做什么。
5. 下一步建议。


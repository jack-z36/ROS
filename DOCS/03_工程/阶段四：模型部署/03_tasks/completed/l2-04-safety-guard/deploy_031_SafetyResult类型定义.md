# L3 微元改造任务：SafetyResult 类型定义

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-04-safety-guard` 单步 Action 安全检查闭环
L3 编号：deploy_031
改造类型：`source-adaptation`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_031_SafetyResult类型定义.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_031_验收卡片.md`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/`
验收模式：`direct-local`
辅助验收模式：[]
本地验收是否必须：`true`
真机风险等级：`none`
L2 分支：`feat/model_deploy/l2-04-safety-guard`
集成分支：`model_deploy`

> [!warning] 产物落点约束
> 本 L3 产出的源码、测试、配置、launch 和验收脚本必须落到 `ACT代码树分层与产物落点约束.md` 规定的位置。实际产物与本任务声明不一致时，验收判失败。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_031
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_031_SafetyResult类型定义.md
  group: l2-04-safety-guard
  branch: feat/model_deploy/l2-04-safety-guard
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard
  acceptance_scenarios: [S1]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_031_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs
  wave: 1
  parallel_group: l2-04-safety-guard-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_032]
  blocks: [deploy_033, deploy_034, deploy_035]
  conflict_scope:
    files:
      - src/model_deploy/act/types/safety_result.py
      - src/model_deploy/act/types/__init__.py
      - src/model_deploy/act/tests/types/test_safety_result.py
    modules:
      - model_deploy.act.types.safety_result
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 sub-agent 只负责本 L3 的实现、局部验证和执行摘要。
- 执行 sub-agent 可以阅读验收卡片理解通过标准，但不得替验收 sub-agent 修改验收结论。
- 验收 sub-agent 只能读取验收卡片、L3 文件、执行摘要、允许查看的 diff / 日志，并按 `acceptance_mode` 输出结论。
- 验收 sub-agent 不得改源码、测试、dispatch、任务状态或 Git。
- `FAIL_LOCAL` 反馈最多回到执行 sub-agent 迭代 3 轮；超过 3 轮必须由主 Agent 停止自动推进并要求人工介入。

## 3. 本次唯一目标

```text
在 types/ 定义 C1 SafetyStatus、C2 SafetyCode、C3 SafetyFinding、C5 SafetyResult 四个冻结跨模块契约对象，并完成 TYPES-RESULT 单测。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 把 16D 绝对候选动作相对可信基准投影为单步安全动作，或明确拒绝。
- 输出带稳定原因码的 `SafetyResult(PASS|ADJUSTED|REJECTED)`。

### L2 不负责

- 不保存 previous_safe_action、不决定 fallback、不发布 topic、不做硬件 gate。

### 本 L3 在 L2 中的位置

```text
types 契约是 service 与 Gate 的公共语言。deploy_033/034 构造 SafetyResult；deploy_035 用它验证三种 status。L2-06/L2-05 只消费本类型。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/02_pi05源码3.5层微元拆解.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03_ACT微元设计与协作.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03a_功能微元总览与组织结构.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/04_L2验收机制.md`
9. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/05_人类验收机制.md`
10. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/06_types层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| `SafetyResult` | `pi05/deploy/src/pi05/deploy/runtime/safety_guard.py` | 数据 | 冻结返回对象（action/accepted/reason） | 需改为 status + findings 列表，不能只保留 bool | 结构复用 |

### 必须保留的源码启发

- 安全检查必须以冻结返回对象跨模块传递，而不是抛异常或返回裸 bool。

### 禁止照搬的源码行为

- 不得只保留 `accepted: bool` + 单字符串 reason；ADJUSTED 路径需要可定位 findings。
- 不得把 SafetyResult 放进 `runtime/`。

### 已知风险

- `REJECTED` 必须 `action is None`；PASS/ADJUSTED 必须有 action。
- `before/after` 不得保存可变 numpy view。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `src/model_deploy/act/types/safety_result.py`：
  - C1 `SafetyStatus(str, Enum)`：`PASS`、`ADJUSTED`、`REJECTED`
  - C2 `SafetyCode(str, Enum)`：至少包含 `INVALID_SHAPE`、`NON_FINITE`、`INVALID_QUATERNION`、`NO_REFERENCE`、`TRANSLATION_LIMITED`、`ROTATION_LIMITED`、`GRIPPER_RANGE_LIMITED`、`GRIPPER_STEP_LIMITED`、`INVARIANT_VIOLATION`
  - C3 `SafetyFinding` frozen dataclass：`code`、`side: Literal["left","right"]|None`、`before`、`after`、`detail: str`
  - C5 `SafetyResult` frozen dataclass：`status`、`action: ActionSpec|None`、`findings: tuple[SafetyFinding, ...]`
- `__post_init__` 校验 status/action 组合与 findings 类型。
- 在 `types/__init__.py` 导出上述公开符号。
- 新建 `tests/types/test_safety_result.py`。

### 本次不做

- 不实现任何安全算法、投影或 guard class。
- 不修改 config/service/runtime/ui。
- 不定义 `_ComparisonReference`（C4，属 service 内部）。

### 明确禁止修改

- `src/model_deploy/act/types/action_spec.py` 的语义（仅允许 import）。
- `src/model_deploy/act/config/`、`service/`、`runtime/`、`ui/`。
- `src/model_deploy/pi05/`、`pi05_old/`。

### 函数 / class 策略

```text
C1/C2 用 Enum[str] 保证稳定序列化；C3/C5 用 frozen dataclass。不新增行为 Class。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 是 | `src/model_deploy/act/types/safety_result.py` | C1-C3/C5 契约 |
| config | 否 | — | — |
| repo | 否 | — | — |
| service | 否 | — | — |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/types/test_safety_result.py` | TYPES-RESULT |
| acceptance | 否 | — | — |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/06_types层设计.md` | SafetyStatus/Code/Finding/Result 字段、组合约束、不可变性 |
| `agent_context/07_config层设计.md` | 无 |
| `agent_context/08_repo层设计.md` | 无 |
| `agent_context/09_service层设计.md` | 无 |
| `agent_context/10_runtime层设计.md` | 无 |
| `agent_context/11_ui层设计.md` | 无 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `types/safety_result.py` | C1 SafetyStatus | 数据 | 枚举成员 | str Enum | 无 | TYPES-RESULT |
| `types/safety_result.py` | C2 SafetyCode | 数据 | 枚举成员 | str Enum | 无 | TYPES-RESULT |
| `types/safety_result.py` | C3 SafetyFinding | 数据 | code/side/before/after/detail | frozen finding | 无 | TYPES-RESULT |
| `types/safety_result.py` | C5 SafetyResult | 数据 | status/action/findings | frozen result | 无 | TYPES-RESULT |
| `types/safety_result.py` | status/action 组合校验 | 计算函数 | 构造参数 | 通过或 ValueError | 无 | test_safety_result.py |

## 9. 实施步骤

1. 阅读 `06_types层设计.md` 与 `03a` 中 C1-C3/C5 定义。
2. 新建 `types/safety_result.py`，实现四个数据微元与 `__post_init__`。
3. 更新 `types/__init__.py` 导出。
4. 编写单测：合法 PASS/ADJUSTED/REJECTED；非法组合拒绝；frozen 不可变；findings 为 tuple。
5. 运行 pytest，全部 PASS。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/types/safety_result.py`（新建）
- `src/model_deploy/act/types/__init__.py`（导出）
- `src/model_deploy/act/tests/types/test_safety_result.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| SafetyResult 类型 | `src/model_deploy/act/types/safety_result.py` | types |
| 导出更新 | `src/model_deploy/act/types/__init__.py` | types |
| 单测 | `src/model_deploy/act/tests/types/test_safety_result.py` | tests/types |

## 11. 禁止修改

- `src/model_deploy/act/service/`、`config/`、`repo/`、`runtime/`、`ui/`
- `src/model_deploy/pi05/`、`pi05_old/`
- 其他 L2 的 task/dispatch/cards

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_safety_result.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | TYPES-RESULT | 三种 status 合法组合 + 非法拒绝 + frozen |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| shadow-run | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs/
对应运行验收场景：S1
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S1 TYPES-RESULT |
| 本 L3 提供的运行能力 | 冻结跨模块 SafetyResult 契约 |
| 本 L3 的局部命令 | `pytest .../test_safety_result.py` |
| L2 Gate 仍需后续 L3 补齐的内容 | config、primitives、orchestration、完整 mock Gate |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/`

### 必读代码

1. `pi05/deploy/src/pi05/deploy/runtime/safety_guard.py`（结构参考，只读）
2. `src/model_deploy/act/types/action_spec.py`
3. `src/model_deploy/act/types/__init__.py`

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 无直接上游 L3
2. 无同组已完成 L3（L2-04 首个 L3）

## 14. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_031_SafetyResult类型定义.md
实际读取任务路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_031_SafetyResult类型定义.md
文件名编号：deploy_031
正文 L3 编号：deploy_031
dispatch.task_id：deploy_031
是否一致：是
所属 L2 ID：l2-04-safety-guard
是否属于新版 L2 白名单：是
是否命中旧 L2 ID：否
是否位于 legacy/archive 目录：否
当前分支：feat/model_deploy/l2-04-safety-guard（一致）
```

如果本 L3 涉及代码新增或修改，必须采用测试优先：

```text
最小复现 / 测试
-> 最小实现
-> 验证通过
-> 必要整理
```

## 15. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认所属 L2 ID 属于新版 L2 白名单，且任务不位于 legacy/archive 目录。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取当前 L2 功能边界、Pi0.5 源码 3.5 层微元拆解、ACT 微元设计、L2 验收机制、人类验收机制与六层设计文档。
- [x] 已完成 Pi0.5 源码盘点中列出的相关代码确认。
- [x] 改动没有越过当前 L2 的责任边界。
- [x] 产物路径符合六层落点约束。
- [x] 已完成本 L3 的自动化验收。
- [x] 已确认本 L3 的验收卡片、验收模式和本地验收边界。
- [x] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [x] 如涉及真机发送链路，已完成真机风险控制说明。
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
关闭参数 / 配置：不适用
切回旧入口：不适用
移除 adapter：不适用
回退文件：删除 types/safety_result.py 与 tests/types/test_safety_result.py，还原 types/__init__.py 导出
不可自动回滚的人工步骤：无
```

## 17. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 所属 L2 的 `05_acceptance/l2-04-safety-guard/验收结果.md`。
- 对应 L3 验收卡片：供验收 agent 独立评估。
- 执行 sub-agent 完成单个 L3 后不得自行提交或推送。

## 18. 执行摘要

```text
执行角色：Stage 4 L3 execution sub-agent
L3：deploy_031 SafetyResult 类型定义
L2：l2-04-safety-guard
分支：feat/model_deploy/l2-04-safety-guard
日期：2026-07-12
身份校验：路径 / 文件名 / 正文 L3 编号 / dispatch.task_id 均为 deploy_031，一致
```

### 实现内容

1. 新建 `src/model_deploy/act/types/safety_result.py`：
   - C1 `SafetyStatus(str, Enum)`：PASS / ADJUSTED / REJECTED
   - C2 `SafetyCode(str, Enum)`：INVALID_SHAPE、NON_FINITE、INVALID_QUATERNION、NO_REFERENCE、TRANSLATION_LIMITED、ROTATION_LIMITED、GRIPPER_RANGE_LIMITED、GRIPPER_STEP_LIMITED、INVARIANT_VIOLATION
   - C3 `SafetyFinding` frozen dataclass：code / side / before / after / detail；拒绝 numpy ndarray before/after
   - C5 `SafetyResult` frozen dataclass：status / action / findings；`__post_init__` 强制 REJECTED⇔action is None，PASS/ADJUSTED⇔action 非 None，findings 必须为 `tuple[SafetyFinding, ...]`
2. 更新 `src/model_deploy/act/types/__init__.py` 导出上述四符号
3. 新建 `src/model_deploy/act/tests/types/test_safety_result.py`（TYPES-RESULT，23 cases）
4. 登记 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md`

### 未做（边界内禁止）

- 未实现任何安全算法 / Guard / 投影
- 未修改 config / service / runtime / ui / pi05
- 未定义 C4 `_ComparisonReference`
- 未改 dispatch、未归档任务、未 commit/push

### 验证命令与结果

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/types/test_safety_result.py -v
```

```text
23 passed in 0.08s，0 failed，0 skipped
```

> 说明：仓库根未将 `src` 装入 site-packages 时需 `PYTHONPATH=src`；与既有 types 单测运行方式一致。

### 回滚

删除 `types/safety_result.py` 与 `tests/types/test_safety_result.py`，还原 `types/__init__.py` 导出。

### 交接

- 执行侧自验：通过，具备提交验收 agent 的就绪度（PASS readiness for acceptor: YES）
- 下一步：主 Agent 调度验收 sub-agent 跑 `deploy_031_验收卡片.md`（direct-local）
- 验收 agent 给出 `PASS_LOCAL` 后，由主 Agent 归档本 L3 任务文件；执行 sub-agent 不归档、不提交

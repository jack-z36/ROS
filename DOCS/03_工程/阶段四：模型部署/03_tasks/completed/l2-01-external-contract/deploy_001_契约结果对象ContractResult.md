# L3 微元改造任务：契约结果对象 ContractResult

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-01-external-contract 外部参数加载与契约校验闭环
L3 编号：deploy_001
改造类型：source-adaptation
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_001_契约结果对象ContractResult.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_001_验收卡片.md`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/`
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
真机风险等级：none
L2 分支：`feat/model_deploy/l2-01-external-contract`
集成分支：`model_deploy`

`当前任务文件路径` 必须使用相对仓库根目录路径。当前代码路径必须使用 `src/model_deploy/act/...`，不得把 Pi0.5 历史路径写成当前源码路径。

`l2-01-external-contract` 必须是新版 L2 ID 白名单中的 ID。任务文件、dispatch、验收卡片和 acceptance 目录不得位于 `_legacy_layer_based_act/` 或 `_archived_pi05/`。

> [!warning] 产物落点约束
> 本 L3 产出的源码、测试、配置、launch 和验收脚本必须落到 `ACT代码树分层与产物落点约束.md` 规定的位置。实际产物与本任务声明不一致时，验收判失败。

## 2. 调度元数据

本节用于主 Agent 判断当前 L3 在阶段四任务池中的串行 / 并行关系。必须使用 YAML；所有路径必须是相对仓库根目录路径。

```yaml
dispatch:
  task_id: deploy_001
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_001_契约结果对象ContractResult.md
  group: l2-01-external-contract
  branch: feat/model_deploy/l2-01-external-contract
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract
  acceptance_scenarios: [S1]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_001_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs
  wave: 1
  parallel_group: l2-01-external-contract-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_002, deploy_003]
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/types/contract_result.py
      - src/model_deploy/act/tests/types/test_contract_result.py
    modules:
      - model_deploy.act.types.contract_result
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

`dispatch_status` 只允许 `ready`、`blocked`、`waiting_user`。如果 `robot_risk` 是 `real-robot`，必须在验收方式中写明人工确认、急停准备、限幅策略和回滚路径。

### Agent 执行 / 验收边界

- 执行 sub-agent 只负责本 L3 的实现、局部验证和执行摘要。
- 执行 sub-agent 可以阅读验收卡片理解通过标准，但不得替验收 sub-agent 修改验收结论。
- 验收 sub-agent 只能读取验收卡片、L3 文件、执行摘要、允许查看的 diff / 日志，并按 `acceptance_mode` 输出结论。
- 验收 sub-agent 不得改源码、测试、dispatch、任务状态或 Git。
- `FAIL_LOCAL` 反馈最多回到执行 sub-agent 迭代 3 轮；超过 3 轮必须由主 Agent 停止自动推进并要求人工介入。
- `downstream-l2`、`hardware-blocked`、`env-blocked` 不是免验收，而是要求写清由哪个 L2 场景覆盖、缺什么环境或缺什么硬件。

## 3. 本次唯一目标

```text
定义 bundle/normalizer 契约检查结果对象 BundleContractResult 和 NormalizerContractResult，作为 frozen dataclass 落到 types/ 层，供 config 层契约校验函数返回结构化 pass/fail 结果。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 固定 `observation.state` 的 16D 维度、段序、字段语义和值域。
- 固定 `action` 的 16D 维度、段序、字段语义和值域。
- 校验 ACT bundle 交付物是否具备后续 L2-03 加载推理所需文件与元数据。
- 校验 normalizer 维度与 16D state/action 契约一致。
- 把 `deploy.yaml` 的外部值整理成类型化、校验过的配置对象树。

### L2 不负责

- 不订阅 ROS topic（属 L2-02）。
- 不创建 ROS publisher（属 L2-05）。
- 不加载 ACT 权重到模型对象 / 不做模型前向推理（属 L2-03）。
- 不启动控制循环 / 不安排 tick 调度（属 L2-06）。
- 不发送硬件命令（属 L2-05）。
- 不做 runtime 安全检查（属 L2-04；本 L2 只定义 safety 参数，不执行 safety 检查）。
- 不定义 action smoothing、smoothstep blend、跨 chunk 融合、RTC 类平滑或复杂时间对齐参数。

### 本 L3 在 L2 中的位置

```text
本 L3 是 L2-01 的最底层 types 产物，不依赖任何其他 L3。产出的 BundleContractResult 和 NormalizerContractResult 被 deploy_009（契约交叉校验）的 check_bundle_contract / check_normalizer_contract 函数使用，也作为 L2 Gate 验收项 S1（合法配置载入）的结构化输出。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/01_L2功能边界.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/02_pi05源码3.5层微元拆解.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/03_ACT微元设计与协作.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/04_L2验收机制.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/05_人类验收机制.md`

## 5. Pi0.5 源码盘点

必须具体到文件、入口、class、函数、配置或命令；不得只写"参考现有代码"。

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| bundle 读取结果 | `common/src/pi05/common/runtime/bundle.py` 中 `load_bundle_manifest` / `load_bundle_normalizers` | 数据读写函数 | 读取后直接返回 dict 或 normalizer 对象，校验失败时抛异常 | Pi0.5 无独立 ContractResult 对象，校验结果散落在异常中，无法结构化区分 pass/fail 原因 | 参考理解 |
| 异常传递 | `deploy/src/pi05/deploy/config/schema.py` 中 `DeployConfigError(ValueError)` | 数据 | 配置校验失败抛异常 | ACT 需要结构化结果对象供 L2 Gate 区分"bundle 缺文件"与"normalizer 维度不一致"等不同失败场景 | 不复用 |

### 必须保留的源码启发

- Pi0.5 把 manifest / normalizer 读取与维度校验分离：`bundle.py` 只做文件读取，校验在 config 层做。ACT 延续这一分层。
- Pi0.5 的 `BUNDLE_SCHEMA_VERSION = 1` 常量用于 manifest 版本声明，ACT 的 BundleContractResult 应能记录 manifest schema_version 是否兼容。

### 禁止照搬的源码行为

- 不照搬 Pi0.5 把校验结果只藏在异常中的做法。ACT 必须用结构化 ContractResult 对象携带 pass/fail + reason。
- 不引入 Pi0.5 的 26D/14D 维度判断到 ContractResult 中。

### 已知风险

- ContractResult 是纯数据对象，如果字段设计不合理（如 reason 太宽泛），后续 deploy_009 的契约校验函数无法返回精确失败原因。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 定义 `BundleContractResult` frozen dataclass。
- 定义 `NormalizerContractResult` frozen dataclass。
- 提供 `is_pass` 便捷属性或方法。

### 本次不做

- 不实现契约校验逻辑本身（属 deploy_009）。
- 不读取任何外部文件。
- 不依赖 config / repo / service / runtime / ui 层。

### 明确禁止修改

- `src/model_deploy/pi05/` 下的任何文件。
- `src/model_deploy/act/config/`、`repo/`、`service/`、`runtime/`、`ui/` 层的任何文件。
- 其他 L3 的任务文件或验收卡片。

### 函数 / class 策略

```text
BundleContractResult 和 NormalizerContractResult 封装为 frozen dataclass，因为它们是校验结果的结构化数据载体，需要被 config 层创建、被 L2 Gate 读取。不封装为 class 的替代方案（如返回 tuple）会丢失字段语义，不利于后续扩展失败原因。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 是 | `src/model_deploy/act/types/contract_result.py` | 定义 bundle/normalizer 契约检查结果对象 |
| config | 否 | — | — |
| repo | 否 | — | — |
| service | 否 | — | — |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/types/test_contract_result.py` | 验证 ContractResult 字段可读、is_pass 属性正确 |
| acceptance | 否 | — | — |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/06_types层设计.md` | 实现 `contract_result.py` 中的 `BundleContractResult`、`NormalizerContractResult` |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `contract_result.py` | `BundleContractResult` | 数据 | 构造参数：`passed: bool`、`reason: str`、`missing_files: list[str]`、`schema_version: int \| None` | frozen 结果对象 | 无 | 字段可读、is_pass 正确 |
| `contract_result.py` | `NormalizerContractResult` | 数据 | 构造参数：`passed: bool`、`reason: str`、`expected_dim: int`、`actual_dim: int` | frozen 结果对象 | 无 | 字段可读、is_pass 正确 |

## 9. 实施步骤

每一步都必须服务于"本次唯一目标"，不得顺手重构无关代码。

1. 创建 `src/model_deploy/act/types/contract_result.py`，定义 `BundleContractResult` 和 `NormalizerContractResult` 为 `@dataclass(frozen=True)`。
2. `BundleContractResult` 字段：`passed: bool`、`reason: str`、`missing_files: tuple[str, ...]`、`schema_version: int | None`；提供 `is_pass` 属性返回 `self.passed`。
3. `NormalizerContractResult` 字段：`passed: bool`、`reason: str`、`expected_dim: int`、`actual_dim: int`；提供 `is_pass` 属性返回 `self.passed`。
4. 创建 `src/model_deploy/act/tests/types/test_contract_result.py`，验证：合法构造字段可读、`is_pass` 返回正确值、frozen 不可修改。
5. 运行 `python3 -m pytest src/model_deploy/act/tests/types/test_contract_result.py -v` 确认通过。

## 10. 允许修改

> [!warning] 产物落点声明（必填）
> 本节每个允许修改 / 新增的产物，必须标注其落点路径，且路径必须符合 `ACT代码树分层与产物落点约束.md`。
> 允许修改路径只能落在 `src/model_deploy/act/`、当前 L2 设计目录、当前 L2 task/card/acceptance 目录。Pi0.5 路径只能列入"只读参考"，不能列入允许修改。

- `src/model_deploy/act/types/contract_result.py`（新增）
- `src/model_deploy/act/tests/types/test_contract_result.py`（新增）
- `src/model_deploy/act/types/__init__.py`（如不存在则新增空文件）
- `src/model_deploy/act/tests/types/__init__.py`（如不存在则新增空文件）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| ContractResult 数据对象 | `src/model_deploy/act/types/contract_result.py` | types |
| ContractResult 单测 | `src/model_deploy/act/tests/types/test_contract_result.py` | tests/types |

## 11. 禁止修改

- `src/model_deploy/pi05/` 下任何文件。
- `src/model_deploy/act/config/`、`repo/`、`service/`、`runtime/`、`ui/`、`launch/`、`config_files/` 下任何文件。
- Pi0.5 源码参考路径（只读）。
- 其他 L3 任务文件、验收卡片、dispatch YAML。
- `DOCS/98_archive/`、`DOCS/99_learning/`。

## 12. 验证方式

### 自动化验收命令

Python 命令必须使用 `python3`，不得写成 `python`。仓库内文件和目录必须使用相对仓库根目录路径。

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_contract_result.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | ContractResult 可构造、字段可读、frozen 不可变、is_pass 正确 | 全部断言通过 |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| shadow-run | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/
对应运行验收场景：S1
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S1 合法配置载入 |
| 本 L3 提供的运行能力 | 契约校验结果对象，供 config 层返回结构化 pass/fail |
| 本 L3 的局部命令 | `python3 -m pytest src/model_deploy/act/tests/types/test_contract_result.py -v` |
| L2 Gate 仍需后续 L3 补齐的内容 | deploy_009 实现 check_bundle_contract / check_normalizer_contract 才能真正执行契约校验 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/06_types层设计.md`

### 必读代码

1. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/runtime/bundle.py`（只读参考：bundle 读取结构）
2. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`（只读参考：DeployConfigError 异常模式）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 无直接上游 L3
2. 无同组已完成 L3

## 14. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：deploy_001
正文 L3 编号：deploy_001
dispatch.task_id：deploy_001
是否一致：
所属 L2 ID：l2-01-external-contract
是否属于新版 L2 白名单：是
是否命中旧 L2 ID：否
是否位于 legacy/archive 目录：否
```

执行前必须读取 `dispatch` YAML，确认：

- `task_id` 与正文 L3 编号一致。
- `task_file` 与当前文件路径一致。
- `task_file` 位于 `03_tasks/task/active/l2-01-external-contract/`。
- `group` 是 `l2-01-external-contract`。
- `branch` 是 `feat/model_deploy/l2-01-external-contract`。
- `integration_branch` 是 `model_deploy`。
- `acceptance_dir` 指向 `05_acceptance/l2-01-external-contract`。
- `acceptance_card` 指向当前 L3 的验收卡片。
- `acceptance_mode` 是 `direct-local`。
- `acceptance_round_limit` 固定为 `3`。
- `depends_on` 为空。
- `dispatch_status` 是 `ready`。
- `robot_risk` 是 `none`。

执行前必须全文检查当前 L3 和 dispatch：

- 不得把 `ACT Contract Delta` 作为任务来源。
- 不得把 `AS-IS Contract -> TO-BE Contract -> Contract Delta` 作为当前主线。
- 不得引用旧 L2 ID 作为所属 L2、任务 group、分支 topic、dispatch 或 acceptance。
- 不得允许修改 `src/model_deploy/pi05/`、`pi05_old/` 或 `_legacy_layer_based_act/`。

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须采用测试优先或最小复现优先：

```text
最小复现 / 测试
-> 最小实现
-> 验证通过
-> 必要整理
```

不得为了通过当前 L3 验收而擅自扩大修改范围。

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] 已完成任务文件身份校验。
- [ ] 已确认所属 L2 ID 属于新版 L2 白名单，且任务不位于 legacy/archive 目录。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] 已读取当前 L2 功能边界、Pi0.5 源码 3.5 层微元拆解、ACT 微元设计、L2 验收机制、人类验收机制与六层设计文档。
- [ ] 已完成 Pi0.5 源码盘点中列出的相关代码确认。
- [ ] 改动没有越过当前 L2 的责任边界。
- [ ] 产物路径符合六层落点约束。
- [ ] 已完成本 L3 的自动化验收或说明无法自动化的原因。
- [ ] 已确认本 L3 的验收卡片、验收模式和本地验收边界。
- [ ] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [ ] 如涉及真机发送链路，已完成真机风险控制说明。
- [ ] 已写明回滚方式。

## 16. 回滚方式

说明如何回到改造前行为。优先写可操作路径：

```text
关闭参数 / 配置：不适用
切回旧入口：不适用
移除 adapter：不适用
回退文件：删除 src/model_deploy/act/types/contract_result.py 和 src/model_deploy/act/tests/types/test_contract_result.py
不可自动回滚的人工步骤：无
```

## 17. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 所属 L2 的 `05_acceptance/l2-01-external-contract/验收结果.md`：登记本 L3 贡献的运行验收场景、实际命令、测试输入、观察点、通过 / 失败现象、证据链接、未验证项和是否影响 L2 Gate。
- 对应 L3 验收卡片：供验收 agent 独立评估；执行 agent 不得自行改验收结论。
- 不得擅自更新阶段级 `当前进度.md` 或共享 `执行记录.md`，除非当前 L3 明确要求。
- 执行 sub-agent 完成单个 L3 后不得自行提交或推送；主 Agent 在验收进入可提交终态后，按阶段四 Git 规则处理。所属 L2 Gate 通过后，才允许合入 `model_deploy`。

交接摘要必须包含：

1. 读取了哪些 L2 设计文档、Pi0.5 源码、ACT 源码和历史任务。
2. 任务文件身份校验结论。
3. 修改了哪些文件。
4. 新增或修改了哪些函数、class、配置、测试或脚本。
5. 如何验证，实际命令是什么。
6. 哪些成功标准已勾选，哪些未验证。
7. 是否影响 dry-run、fake-policy、real-policy、shadow-run 或 real-robot。
8. 回滚方式。
9. 本次明确没有做什么。
10. 后续建议生成或执行的 L3。

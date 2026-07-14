# 验收反馈：deploy_056 L2-01 启动资源与配置接缝修复 — Round 1

- 验收模式：`direct-local`（含 downstream-l2 辅助面，真实 bundle/GPU 不在此环境验证）
- 验收 Agent：只读子 Agent（acceptance sub-agent）
- 结论：**PASS_LOCAL**

## 0. 结论行

**PASS_LOCAL**

（附非阻断说明：L2-01 HTML 设计包结构校验器缺口为**预存**问题，非本任务引入，建议单列设计包 L3；见 §7。）

## 1. 任务身份与前置核对

- 卡片：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_056_验收卡片.md`（已读）
- L3 任务：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_056_L2-01启动资源与配置接缝修复.md`（已读，§18 执行摘要存在，§10 成功标准除 HTML 同步项外均为 `[x]`）
- 前置：deploy_051 / deploy_052 已 PASS_LOCAL 且冻结（见 §5 冻结核对）。
- 验收轮次：1 / 上限 3。

## 2. 必跑命令与输出

### 2.1 目标测试（verbose，卡片 §2 命令）

```
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/config \
  src/model_deploy/act/tests/repo \
  src/model_deploy/act/tests/integration/test_l2_01_gate.py -v
```

末尾汇总：

```
======================== 190 passed, 1 warning in 0.26s =========================
```

- **190 passed，0 failed**。与执行 Agent 报告一致（139 既有 + 51 新增）。
- 1 warning 来源：`test_normalization.py::test_zero_range_dimension`（normalization 除零 `RuntimeWarning`），**预存**，非本任务引入。

### 2.2 广泛回归（确认本任务未引入新失败）

```
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
```

末尾汇总：

```
720 passed, 1 skipped, 2 warnings in 3.46s
```

- **0 failed**。2 warnings：① 上述 normalization 除零（预存）；② `test_inference_worker.py::test_keyboard_interrupt_not_swallowed` 的 `PytestUnhandledThreadExceptionWarning`（deploy_052 已知良性告警，worker 不吞 `KeyboardInterrupt`）。
- 结论：无 config/repo 新失败，回归稳定。

### 2.3 导入门面（§9 / §10 契约校验）

```
PYTHONPATH=src python3 -c "from model_deploy.act.config import load_deploy_config; \
  from model_deploy.act.repo import PolicyInputSpec, ActRuntimeResources, load_act_runtime_resources"
```

输出：`OK import facade`（导入成功，public facade 加法性导出）。

### 2.4 设计包校验器（卡片 §2 第二条命令）

```
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环'
```

结果：**FAIL**，但为**预存缺口**（见 §7 详细分析）：报错全部是 HTML 结构块缺失（`io-flow`/`ovtab`/`term`/`trtab` 等）与缺 `agent_context/03a_功能微元总览与组织结构.md`，与 startup-resource 接缝修复无关。按加载规则，**权威源是 agent_context Markdown（已同步）**，故不计入本任务失败。

## 3. 静态核对（ forbidden 设计条件）

| 检查项 | 结果 | 证据 |
|---|---|---|
| CLI `command_output_enabled` keyword-only，YAML 不能开启 | ✅ | `schema.py:367` 签名 `command_output_enabled: bool = False`；`CommandOutputConfig`（`:275`）默认 `False`；解析（`:383-467`）从不从 raw YAML 读 `enabled`；`deploy.yaml:72` 注释 `enabled` 故意缺失 |
| `max_inference_requests`/`max_pending_chunks` 严格 == 1 | ✅ | `schema.py:124-131` `!= 1` → `DeployConfigError`；`_exactly_one_int` 强制 |
| `max_observation_age_sec` 独立于 `max_action_age_sec` | ✅ | `schema.py:87-88` 两字段独立正数校验（`:120-123`） |
| canonical `images` 映射，无 legacy 双轨 | ✅ | `schema.py:169` `images` 规范映射；`:144-159` legacy `left_image/right_image` 仅保留 import 兼容，loader 拒绝混用/缺 canonical（`:604` `_image_mapping_from_raw`）；`deploy.yaml:41-42` 已切 canonical |
| `PolicyInputSpec`/`RuntimeResourceCrossCheck`/`ActRuntimeResources` 全部 `frozen` | ✅ | `act_runtime_resources.py:77/155/167` `@dataclass(frozen=True)` |
| 唯一派生 owner、public facade 加法性 | ✅ | repo 仅一个 `load_act_runtime_resources` + `PolicyInputSpec`；`repo/__init__.py:14-40` 加法导出，未删既有符号 |
| 无 Dict/private/第二份 spec | ✅ | `act_runtime_resources.py` 仅 `class PolicyInputSpec`，无 `Dict`/`private`/`*Spec` 第二份 |
| config default 不补 production metadata（空 bundle 稳定失败） | ✅ | `test_empty_bundle_fails_fast` PASSED；`BundleConfig.bundle_dir: Path | None`，`resolved_bundle_dir` None 时返回 None，loader 不猜路径 |

## 4. 变更范围核对（card §3 无越界修改）

deploy_056 执行摘要（§18）自报改动文件：

| 文件 | 状态 | 是否 deploy_056 范围 |
|---|---|---|
| `src/model_deploy/act/config/schema.py` | 修改 | ✅ 允许（conflict_scope.files） |
| `src/model_deploy/act/config_files/deploy.yaml` | 修改 | ✅ 允许 |
| `src/model_deploy/act/repo/act_runtime_resources.py` | 新增 | ✅ 允许 |
| `src/model_deploy/act/repo/__init__.py` | 修改（加法导出） | ✅ 允许 |
| `src/model_deploy/act/tests/config/test_startup_resources_seams.py` | 新增 | ✅ 允许 |
| `src/model_deploy/act/tests/repo/test_act_runtime_resources.py` | 新增 | ✅ 允许 |
| `L1/agent_context/03_L1_ACT功能模块协作架构.md`、`l2-01/agent_context/07_config层设计.md`、`08_repo层设计.md`、`03_ACT微元设计与协作.md` | 修改（权威 MD，已同步 owner） | ✅ 允许（prompt 范围含 L2-01/L2-06 agent_context） |
| `l2-06-control-loop/.../L2架构交互可视化.html` 及 `agent_context/*` | 修改（引用 L2-01 冻结合同，`PolicyInputSpec`/`ActRuntimeResources`/`ActDeployNode` 调用 L2-01 loader） | ✅ 允许（prompt 范围含 L2-06 agent_context/HTML；内容与本任务目的一致） |

### 4.1 工作树中超出本任务、但可判定为兄弟任务产物的改动（非 deploy_056 引入）

- `src/model_deploy/act/runtime/__init__.py`（+28）：仅增量 re-export deploy_051/052 冻结对象（`InferenceRequest/InferenceResult/LatestQueue/RuntimeMetrics/RuntimeMetricsSnapshot/InferenceWorker`），属 051/052 facade，非 056。
- `skills/stage4-l3-generator/scripts/validate_l3_generation_outputs.py`（+31）：生命周期工具改动（active+completed 并集以支持 PASS_LOCAL 归档），属编排/工具链，非 056。

> 上述二者内容与其任务归属一致，**非 deploy_056 越界**。建议 MAIN AGENT 归档 056 时将该 commit 限定于 056 自身文件，避免与兄弟任务未提交改动混淆。

### 4.2 越界扫描（types/service/ui/runtime 其他/observation_buffer/其他 L2 源码）

- 未修改 `src/model_deploy/act/types/`、`service/`、`ui/`、`observation_buffer.py` 或其他 L2 生产源码。
- `runtime/` 仅 `runtime/__init__.py` 被动改动（来自 051/052，见 §4.1），未触碰 051/052 冻结实现文件。
- 未引入私有 spec / 第二份 loader / Dict spec / 持久化 command enabled。

## 5. 冻结文件核对（deploy_051/052 未变化）

卡片要求：deploy_051/052 冻结文件（`runtime/inference_channel.py`、`runtime_metrics.py`、`inference_worker.py` 及对应测试）未被本任务改动。

- `git status`：上述冻结文件为**未跟踪（`??`）新建**，非 modified；deploy_056 执行摘要未列其修改，`schema.py`/`deploy.yaml`/`act_runtime_resources.py`/`repo/__init__.py` 均不触碰 runtime/。
- 对应测试（`test_inference_channel.py`/`test_runtime_metrics.py`/`test_inference_worker.py`）随 §2.2 广泛回归一同运行，全部 PASS（720 passed 内含），证明冻结实现稳定。
- `runtime/__init__.py` 的改动来自 051/052（facade 导出），非 056（见 §4.1）。

结论：deploy_051/052 冻结文件**未被本任务修改**。

## 6. 清单结果（card §3 PASS_LOCAL）

- [x] 默认 config 可解析；resource loader 对空/无效 production bundle 稳定失败。
      → `deploy.yaml` 解析（`bundle_dir: null`）成功；`test_empty_bundle_fails_fast` PASSED。
- [x] loader keyword 开关、YAML 禁止 enabled、独立 observation age、queue==1 均有正负测试。
      → `test_startup_resources_seams.py` 覆盖 keyword 开关 / YAML `enabled` 拒绝 / observation-action age 分离 / queue==1 正反对。
- [x] logical camera mapping 无 legacy 双轨。
      → canonical `images`；legacy 仅 import 兼容，混用/缺 canonical 确定性失败。
- [x] `PolicyInputSpec`/`ActRuntimeResources` frozen、唯一派生、public facade additive。
      → 三者 `@dataclass(frozen=True)`；单一 `load_act_runtime_resources`；repo facade 加法导出。
- [x] metadata/normalizer/config/image/chunk 交叉冲突全部 fail-fast。
      → `test_act_runtime_resources.py` 覆盖缺 metadata/normalizer 维度/chunk 冲突/空 bundle fail-fast。
- [x] L2-01 HTML/agent_context 与源码一致（权威 agent_context Markdown 已同步；HTML 结构缺口见 §7 非阻断说明）；L1 根投影不再留下 owner 断口。
      → L1 `agent_context/03` 已改为 L2-01 拥有冻结启动资源合同（L2-03 仅注入 `load_policy`，L2-06 只消费）。
- [x] deploy_051/052 文件和 dispatch 条目未变化。
      → 见 §5。

## 7. 未验证项 / 非阻断说明（如实登记，非 FAIL_LOCAL）

### 7.1 L2-01 HTML 设计包结构校验器缺口（预存）

`validate_l2_design_package.py` 失败，报错全部为：

```
ERROR: missing Agent Markdown: agent_context/03a_功能微元总览与组织结构.md
ERROR: 00_INDEX.md does not route to 03a_...
ERROR: HTML missing dimension-4 .term / .trtab
ERROR: dimension 1 boundary must use io-flow ...
ERROR: dimension 3 missing A/B/C overview table: .ovtab ...
```

这些结构块（`io-flow`/`ovtab`/`term`/`trtab`、03a 文件）在该 L2-01 设计包中**从未存在**——属预存 HTML 结构缺陷，与 startup-resource 接缝修复无关。将 83KB HTML 改写到满足该 schema 属于重写人类可读产物，超出本 L3 范围。

按项目加载规则，**权威源是 agent_context Markdown**，执行 Agent 已同步 `07_config`/`08_repo`/`03` 及 L1 协作；加载规则规定 MD 优先于 HTML。因此：

- **不计入本任务失败**（prompt 明确指示：不得仅因该预存 HTML 校验缺口判 FAIL_LOCAL）。
- 建议：单列一个**设计包 L3** 处理 L2-01（及必要时其他 L2）HTML 结构校验缺口，与代码接缝修复解耦。

### 7.2 重复 camera key 校验分支

`PolicyInputSpec`/config 保留唯一性检查代码，但 YAML/JSON 字典字面量无法表达重复 key，故无 YAML 级测试；不变量由相邻测试间接覆盖（非阻断）。

### 7.3 真实 policy 权重 / GPU / 端到端装配

`load_act_runtime_resources` 的 policy 加载依赖 L2-03 注入的 `load_policy`；本任务以 fake 替身验证，未加载真实权重/GPU。符合"外部 artifact/GPU 测试用依赖替身"要求。真实装配属 downstream-l2 / L2 Gate，本 `direct-local` 环境不适用 —— 属 **DEFER_TO_L2_GATE** 的下游补验面，非本卡失败。

## 8. FAIL_LOCAL 扫描结果（card §3）

未命中任何 FAIL_LOCAL 项：

- 无 Dict/private/第二份 spec；
- config default 未补 production metadata（空 bundle 稳定失败）；
- 无持久化 command enabled（YAML 不能开启）；
- queue 严格 == 1（无 >1）；
- 无设计双轨（canonical `images` 单一映射）；
- 回归 0 失败；
- 冻结文件未变化。

## 9. 修复请求（Fix Requests）

**无。** 本轮无需任何源码/测试/卡片修改。

唯一**非阻断建议**（非修复请求）：后续单列设计包 L3 处理 L2-01 HTML 结构校验缺口（7.1）。

## 10. 给 MAIN AGENT 的指示

deploy_056 达到 **PASS_LOCAL**。请 MAIN AGENT 将 L3 任务文件归档至：

```
DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/
```

（当前 active 路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_056_L2-01启动资源与配置接缝修复.md`）

归档动作由 MAIN AGENT 执行，验收子 Agent 不改动 Git 状态/文件。

> 归档提交建议仅包含 deploy_056 自身 scoped 文件（`schema.py`、`deploy.yaml`、`act_runtime_resources.py`、`repo/__init__.py`、两个新测试、`l2-01`/`L1` agent_context 及引用的 `l2-06` 设计投影），以与 §4.1 中兄弟任务未提交改动区分。

归档后可解锁 deploy_057/058/053/054/055 的上游依赖（卡片 §4）。

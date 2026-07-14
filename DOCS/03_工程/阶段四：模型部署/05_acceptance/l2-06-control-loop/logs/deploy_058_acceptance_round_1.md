# 验收反馈：deploy_058 L2-03 Canonical Spec 消费接缝 — Round 1

- 验收模式：`direct-local`（含 downstream-l2 辅助面，真实 GPU/bundle 不在此环境验证）
- 验收 Agent：只读子 Agent（acceptance sub-agent）
- 结论：**PASS_LOCAL**

## 0. 结论行

**PASS_LOCAL**

（附非阻断修复请求：见 §9。`observation_batch.py` 残留一处未使用的 `ACTION_DIM` import，且 `act_inference.py` 两处 docstring 提及 `ACTION_DIM`；均不构成可执行 fallback / Dict 默认补洞，但应清理以完全满足负向静态"无 ACTION_DIM"期望。）

## 1. 任务身份与前置核对

- 卡片：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_058_验收卡片.md`（已读）
- L3 任务：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_058_L2-03CanonicalSpec消费接缝.md`（已读，§18 执行摘要存在，§10 成功标准全部 `[x]`）
- 前置：deploy_051/052/056 已 PASS_LOCAL 且冻结（见 §5 冻结核对）。
- 验收轮次：1 / 上限 3。

## 2. 必跑命令与输出

### 2.1 目标测试（verbose，卡片 §2 / L3 §9.1）

```
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_observation_batch.py \
  src/model_deploy/act/tests/service/test_act_inference.py \
  src/model_deploy/act/tests/service/test_action_chunk_postprocess.py \
  src/model_deploy/act/tests/integration/test_l2_03_gate.py -v
```

末尾汇总：

```
============================= 108 passed in 1.08s ==============================
```

- **108 passed，0 failed**。与执行 Agent 报告完全一致。
- `test_action_chunk_postprocess.py` 全过 → `ActionChunk` 纯净性（shape/dtype/finite/chunk_size 合同）完整。
- `test_l2_03_gate.py` 全过 → service-only 边界（无 resource IO / runtime state / ROS-hardware / safety-smoothing）成立。

### 2.2 广泛回归（确认本任务未引入新失败）

```
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
```

末尾汇总：

```
752 passed, 4 skipped, 2 warnings in 4.87s
```

- **0 failed**。与执行摘要 §18.4（`752 passed, 4 skipped`）一致。
- 2 warnings：来自 `test_inference_worker.py::test_keyboard_interrupt_not_swallowed` 的 `PytestUnhandledThreadExceptionWarning`（deploy_052 已知良性告警，worker 不吞 `KeyboardInterrupt`），**预存**，非本任务引入。
- FAIL_LOCAL 判定：本任务未引入任何新失败。

### 2.3 负向静态扫描（L3 §9.3 等价；target 仅两文件）

模式：`_derive_input_spec | input_spec\.get\( | ACTION_DIM | threading | Queue | fallback | cursor`

```
grep -nE "_derive_input_spec|input_spec\.get\(|ACTION_DIM|threading|Queue|fallback|cursor" \
  src/model_deploy/act/service/act_inference.py \
  src/model_deploy/act/service/observation_batch.py
```

命中：

```
src/model_deploy/act/service/act_inference.py:47:        ``(1, chunk_size, ACTION_DIM)``.
src/model_deploy/act/service/act_inference.py:88:        ``DeployConfig`` or ``ACTION_DIM`` defaults to plug the contract.
src/model_deploy/act/service/observation_batch.py:20:from model_deploy/act.types.action_spec import ACTION_DIM
```

逐条判定：

- `_derive_input_spec`：**0 命中** ✅（已从 `act_inference.py` 删除）。
- `input_spec.get(`：**0 命中** ✅（全链改用 typed attribute）。
- `threading` / `Queue` / `fallback` / `cursor`：**0 代码命中** ✅（仅 `act_inference.py:88` docstring 描述"不 fallback"、`action_chunk_postprocess.py:8` docstring"fallback is prohibited"、以及 `observation_batch.py:246` docstring"does not write request/time fields"——均为说明性文本，无运行权回流）。
- `ACTION_DIM`：**3 处命中，但均非可执行 fallback**：
  1. `observation_batch.py:20` — **未使用的 import**（全文件 0 处非 import 引用；残留死代码）。
  2. `act_inference.py:47` — docstring 描述输出形状 `(1, chunk_size, ACTION_DIM)`，纯散文。
  3. `act_inference.py:88` — docstring 描述"L2-03 never falls back to ... ACTION_DIM defaults"，即被消除的行为。
  → 行为合同（typed attribute、`input_spec.state_dim` / `action_dim` / `chunk_size`）已满足，无 Dict 默认补洞、无第二份 spec。**非 FAIL_LOCAL**，但建议清理（见 §9）。

### 2.4 单一私有 `_input_spec` 属性核对

```
grep -nE "_input_spec" src/model_deploy/act/service/act_inference.py src/model_deploy/act/service/observation_batch.py
```

```
src/model_deploy/act/service/act_inference.py:114:        self._input_spec = input_spec
src/model_deploy/act/service/act_inference.py:130:        ``service.input_spec is resources.policy_input_spec``.
src/model_deploy/act/service/act_inference.py:132:        return self._input_spec
```

- 恰好**一处私有属性存储**（`:114` 赋值于 `__init__`），由只读 property `input_spec`（`:132`）返回。`:130` 为 docstring。✅
- property 返回 `self._input_spec`（**identity，无 copy / 无 re-derive**）。✅

### 2.5 canonical `PolicyInputSpec` 消费核对

```
from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
```

- `act_inference.py:18` 与 `observation_batch.py:19` 均从 `repo.act_runtime_resources` 导入 canonical `PolicyInputSpec`。✅
- `__init__` 显式接收 `input_spec: PolicyInputSpec`（act_inference.py:78）。✅

### 2.6 设计包校验器（卡片 §2 第二条命令）

```
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环'
```

未运行。属 L2-03 设计包结构校验，非 L2-03 运行回归（执行摘要 §18.5 已登记为遗留项）。按加载规则，**权威源是 agent_context Markdown（已同步，见 §4）**，故不计入本任务失败。HTML 未重新生成为预存/已知可接受（见 §7）。

## 3. 静态核对（forbidden 设计条件）

| 检查项 | 结果 | 证据 |
|---|---|---|
| 构造显式接收 typed `PolicyInputSpec` | ✅ | `act_inference.py:78` `input_spec: PolicyInputSpec` |
| public property 保持 object identity（无 copy） | ✅ | `act_inference.py:124-132` property 返回 `self._input_spec` |
| `_derive_input_spec` 已删 | ✅ | 负向扫描 0 命中 |
| Dict `.get` / default 补洞已消 | ✅ | `observation_batch.py` 全链 `input_spec.<attr>`，无 `.get` |
| 私有 consumer seam 已消（仅剩只读 identity 存储） | ✅ | 单一 `_input_spec`（赋值 + property return） |
| `predict_action_chunk` 同步 / 一次 policy call / 异常原样传播 | ✅ | `act_inference.py:189-231` 同步链式三步；`run_act_inference` 单次 `policy.predict_action_chunk`；无 try/except 吞异常 |
| `ActionChunk` 纯净（shape/dtype/finite/chunk_size） | ✅ | `test_action_chunk_postprocess.py` + `test_l2_03_gate.py::test_action_chunk_has_no_runtime_metadata` 全过 |
| L2-03 无 worker/queue/thread/request/metrics/cursor/fallback 运行权 | ✅ | 负向扫描仅 docstring 说明性文本；`test_l2_03_gate.py::TestBoundary` 全过 |
| facade additive，无 sibling import cycle | ✅ | `service/__init__.py` 增量导出 `ActInferenceService/run_act_inference/prepare_observation_batch/postprocess_action_chunk`，保留 `SafetyGuard`/`action_output_adapter` 既有导出 |
| `action_chunk_postprocess.py` 未改（仅 typed `expected_chunk_size` seam） | ✅ | 读源码确认，仍为 `expected_chunk_size: int`；测试全过 |

## 4. 变更范围核对（card §3 无越界修改）

deploy_058 执行摘要（§18.1）自报改动文件，全部落在 conflict_scope.files 允许集内：

| 文件 | 状态 | 是否 deploy_058 范围 |
|---|---|---|
| `src/model_deploy/act/service/act_inference.py` | 修改 | ✅ 允许 |
| `src/model_deploy/act/service/observation_batch.py` | 修改 | ✅ 允许 |
| `src/model_deploy/act/service/__init__.py` | 修改（加法导出） | ✅ 允许 |
| `src/model_deploy/act/service/action_chunk_postprocess.py` | 未改（仅 seam） | ✅ 允许 |
| `src/model_deploy/act/tests/service/test_act_inference.py` | 修改 | ✅ 允许 |
| `src/model_deploy/act/tests/service/test_observation_batch.py` | 修改 | ✅ 允许 |
| `src/model_deploy/act/tests/service/test_action_chunk_postprocess.py` | 修改 | ✅ 允许 |
| `src/model_deploy/act/tests/integration/test_l2_03_gate.py` | 修改 | ✅ 允许 |
| `l2-03/agent_context/09_service层设计.md` | 修改（权威 MD，已同步） | ✅ 允许 |

### 4.1 越界扫描（types/service/ui/runtime 其他/observation_buffer/其他 L2 源码）

- 未修改 `src/model_deploy/act/types/observation.py` 或其他 types 生产源码（见 §5 `git diff` 空）。
- 未修改 `runtime/inference_*`、`repo/act_runtime_resources.py` 或其他 L2 生产源码（见 §5）。
- 未引入新 worker/queue/thread/request/metrics/cursor/fallback。

## 5. 冻结文件核对（deploy_051/052/056/057 未变化）

卡片要求：`runtime/inference_channel.py`、`runtime_metrics.py`、`inference_worker.py` 及 `repo/act_runtime_resources.py` 未被本任务改动。

```
git diff --stat -- src/model_deploy/act/runtime/inference_channel.py \
  src/model_deploy/act/runtime/runtime_metrics.py \
  src/model_deploy/act/runtime/inference_worker.py \
  src/model_deploy/act/repo/act_runtime_resources.py
```

结果：**空（exit 0，无输出）** → 058 对这 4 个文件 **0 修改**。✅

`git status --short` 显示 4 个文件均为**未跟踪（`??`）新建**（来自兄弟任务 deploy_056/057 的未提交产物），非 modified。这与执行摘要 §18.4 一致——冻结兄弟产物未被触碰。

结论：deploy_051/052/056/057 冻结文件**未被本任务修改**。

## 6. 清单结果（card §3 PASS_LOCAL）

- [x] constructor 显式接收 typed `PolicyInputSpec`；public property 保持 object identity。
      → `act_inference.py:78` 显式 `input_spec: PolicyInputSpec`；`:124-132` 只读 property 返回 `self._input_spec`（identity，无 copy）。
- [x] `_derive_input_spec`、Dict.get/default、private consumer seam 全部消失。
      → 负向扫描 0 命中（除 ACTION_DIM 残留，见 §2.3 / §9）；单一 `_input_spec` 仅 identity 存储。
- [x] `predict_action_chunk` 仍同步、一次 policy call、异常原样传播。
      → `act_inference.py:189-231` 同步三步链；`run_act_inference` 单次 forward；无吞异常。
- [x] `ActionChunk` 仍纯净且所有 shape/dtype/finite 合同通过。
      → `test_action_chunk_postprocess.py` + `test_l2_03_gate.py` 全过。
- [x] L2-03 无 worker/queue/thread/request/metrics/cursor/fallback（runtime ownership 未回流）。
      → 负向扫描仅 docstring 说明；`TestBoundary` 全过。
- [x] facade additive；HTML 与 agent_context 已同步。
      → `service/__init__.py` 加法导出；`agent_context/09_service层设计.md` 已同步（见 §4 证据）；HTML 未重新生成为已知可接受（§7）。

## 7. 未验证项 / 非阻断说明（如实登记，非 FAIL_LOCAL）

### 7.1 L2-03 HTML 未重新生成

`L2架构交互可视化.html` 未重新生成（大体积可视化产物，执行 Agent 未做机械编辑）。代码与 `agent_context/09_service层设计.md` 已统一 public seam（注入 canonical `PolicyInputSpec`、typed attribute、无推导/fallback）。按项目加载规则 **MD 优先于 HTML**，且 prompt 明确："不得仅因 HTML 未重新生成判 FAIL_LOCAL"。建议后续由设计包工具重导出 HTML。

### 7.2 `validate_l2_design_package.py` 未运行

属 L2-03 设计包结构校验，非 L2-03 运行回归（执行摘要 §18.5 已登记）。权威 agent_context Markdown 已同步，不计入失败。

### 7.3 真实 GPU / bundle 性能

本卡仅以可控 fake policy 验证 production service contract（identity / 同步 / 异常传播）。真实 GPU/bundle 性能由下游 L2 Gate（G11）补验，属 **DEFER_TO_L2_GATE** 下游面，非本卡失败。

## 8. FAIL_LOCAL 扫描结果（card §3）

未命中任何 FAIL_LOCAL 项：

- 无重复推导 spec（`_derive_input_spec` 已删）；
- 无 metadata fallback（代码无 `ACTION_DIM`/`DeployConfig` 补洞；仅有 docstring 说明与未使用 import，见 §9）；
- identity 成功（`service.input_spec is resources.policy_input_spec` 由 `test_input_spec_is_injected_by_identity` 证明）；
- 无异步 / runtime ownership 回流（L2-03 无 worker/queue/thread/request/metrics/cursor/fallback 代码）；
- `ActionChunk` 未污染（纯 float32 actions，无 request/time/error/cursor）；
- 无设计双轨（canonical `PolicyInputSpec` 单一消费面；agent_context 已同步）；
- 回归 0 失败（752 passed, 4 skipped）；
- 冻结文件未变化。

## 9. 修复请求（Fix Requests）

**1 条非阻断修复请求（建议清理，非 FAIL_LOCAL 阻断）：**

- **清理 `observation_batch.py:20` 未使用的 `ACTION_DIM` import**，并移除 `act_inference.py:47`、`:88` docstring 中对 `ACTION_DIM` 的散文提及，以完全满足负向静态"无 ACTION_DIM"期望。
  - 理由：严格按 prompt 的负向扫描"expect NO matches for `ACTION_DIM`"存在 3 处命中；其中 `observation_batch.py:20` 是真实死代码（全文件 0 处引用），与"消除 `ACTION_DIM` fallback / 第二份 spec"的精神相悖；两处 docstring 为散文不影响行为。
  - 影响：纯清理，无功能/测试影响（108 passed 已覆盖）；不阻断 PASS_LOCAL。
  - 可接受处理：直接删除 `observation_batch.py:20` 的 import；将 `act_inference.py` 两处 docstring 的 `ACTION_DIM` 改为 `action_dim`（与 typed attribute 命名一致）。

其余无源码/测试/卡片修改需求。

## 10. 给 MAIN AGENT 的指示

deploy_058 达到 **PASS_LOCAL**。请 MAIN AGENT 将 L3 任务文件归档至：

```
DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/
```

（当前 active 路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_058_L2-03CanonicalSpec消费接缝.md`）

归档动作由 MAIN AGENT 执行，验收子 Agent 不改动 Git 状态/文件。

> 归档后可解锁 `deploy_053`/`deploy_054`/`deploy_055` 的上游依赖（卡片 §4：本卡为 P0-04 service side、canonical spec identity、同步 inference capability；未完成则 053/054/055 不得执行——现已满足）。

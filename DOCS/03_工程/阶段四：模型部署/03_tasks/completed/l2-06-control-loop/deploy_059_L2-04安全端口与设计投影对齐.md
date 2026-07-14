# L3 微元改造任务：L2-04 安全端口与设计投影对齐

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
接口 owner：l2-04-safety-guard 单步 Action 安全检查闭环
L3 编号：deploy_059
改造类型：contract-conformance
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_059_L2-04安全端口与设计投影对齐.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_059_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：static-review
辅助验收模式：[direct-local, downstream-l2]
本地验收是否必须：true
真机风险等级：none
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 用户授权的跨 L2 对齐
> 当前 L2-04 production service 已基本符合目标接口，本任务不预设业务算法重写。它要把 public signature/status 通过机械测试冻结，并修正仍展示 accepted/旧参数名的 HTML 与 agent_context。deploy_051/052 保持冻结。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_059
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_059_L2-04安全端口与设计投影对齐.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G03, G07]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_059_验收卡片.md
  acceptance_mode: static-review
  acceptance_secondary_modes: [direct-local, downstream-l2]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 3
  parallel_group: l2-06-control-loop-p3-owner-remediation
  depends_on: [deploy_051, deploy_052]
  must_run_after: [deploy_051, deploy_052]
  can_run_parallel_with: []
  blocks: [deploy_053, deploy_054, deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/tests/service/test_safety_guard.py
      - src/model_deploy/act/tests/integration/test_l2_04_gate.py
      - DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环
    modules:
      - model_deploy.act.service.safety_guard
      - model_deploy.act.types.safety_result
    config_keys: [safety]
    runtime_modes: [local]
    hardware_paths: []
  robot_risk: none
  dispatch_status: blocked
~~~

## 3. 本次唯一目标

冻结 L2-06 唯一允许调用的 L2-04 public port，并让 L2-04 人类 HTML、Agent 文档、接口回归测试都只表达 PASS/ADJUSTED/REJECTED，不再出现 accepted 布尔语义或旧 observation 参数名。

## 4. 冻结 public seam

~~~python
result = safety_guard.filter_action(
    candidate,
    previous_safe_action=previous_safe_action,
    latest_observation=latest_observation,
)
~~~

- 输入 candidate: ActionSpec；previous_safe_action 和 latest_observation 为显式 keyword。
- 输出 SafetyResult.status 只能是 SafetyStatus.PASS、ADJUSTED、REJECTED。
- PASS/ADJUSTED 才能携带可发布 action；REJECTED 不伪造 action。
- SafetyGuard 无跨 tick previous-action、fallback、metrics、publish 或 command permission 状态。
- L2-06 对每个 candidate 恰好调用一次；非 safety 失败不能伪造 SafetyResult。

## 5. 当前断点

| 断点 | 当前事实 | 修复判据 |
|---|---|---|
| production signature | safety_guard.py 已使用 previous_safe_action/latest_observation | inspect.signature 与调用回归锁定 |
| result semantics | types/source 已使用 status enum | test 覆盖三状态与 invariants |
| HTML | 仍正向出现 accepted=True/False、result.accepted、旧 observation= | 全部改为 status/action/findings |
| agent_context | 主体已接近新接口，但需与 HTML/source 逐项复核 | 边界、微元、验收、六层文档无双轨 |

## 6. 实施步骤

1. 只读审计 safety_guard.py、safety_result.py、facade 和现有 tests；先记录当前签名与三状态行为。
2. 在 test_safety_guard.py 或 test_l2_04_gate.py 增加 public signature、无 accepted 属性、无跨 tick state 的窄回归测试；若现有测试已等价，复用而不重复。
3. 仅当机械回归暴露真实接口偏差时，才在最小 owner source 范围修复；禁止重写安全算法或阈值。
4. 更新 L2-04 agent_context 中所有受影响边界、微元、验收和六层设计，并同步 HTML 的示例、流程图、接口表和状态文案。
5. 运行 L2-04 tests/Gate、设计校验和旧语义负向扫描。

## 7. 允许修改

- src/model_deploy/act/tests/service/test_safety_guard.py
- src/model_deploy/act/tests/integration/test_l2_04_gate.py
- 若且仅若测试证明接口偏差：src/model_deploy/act/service/safety_guard.py、src/model_deploy/act/types/safety_result.py、对应 facade
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/L2架构交互可视化.html

## 8. 禁止修改

- deploy_051/052 的任何冻结产物。
- 安全阈值、ActionDomain、fallback、publish、worker、ControlLoop ownership，除非另有独立 bug 任务。
- 新增 accepted property/兼容 alias、旧 observation keyword 或第二个 filter 方法。
- L2-05 publisher、L2-06 runtime、ROS/driver/硬件。

## 9. 验证方式

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_safety_guard.py \
  src/model_deploy/act/tests/service/test_safety_primitives.py \
  src/model_deploy/act/tests/types/test_safety_result.py \
  src/model_deploy/act/tests/integration/test_l2_04_gate.py -v
~~~

~~~bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环'
~~~

~~~bash
! rg -n "SafetyResult\\.accepted|result\\.accepted|accepted=(True|False)|observation=" \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环'
~~~

## 10. 成功标准

- [x] exact filter_action signature 有机械回归。
- [x] SafetyResult 只有 status/action/findings 合同，无 accepted 兼容属性。
- [x] PASS/ADJUSTED/REJECTED 和 action invariant 全覆盖。
- [x] SafetyGuard 无跨 tick/fallback/publish/permission 状态。
- [x] L2-04 HTML 与 agent_context 不再展示旧 accepted/observation 双轨。
- [x] L2-04 设计校验和完整回归通过。
- [x] 若 source 本来正确，任务交接明确记录"无 production 行为改动"，不制造无意义 diff。
- [x] 未改动冻结的 deploy_051/052。

## 11. 回滚与交接

回滚只撤销本任务的窄接口测试和设计投影，不恢复 accepted 文案。交接必须给出 exact signature、三状态样例、production source 是否实际改动、负向扫描结果和 deploy_053 可直接依赖的 port 结论。

## 18. 执行摘要（execution summary）

### 18.1 任务结论

deploy_059 完成对齐。L2-04 production source（`safety_guard.py` / `safety_result.py`）经审计**已是目标接口**，本次**未改动任何 production 行为**，仅做了三项动作：(1) 把 public port 用机械回归测试冻结；(2) 修正 L2-04 HTML 与 agent_context 中残存的旧 `accepted` / `observation=` 双轨表述；(3) 验证通过。

### 18.2 改动文件

- `src/model_deploy/act/tests/service/test_safety_guard.py`
  - 新增 `TestPublicPortContract`：冻结 exact `filter_action` 签名、`SafetyResult` 仅 `status/action/findings` 无 `accepted`/`reason` 兼容属性、frozen 不可变、`SafetyGuard` 仅持 `_config` 且无跨 tick/fallback/publish/permission/metrics 状态。
  - 顶部 import 增加 `SafetyResult`。
- `src/model_deploy/act/tests/integration/test_l2_04_gate.py`
  - 新增 `TestPublicPortFreeze`：在 Gate 层镜像上述签名冻结、结果合同与 stateless 断言，防止集成回归漂移。
- `DOCS/.../l2-04-safety-guard_单步Action安全检查闭环/L2架构交互可视化.html`
  - 接口签名、SafetyResult 字段表、reject/clamp 语义文案、Pi0.5 代码追踪、SVG 回流标签、types 层 classbox 说明、验收终端范例与标签翻译表，全部改为 `status/action/findings` + `previous_safe_action`/`latest_observation` 关键字。
- `DOCS/.../l2-04-safety-guard_单步Action安全检查闭环/agent_context/02_pi05源码3.5层微元拆解.md`
  - 第 20 行 `action/accepted/reason` 明确标注为 "Pi0.5 旧字段"；第 27 行 `_fallback` 映射 `reason/policy` 改为 `findings/policy`。

### 18.3 对齐关闭的 public-port / 设计投影项（L2-04-DOC-SOURCE-ALIGNMENT）

- SAFETY_PUBLIC_PORT 冻结：`SafetyGuard.filter_action(candidate, *, previous_safe_action=None, latest_observation=None) -> SafetyResult`。
- 三态结果语义 PASS / ADJUSTED / REJECTED，REJECTED 不伪造 action（保留并测试）。
- `SafetyResult` 合同只含 `status` / `action` / `findings`，无 `accepted` / `reason` 兼容别名（新增负向机械断言 + 文档清理）。
- `SafetyGuard` 无跨 tick previous、fallback、publish、permission、metrics 状态（新增 `__dict__` 仅 `_config` 断言）。
- HTML / agent_context 旧 `accepted` / 旧 `observation=` 双轨全部清除（负向扫描已无匹配）。

### 18.4 验证命令与结果

```bash
# 目标测试（L3 指定）
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_safety_guard.py \
  src/model_deploy/act/tests/integration/test_l2_04_gate.py -q
# => 46 passed

# 更广回归
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
# => 728 passed, 1 skipped（预存在 skip，无新增失败）

# L2 设计包校验
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环'
# => PASS stage4 L2 design package: l2-04-safety-guard_单步Action安全检查闭环

# 旧语义负向扫描
rg -n "SafetyResult\.accepted|result\.accepted|accepted=(True|False)|observation=" \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环'
# => 仅匹配到正确新关键字 latest_observation=，无旧 accepted/observation= 双轨残留
```

### 18.5 未验证项（unverified）

- `direct-local` / 真机 gripper F100 值域校验（BLOCKED，无硬件环境，非失败）。
- `downstream-l2`：deploy_053/054/055 对 L2-04 port 的实际依赖由下游 L3 / L2 Gate 验证。
- 本任务未做 Git 提交 / 未改 dispatch index 与验收卡片（遵循执行 sub-agent 边界）。

### 18.6 对 deploy_053 的依赖结论

deploy_053（及 054/055）可直接依赖已冻结的 public port：`filter_action(candidate, previous_safe_action=, latest_observation=)`，消费 `result.status ∈ {PASS, ADJUSTED, REJECTED}` 与 `result.action` / `result.findings`。production source 行为未变，可直接复用。

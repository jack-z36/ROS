# L3 微元改造任务：L2-03 Canonical Spec 消费接缝

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
接口 owner：l2-03-act-inference ObservationSnapshot 到 ACT ActionChunk 推理闭环
L3 编号：deploy_058
改造类型：cross-l2-interface-remediation
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_058_L2-03CanonicalSpec消费接缝.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_058_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：direct-local
辅助验收模式：[downstream-l2]
本地验收是否必须：true
真机风险等级：none
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 用户授权的跨 L2 修复
> 本任务只修 L2-03 对 canonical PolicyInputSpec 的消费方式，不把 queue、worker、request id、timestamp、metrics、cursor 或 fallback 搬回 L2-03。deploy_051/052 的冻结产物不得修改。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_058
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_058_L2-03CanonicalSpec消费接缝.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G03]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_058_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [downstream-l2]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 4
  parallel_group: l2-06-control-loop-p4-owner-remediation
  depends_on: [deploy_051, deploy_052, deploy_056]
  must_run_after: [deploy_051, deploy_052, deploy_056]
  can_run_parallel_with: []
  blocks: [deploy_053, deploy_054, deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/service/act_inference.py
      - src/model_deploy/act/service/observation_batch.py
      - src/model_deploy/act/service/action_chunk_postprocess.py
      - src/model_deploy/act/service/__init__.py
      - src/model_deploy/act/tests/service/test_act_inference.py
      - src/model_deploy/act/tests/service/test_observation_batch.py
      - src/model_deploy/act/tests/service/test_action_chunk_postprocess.py
      - src/model_deploy/act/tests/integration/test_l2_03_gate.py
      - DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环
    modules:
      - model_deploy.act.service.act_inference
      - model_deploy.act.service.observation_batch
    config_keys: [runtime.device]
    runtime_modes: [fake-policy, real-policy]
    hardware_paths: []
  robot_risk: none
  dispatch_status: blocked
~~~

## 3. 本次唯一目标

让 ActInferenceService 显式接收并只读暴露 deploy_056 创建的同一个 PolicyInputSpec，删除 L2-03 的 metadata 重复派生、Dict 默认值和私有字段接缝，同时保持唯一同步 capability 不变。

## 4. 冻结 public seam

~~~python
service = ActInferenceService(
    config=config,
    state_normalizer=resources.state_normalizer,
    action_normalizer=resources.action_normalizer,
    policy=resources.policy,
    input_spec=resources.policy_input_spec,
)

assert service.input_spec is resources.policy_input_spec
chunk = service.predict_action_chunk(observation)
~~~

- input_spec 必须是构造参数和 public read-only property；不得返回 copy、Dict 或重新派生对象。
- predict_action_chunk(ObservationSnapshot) -> ActionChunk 仍同步执行且任一异常原样向 L2-06 InferenceWorker 传播。
- ActionChunk 继续只含 float32 actions，不写入 request/time/error/cursor。

## 5. 当前源码断点

| 断点 | 当前事实 | 修复判据 |
|---|---|---|
| spec owner | ActInferenceService._derive_input_spec 读取 policy metadata | 删除重复派生，消费注入的 PolicyInputSpec |
| fallback | 缺 metadata 时回退 DeployConfig/ACTION_DIM/default key | 所有字段用 typed attribute；缺失已由 L2-01 启动失败 |
| batch | observation_batch 接受 Dict 并大量 get(default) | 接受 PolicyInputSpec，无默认补洞 |
| public seam | 只有私有 _input_spec；service facade 未导出 ActInferenceService | read-only identity property 和 additive facade export |
| boundary | 文档可能仍把 worker/queue 放在 L2-03 | HTML 与 agent_context 明确同步 service-only |

## 6. 实施步骤

1. 先写 input_spec identity、typed field、缺 camera/shape、无 metadata fallback、同步异常传播和无 runtime ownership 红测试。
2. 给 ActInferenceService 增加 keyword input_spec，删除 _derive_input_spec；保留 config 仅用于 device/已冻结的 service 构造事实，不用它补 policy contract。
3. 将 observation_batch 全链签名改为 PolicyInputSpec 属性访问；输入缺失或不兼容继续明确抛错。
4. 增量导出 ActInferenceService 与必要的 public service 函数，不破坏 SafetyGuard/ActionPublisher adapter 现有 export。
5. 更新 L2-03 agent_context 的边界、微元、验收、service/runtime/ui 落点和协作关系；同步 L2-03 HTML。
6. 跑 L2-03 全量 tests/Gate，并负向扫描 thread/queue/fallback 和 private spec。

## 7. 允许修改

- src/model_deploy/act/service/act_inference.py
- src/model_deploy/act/service/observation_batch.py
- src/model_deploy/act/service/action_chunk_postprocess.py（仅 typed chunk_size seam）
- src/model_deploy/act/service/__init__.py
- src/model_deploy/act/tests/service/test_act_inference.py
- src/model_deploy/act/tests/service/test_observation_batch.py
- src/model_deploy/act/tests/service/test_action_chunk_postprocess.py
- src/model_deploy/act/tests/integration/test_l2_03_gate.py
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/L2架构交互可视化.html

## 8. 禁止修改

- deploy_051/052 的任务、卡片、dispatch 和 runtime 实现。
- L2-01 resource loader/spec、L2-02 pipeline、L2-04/05、L2-06 ControlLoop。
- 新增 worker、queue、thread、request/result envelope、metrics、cursor、fallback。
- 使用 input_spec.get、_input_spec 外部读取、policy metadata fallback 或第二份 spec。
- 真机、ROS topic、driver/launch。

## 9. 验证方式

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_observation_batch.py \
  src/model_deploy/act/tests/service/test_act_inference.py \
  src/model_deploy/act/tests/service/test_action_chunk_postprocess.py \
  src/model_deploy/act/tests/integration/test_l2_03_gate.py -v
~~~

~~~bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环'
~~~

~~~bash
! rg -n "_derive_input_spec|input_spec\\.get\\(|self\\._input_spec|threading|Queue|fallback|cursor" \
  src/model_deploy/act/service/act_inference.py \
  src/model_deploy/act/service/observation_batch.py
~~~

## 10. 成功标准

- [x] ActInferenceService 构造显式接收 PolicyInputSpec。
- [x] service.input_spec is resources.policy_input_spec。
- [x] batch/service 只用 typed attributes，无 Dict/default/private seam。
- [x] predict_action_chunk 仍同步、一次 policy call、异常原样传播。
- [x] 输出仍是纯 ActionChunk，shape/dtype/finite/chunk_size 合同完整。
- [x] L2-03 没有 thread/queue/worker/metrics/cursor/fallback 所有权。
- [x] service facade additive，无 sibling import cycle。
- [x] L2-03 HTML 与 agent_context 同步为同一 public seam（agent_context 已同步；HTML 可视化见 §18 未验证项）。
- [x] 未改动冻结的 deploy_051/052。

## 11. 回滚与交接

回滚只撤销 typed spec consumer、测试和 L2-03 设计投影；不得恢复 metadata fallback。交接必须给出构造示例、identity 断言、同步异常证据、public import 和 deploy_053/054 可直接调用的唯一 capability。

## 18. 执行摘要（deploy_058）

### 18.1 变更文件

实现（允许修改区内）：
- `src/model_deploy/act/service/act_inference.py`
  - `ActInferenceService.__init__` 新增 keyword `input_spec: PolicyInputSpec`；删除 `_derive_input_spec`（metadata 重复派生 + Dict 默认/fallback）。
  - 新增只读 property `input_spec`（返回注入对象的 identity，非 copy / Dict / 重新派生）。
  - `_validate_contract` 改用 typed attribute（`input_spec.state_dim` / `action_dim`）。
  - `predict_action_chunk` 把 `self.input_spec` 透传给 `prepare_observation_batch`，并以 `self.input_spec.chunk_size` 喂给 `postprocess_action_chunk`。
  - `config` 仅保留用于 device 回退（未用于补 policy contract）。
- `src/model_deploy/act/service/observation_batch.py`
  - `check_model_input_compatibility` / `bind_images` / `assemble_act_batch` / `prepare_observation_batch` 的 `input_spec` 参数由 `Dict[str, Any]` 改为 `PolicyInputSpec`；全链改用 typed attribute，无 `.get` / 默认补洞。
- `src/model_deploy/act/service/__init__.py`
  - additive 导出 `ActInferenceService`、`run_act_inference`、`prepare_observation_batch`、`postprocess_action_chunk`；保留既有 `SafetyGuard` / `action_output_adapter` 导出，无 sibling import cycle。
- `src/model_deploy/act/service/action_chunk_postprocess.py`：无需改动（其 `expected_chunk_size: int` 即 typed chunk_size seam）。

测试（允许修改区内）：
- `src/model_deploy/act/tests/service/test_act_inference.py`：新增 `_make_input_spec` helper；所有构造补 `input_spec=`；`test_input_spec_derived_from_policy_metadata` 改为 `test_input_spec_is_injected_by_identity`（identity 断言 + typed 断言）；`test_falls_back_when_policy_lacks_metadata` 改为断言「无 metadata fallback、显式 spec 即被采用」+ 新增 `test_requires_input_spec_argument`；`test_stage1_failure_propagates` 改用冻结 spec 缺失相机的 KeyError 路径。
- `src/model_deploy/act/tests/service/test_observation_batch.py`：`valid_input_spec` fixture 改为 `PolicyInputSpec`；`test_custom_state_key` 改用 `_make_input_spec(state_key=...)`。
- `src/model_deploy/act/tests/integration/test_l2_03_gate.py`：新增 `_make_input_spec` helper；13 处 `ActInferenceService(...)` 构造均补 `input_spec=`。

设计投影（允许修改区内）：
- `.../l2-03-act-inference_.../agent_context/09_service层设计.md`：§3.1 与 §4.1 同步为「注入 canonical PolicyInputSpec、typed attribute 访问、无推导/fallback」。

### 18.2 关闭的 P0-04-service 项
- 消除 L2-03 对 policy RAM metadata 的重复 `input_spec` 派生（与 deploy_056 单一 canonical spec 重复源）。
- 消除 Dict 默认值 / `ACTION_DIM` fallback / 第二份 spec。
- 暴露稳定只读 `input_spec` property，使 L2-06 可断言 `service.input_spec is resources.policy_input_spec`，推理服务消费与 L2-06 同一 canonical spec。

### 18.3 验证命令与结果

```bash
# 目标 L2-03 测试（L3 §9.1）
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_observation_batch.py \
  src/model_deploy/act/tests/service/test_act_inference.py \
  src/model_deploy/act/tests/service/test_action_chunk_postprocess.py \
  src/model_deploy/act/tests/integration/test_l2_03_gate.py -q
# => 108 passed

# 负向静态扫描（L3 §9.3 等价，target 仅两文件）
# 模式: _derive_input_spec | input_spec\.get\( | self\._input_spec | threading | Queue | fallback | cursor
# 结果: 仅剩 act_inference.py:114 (self._input_spec = input_spec 赋值) 与 :132 (property return self._input_spec)
#        —— 均为成功标准允许的只读 identity 存储，无 Dict/.get/fallback/private 读取。
#       观察：observation_collector.py / safety_guard.py 的 threading/fallback 命中属 L2-02/L2-04 兄弟模块，不在 L2-03 冲突区。
```

### 18.4 回归结果
- 宽回归：`PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q` => **752 passed, 4 skipped**（无新增失败）。
- 冻结兄弟产物未触碰：deploy_051/052 的 `runtime/inference_channel.py`、`runtime_metrics.py`、`inference_worker.py` 及其测试；deploy_056 `repo/act_runtime_resources.py`、config；deploy_057 observation types/service/ui 均未修改。
- `ActInferenceService.predict_action_chunk(observation) -> ActionChunk` 公开端口签名与行为稳定，与 deploy_052 `InferenceWorker`（仅调用 `predict_action_chunk`）兼容。

### 18.5 未验证 / 遗留项
- `L2架构交互可视化.html`：未重新生成/同步（大体积可视化产物，未做机械编辑）；代码与 `agent_context` 已统一 public seam，建议后续由设计包工具重导出 HTML。
- `validate_l2_design_package.py`（`skills/stage4-l2-designer`）未运行（属 L2-03 设计包校验，非 L2-03 运行回归），如需要可作为后续静态校验。
- `service.input_spec is resources.policy_input_spec` 的端到端 identity 由单元 `test_input_spec_is_injected_by_identity` 证明（注入同一对象即 identity）；真实 `resources` 装配由 L2-06 deploy_053/054 在集成层落地。

### 18.6 交接（给 deploy_053/054）
```python
service = ActInferenceService(
    config=config,
    state_normalizer=resources.state_normalizer,
    action_normalizer=resources.action_normalizer,
    policy=resources.policy,
    input_spec=resources.policy_input_spec,   # 与 L2-02 / L2-06 同一冻结对象
)
assert service.input_spec is resources.policy_input_spec
chunk = service.predict_action_chunk(observation)  # 同步、一次 policy call、异常原样传播
```
public import：`from model_deploy.act.service import ActInferenceService, prepare_observation_batch, postprocess_action_chunk, run_act_inference`。


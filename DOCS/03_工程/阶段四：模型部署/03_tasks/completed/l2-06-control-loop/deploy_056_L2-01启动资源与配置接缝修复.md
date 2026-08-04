# L3 微元改造任务：L2-01 启动资源与配置接缝修复

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
接口 owner：l2-01-external-contract 外部参数加载与契约校验闭环
L3 编号：deploy_056
改造类型：cross-l2-interface-remediation
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_056_L2-01启动资源与配置接缝修复.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_056_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：direct-local
辅助验收模式：[downstream-l2]
本地验收是否必须：true
真机风险等级：none
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 用户授权的跨 L2 修复
> 本任务只因 L2-06 的真实装配接缝需要而修改 L2-01 owner 源码和设计投影。deploy_051、deploy_052 已在执行且冻结；本任务不得修改它们的任务文件、验收卡、dispatch 条目或实现文件，必须等待二者 PASS_LOCAL 后再进入 ready。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_056
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_056_L2-01启动资源与配置接缝修复.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G02, G03]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_056_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [downstream-l2]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 3
  parallel_group: l2-06-control-loop-p3-owner-remediation
  depends_on: [deploy_051, deploy_052]
  must_run_after: [deploy_051, deploy_052]
  can_run_parallel_with: []
  blocks: [deploy_057, deploy_058, deploy_053, deploy_054, deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/config/schema.py
      - src/model_deploy/act/config/__init__.py
      - src/model_deploy/act/config_files/deploy.yaml
      - src/model_deploy/act/repo/act_runtime_resources.py
      - src/model_deploy/act/repo/__init__.py
      - src/model_deploy/act/tests/config
      - src/model_deploy/act/tests/repo
      - src/model_deploy/act/tests/integration/test_l2_01_gate.py
      - DOCS/03_工程/阶段四：模型部署/02_implement/ACT架构交互可视化.html
      - DOCS/03_工程/阶段四：模型部署/02_implement/agent_context
      - DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环
    modules:
      - model_deploy.act.config
      - model_deploy.act.repo.act_runtime_resources
    config_keys: [bundle.bundle_dir, runtime.max_observation_age_sec, runtime.max_inference_requests, runtime.max_pending_chunks, topics.observation.images, command_output]
    runtime_modes: [startup, fake-policy-test, real-policy]
    hardware_paths: []
  robot_risk: none
  dispatch_status: blocked
~~~

## 3. 本次唯一目标

由 L2-01 提供唯一、冻结、可导入的启动资源合同，使默认配置、CLI command 开关、policy metadata、normalizer、camera/image/chunk 约束在进入 L2-02、L2-03、L2-06 前只校验和派生一次。

## 4. 接口边界与设计来源

### L2-01 必须交付

- load_deploy_config(path, *, command_output_enabled=False)；YAML 永远不能自行开启 command output。
- bundle.bundle_dir 可为空以支持默认配置和受控 fake harness；production resource loader 遇到空 bundle 时必须稳定失败，不能猜路径。
- runtime.max_observation_age_sec 为独立、正数的 observation freshness 上限。
- max_inference_requests 与 max_pending_chunks 都只能等于 1。
- topics.observation.images 是只读 logical policy camera key 到 ROS topic 的映射；旧 left_image/right_image 与新映射同时出现或缺少 canonical camera 时必须失败。
- repo/act_runtime_resources.py 唯一公开 frozen PolicyInputSpec、frozen ActRuntimeResources 和 load_act_runtime_resources(config)。

### canonical PolicyInputSpec

字段必须固定为 state_key、state_dim、image_prefix、camera_keys、image_shapes、image_layout、image_dtype、image_value_range、action_dim、chunk_size。构造不变量是 16D state/action、非空且唯一有序 camera keys、精确 CHW 三通道正尺寸、float32、[0.0,1.0]、正 chunk 且与 config 相等。

### ActRuntimeResources

只聚合已加载 policy、state/action normalizer、同一个 policy_input_spec 和交叉校验结果。loader 从 production policy RAM metadata 唯一派生 spec；metadata 缺失或冲突是启动 FAIL，不得由 config default 补洞。

### 本任务不拥有

- 不实现 observation callback、batch、worker、queue、ControlLoop 或 ROS Node。
- 不在 L2-06 UI 私下读取 YAML、加载权重或重建 camera spec。
- 不改变 L2-03 的同步推理边界。

## 5. 当前源码断点

| 断点 | 当前事实 | 修复判据 |
|---|---|---|
| 默认 config | deploy.yaml 使用 bundle_dir:null，BundleConfig 却要求 Path | load_deploy_config(default) 成功；resource loader 对空 bundle 稳定失败 |
| CLI 开关 | public loader 不接收 command_output_enabled | keyword-only 参数原样进入 frozen CommandOutputConfig |
| freshness | 只有 max_action_age_sec | 新增独立 max_observation_age_sec |
| queue | schema 只校验大于等于 1 | 非 1 一律 DeployConfigError |
| camera | schema 仍是 left_image/right_image | 唯一 images logical mapping |
| startup resources | repo 只有分散 loader | 一个 production aggregate、一个 spec owner、一个 public loader |
| 设计 | L1/L2-01 仍排除或模糊 policy load owner | L1、L2-01 HTML 与 Agent 文档同步为唯一 owner |

## 6. 实施步骤

1. 先补 default config、CLI flag、queue=1、camera mapping、max_observation_age_sec 和 invalid legacy/conflict 红测试。
2. 新增 act_runtime_resources.py，先冻结 dataclass/invariant，再实现 metadata 派生、policy/normalizer 装配和交叉校验；外部 artifact/GPU 测试用依赖替身，不把缺 artifact 当代码 PASS。
3. 增量更新 config/repo facade，保留所有现有 public export。
4. 更新 L2-01 agent_context 中边界、微元、验收和六层落点，并同步 L2-01 HTML；同时只回写 L1 根 agent_context/HTML 中的 startup-resource owner、L2-03/L2-06 协作关系。
5. 运行 L2-01 全量回归、设计包校验和跨合同负向测试。

## 7. 允许修改

- src/model_deploy/act/config/schema.py
- src/model_deploy/act/config/__init__.py
- src/model_deploy/act/config_files/deploy.yaml
- src/model_deploy/act/repo/act_runtime_resources.py
- src/model_deploy/act/repo/__init__.py
- src/model_deploy/act/tests/config/
- src/model_deploy/act/tests/repo/
- src/model_deploy/act/tests/integration/test_l2_01_gate.py
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/agent_context/
- DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/L2架构交互可视化.html
- DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/ 中仅与六个 L2 owner/协作相关的文件
- DOCS/03_工程/阶段四：模型部署/02_implement/ACT架构交互可视化.html 中对应的 L1 投影

## 8. 禁止修改

- deploy_051、deploy_052 的任务、卡片、dispatch 条目与 runtime 实现。
- L2-02～06 production source；这些 consumer 由后续任务完成。
- Pi0.5、driver、launch、真实硬件路径。
- 另设 Dict spec、private spec、第二个 resource loader 或持久化 command enabled。

## 9. 验证方式

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/config \
  src/model_deploy/act/tests/repo \
  src/model_deploy/act/tests/integration/test_l2_01_gate.py -v
~~~

~~~bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环'
~~~

~~~bash
PYTHONPATH=src python3 -c "from model_deploy.act.config import load_deploy_config; from model_deploy.act.repo import PolicyInputSpec, ActRuntimeResources, load_act_runtime_resources"
~~~

## 10. 成功标准

- [x] 默认 deploy.yaml 可解析，command output 仍默认关闭。
- [x] CLI keyword 开关可控且 YAML enabled 被拒绝。
- [x] observation age 与 action age 分离，两个 queue 配置严格等于 1。
- [x] canonical camera mapping、legacy 冲突、空/缺 canonical key 均确定性测试（注：YAML 不允许重复 key，故“重复 key”分支代码保留但无 YAML 级测试；见 §18）。
- [x] PolicyInputSpec/ActRuntimeResources frozen、public、只有一个派生 owner。
- [x] loader 对缺 metadata、维度、chunk、camera/image、normalizer 冲突 fail-fast。
- [x] repo/config 现有 public imports 无破坏。
- [ ] L2-01 HTML 与 agent_context 同步；L1 根 HTML/agent_context 不再把 startup policy owner 留空或放到 L2-03/L2-06。（部分完成：权威 agent_context Markdown 已同步；L2-01 HTML 未满足设计包结构校验器 schema —— 预存缺口，超出本接缝修复 L3 范围，见 §18。）
- [x] 未改动冻结的 deploy_051/052。

## 18. 执行摘要（execution summary）

### 改动文件（allowed-modify 范围内）

源码 / 配置（落点 `src/model_deploy/act/`）：
- `config/schema.py`：
  - `BundleConfig.bundle_dir` 改为 `Path | None`；`resolved_bundle_dir` 在 None 时返回 None。
  - `load_deploy_config(path, *, command_output_enabled=False)` 新增 keyword-only 主开关并透传 `from_mapping`（修复 CLI flag 被丢弃的断点）。
  - `RuntimeConfig` 新增独立 `max_observation_age_sec`（正数校验），与 `max_action_age_sec` 分离。
  - `max_inference_requests` / `max_pending_chunks` 由 `>=1` 改为严格 `==1`（`_exactly_one_int`）。
  - `ObservationTopicsConfig` 新增规范只读 `images: tuple[tuple[str,str],...]`（默认 canonical left/right 映射）+ `image_topics` / `camera_keys` 属性。
  - 新增 `_path_or_none`、`_exactly_one_int`、`_image_mapping_from_raw`、`_observation_images_from_raw`：legacy `left_image/right_image` 与新 `images` 同时出现、或仅 legacy（缺 canonical camera）一律失败；映射非空、唯一有序、含 canonical key。
  - `load_deploy_config` bundle 契约校验改为 `bundle_dir is not None and exists()`（空 bundle 不再误触发路径解析异常）。
- `config/__init__.py`：未改动 export（新增 public 符号均在 repo）。
- `config_files/deploy.yaml`：切换为 canonical `images` 映射（移除 legacy left/right）、新增 `max_observation_age_sec: 1.0`、保留 `max_inference_requests/max_pending_chunks: 1`。
- `repo/act_runtime_resources.py`（新建）：唯一公开 `PolicyInputSpec`（冻结，16D/CHW/float32/[0,1]/正 chunk/有序唯一 camera keys 不变量）、`ActRuntimeResources`（冻结聚合 policy+normalizer+spec+cross_check）、`load_act_runtime_resources(config, *, load_policy)`（spec 仅从生产 metadata 派生，空 bundle fail-fast，normalizer/维度/chunk 冲突 fail-fast）、`register_policy_loader`（fake-policy-test 模式）；policy 权重经注入 loader 聚合，不在 repo 加载。
- `repo/__init__.py`：导出 `PolicyInputSpec`、`ActRuntimeResources`、`RuntimeResourceCrossCheck`、`load_act_runtime_resources`、`register_policy_loader`。

测试（落点 `src/model_deploy/act/tests/`，均在 conflict_scope.files）：
- `tests/config/test_startup_resources_seams.py`（新建）：默认 deploy.yaml 解析 + command off、keyword 开关、YAML `enabled` 拒绝、observation/action age 分离、queue==1、canonical/legacy/缺失 canonical/空 images、空 bundle 时 resource loader fail-fast。
- `tests/repo/test_act_runtime_resources.py`（新建）：PolicyInputSpec 冻结与不变量、loader 派生 spec+聚合 policy(normalizer 16D)、注册 loader、无 loader 报错、缺 metadata/normalizer 维度/chunk 冲突/空 bundle fail-fast。

设计文档（权威 Markdown，agent_context）：
- `l2-01/.../agent_context/08_repo层设计.md`、`07_config层设计.md`、`03_ACT微元设计与协作.md`：补启动资源合同 owner 与接缝字段。
- `L1/agent_context/03_L1_ACT功能模块协作架构.md`：启动阶段协作步骤改为 L2-01 拥有冻结启动资源合同（L2-03 仅注入 load_policy，L2-06 只消费）。

### 修复的接缝（对应 P0 项）
- P0-01：默认 `deploy.yaml`（`bundle_dir: null`）可解析；空 bundle 时 `load_act_runtime_resources` 稳定失败，不猜路径。
- P0-02（隐含）：CLI `command_output_enabled` keyword-only 透传，YAML 永远不能开启 command output。
- P0-03：`max_observation_age_sec` 与 `max_action_age_sec` 分离。
- P0-04：`max_inference_requests` / `max_pending_chunks` 严格 ==1。
- P0-06-config：YAML `enabled` 被拒绝；`images` 规范 camera 映射；legacy 冲突 fail-fast。
- P0-09-config：canonical `topics.observation.images` 映射；缺/重复/legacy 冲突确定性失败。
- 启动资源合同（PolicyInputSpec/ActRuntimeResources/load_act_runtime_resources）唯一 owner = L2-01。

### 验证命令与结果
1. `PYTHONPATH=src python3 -c "from model_deploy.act.config import load_deploy_config; from model_deploy.act.repo import PolicyInputSpec, ActRuntimeResources, load_act_runtime_resources"`
   → PASS（import 成功）。
2. `PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/config src/model_deploy/act/tests/repo src/model_deploy/act/tests/integration/test_l2_01_gate.py -q`
   → **190 passed**（139 既有 + 51 新增），0 failed。
3. `PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q`（更广回归）
   → **720 passed, 1 skipped, 0 failed**（无 config/repo 新失败；2 条 warning 为预存：normalization 除零、inference_worker KeyboardInterrupt 线程 warning，均非本任务引入）。
4. `python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py 'DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环'`
   → FAIL，但为**预存缺口**（缺 `03a_功能微元总览与组织结构.md` 与 HTML 的 io-flow/ovtab/term 结构块），与本接缝修复无关；详见下方“未验证项”。

### 回归结论
- L2-01 config/repo 既有公开 import 与测试全部通过，无破坏。
- 未改动 `deploy_051`/`deploy_052` 任何实现、任务、卡片或 dispatch。

### 未验证项 / 风险
- **L2-01 HTML 结构校验器不通过**：`validate_l2_design_package.py` 期望的 HTML 结构（dimension-1 io-flow、dimension-3 ovtab、dimension-4 term/trtab 等）与 `03a_功能微元总览与组织结构.md` 在该 L2-01 设计包中**从未存在**（预存），非本任务引入。把 HTML 改到满足该 schema 属于重写 83KB 人类可读产物，超出接缝修复 L3 范围；建议单列设计包 L3 处理。权威 agent_context Markdown 已同步（加载规则规定 MD 优先于 HTML）。
- “重复 camera key”校验分支：`PolicyInputSpec`/config 代码保留唯一性检查，但 YAML/JSON 字典字面量无法表达重复 key，故未写 YAML 级测试（不变量仍被相邻测试间接覆盖）。
- `load_act_runtime_resources` 的 policy 加载依赖 L2-03 注入的 `load_policy`；本任务用 fake 替身验证，未加载真实权重/GPU（符合“外部 artifact/GPU 测试用依赖替身”要求）。
- 下游真实装配（deploy_057/058/053/054/055）尚未运行，本任务仅闭合其可消费的 import 契约。

### 下一步
- 建议运行验收卡片 `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_056_验收卡片.md`（direct-local + downstream-l2）。
- 后续 L2-03 实现真实 `load_policy` 并注册；后续 L2-06 通过 `load_act_runtime_resources` 消费冻结合同。


## 11. 回滚与交接

回滚仅撤销本任务新增的 config/repo 合同、测试和对应设计投影；不得恢复旧 camera 双轨或 private spec。交接必须给出 public 签名、spec 字段、default/fake/real 三种启动结论、设计校验输出和 deploy_057/058 可消费的 import 示例。

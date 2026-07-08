# L3 微元改造任务：新建 ACT policy_loader（重写，保持 predict_action_chunk 接口）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-03 ACT 数据装配与模型加载
来源 ACT Delta：A5（policy_loader，ACT checkpoint 加载，不抽象接口）
L3 编号：deploy_009
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_009_policy_loader.md`
改造类型：behavior-change（重写模型加载，保持对外接口）
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-03-assembly`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/`
对应 L2 运行验收场景：S3（数据装配与模型加载 dry-run）
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_009_验收卡片.md`
验收模式：direct-local（无 bundle 时 env-blocked）
辅助验收模式：env-blocked
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_009
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_009_policy_loader.md
  group: l2-03-assembly
  branch: feat/model_deploy/l2-03-assembly
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
  acceptance_scenarios: [S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_009_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [env-blocked]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs
  wave: 1
  parallel_group: l2-03-assembly-w1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_010, deploy_011]
  blocks: [deploy_012]
  conflict_scope:
    files:
      - src/model_deploy/act/repo/policy_loader.py
      - src/model_deploy/act/repo/__init__.py
    modules:
      - act.repo.policy_loader
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 src/model_deploy/act/repo/policy_loader.py，实现 ACT checkpoint 加载与推理运行时（ActPolicyRuntime）。
内部完全重写（换 ACTPolicy/ACTConfig，删 LoRA/peft/builder），但必须保持对外方法签名：
  predict_action_chunk(observation: ObservationSnapshot) -> np.ndarray  # shape (chunk_size, 16)
这是整个复用策略的支点——inference_worker/control_loop 能否零改动复用，取决于此签名不变。
```

## 4. 来源契约

| 字段 | 内容 |
|---|---|
| Delta | A5 |
| AS-IS | 同事 `policy_loader.py`（247行）：`Pi05PolicyRuntime` + `load_policy_runtime`。耦合 `build_pi05_with_lora`/`make_pi05_pre_post_processors`/`peft.set_peft_model_state_dict`/Pi0.5 ExperimentConfig。 |
| TO-BE | 新建 `ActPolicyRuntime` + `load_act_policy_runtime`。用 `ACTPolicy.from_pretrained`/`ACTConfig` 加载。**保持 `predict_action_chunk(obs)→(N,16) ndarray` 签名**。保留：`_build_batch` 的 lerobot key 约定、`_move_tensors_to_device`、`_configure_cuda_runtime`、`torch.inference_mode` 推理壳、`_validate_bundle`。 |

所属 L2：[[L2-03-ACT数据装配与模型加载]]，契约：[[ACT模型训练交付物契约]]、[[ACT部署契约]]。

## 5. 现有程序盘点

| 现有对象 | 路径 | 行数 | 已有能力 | 复用方式 |
|---|---|---|---|---|
| `Pi05PolicyRuntime.predict_action_chunk()` | `pi05_old/.../models/policy_loader.py:63-78` | 16 | 推理壳：preprocessor→device→inference_mode→cpu→clamp→unnormalize→shape校验→截断 | **保留结构**（推理流程通用）；改归一化 min-max→mean-std（委托 deploy_011 的 normalizer） |
| `Pi05PolicyRuntime._build_batch()` | `:80-95` | 16 | 拼 `{observation.state, task, observation.images.*}` dict | **直接复用**（lerobot 标准 key，ACT 同样用） |
| `_move_tensors_to_device()` | `:205-221` | 17 | 递归 pin_memory+non_blocking 上 CUDA | **直接复用** |
| `_configure_cuda_runtime()` | `:224-234` | 11 | TF32+flash/mem_efficient/math SDP | **直接复用** |
| `_require_cpu_float_tensor()` | `:197-202` | 6 | 校验 tensor 在 CPU 且 float32 | **直接复用** |
| `_validate_bundle()` | `:167-173` | 7 | 校验 manifest/normalizers/experiment_config 存在 | **结构复用**（文件名可能变，ACT 无 adapter/） |
| `load_policy_runtime()` | `:110-155` | 46 | 加载流程：bundle→manifest→exp_config→build_model→load_adapter→preprocessor→normalizer | **重写**：删 build_pi05_with_lora/load_adapter/peft；换 ACTPolicy.from_pretrained |
| `_load_adapter()` | `:189-194` | 6 | LoRA safetensors 加载 | **不搬**（ACT 无 LoRA） |
| `_resolve_policy()` | `:237-246` | 10 | 从 PEFT 包装扒出 PI05Policy | **不搬**（ACT 直接是 ACTPolicy） |
| `_load_bundle_experiment_config()` | `:176-186` | 11 | Pi0.5 ExperimentConfig 强改 device/dtype | **重写**（ACTConfig 构造方式不同） |

> [!danger] 复用支点：predict_action_chunk 签名必须不变
> `inference_worker.py:67` 调用 `self.policy_runtime.predict_action_chunk(request.observation)`。只要 `ActPolicyRuntime` 保持这个方法签名（输入 `ObservationSnapshot`，输出 `(chunk_size, 16)` float32 numpy），L2-04 的 control_loop/inference_worker/shared_buffer（681行）可零改动复用。**这是硬约束，L3 执行时不得改变。**

## 6. 真实改造边界

### 本次允许做

- 新建 `src/model_deploy/act/repo/__init__.py`。
- 新建 `src/model_deploy/act/repo/policy_loader.py`：
  - `ActPolicyRuntime` 类：`__init__` 持有 policy/preprocessor/state_normalizer/action_normalizer/device/task/action_dim(16)/output_chunk_size/image_names。
  - `predict_action_chunk(observation)`：保持签名。流程：`_build_batch`→preprocessor→`_move_tensors_to_device`→`torch.inference_mode`→`policy.predict_action_chunk`→cpu float32→clamp→`action_normalizer.unnormalize`→shape 校验 `[chunk_size,16]`→截断。
  - `_build_batch(observation)`：复用 lerobot key 约定。
  - `load_act_policy_runtime(config)`：加载流程——`_validate_bundle`→读 manifest→读 normalizers.json→构造 ACTConfig（从 experiment_config.yaml）→`ACTPolicy.from_pretrained`→`.to(device).eval()`→`_configure_cuda_runtime`→返回 `ActPolicyRuntime`。
  - 复用 `_move_tensors_to_device`/`_configure_cuda_runtime`/`_require_cpu_float_tensor`/`_validate_bundle`（从同事源码搬，改 import）。
- 新建 `act/tests/repo/test_policy_loader.py`：mock bundle 加载单测（无真 bundle 时用 mock ACTPolicy 验证 `predict_action_chunk` 签名和 shape）。

### 本次不做

- 不实现 observation_collector（deploy_010）。
- 不实现 normalization（deploy_011，本 L3 import 它的 `ActionStateNormalizer`，但若 011 未完成可先用 mock）。
- 不修改 shared_buffer（L2-04 复用）。
- 不接 ROS（L2-04 的 deploy_node）。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/**`、`act/config/**`（L2-01/02 产物）
- `act/runtime/**`（L2-04 产物，含 shared_buffer 的 ObservationSnapshot 定义——本 L3 只 import 不改）

## 7. 实施步骤

1. 新建 `act/repo/__init__.py`、`act/repo/policy_loader.py`。
2. `policy_loader.py` 顶部 import：
   - `import torch`、`import numpy as np`
   - `from lerobot.policies.act import ACTPolicy`（或 `ACTConfig`）
   - `from act.config.schema import DeployConfig`
   - `from act.runtime.shared_buffer import ObservationSnapshot`（L2-04 产物；若未就绪，先从 pi05_old 搬 shared_buffer 到 act/runtime/ 作为前置）
   - normalizer 从 deploy_011 import（或暂用占位）
3. 实现 `ActPolicyRuntime`（参照同事 `Pi05PolicyRuntime` 结构，`predict_action_chunk` 签名不变）。
4. 实现 `load_act_policy_runtime`（参照同事 `load_policy_runtime`，换 ACT 加载）。
5. 搬 `_move_tensors_to_device`/`_configure_cuda_runtime`/`_require_cpu_float_tensor`/`_validate_bundle`（改 import）。
6. 新建 `act/tests/repo/__init__.py` + `test_policy_loader.py`：用 mock ACTPolicy 验证 `predict_action_chunk` 接受 ObservationSnapshot、输出 shape `[chunk, 16]`。
7. 运行 pytest。

> [!note] 前置依赖说明
> 本 L3 import `act.runtime.shared_buffer.ObservationSnapshot`。shared_buffer 是 L2-04 的"直接复用"产物（从同事源码搬，零改动）。若 L2-04 尚未执行，本 L3 执行时需先把 shared_buffer.py 搬到 `act/runtime/`（这属于 L2-04 deploy_013 的范围，但可作为本 L3 的前置动作，在 L3 文件里标注）。**建议 L2-03 与 L2-04 的 shared_buffer 搬运协调**。

## 8. 验证方式

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/repo/test_policy_loader.py -v
```

| 层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit | 是 | mock ACTPolicy 验证签名 | `predict_action_chunk` 输出 shape `[chunk,16]` float32 |
| dry-run | 视 bundle | 加载真 ACT bundle 离线推理 | 无 bundle 时标 BLOCKED_ENV |
| 其余 | 否 | — | — |

L2 贡献：ACT 模型加载与推理运行时就绪，predict_action_chunk 接口固化（L2-04 复用支点）。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 |
|---|---|---|
| policy_loader 源码 | `src/model_deploy/act/repo/policy_loader.py` | repo |
| repo 包标记 | `src/model_deploy/act/repo/__init__.py` | repo |
| 单测 | `src/model_deploy/act/tests/repo/test_policy_loader.py` | tests/repo |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/**`、`act/config/**`、`act/runtime/**`（仅 import ObservationSnapshot，不改）

## 11. 必读上下文

### 必读任务文档
- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-03-ACT数据装配与模型加载.md`（复用边界 + predict_action_chunk 契约）
- `DOCS/03_工程/阶段四：模型部署/01_contracts/ACT模型训练交付物契约.md`（bundle 结构、加载校验）

### 必读代码（AS-IS 参考）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py`（247行，重写参考）
- `src/model_deploy/third_party/lerobot/src/lerobot/policies/act/`（ACTPolicy/ACTConfig 用法）

### 必读约束文档
- `DOCS/02_约束/编程执行/Agent编程执行原则.md`
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`（第三节 shape 边界校验、第五节横切显式接入）
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-03-assembly`。
- 依赖校验：L2-01（Types）、L2-02（Config）已就绪；shared_buffer.ObservationSnapshot 可 import（若否，先搬 shared_buffer）。
- 接口硬约束：`predict_action_chunk` 签名不得改变。
- TDD：先写 mock 单测验证签名，再实现加载。
- 落点校验。

## 13. 成功标准

- [ ] `act/repo/policy_loader.py` 存在，含 `ActPolicyRuntime` + `load_act_policy_runtime`。
- [ ] `predict_action_chunk(observation)` 签名与同事一致（输入 ObservationSnapshot，输出 `(chunk,16)` float32 ndarray）。
- [ ] 加载流程用 `ACTPolicy`/`ACTConfig`，无 `build_pi05_with_lora`/`peft`/`load_adapter`。
- [ ] `_build_batch` 用 lerobot key（`observation.state`/`observation.images.*`）。
- [ ] `_validate_bundle` 校验 manifest/normalizers/experiment_config 存在。
- [ ] mock 单测 PASSED（无真 bundle 时 signature/shape 验证通过）。
- [ ] 未修改 pi05/third_party/pi05_old/types/config。

## 14. 回滚方式

删除 `src/model_deploy/act/repo/policy_loader.py`。

## 15. 完成后交接

（执行 sub-agent 完成后填写）

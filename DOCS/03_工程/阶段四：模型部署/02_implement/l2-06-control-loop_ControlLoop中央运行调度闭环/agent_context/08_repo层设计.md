# repo 层设计：L2-06

## 1. 产物结论

本 L2 不在该层新增源码产物。

原因：bundle、manifest、checkpoint、normalizer 和 policy 权重属于启动期资源访问，继续由 L2-01 repo/startup resource factory 负责。L2-06 runtime 只接收已在 RAM 中且已通过合同校验的对象。

这是一个必须显式回写上游的边界修正：L2-01 旧版文档排除 policy load，但已确认的 L2-03 最新边界同样排除 loader，并要求 L2-06 注入“L2-01 已加载的 policy + 两个 normalizer + config”。为消除无 owner 启动断口，本设计按较新 L2-03 约束冻结 L2-01 startup resource factory 为唯一 owner；P0-03 实现前必须同步修正 L2-01 边界文档，不允许由 L2-06 UI 私下加载权重。

验收如何确认：`runtime/` 和 `ui/act_deploy_node.py` 不出现 `open/yaml/torch.load/from_pretrained/Path.read_*`；policy、normalizers 与 input metadata 在 worker/timer 前已就绪。

## 2. Canonical 启动资源合同

上游修复只允许采用下面一个权威合同；不得再保留 Dict/private property/另一份 camera spec 的备选路径。owner 是 L2-01 repo，目标文件与 public facade 固定为：

```text
src/model_deploy/act/repo/act_runtime_resources.py
src/model_deploy/act/repo/__init__.py
```

```text
PolicyInputSpec (frozen)
├─ state_key: str
├─ state_dim: int
├─ image_prefix: str
├─ camera_keys: tuple[str, ...]
├─ image_shapes: tuple[tuple[str, tuple[int,int,int]], ...]  # CHW
├─ image_layout: Literal["CHW"]
├─ image_dtype: "float32"
├─ image_value_range: tuple[float,float]                    # [0.0,1.0]
├─ action_dim: int
└─ chunk_size: int

ActRuntimeResources (frozen aggregate)
├─ policy                         # 已 load、device/eval/compile/warmup 决策完成
├─ state_normalizer               # vector_dim=16
├─ action_normalizer              # vector_dim=16
├─ policy_input_spec: PolicyInputSpec  # 从 policy RAM metadata 唯一派生
└─ contract_results               # config/bundle/normalizer/policy 交叉校验证据
```

`PolicyInputSpec` 构造不变量：state/action dim 均为 16；chunk size 与 config 相等且正数；camera keys 非空、唯一且顺序稳定；image-shape keys 精确等于 camera keys，每个 shape 为正数 `(C,H,W)` 且 C=3；layout/dtype/range 精确为 `CHW/float32/[0.0,1.0]`。loader 不得用 config default 填补缺失的 production policy metadata；metadata 缺失是启动 FAIL。

唯一 public function 签名冻结为：

```python
load_act_runtime_resources(config: DeployConfig) -> ActRuntimeResources
```

`repo.__init__` 必须增量公开 `PolicyInputSpec`、`ActRuntimeResources` 与 `load_act_runtime_resources`，同时保留当前 `ActionStateNormalizer`、manifest/normalizer/experiment/bundle loader 等全部 public export；不得用新 `__all__` 覆盖 L2-01 已有接口。当前代码只有分散的 manifest/normalizer/checkpoint loader，没有 production policy loader/aggregate，因此是 P0 启动 FAIL。

## 3. 与 L2-03/L2-02 的交付

```text
ActRuntimeResources.policy + normalizers + DeployConfig
  + ActRuntimeResources.policy_input_spec
  -> 构造 L2-03 ActInferenceService(..., input_spec=同一对象)

ActRuntimeResources.policy_input_spec + DeployConfig
  -> 构造 L2-02 typed observation pipeline

两个构造结果的 camera keys / image contract / chunk size
  -> A5 startup preflight 再次等值校验
```

当前 L2-03 会自己派生 private `_input_spec`。P0 修复后必须改为消费 aggregate 中同一个 `PolicyInputSpec`，不得再次派生；它只通过 read-only `input_spec` property 返回原对象。A5 禁止读取 `_input_spec`，L2-02/03 的 camera/image/chunk 合同必须以 identity（`is`）通过 B12。

## 4. class、函数、I/O 与依赖

- class 设计：L2-06 repo 无 class。
- 函数设计：L2-06 repo 无函数；A5 只调用上游 public resource function。
- 输入：config path 和 bundle path 仅进入 L2-01 repo。
- 输出：validated RAM resources；L2-06 不接收半加载对象或 path 替代物。
- 副作用：所有文件/GPU resource I/O 在 control timer 创建前完成；tick/worker 不访问文件。
- 依赖方向：UI startup 可调用 repo；runtime/service 不调用 repo；repo 不依赖 UI/runtime。

## 5. 失败语义

- 文件/manifest/normalizer/policy 任一缺失或不一致：启动 FAIL，worker/timer 不创建。
- 已配置的真实 bundle 在验收机不可取得：loader 已被 local Gate 证明时可 `BLOCKED_ARTIFACT`；`bundle_dir` 未配置/格式错误或 loader 不存在仍是 FAIL。
- GPU/torch runtime 在当前机器不可用：实现完整且 CPU/local path 已证明时可 `BLOCKED_ENV`。
- 不允许用 `bundle_dir` 不存在来隐式选择 fake policy。
- compile/warmup 失败是否降级必须由 resource loader 明确返回/记录；worker 不自行尝试编译或加载。

## 6. Pi0.5 与验收

Pi0.5 参考：`pi05_vla_deploy_node.py:66-83` 在 node 启动中调用 `load_policy_runtime(config)` 后创建 worker。ACT 保留“timer 前加载”的顺序，但把具体资源 I/O 留在 repo public function。

验收标签：`REPO_POLICY_RESOURCE`、`REPO_INPUT_SPEC_PUBLIC`、`REPO_NO_RUNTIME_IO`、`PUBLIC_CONTRACT_IMPORTS`、`STARTUP_ATOMIC_ORDER`。

本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。

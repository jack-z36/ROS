# L2-03 ACT 数据装配与模型加载

> [!info] 归属
> - 对应分层：Repo + Service（输入侧，依赖 Types + Config）
> - 关联 ACT Delta：A5（policy_loader）、A6（observation_collector + batch adapter）
> - 关联契约：[[ACT部署契约]]、[[ACT模型训练交付物契约]]

## 一句话定位

隐藏「ROS observation topic → ACT 模型 batch」的装配逻辑：observation_collector 装配 16D state snapshot，policy_loader 加载 ACT checkpoint 并构造模型输入。**不抽象 PolicyBackend 接口**。

## 本次唯一目标

- 新建 `src/model_deploy/act/repo/policy_loader.py`：加载 ACT bundle（checkpoint + manifest + normalizers + config），校验合法性，构造 `ActPolicyRuntime`。
- 新建 `src/model_deploy/act/service/observation_collector.py`：订阅 `/act/observation/*`，装配 16D state（分组段序）+ 双目图像 snapshot。
- `_build_batch()`：唯一的 `ObservationSnapshot → ACT processor input` 映射位置。

## 同事源码复用边界

| ACT 目标 | 同事源文件 | 方式 | 复用要点 |
|---|---|---|---|
| `act/repo/policy_loader.py` | `pi05_old/.../deploy/src/pi05/deploy/models/policy_loader.py` (246行) | **重写，保持接口** | 内部完全重写（换 `build_pi05_with_lora` → `ACTPolicy.from_pretrained` + `ACTConfig`）。**必须保持对外接口 `predict_action_chunk(observation: ObservationSnapshot) -> np.ndarray [chunk_size, 16]` 不变**——这是 inference_worker 复用的唯一契约。保留：`_build_batch` 的 dict key 约定（`observation.state`/`observation.images.*`，lerobot 标准 key）、`_move_tensors_to_device` 工具、`torch.inference_mode` 推理壳、CUDA 配置。改：归一化 min-max→mean-std（ACT 默认）；删 LoRA/peft/builder 依赖 |
| `act/service/observation_collector.py` | `pi05_old/.../deploy/src/pi05/deploy/runtime/observation_collector.py` (154行) | **结构复用** | 保留 `ObservationCollector` 装配逻辑 + `time.monotonic()` 时效性门控 + snapshot 完整性判断框架。改：`_required_value_keys` 字段列表从 8 个关节/EE 字段 → 4 个 TCP/gripper 字段；增加 `update_tcp_pose()`/`update_gripper_state()` |
| `act/repo/normalization.py` | `pi05_old/.../common/src/pi05/common/data/normalization.py` (310行) | **部分复用** | `ActionStateNormalizer` 类保留（通用归一化/反归一化逻辑）。改：归一化模式 min-max→mean-std（`y=(x-mean)/std`）；剥离 `build_normalizer_from_lerobot()`/`build_state_action_normalizers()`（训练侧工厂，部署用不到，从 normalizers.json 直接重建）。`ensure_vector_stats()` 不搬 |
| `act/service/image_preprocess.py` | `pi05_old/.../common/src/pi05/common/data/image_preprocess.py` (76行) | **直接复用** | 通用 RGB→CHW float tensor + resize。仅改默认尺寸参数 |

> [!warning] policy_loader 是复用策略的支点
> 整个调度层（shared_buffer/control_loop/inference_worker，681 行）能否**一行不改地直接复用**，取决于 `act/repo/policy_loader.py` 是否保持这个方法签名：
> ```python
> class ActPolicyRuntime:
>     def predict_action_chunk(self, observation: ObservationSnapshot) -> np.ndarray:
>         # 返回 shape (chunk_size, 16) 的 float32 numpy
> ```
> 内部怎么加载 ACT、怎么 build batch、怎么调 `ACTPolicy.predict_action_chunk` 都可以重写，但这个对外方法签名不能变。**L3 执行时这是硬约束。**

## 明确不做

- 不定义 PolicyBackend / PolicyInterface ABC（依据《Agent编程执行原则》「不提前抽象」）。
- 不预留触觉装配逻辑。
- 不修改 Pi0.5 policy_loader。
- 不做硬件发送（由 L2-04 发布 / L2-05 bridge 执行）。

## policy_loader 边界校验（对照《架构边界与机械约束原则》第三、五节）

加载 ACT bundle 时必须校验：
- `manifest.json.model.policy_type == "act"`，否则报错。
- `manifest.json.model.state_dim == 16` 且 `action_dim == 16`，否则报错。
- `normalizers.json` 的 mean/std 数组长度均为 16，否则报错。
- `experiment_config.yaml` 重建 ACTConfig（dim_model、chunk_size、vision_backbone 等），与 checkpoint 匹配。
- 加载失败抛结构化错误，不静默继续。

bundle 是横切能力，必须通过显式 loader 接入，业务层不散落读取 bundle 文件（第五节）。

## observation_collector 边界

- 订阅 `/act/observation/image/{left,right}_gripper_fisheye`、`/act/observation/arm/{left,right}_tcp_pose`、`/act/observation/gripper/{left,right}_state`。
- 必需字段齐全且未过期（基于 `time.monotonic()`）才生成 `ObservationSnapshot`。
- snapshot 含：双目图像、left/right TCP pose（PoseStamped→quaternion）、left/right gripper width。
- state 编码集中在 `encode_state()`（L2-01 的 state_codec），不散落到 ROS 回调。

## 依赖

- L2-01：state_codec（encode_state）、action_spec（常量）。
- L2-02：config schema（topic、bundle 路径、维度）。
- `src/model_deploy/third_party/lerobot/`：ACT policy 类（`policies/act/`）。

## L3 草案

| L3 | 目标 | 验收模式 |
|---|---|---|
| deploy_009 | 从同事 policy_loader 重写：建 `act/repo/policy_loader.py`，`ACTPolicy` 加载，**保持 `predict_action_chunk` 签名**，manifest/normalizers 校验 | downstream-l2（dry-run 覆盖） |
| deploy_010 | 从同事 observation_collector 结构复用：建 `act/service/observation_collector.py`，16D snapshot + 时效性门控 | downstream-l2 |
| deploy_011 | 从同事 normalization 部分复用：建 `act/repo/normalization.py`，`ActionStateNormalizer` mean-std 模式 + 从 JSON 重建 | downstream-l2 |
| deploy_012 | dry-run 验证：加载合法 ACT bundle，离线推理输出 [n_action_steps, 16] | direct-local（需 bundle；无 bundle 时 env-blocked） |

## 真机风险

低。不触碰硬件。但依赖 ACT bundle 就绪才能完整验证（无 bundle 时 deploy_012 为 env-blocked）。

## 回滚方式

删除 `src/model_deploy/act/repo/policy_loader.py`、`act/repo/normalization.py` 和 `act/service/observation_collector.py`。

## L2 Gate（AI 侧自动化）

- required L3：deploy_009 ~ deploy_012。
- 运行命令：`pytest src/model_deploy/act/tests/deploy/ -v`（有 bundle 时）；无 bundle 时 deploy_012 标 BLOCKED_ENV。
- 通过现象（有 bundle）：policy_loader 加载成功；observation snapshot 维度=16；离线推理输出 shape [n_action_steps, 16]。

## 人类验收标准

验收性质为「机械」（需 ACT bundle）：

| 验收项 | 运行命令 | 通过现象 |
|---|---|---|
| 1 | `pytest src/model_deploy/act/tests/deploy/test_policy_loader.py -v`（有 bundle） | 加载成功，policy_type=act，state_dim=16，action_dim=16 |
| 2 | `pytest src/model_deploy/act/tests/deploy/test_observation_collector.py -v` | snapshot.state shape [16]，段序分组正确；缺 TCP pose 不生成 snapshot |
| 3 | 离线推理脚本（喂数构造 snapshot，跑一次 predict_action_chunk） | 输出 shape [n_action_steps, 16]，action 段序交替 |

> [!note] bundle 未就绪时的处理
> 若 ACT bundle 尚未交付（阶段三未完成），验收项 1/3 标记为 BLOCKED_ENV，人类验收可暂缓该项，但 deploy_010（observation_collector 单测，不依赖 bundle）仍可验收。bundle 就绪后补跑。

用户签字位置：`05_acceptance/l2-03-assembly/验收结果.md` 末尾「人类验收」段。

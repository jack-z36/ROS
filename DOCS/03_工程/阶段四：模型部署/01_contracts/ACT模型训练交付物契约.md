# ACT 模型训练交付物契约

> [!info] 产物归属
> - 类型：模型训练交付物契约（阶段四开发工作流 · 契约层）。
> - 目标路径：`DOCS/03_工程/阶段四：模型部署/01_contracts/ACT模型训练交付物契约.md`。
> - 适用模型：ACT（Action Chunking Transformer，lerobot 框架 `policies/act/`）。
> - 关联契约：[[ACT部署契约]]。
> - 并存说明：本文件与 [[模型训练交付物契约]]（Pi0.5 版）并存。第一版部署以 ACT 为主，Pi0.5 契约作为历史保留。

## 一句话要求

请交付一个可部署的 `deploy_bundle` 目录（ACT checkpoint + 配置 + 归一化参数），而不是只交付训练 checkpoint、wandb 链接或单个权重文件。

部署侧期望拿到：

```text
deploy_bundle/
├── manifest.json
├── normalizers.json
├── experiment_config.yaml
├── checkpoint/
│   ├── policy.safetensors      # 或 .pt，视训练侧导出格式
│   └── preprocessor_config.json # 若训练侧对图像有预处理配置
└── RELEASE.md
```

部署侧会把该目录放到 4090 推理主机本地，并在部署配置中填写：

```yaml
bundle:
  bundle_dir: /home/hit/ROS/model_bundles/current
  policy_type: act
```

## 与 Pi0.5 bundle 的区别

| 项 | Pi0.5 bundle | ACT bundle |
|---|---|---|
| 模型结构 | Pi0.5 VLA + LoRA adapter | ACT（Action Chunking Transformer，CVAE + ResNet18 backbone） |
| 权重形式 | `adapter/adapter_model.safetensors`（LoRA） | `checkpoint/policy.safetensors`（完整 policy 权重，无 LoRA） |
| 加载方式 | 加载 base model + 注入 LoRA adapter | 直接加载完整 ACT policy |
| state 维度 | 14D（旧）或按 Pi0.5 契约 | **16D**（第一版，不含触觉） |
| action 维度 | 14D | **16D**（与阶段二数据清洗同构） |
| 归一化 | min-max [-1,1] | **mean-std**（lerobot ACT 默认 `NormalizationMode.MEAN_STD`） |
| chunk_size | 30 | 100（默认）或训练实际值 |
| temporal_ensemble | 不适用 | 可选（`temporal_ensemble_coeff`） |

## 必须交付的文件

| 文件 / 目录 | 是否必须 | 作用 | 验收要求 |
|---|---:|---|---|
| `manifest.json` | 是 | 描述模型输入输出契约、相机 key、state/action 维度、chunk size 等。 | 必须能说明该 bundle 是 ACT 模型、吃什么 observation、输出什么 action。 |
| `normalizers.json` | 是 | 保存训练数据统计得到的 state/action 归一化与反归一化参数（mean/std）。 | `state` / `action` 的维度必须与 `manifest.json` 一致（16D）。 |
| `experiment_config.yaml` | 是 | 保存重建 ACT 结构所需的训练配置。 | 部署程序能用它重建 ACT 结构（dim_model、chunk_size、vision_backbone 等）。 |
| `checkpoint/policy.safetensors` | 是 | 训练得到的完整 ACT policy 权重。 | 文件存在且可被 `safetensors` 加载。 |
| `checkpoint/preprocessor_config.json` | 视情况 | 若训练侧对图像有预处理配置（如 resize/normalize），交付该文件。 | 若图像预处理非标准，缺该文件视为交付不完整。 |
| `RELEASE.md` | 是 | 人可读的版本说明。 | 见下方模板。 |

## 不要只交付这些东西

| 只交付这个 | 问题 |
|---|---|
| 单个 `.safetensors` 权重 | 部署侧不知道模型结构、normalizer、camera names、action schema。 |
| 训练 checkpoint 目录（含 optimizer/scheduler） | checkpoint 通常包含 optimizer / scheduler / trainer 状态，不等于部署 bundle。 |
| wandb run 链接 | 不能作为部署输入。 |
| LeRobotDataset 目录 | 数据集不是部署侧直接加载的模型产物。 |
| 只给 HuggingFace repo id | 真机部署需要可复现、可离线的本地 bundle。 |

## `manifest.json` 示例

请让 `manifest.json` 直接写清楚模型输入输出契约：

```json
{
  "schema_version": 1,
  "created_at_utc": "2026-07-XXT00:00:00Z",
  "project": {
    "project_name": "act_rm65_deploy",
    "run_name": "act_rm65_v1"
  },
  "model": {
    "policy_type": "act",
    "dtype": "float32",
    "chunk_size": 100,
    "n_action_steps": 100,
    "n_obs_steps": 1,
    "state_dim": 16,
    "action_dim": 16,
    "temporal_ensemble_coeff": null
  },
  "observation": {
    "fps": 15,
    "image_size": 224,
    "cameras": [
      "left_gripper_fisheye",
      "right_gripper_fisheye"
    ],
    "features": {
      "observation.images.left_gripper_fisheye": {
        "dtype": "image",
        "shape": [3, 224, 224]
      },
      "observation.images.right_gripper_fisheye": {
        "dtype": "image",
        "shape": [3, 224, 224]
      },
      "observation.state": {
        "dtype": "float32",
        "shape": [16],
        "semantic": [
          "left_tcp_xyz_m[3]",
          "left_tcp_quat_xyzw[4]",
          "right_tcp_xyz_m[3]",
          "right_tcp_quat_xyzw[4]",
          "left_gripper_width[1]",
          "right_gripper_width[1]"
        ]
      },
      "action": {
        "dtype": "float32",
        "shape": [16],
        "semantic": [
          "left_tcp_xyz_m[3]",
          "left_tcp_quat_xyzw[4]",
          "left_gripper_width[1]",
          "right_tcp_xyz_m[3]",
          "right_tcp_quat_xyzw[4]",
          "right_gripper_width[1]"
        ]
      }
    }
  },
  "artifacts": {
    "checkpoint_dir": "checkpoint",
    "normalizers_path": "normalizers.json",
    "experiment_config_path": "experiment_config.yaml"
  }
}
```

> [!warning] state 段序与 action 段序不同（与阶段二数据清洗一致）
> - **observation.state（16D）**：分组排列 `left_tcp[7] + right_tcp[7] + left_gripper_width[1] + right_gripper_width[1]`（先所有左段，再所有右段）。
> - **action（16D）**：交替排列 `left_tcp[7] + left_gripper_width[1] + right_tcp[7] + right_gripper_width[1]`（左pose+左夹爪 → 右pose+右夹爪）。
> - 这是阶段二 `数据清洗交付说明.md` 中 `STATE_SEGMENT_DEFINITIONS` / `ACTION_SEGMENT_DEFINITIONS` 的定义顺序决定的，不是笔误。部署侧 codec 必须严格遵循，否则段序错位会导致动作错误。
> - 第一版 **不含触觉**。后续版本 state 升级为 32D 时，在末尾追加 16D 触觉段（4 片 × 4D），action 始终保持 16D。

## `normalizers.json` 示例

ACT 默认使用 **mean-std 归一化**（`NormalizationMode.MEAN_STD`），与 Pi0.5 的 min-max 不同。数组长度必须和 `manifest.json` 中的 `state_dim` / `action_dim` 对齐（16D）。

```json
{
  "state": {
    "mean": [
      0.0, 0.0, 0.3,
      0.0, 0.0, 0.0, 1.0,
      0.0, 0.0, 0.3,
      0.0, 0.0, 0.0, 1.0,
      0.5, 0.5
    ],
    "std": [
      0.2, 0.2, 0.2,
      0.5, 0.5, 0.5, 0.5,
      0.2, 0.2, 0.2,
      0.5, 0.5, 0.5, 0.5,
      0.5, 0.5
    ]
  },
  "action": {
    "mean": [
      0.0, 0.0, 0.3,
      0.0, 0.0, 0.0, 1.0,
      0.5,
      0.0, 0.0, 0.3,
      0.0, 0.0, 0.0, 1.0,
      0.5
    ],
    "std": [
      0.2, 0.2, 0.2,
      0.5, 0.5, 0.5, 0.5,
      0.5,
      0.2, 0.2, 0.2,
      0.5, 0.5, 0.5, 0.5,
      0.5
    ]
  }
}
```

上面数值只是示例，实际数值必须来自训练数据统计（来自 LeRobotDataset v3 的 `meta/stats.json`，pooled variance 聚合）。

> [!warning] 归一化方式必须与训练侧一致
> lerobot ACT 默认 `normalization_mapping.ACTION = MEAN_STD`、`STATE = MEAN_STD`。若训练侧改成了 `MIN_MAX`，必须在 `experiment_config.yaml` 中显式声明，否则部署侧反归一化会用错公式。部署侧的反归一化公式：`action_real = action_normalized * std + mean`。

## `experiment_config.yaml` 示例

请把能重建 ACT 结构的训练配置放进来。示例（默认值来自 lerobot `ACTConfig`）：

```yaml
model:
  policy_type: act
  dtype: float32
  chunk_size: 100
  n_action_steps: 100
  n_obs_steps: 1
  state_dim: 16
  action_dim: 16
  # ACT 架构参数
  vision_backbone: resnet18
  pretrained_backbone_weights: ResNet18_Weights.IMAGENET1K_V1
  replace_final_stride_with_dilation: false
  dim_model: 512
  n_heads: 8
  dim_feedforward: 3200
  feedforward_activation: relu
  n_encoder_layers: 4
  n_decoder_layers: 1
  use_vae: true
  latent_dim: 32
  n_vae_encoder_layers: 4
  temporal_ensemble_coeff: null
  pre_norm: false
  dropout: 0.1
  kl_weight: 10.0
  normalization_mapping:
    VISUAL: MEAN_STD
    STATE: MEAN_STD
    ACTION: MEAN_STD

data:
  dataset_version: act_rm65_clean_v1
  fps: 15
  image_size: 224
  cameras:
    - left_gripper_fisheye
    - right_gripper_fisheye

runtime_recommendation:
  task: "put the object into the container"
  device: cuda:0
  dtype: float32
  chunk_size: 100
  n_action_steps: 100
```

## `RELEASE.md` 示例

请额外给一个人能读懂的版本说明：

```markdown
# act_rm65_v1

## 基本信息

- model_version: act_rm65_v1
- trained_by: <训练负责人>
- created_at: 2026-07-XX
- dataset_version: act_rm65_clean_v1
- training_code_commit: <commit hash>
- deploy_contract: ACT部署契约 / 2026-07-XX

## 部署输入

- left image: left_gripper_fisheye
- right image: right_gripper_fisheye
- state: 16D = left_tcp(xyz+quat_xyzw) + right_tcp(xyz+quat_xyzw) + left_gripper_width + right_gripper_width
- 不含触觉（第一版）

## 部署输出

action_dim = 16

action =
  left_tcp_xyz_m[3] + left_tcp_quat_xyzw[4] + left_gripper_width[1]
  + right_tcp_xyz_m[3] + right_tcp_quat_xyzw[4] + right_gripper_width[1]

units:
  tcp position: m
  tcp rotation: quaternion xyzw（归一化，模长=1）
  gripper: normalized [0,1]（0=闭合, 1=全开）

## 推荐运行参数

- task: "put the object into the container"
- chunk_size: 100
- n_action_steps: 100
- dtype: float32
- device: cuda:0

## 已知限制

- <填写限制>
```

## 部署侧配置示例

部署侧拿到这个目录后，会放到推理主机，例如：

```text
/home/hit/ROS/model_bundles/act_rm65_v1/
```

然后把软链接 `current` 指向这个版本：

```bash
ln -sfn /home/hit/ROS/model_bundles/act_rm65_v1 /home/hit/ROS/model_bundles/current
```

部署配置只写：

```yaml
bundle:
  bundle_dir: /home/hit/ROS/model_bundles/current
  policy_type: act
```

## 部署侧消费约束

部署侧 `policy_loader` 加载 ACT bundle 时必须做以下边界校验（对照《架构边界与机械约束原则》第三节「数据 shape 必须在边界解析或校验」）：

- `manifest.json.model.policy_type == "act"`，否则报错。
- `manifest.json.model.state_dim == 16` 且 `action_dim == 16`，否则报错（shape mismatch 不静默继续）。
- `normalizers.json` 的 `state.mean`/`state.std`/`action.mean`/`action.std` 数组长度均为 16，否则报错。
- `experiment_config.yaml.model.chunk_size` / `n_action_steps` / `dim_model` 等参数与 checkpoint 实际结构匹配，否则加载时 torch 报错。
- 加载成功后，离线推理输出必须为 `[n_action_steps, 16]` 或 `[1, n_action_steps, 16]` 的 action chunk。

任何一项不匹配，部署侧不得继续向硬件发送命令。

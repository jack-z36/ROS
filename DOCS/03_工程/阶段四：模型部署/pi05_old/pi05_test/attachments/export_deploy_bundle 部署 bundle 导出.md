---
tags:
  - 附件
---

# export_deploy_bundle (部署 bundle 导出)

> [!abstract]
> 把训练产物（LoRA adapter + tokenizer + 数据集 stats + Pi0.5 base 元数据）打包成"部署 bundle 目录"，让 `pi05_vla_deploy_node` 加载后能直接上机器人。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `export_deploy_bundle` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py` (Common Community 7) |
| 调用位置 | `trainer.py:247-252`（`_maybe_export_deploy_bundle`） |
| 现实含义 | "训练完 → 一键转成可部署包" |

## 调用

```python
bundle_dir = export_deploy_bundle(
    self.config,
    adapter_dir=final_adapter_dir,         # export_final_adapter 输出
    output_dir=self.config.logging.run_export_dir,
    overwrite=True,
)
```

## 典型 bundle 目录结构

```
/workspace/runs/pour_demo/v1/exports/v1/
├── manifest.json                    # bundle 元数据 + image_names + state/action dim
├── adapter/                         # LoRA adapter
│   ├── adapter_model.safetensors
│   └── adapter_config.json
├── base/                            # Pi0.5 base 元数据（small）
│   ├── config.json
│   └── preprocessor_config.json
├── processor/                       # tokenizer + image processor
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── preprocessor_config.json
├── dataset_stats.json               # 用于 state/action 归一化
└── tactile_preprocess.json          # 若启用触觉
```

## manifest.json 关键字段

```json
{
  "model_type": "pi05_lora",
  "policy_image_names": ["top", "left_wrist", "right_wrist"],
  "state_dim": 26,
  "action_dim": 14,
  "chunk_size": 30,
  "n_action_steps": 30,
  "task": "bimanual manipulation",
  "lora": {"rank": 16, "alpha": 32, "dropout": 0.05, "target_modules": "all-linear"}
}
```

## 在数据流中的位置

```text
训练结束
    ↓
export_final_adapter(accelerator, model, run_output_dir)  →  final_adapter_dir
    ↓
export_deploy_bundle(config, adapter_dir, output_dir, overwrite)
    ↓
/runs/<project>/<run>/exports/<run>/  ←  bundle_dir
    ↓
pi05_vla_deploy_node --config deploy.yaml  (config.bundle.bundle_dir=bundle_dir)
    ↓
load_policy_runtime(config)  →  Pi0.5 + LoRA  ←  ready
```

## 关键约束

- **`overwrite=True`**：每次训练覆盖旧 bundle，避免累加
- **导出失败只打 warning**：见 `trainer.py:253-255`，不影响训练成功状态
- **bundle 目录可拷贝**：自带 base config + adapter，不依赖 HF hub
- 与 [[Pi05LoraTrainer LoRA 训练器]]、[[Pi05VlaDeployNode ROS2 部署节点]] 跨端配套

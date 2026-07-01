---
tags:
  - 附件
---

# export_deploy_bundle (打包 deploy bundle)

> [!abstract]
> 把训练产物打成 1 个独立目录：拷贝 LoRA adapter + 用 LeRobot dataset 重算 state/action normalizer + 写 manifest.json + 复制 experiment_config.yaml + 可选复制 tactile_preprocess.json。`Pi05LoraTrainer` 训练完调它，`Pi05VlaDeployNode` 启动时调 `load_bundle_*` 加载。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `export_deploy_bundle` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:25-55` |
| 调用方 | `trainer.py:247-252` (`_maybe_export_deploy_bundle`) |
| 现实含义 | "训练完 → 1 个目录拷走就能上机器人" 的打包器 |

## 函数签名

```python
def export_deploy_bundle(
    config: ExperimentConfig,
    *,
    adapter_dir: Path,
    output_dir: Path,
    overwrite: bool = False,
) -> Path:
    ...
```

## 行为

```text
1. resolve adapter_dir（不存在 → FileNotFoundError）
2. resolve output_dir
3. _prepare_output_dir(output_dir, overwrite=overwrite)
4. shutil.copytree(adapter_dir, output_dir/adapter, dirs_exist_ok=overwrite)
5. 重新打开 LeRobotDataset 算 normalizer:
   dataset = LeRobotDataset(repo_id=dataset_path.name, root=dataset_path)
   state_norm, action_norm = build_state_action_normalizers(dataset)
6. 写 experiment_config.yaml = config.raw
7. _copy_tactile_preprocess(config, output_dir)  ← 仅 VTLA
8. 写 normalizers.json
9. 写 manifest.json
10. 返回 output_dir
```

## 关键约束

- **`adapter_dir` 必须存在且非空**：`adapter_dir.exists()` 校验
- **`output_dir` 已存在且非空 + `overwrite=False` → 抛 `FileExistsError`**：避免误覆盖
- **`overwrite=True` 会 `shutil.rmtree(output_dir)`**：旧 bundle 全部清空
- **normalizer 必须从 LeRobot dataset 重新算**：训练时算的 normalizer 可能在内存里没落盘；这里走 LeRobot 的 `meta/stats` 优先，回退到 `linspace(0, len-1, 2048)` 采样
- **adapter 是 PEFT safetensors 格式**：见 `save_pretrained` 输出
- 与 [[load_bundle_manifest 加载 manifest]]、[[load_bundle_normalizers 加载 normalizers]]、[[ActionStateNormalizer min-max 归一化]] 配套

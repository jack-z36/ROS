---
tags:
  - 附件
---

# load_bundle_manifest (加载 manifest)

> [!abstract]
> 部署节点启动时调它读 `manifest.json` 拿到 bundle 元信息（schema_version / project / model / observation / artifacts），是 bundle 与部署侧 schema 之间的入口。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `load_bundle_manifest` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:58-62` |
| 调用方 | 部署节点启动逻辑（`pi05.deploy.models.load_policy_runtime`） |
| 现实含义 | "我拿到的 bundle 是什么 schema 的？policy 配什么？相机有哪些？" |

## 函数签名

```python
def load_bundle_manifest(bundle_dir: str | Path) -> dict[str, Any]:
    ...
```

## 行为

```python
bundle_dir = Path(bundle_dir).expanduser().resolve()
manifest_path = bundle_dir / MANIFEST_NAME  # "manifest.json"
with manifest_path.open("r", encoding="utf-8") as f:
    return json.load(f)
```

## manifest.json 完整结构

```json
{
  "schema_version": 1,
  "created_at_utc": "2025-12-19T10:30:00+00:00",
  "project": {
    "project_name": "pi05_pour",
    "run_name": "pour_demo_v1"
  },
  "model": {
    "pretrained_path": "lerobot/pi05_base",
    "dtype": "bfloat16",
    "chunk_size": 30,
    "n_action_steps": 30,
    "state_dim": 26,
    "action_dim": 14,
    "max_action_dim": 14
  },
  "observation": {
    "fps": 30,
    "image_size": 224,
    "cameras": ["top", "left_wrist", "right_wrist"],
    "features": {},
    "tactile_preprocess_path": "tactile_preprocess.json"
  },
  "artifacts": {
    "adapter_dir": "adapter",
    "normalizers_path": "normalizers.json",
    "experiment_config_path": "experiment_config.yaml"
  }
}
```

## 在数据流中的位置

```text
export_deploy_bundle(...)  →  bundle_dir/manifest.json
    ↓
load_bundle_manifest(bundle_dir)  →  manifest dict
    ↓
load_policy_runtime(manifest, ...)  →  读 pretrained_path / dtype / chunk_size 构造 Pi0.5
    ↓
Pi05VlaDeployNode 启动
```

## 关键约束

- **`MANIFEST_NAME = "manifest.json"`**：固定文件名（`bundle.py:18`）
- **`schema_version` 当前为 1**：`BUNDLE_SCHEMA_VERSION = 1`（`bundle.py:22`）—— 部署侧遇到不兼容的 version 应报错
- **`tactile_preprocess_path` 是相对路径**（`"tactile_preprocess.json"` 或 `None`），部署侧要 join bundle_dir
- **UTF-8 encoding**：中文字段能写能读
- 与 [[export_deploy_bundle 打包 deploy bundle]]、[[manifest.json bundle 契约]] 配套

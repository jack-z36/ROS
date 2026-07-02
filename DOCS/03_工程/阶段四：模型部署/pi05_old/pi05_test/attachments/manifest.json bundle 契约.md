---
tags:
  - 附件
---

# manifest.json (bundle 契约)

> [!abstract]
> 每个 deploy bundle 根目录的 `manifest.json` 文件：描述 bundle 的 schema_version / 项目元信息 / 模型配置 / 观测配置 / 产物路径，是部署侧"自描述 bundle" 的唯一入口。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 文件名 | `manifest.json`（常量 `MANIFEST_NAME = "manifest.json"`） |
| 生成位置 | `bundle.py:51-54`（`_write_json`） |
| 加载位置 | `load_bundle_manifest(bundle_dir)` |
| 现实含义 | "我拿到的这个 bundle 是什么？该怎么用？" |

## 字段清单

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `schema_version` | `int` | 当前 `1`，未来扩展时递增 |
| `created_at_utc` | `str` (ISO 8601) | bundle 打包时间 |
| `project.project_name` | `str` | YAML `logging.project_name` |
| `project.run_name` | `str` | YAML `logging.run_name` |
| `model.pretrained_path` | `str` | Pi0.5 预训练权重（HuggingFace id 或本地路径） |
| `model.dtype` | `str` | `bfloat16` / `float16` / `float32` |
| `model.chunk_size` | `int` | 30 |
| `model.n_action_steps` | `int` | 30 |
| `model.state_dim` | `int` | 26 |
| `model.action_dim` | `int` | 14 |
| `model.max_action_dim` | `int` | 14（future-proof 上限） |
| `observation.fps` | `int` | 30 |
| `observation.image_size` | `int` | 224 |
| `observation.cameras` | `list[str]` | `["top", "left_wrist", "right_wrist"]` |
| `observation.features` | `dict` | 透传 YAML features |
| `observation.tactile_preprocess_path` | `str \| None` | `"tactile_preprocess.json"` 或 `None` |
| `artifacts.adapter_dir` | `str` | 相对路径，永远是 `"adapter"` |
| `artifacts.normalizers_path` | `str` | `"normalizers.json"` |
| `artifacts.experiment_config_path` | `str` | `"experiment_config.yaml"` |

## 关键约束

- **相对路径**：所有 `artifacts.*` 字段都是相对 bundle_dir 的，部署侧要 `bundle_dir / manifest["artifacts"]["adapter_dir"]`
- **schema_version=1 是当前唯一版本**：加载侧遇到更大版本应抛兼容错误
- **`tactile_preprocess_path` 是 `None` 而非缺字段**：非 VTLA bundle 此字段是 null
- **与 [[normalizers.json 归一化 JSON]]、`experiment_config.yaml` 一起构成"3 件套"
- 与 [[load_bundle_manifest 加载 manifest]] 配套

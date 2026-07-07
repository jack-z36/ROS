# repo 层设计 — L2-01 外部参数加载与契约校验闭环

> `l2_id`：`l2-01-external-contract`
> 上游边界来源：`01_L1_ACT功能模块边界.md` L2-01 段 + `02_L1_ACT功能模块协作架构.md`。本文件任务边界继承自当前 L1/L2 功能边界。

## 目标源码路径

```text
src/model_deploy/act/repo/
├── bundle_reader.py
├── manifest_parser.py
├── normalizer_loader.py
└── experiment_config_loader.py
```

## 层职责（来自 ACT 代码树分层约束）

进程外资源读取和反序列化。禁止 ROS topic、硬件 SDK、运行调度。`repo/` 依赖 `types`、`config`（不反向）。

> **读取/校验分离原则**：本层函数只做"路径→RAM 对象"（读文件、反序列化、存在性检查），**不做业务校验**（类型/范围/dim 一致归 `config/`）。

## 文件设计

### bundle_reader.py

- 文件职责：bundle 目录存在性检查 + checkpoint 路径解析。
- class 设计：无（纯函数）。
- 函数设计：
  - `check_bundle_files(bundle_dir) -> None`：检查 manifest.json/normalizers.json/experiment_config.yaml/checkpoint 存在，缺失抛 `FileNotFoundError`。
  - `resolve_checkpoint_path(bundle_dir) -> Path`：解析 checkpoint 路径。
- 输入/输出：bundle 路径 → 存在性确认 / checkpoint Path。
- 副作用：跨进程读（文件系统 stat）。
- 依赖方向：`repo` → `types`（用文件名常量）。不依赖 `config`（不做校验）。
- Pi0.5 参考：`deploy/models/policy_loader.py:_validate_bundle`（存在性校验段，复用）；`common/runtime/bundle.py:resolve_bundle_adapter_dir`。
- 验收覆盖：单测——合法 bundle 通过；缺各类文件抛 FileNotFoundError。

### manifest_parser.py

- 文件职责：读 manifest.json → dict。
- class 设计：无。
- 函数设计：`read_bundle_manifest(bundle_dir) -> dict`（json.load）。
- 输入/输出：bundle 路径 → manifest dict。
- 副作用：跨进程读。
- 依赖方向：`repo` → `types`（用 `MANIFEST_NAME` 常量）。
- Pi0.5 参考：`common/runtime/bundle.py:load_bundle_manifest`（**强复用**）。
- 验收覆盖：单测——合法 manifest 读出 dict；坏 JSON 抛异常。

### normalizer_loader.py

- 文件职责：读 normalizers.json → `(state_normalizer, action_normalizer)` 对象。
- class 设计：无（复用 `ActionStateNormalizer` 类，该类归 `types/` 或 `repo/` 共享；算法模型无关）。
- 函数设计：`read_bundle_normalizers(bundle_dir) -> tuple[ActionStateNormalizer, ActionStateNormalizer]`。
- 输入/输出：bundle 路径 → 两个 normalizer 对象。
- 副作用：跨进程读 + 反序列化。
- 依赖方向：`repo` → `types`（用 `NORMALIZERS_NAME` + `ActionStateNormalizer`）。
- Pi0.5 参考：`common/runtime/bundle.py:load_bundle_normalizers`（**强复用**）；`common/data/normalization.py:ActionStateNormalizer`（**直接复用类**）。
- 验收覆盖：单测——合法 normalizers 读出对象；dim 不匹配由 `config/` 校验（本层不校验）。

### experiment_config_loader.py

- 文件职责：读 bundle 内 experiment_config.yaml → `ExperimentConfig` 对象。
- class 设计：`ExperimentConfig`（frozen dataclass，含 model/data dims）。
- 函数设计：`read_experiment_config(bundle_dir) -> ExperimentConfig`。
- 输入/输出：bundle 路径 → ExperimentConfig。
- 副作用：跨进程读。
- 依赖方向：`repo` → `types`。
- Pi0.5 参考：`common/config/schema.py:ExperimentConfig` + `load_experiment_config`（参考）。**关键差异**：ACT **不**像 Pi0.5 那样用 `object.__setattr__` 覆写 dims，而是保留原值供 `config/` 交叉校验。
- 验收覆盖：单测——合法 experiment_config 读出；yaml 解析错误抛异常。

## 边界继承声明

本文件的 `repo/` 任务边界来自当前 L1/L2 功能边界（L2-01 负责外部资源读取），不是旧 layer-based 卡片。

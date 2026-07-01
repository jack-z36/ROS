---
tags: [program-principle, concept]
analysis: pi05-runtime-train-bundle
---

# Deploy bundle contract

> [!abstract]
> deploy bundle 是训练和部署之间的 artifact 契约，不是任意训练输出目录。

## 在本代码库中的具体含义

bundle 必须至少包含 `adapter/`、`manifest.json`、`normalizers.json`、`experiment_config.yaml`。导出逻辑在 `common/runtime/bundle.py:25-55`，加载校验在 `deploy/models/policy_loader.py:167-173`。

## 容易误解

部署端不会直接使用 trainer 的全部输出目录；它按 bundle contract 找 adapter、normalizer 和 config。


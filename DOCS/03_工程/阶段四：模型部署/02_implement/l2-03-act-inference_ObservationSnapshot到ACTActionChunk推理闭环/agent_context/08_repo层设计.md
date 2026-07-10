# repo 层设计：L2-03

## 1. 本 L2 不在该层新增源码产物

L2-03 没有 repo 层文件。它只接收已经进入 RAM 的资源，不能从 service 反向打开任何进程外资源。

## 2. L2-01 提供、L2-03 复用的资源

| 资源 | 创建/加载方 | L2-03 使用方式 |
|---|---|---|
| `DeployConfig` | L2-01 config | 只读推理维度和 device 语义 |
| `ActionStateNormalizer` 两个实例 | L2-01 repo/config | 调用 state `normalize`、action `unnormalize` |
| ACT policy | L2-01 repo/startup | 调用 `predict_action_chunk(batch)` |
| bundle/manifest/checkpoint 契约结果 | L2-01 | 信任其启动结论，不再重读 |

service 可以为了类型标注 import normalizer 类型，但不得调用 normalizer loader、bundle reader、manifest parser 或 experiment config loader。

## 3. 明确禁止的 repo 产物

以下文件或职责出现在 L2-03 变更中均为边界错误：

```text
src/model_deploy/act/repo/policy_loader.py
load_act_policy_runtime(...)
load_bundle_manifest(...)
load_bundle_normalizers(...)
resolve_checkpoint_path(...)
ACTPolicy.from_pretrained(...)
torch.compile(...)
model.to(...)
policy.eval() 的启动配置逻辑
生产 fake-policy 构造或选择逻辑
```

它们分别属于 L2-01 的资源读取、模型加载和启动配置职责。

## 4. 为什么不复用 Pi0.5 policy runtime

Pi0.5 `Pi05PolicyRuntime` 同时包住 loader、processor、normalizer、device 和推理函数。当前 L1 已把前半部分明确交给 L2-01；若 L2-03 再创建同名 runtime/loader，会出现两个 policy 所有者和两个 normalizer 来源。

L2-03 的 service class 只保存对已注入对象的引用，不能命名或实现为 repo runtime loader。

## 5. 测试边界

- 不新增 `tests/repo/test_policy_loader.py` 等 L2-03 repo 测试。
- L2-03 测试在 service fixture 中注入 stub policy 和 recording normalizer。
- 真实 policy dry-run 的前置由 L2-01 完成，L2-03 只验证调用行为与结果契约。

## 6. 验收

静态文件列表与 `rg` 检查必须证明：L2-03 代码没有 repo loader、新 bundle I/O、模型权重加载或 real/fake 选择。

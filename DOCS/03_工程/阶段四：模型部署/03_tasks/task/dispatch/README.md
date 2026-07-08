# 当前 L2 dispatch 入口

本目录只存放新版 ACT 功能闭环 L2 的 dispatch YAML。

dispatch 文件名必须使用新版 L2 ID：

```text
l2-01-external-contract.yaml
l2-02-observation-snapshot.yaml
l2-03-act-inference.yaml
l2-04-safety-guard.yaml
l2-05-action-publisher.yaml
l2-06-control-loop.yaml
```

旧 dispatch 已隔离到 `03_tasks/_legacy_layer_based_act/`，不得作为当前循环工程调度来源。

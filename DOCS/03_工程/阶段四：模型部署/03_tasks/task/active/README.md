# 当前 L3 active 入口

本目录只存放新版 ACT 功能闭环 L2 的 active L3。

允许的 L2 ID：

```text
l2-01-external-contract
l2-02-observation-snapshot
l2-03-act-inference
l2-04-action-smoothing
l2-05-safety-guard
l2-06-action-publisher
l2-07-control-loop
```

旧 `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware` 已隔离到 `03_tasks/_legacy_layer_based_act/`，不得从那里执行当前 L3。

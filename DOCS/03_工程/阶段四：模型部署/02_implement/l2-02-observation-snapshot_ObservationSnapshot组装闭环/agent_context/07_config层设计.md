# config 层设计：L2-02

## 1. 目标源码路径

```text
本 L2 不在该层新增源码产物。
```

## 2. 原因

L2-02 消费 L2-01 已定义的 `DeployConfig`、topic config、image config 和 stale timeout，不重新定义配置 schema。

如果 L2-02 在 `config/` 重新声明 observation topic 或 image 参数，会造成 L2-01 与 L2-02 两套配置权威，破坏 L1 中“L2-01 是静态契约地基”的边界。

## 3. 使用的配置对象

- `DeployConfig.topics.observation`
- `DeployConfig.image`
- `DeployConfig.safety.stale_observation_timeout_s` 或等价 runtime freshness 参数
- L2-01 state spec / codec 配置

## 4. class 设计

无新增 class。

## 5. 函数设计

无新增函数。

## 6. 输入输出

| 输入 | 输出 |
|---|---|
| L2-01 公开配置对象 | L2-02 service/runtime/ui 创建参数 |

## 7. 副作用

无。

## 8. 依赖方向

L2-02 的 service/runtime/ui 可以读取 L2-01 公开配置对象，但不得反向修改配置 schema。

## 9. Pi0.5 参考

Pi0.5 `DeployConfig` 中 observation topics 和 image config 可作为字段组织参考，但不作为当前 schema 权威。

## 10. 验收如何确认

- L2-02 设计包中不存在新的 `src/model_deploy/act/config/*` 目标。
- L2-02 使用 L2-01 的 topic / image / stale 配置。
- 缺配置、非法 topic、非法 image shape 由 L2-01 Gate 覆盖。

## 11. 边界继承声明

本文件服务当前 L1/L2 功能边界，不从旧 layer-based L2 卡片继承任务边界。


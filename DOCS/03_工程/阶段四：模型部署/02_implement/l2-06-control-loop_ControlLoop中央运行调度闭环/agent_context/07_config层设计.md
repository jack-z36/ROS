# config 层设计：L2-06

本 L2 不在该层新增源码产物。

原因：`control_hz`、prefetch、chunk age、fallback policy 与 safety 参数由 L2-01 `DeployConfig` schema 提供；ControlLoop 接收已校验的配置，不读取 YAML、不定义默认值。

验收如何确认：构造非法/边界配置的上游 schema 测试必须在 timer 启动前失败；runtime mock 用合法 `DeployConfig` 验证节拍和 fallback。

层职责：运行参数语言；只依赖 types。输入为已解析 `DeployConfig`，输出为只读运行参数视图；副作用无。本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。Pi0.5 参考：`pi05_vla_deploy_node.py:47-65` 的构造注入。

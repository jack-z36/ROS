# 阶段四契约参考库

本目录是阶段四模型部署的参考语义库，不是当前 ACT L2 / L3 拆解权威。

当前 ACT 第一版开发的权威优先级是：

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/00_L1_ACT部署程序任务文档.md`
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/01_L1_ACT功能模块边界.md`
4. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/02_L1_ACT功能模块协作架构.md`
5. 当前 L2 设计目录：`DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/<l2_id>_<中文短名>/`
6. 本目录下的参考契约

## 使用规则

- `ACT部署契约.md`、`ACT模型训练交付物契约.md` 可用于补充 topic、shape、bundle、normalizer、硬件接口和安全语义。
- `ACT Contract Delta.md`、`AS-IS Contract.md`、`TO-BE Contract.md`、`Contract Delta.md` 是旧规划方法或历史参考输入，不得作为当前 L2/L3 拆解权威。
- L2 设计文档引用本目录时，必须写明引用目的：`topic` / `shape` / `bundle` / `hardware semantics` / `safety semantics`。
- 禁止把本目录中的 Delta 编号、旧 L2 聚类或 AS-IS / TO-BE 结构写成当前 L2 的任务来源。

如果本目录内容与 L1 Agent 架构文档冲突，以 L1 Agent 架构文档为准，并在当前 L2 设计文档中记录冲突和处理方式。

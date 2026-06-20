# 阶段四 L2 运行验收索引

## 适用范围

- 阶段：阶段四：模型部署
- 任务模式：L2 运行验收、L2 Gate 汇总、L2 自动同步前检查
- 适用对象：阶段四每个 L2 的运行方法、测试输入、观察点、通过现象、实际执行记录、验收脚本和日志

## 核心语义

`验收结果.md` 不是单纯的任务完成清单。它必须回答：

```text
这个 L2 完成后，应该怎么运行？
用什么输入或模式运行？
观察哪里？
看到什么现象说明这部分代码是 OK 的？
实际执行结果和日志放在哪里？
```

任务完成清单只用于确认 required L3 是否齐全；真正决定 L2 Gate 的，是运行验收场景是否通过。

## 目录规则

每个 L2 使用一个独立子目录：

```text
05_acceptance/
├── l2-01-types/
├── l2-02-config/
├── l2-03-assembly/
├── l2-04-publish/
└── l2-05-hardware/
```

每个 L2 子目录固定包含：

```text
验收结果.md
L2整体验收报告.md
scripts/
logs/
```

## `验收结果.md` 固定结构

每个 L2 的 `验收结果.md` 必须包含以下章节：

1. 基本信息。
2. 验收目标。
3. 前置条件。
4. Required L3。
5. 运行验收场景。
6. 运行命令。
7. 测试输入。
8. 观察点。
9. 通过现象。
10. 失败现象与排查入口。
11. 实际执行记录。
12. 未验证项。
13. L2 Gate 结论。
14. 自动同步结果。

## 存放约束

- `验收结果.md` 记录 L2 如何运行、如何观察、实际结果、日志链接、未验证项和 Gate 结论。
- `L2整体验收报告.md` 由 L2 整体验收卡片生成，汇总 required L3 的验收反馈、L2 场景覆盖、环境 blocked 项、硬件 blocked 项和 Gate 建议。
- `scripts/` 存放本 L2 验收专用脚本或一次性检查工具；只有复杂或重复场景才需要新增脚本。
- `logs/` 存放本 L2 验收命令输出、人工观察记录和真机 smoke test 记录。
- 可维护源码和测试不得放在本目录；应放在 `src/model_deploy/pi05/` 及其 `tests/` 目录。
- 超大二进制、模型权重、缓存、环境目录和私有配置不得放入本目录。

## L2 Gate 索引

| L2 | 验收结果文档 | L2 分支 | 最低验证层级 | 运行验收重点 |
|---|---|---|---|---|
| L2-01 Types | `l2-01-types/验收结果.md` | `model_deploy-l2-01-types` | unit | 维度、段序、round-trip、非法 shape |
| L2-02 Config | `l2-02-config/验收结果.md` | `model_deploy-l2-02-config` | unit / config load | 配置加载、默认值、非法配置失败 |
| L2-03 Assembly | `l2-03-assembly/验收结果.md` | `model_deploy-l2-03-assembly` | dry-run | observation / batch 构造，不发布真机命令 |
| L2-04 Publish | `l2-04-publish/验收结果.md` | `model_deploy-l2-04-publish` | dry-run + shadow-run | safety guard、policy_action、metrics、sent_to_driver=false |
| L2-05 Hardware | `l2-05-hardware/验收结果.md` | `model_deploy-l2-05-hardware` | shadow-run + gated real-robot | bridge、IK、width 映射、真机 smoke test 阻断条件 |

# RuntimeSmokeTestSuite

## 定义

`RuntimeSmokeTestSuite` 是一组 Runtime MVP smoke test 用例的集合，用于表达 Runtime MVP 的最小验收范围。

## 所属位置

阶段二：数据清洗 / `runtime_mvp` / [[10_Runtime smoke test模块]]

## 现实语义

它表示“要证明 Runtime MVP 最小闭环可用，必须一起跑过哪些 smoke test”。第一版 suite 至少覆盖单场景 fake 成功、fake 全流程成功、缺配置、缺输入和 fake service 可控失败摘要。

## 字段或取值

| 字段 | 含义 |
| --- | --- |
| `suite_id` | smoke test suite 稳定标识。 |
| `title` | 人类可读 suite 名称。 |
| `cases` | [[RuntimeSmokeTestCase]] 列表。 |
| `required_cases` | 必须通过的用例标识列表。 |
| `allowed_service_mode` | 允许的 [[ServiceMode]]，Runtime MVP 第一版为 fake。 |
| `pass_policy` | suite 通过规则，例如所有 required case 均通过。 |
| `output_summary` | suite 期望生成的汇总信息语义。 |

## 有效性规则

- `cases` 不能为空。
- `required_cases` 必须是 `cases` 中存在的 `case_id`。
- Runtime MVP 第一版不得把真实 Service 结果作为 suite 通过条件。
- suite 通过不代表阶段二真实数据清洗能力完成，只代表 Runtime 空流程可验收。

## 上游来源

- [[10_Runtime smoke test模块]] 首次定义本概念。
- suite 覆盖范围来自 [[功能模块清单]] 中功能10目标。

## 下游消费者

- 后续 L3 会据此生成 smoke test 入口或测试集合。
- Runtime MVP 验收摘要会读取 [[RuntimeSmokeTestResult]] 判断 suite 是否通过。

## 不负责

- 不定义具体测试框架名称。
- 不规定测试文件必须如何命名。
- 不替代功能8结构化日志模块和功能9 Manifest 与错误摘要模块的接口定义。

## 相关链接

- [[RuntimeSmokeTestCase]]
- [[RuntimeSmokeTestResult]]
- [[10_Runtime smoke test模块]]

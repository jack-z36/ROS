# deploy_004 验收卡片

> 本卡片由验收 sub-agent 使用，配合任务文件 `03_tasks/task/active/l2-01-types/deploy_004_Types层边界校验与全量单测.md`。
> 本 L3 是 L2-01 的收尾：补全 Types 层边界校验并跑全量单测，通过后 Types 层可进入 L2 Gate。

## 验收元数据

| 字段 | 内容 |
|---|---|
| L3 编号 | deploy_004 |
| 任务 | ACT Types 层边界校验完善 + 全量单测 |
| 验收模式 | direct-local |
| 辅助验收模式 | 无 |
| 本地验收是否必须 | 是 |
| 最低验证层级 | unit |
| 验收运行目录 | `/home/hit/ROS` |
| L2 Git 分支 | `feat/model_deploy/l2-01-types` |
| 验收场景 | S1（Types 层维度与段序单测，含负向） |
| 验收证据落点 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/deploy_004_pytest_all.txt` |

## 验收对象

在 deploy_001~003 已建成的 `action_spec.py` / `state_codec.py` / `action_codec.py` 基础上，补全边界校验并跑全量 types 测试，重点核对：

- `as_vector()` 返回 float32（dtype 校验）。
- `state_codec.encode_state` 校验 `width∈[0,1]`，越界抛 ValueError。
- `conftest.py` 提供 valid / denorm 公共 fixture。
- 全量负向测试覆盖：错维度 / 错 dtype / 模长≠1 / width 越界 / 空 / None。

## 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/ -v
```

## 静态检查清单

| 检查项 | 通过标准 |
|---|---|
| dtype 校验 | `action_spec.as_vector()` 返回 float32 |
| width 值域校验 | `state_codec.encode_state` 校验 `width∈[0,1]`，越界（如 -0.1 / 1.5）抛 ValueError |
| 公共 fixture | `act/tests/types/conftest.py` 提供 valid（合法 state/action）与 denorm（模长≠1 四元数）fixture |
| 负向测试覆盖 | 覆盖：错维度 / 错 dtype / 模长≠1 / width 越界 / 空 / None，均抛预期异常 |
| 全量测试 | `pytest src/model_deploy/act/tests/types/ -v` 全部 PASSED |
| 禁改边界 | 未修改 `pi05/`、`third_party/`、`pi05_old/`；未改已固化的维度常量与段序定义 |
| 产物落点 | 源码与测试均在 `act/types/` 与 `act/tests/types/` 下，符合 `ACT代码树分层与产物落点约束.md` |

## 落点校验

| 产物 | 声明落点 | 实际是否存在 | 是否一致 |
|---|---|---|---|
| action_spec 补充 | `src/model_deploy/act/types/action_spec.py` |  |  |
| state_codec 补充 | `src/model_deploy/act/types/state_codec.py` |  |  |
| action_codec 补充 | `src/model_deploy/act/types/action_codec.py` |  |  |
| 公共 fixture | `src/model_deploy/act/tests/types/conftest.py` |  |  |
| 负向测试 | `act/tests/types/test_action_spec.py`、`test_state_codec.py`、`test_action_codec.py` |  |  |

> 落点与声明不符时判 `FAIL_LOCAL`。

## 结论

- 验收结论：`PASS_LOCAL` / `FAIL_LOCAL` / `BLOCKED_ENV`
- 验收 sub-agent：
- 验收时间：
- 备注（若 FAIL/BLOCKED 填失败项与排查入口）：

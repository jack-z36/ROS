# deploy_008 验收卡片

> 本卡片由验收 sub-agent 使用，配合任务文件 `03_tasks/task/active/l2-02-config/deploy_008_deploy_yaml与全量单测.md`。
> 本 L3 是 L2-02 的收尾：新建 deploy.yaml 完整实例并跑全量 config 单测，通过后 Config 层可进入 L2 Gate。

## 验收元数据

| 字段 | 内容 |
|---|---|
| L3 编号 | deploy_008 |
| 任务 | ACT deploy.yaml 实例与全量 config 单测 |
| 验收模式 | direct-local |
| 辅助验收模式 | 无 |
| 本地验收是否必须 | 是 |
| 最低验证层级 | unit |
| 验收运行目录 | `/home/hit/ROS` |
| L2 Git 分支 | `feat/model_deploy/l2-02-config` |
| 验收场景 | S2（Config 层加载与校验，含负向） |
| 验收证据落点 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/deploy_008_pytest_all.txt` |

## 验收对象

在 deploy_005~007 已建成的 `schema.py` 全段基础上，新建完整 yaml 实例与全量集成测试，重点核对：

- `src/model_deploy/act/config_files/deploy.yaml`：完整配置实例（含 bundle/runtime/topics/safety 全段）。
- `act/tests/config/test_deploy_config_full.py`：加载完整 yaml + 全字段断言 + 负向测试。
- `act/tests/config/conftest.py`：公共 fixture（合法/非法 yaml 构造器）。

## 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/ -v
```

## 静态检查清单

| 检查项 | 通过标准 |
|---|---|
| deploy.yaml 全段 | yaml 含 `bundle`/`runtime`/`image`/`topics`/`safety` 全段 |
| 维度 | `runtime.action_dim==16` 且 `runtime.state_dim==16` |
| topic 前缀 | topics 全部 `/act/*` 前缀（observation 走 `/act/observation/*`，command 走 `/act/policy_action` 等） |
| 完整加载 | `load_deploy_config(deploy.yaml)` 成功，全字段断言通过（mode/dim/topic/safety） |
| 负向：缺段 | 缺 bundle 段时抛 `DeployConfigError` |
| 负向：错 mode | runtime mode 非三档时抛 `DeployConfigError` |
| 负向：topic 空/非 str | observation/command 字段空或非 str 时抛 `DeployConfigError` |
| 负向覆盖完整 | 负向测试覆盖：缺段 / 错 mode / topic 空 / （若 schema 强校验）错 dim |
| 公共 fixture | `conftest.py` 提供 `valid_deploy_yaml_text()` 与 `make_invalid_yaml(mutation)` |
| 全量测试 | `pytest src/model_deploy/act/tests/config/ -v` 全部 PASSED（含 005~008 所有测试） |
| 禁改边界 | 未修改 schema.py 的 dataclass 字段定义（除非修 bug 且标注）；未改 `pi05/`、`pi05_old/`、`act/types/` |
| 产物落点 | 实例在 `act/config_files/`，测试在 `act/tests/config/`，符合 `ACT代码树分层与产物落点约束.md` |

## 落点校验

| 产物 | 声明落点 | 实际是否存在 | 是否一致 |
|---|---|---|---|
| 配置实例 | `src/model_deploy/act/config_files/deploy.yaml` |  |  |
| 全量单测 | `src/model_deploy/act/tests/config/test_deploy_config_full.py` |  |  |
| 公共 fixture | `src/model_deploy/act/tests/config/conftest.py` |  |  |

> 落点与声明不符时判 `FAIL_LOCAL`。

## 结论

- 验收结论：`PASS_LOCAL` / `FAIL_LOCAL` / `BLOCKED_ENV`
- 验收 sub-agent：
- 验收时间：
- 备注（若 FAIL/BLOCKED 填失败项与排查入口）：

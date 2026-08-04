# deploy_005 验收卡片

> 本卡片由验收 sub-agent 使用，配合任务文件 `03_tasks/task/active/l2-02-config/deploy_005_config骨架与基础dataclass.md`。

## 验收元数据

| 字段 | 内容 |
|---|---|
| L3 编号 | deploy_005 |
| 任务 | 新建 ACT config schema 骨架与基础 dataclass |
| 验收模式 | direct-local |
| 辅助验收模式 | 无 |
| 本地验收是否必须 | 是 |
| 最低验证层级 | unit |
| 验收运行目录 | `/home/hit/ROS` |
| L2 Git 分支 | `feat/model_deploy/l2-02-config` |
| 验收场景 | S2（Config 层加载与校验） |
| 验收证据落点 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/deploy_005_pytest.txt` |

## 验收对象

`src/model_deploy/act/config/schema.py`（新建），重点核对：

- `DeployConfigError`（ValueError 子类，直接复用同事源码）。
- 辅助函数集完整：`_str`/`_optional_str`/`_choice`/`_bool`/`_int_value`/`_float`/`_positive_int`/`_non_negative_int`/`_positive_float`/`_float_list`/`_mapping`/`_required_mapping`/`_path`（与同事 `:465-561` 逻辑一致）。
- `BundleConfig`：含 `bundle_dir` + `resolved_bundle_dir`。
- `ImageConfig`：`image_size`/`resize_mode`/`transport`。
- `RuntimeConfig`：mode 三档枚举（dry-run/shadow-run/safe-run）+ `__post_init__` 校验；`action_dim/state_dim` 暂留原值（007 改）。
- `DeployConfig` 顶层容器 + `from_mapping`；`load_deploy_config(path)`。

## 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/test_schema_base.py -v
```

## 静态检查清单

| 检查项 | 通过标准 |
|---|---|
| 辅助函数完整 | `_str/_optional_str/_choice/_bool/_int_value/_float/_positive_int/_non_negative_int/_positive_float/_float_list/_mapping/_required_mapping/_path` 全部存在，与同事源码逻辑一致 |
| BundleConfig | 含 `bundle_dir` 与 `resolved_bundle_dir` |
| ImageConfig | 含 `image_size`/`resize_mode`/`transport` |
| RuntimeConfig 框架 | mode 三档枚举（dry-run/shadow-run/safe-run）+ `__post_init__` 校验存在 |
| DeployConfig 顶层 | `from_mapping` 可解析 bundle/runtime/image（topics/safety 占位，TODO 标注待 006/007 填充） |
| load 最小 yaml | `load_deploy_config` 能加载含 bundle+runtime 的最小合法 YAML，返回 `DeployConfig` 实例 |
| 缺 bundle 报错 | YAML 缺 `bundle` 段时抛 `DeployConfigError` |
| 非法 hz 报错 | runtime 非法 inference_hz（如 ≤0）抛 `DeployConfigError` |
| 禁改边界 | 未修改 `pi05/`、`third_party/`、`pi05_old/`、`act/types/`（L2-01 产物） |
| 产物落点 | 源码与测试均在 `act/config/` 与 `act/tests/config/` 下，符合 `ACT代码树分层与产物落点约束.md` |

## 落点校验

| 产物 | 声明落点 | 实际是否存在 | 是否一致 |
|---|---|---|---|
| config schema 源码 | `src/model_deploy/act/config/schema.py` |  |  |
| config 包标记 | `src/model_deploy/act/config/__init__.py` |  |  |
| config_files 目录 | `src/model_deploy/act/config_files/`（空，008 填） |  |  |
| 测试包标记 | `act/tests/config/__init__.py` |  |  |
| 单测 | `src/model_deploy/act/tests/config/test_schema_base.py` |  |  |

> 落点与声明不符时判 `FAIL_LOCAL`。

## 结论

- 验收结论：`PASS_LOCAL` / `FAIL_LOCAL` / `BLOCKED_ENV`
- 验收 sub-agent：
- 验收时间：
- 备注（若 FAIL/BLOCKED 填失败项与排查入口）：

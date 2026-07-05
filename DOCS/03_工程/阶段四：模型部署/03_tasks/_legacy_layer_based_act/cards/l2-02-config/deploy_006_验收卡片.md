# deploy_006 验收卡片

> 本卡片由验收 sub-agent 使用，配合任务文件 `03_tasks/task/active/l2-02-config/deploy_006_TopicsConfig.md`。

## 验收元数据

| 字段 | 内容 |
|---|---|
| L3 编号 | deploy_006 |
| 任务 | 新建 ACT TopicsConfig（observation TCP/gripper + 单路 command） |
| 验收模式 | direct-local |
| 辅助验收模式 | 无 |
| 本地验收是否必须 | 是 |
| 最低验证层级 | unit |
| 验收运行目录 | `/home/hit/ROS` |
| L2 Git 分支 | `feat/model_deploy/l2-02-config` |
| 验收场景 | S2（Config 层加载与校验） |
| 验收证据落点 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/deploy_006_pytest.txt` |

## 验收对象

`src/model_deploy/act/config/schema.py` 中 TopicsConfig 段（在 deploy_005 骨架上填充），重点核对：

- `ObservationTopicsConfig`：6 字段（双目 + TCP + gripper）—— `left_image` / `right_image` / `left_tcp_pose` / `right_tcp_pose` / `left_gripper_state` / `right_gripper_state`，全部 str 必填。
- `CommandTopicsConfig`：3 字段（单路）—— `policy_action` / `status` / `metrics`。
- `TopicsConfig`：`namespace` + `observation` + `command`（**不含** bridge_output/mux）。
- topic 默认名按 `/act/observation/*` 与 `/act/policy_action` 等拼装。
- 已接入 `DeployConfig` 顶层与 `_deploy_from_mapping`（替换 005 占位）。
- 无 `BridgeTopicsConfig` / `MuxTopicsConfig` 残留。

## 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/test_topics.py -v
```

## 静态检查清单

| 检查项 | 通过标准 |
|---|---|
| ObservationTopicsConfig 字段 | 6 字段：`left_image`/`right_image`/`left_tcp_pose`/`right_tcp_pose`/`left_gripper_state`/`right_gripper_state`，全部 str 必填 |
| CommandTopicsConfig 字段 | 3 字段单路：`policy_action`/`status`/`metrics`（无 left/right arm/hand 多路） |
| topic 前缀 | 默认名前缀 `/act/`（observation 走 `/act/observation/*`，command 走 `/act/policy_action` 等） |
| TopicsConfig 顶层 | 含 `namespace`+`observation`+`command`，**无** `bridge_output`/`mux` |
| 无 Bridge/Mux 残留 | schema.py 中无 `BridgeTopicsConfig`/`MuxTopicsConfig` 类定义 |
| 接入 DeployConfig | `_deploy_from_mapping` 中 `topics=TopicsConfig(...)` 替换 005 占位，TODO 注释已清除 |
| 禁改边界 | 未修改 deploy_005 的 BundleConfig/ImageConfig/辅助函数/RuntimeConfig 框架；未改 `pi05/`、`pi05_old/`、`act/types/` |
| 产物落点 | 源码在 `act/config/schema.py`，测试在 `act/tests/config/test_topics.py`，符合 `ACT代码树分层与产物落点约束.md` |

## 落点校验

| 产物 | 声明落点 | 实际是否存在 | 是否一致 |
|---|---|---|---|
| schema.py 补充 TopicsConfig | `src/model_deploy/act/config/schema.py` |  |  |
| 单测 | `src/model_deploy/act/tests/config/test_topics.py` |  |  |

> 落点与声明不符时判 `FAIL_LOCAL`。

## 结论

- 验收结论：`PASS_LOCAL` / `FAIL_LOCAL` / `BLOCKED_ENV`
- 验收 sub-agent：
- 验收时间：
- 备注（若 FAIL/BLOCKED 填失败项与排查入口）：

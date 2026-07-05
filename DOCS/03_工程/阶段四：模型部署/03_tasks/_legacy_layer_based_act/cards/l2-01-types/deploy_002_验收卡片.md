# deploy_002 验收卡片

> 本卡片由验收 sub-agent 使用，配合任务文件 `03_tasks/task/active/l2-01-types/deploy_002_新建ACT_state_codec.md`。

## 验收元数据

| 字段 | 内容 |
|---|---|
| L3 编号 | deploy_002 |
| 任务 | 新建 ACT state_codec（16D 分组段序） |
| 验收模式 | direct-local |
| 辅助验收模式 | 无 |
| 本地验收是否必须 | 是 |
| 最低验证层级 | unit |
| 验收运行目录 | `/home/hit/ROS` |
| L2 Git 分支 | `feat/model_deploy/l2-01-types` |
| 验收场景 | S1（Types 层维度与段序单测） |
| 验收证据落点 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/deploy_002_pytest.txt` |

## 验收对象

`src/model_deploy/act/types/state_codec.py`，重点核对：

- `ActBimanualState` frozen dataclass 字段为 TCP+width 四段：`left_tcp_pose` / `right_tcp_pose` / `left_gripper_width` / `right_gripper_width`。
- `encode_state(state)` 输出 16D，**分组段序**：左tcp7 + 右tcp7 + 左width1 + 右width1（注意与 action 的交替段序区分）。
- quaternion 模长校验：encode 时 `abs(norm-1.0) > 1e-3` 抛 ValueError。

## 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/test_state_codec.py -v
```

## 静态检查清单

| 检查项 | 通过标准 |
|---|---|
| encode_state 输出维度与段序 | 输出 16D 分组段序：左tcp7 + 右tcp7 + 左width1 + 右width1 |
| ActBimanualState 字段 | 字段为 `left_tcp_pose`/`right_tcp_pose`/`left_gripper_width`/`right_gripper_width` |
| quaternion 模长校验 | quaternion 模长≠1（容差 1e-3）时抛 ValueError |
| 段序区分 | state 为分组段序，不得与 action 交替段序混淆 |
| 禁改边界 | 未修改 `action_spec.py`（deploy_001 产物）、`pi05/`、`pi05_old/` |
| 产物落点 | 源码与测试均在 `act/types/` 与 `act/tests/types/` 下，符合 `ACT代码树分层与产物落点约束.md` |

## 落点校验

| 产物 | 声明落点 | 实际是否存在 | 是否一致 |
|---|---|---|---|
| state_codec 源码 | `src/model_deploy/act/types/state_codec.py` |  |  |
| 单测 | `src/model_deploy/act/tests/types/test_state_codec.py` |  |  |

> 落点与声明不符时判 `FAIL_LOCAL`。

## 结论

- 验收结论：`PASS_LOCAL` / `FAIL_LOCAL` / `BLOCKED_ENV`
- 验收 sub-agent：
- 验收时间：
- 备注（若 FAIL/BLOCKED 填失败项与排查入口）：

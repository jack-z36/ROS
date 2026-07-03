# deploy_001 验收卡片

> 本卡片由验收 sub-agent 使用，配合任务文件 `03_tasks/task/active/l2-01-types/deploy_001_新建ACT_action_spec.md`。

## 验收元数据

| 字段 | 内容 |
|---|---|
| L3 编号 | deploy_001 |
| 任务 | 新建 ACT action_spec（16D TCP+width 结构） |
| 验收模式 | direct-local |
| 辅助验收模式 | 无 |
| 本地验收是否必须 | 是 |
| 最低验证层级 | unit |
| 验收运行目录 | `/home/hit/ROS` |
| L2 Git 分支 | `feat/model_deploy/l2-01-types` |
| 验收场景 | S1（Types 层维度与段序单测） |
| 验收证据落点 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/deploy_001_pytest.txt` |

## 验收对象

`src/model_deploy/act/types/action_spec.py`，重点核对：

- 常量 `ACTION_DIM=16`、`STATE_DIM=16`（及 `TCP_POSE_DOF=7`、`GRIPPER_WIDTH_DOF=1`）。
- `BimanualAction` frozen dataclass 字段为 TCP+width 四段：`left_tcp_pose` / `left_gripper_width` / `right_tcp_pose` / `right_gripper_width`。
- `split_bimanual_action(action)` 按**交替段序**拆解 16D：`[0:7]→left_tcp, [7]→left_width, [8:15]→right_tcp, [15]→right_width`。

## 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/test_action_spec.py -v
```

## 静态检查清单

| 检查项 | 通过标准 |
|---|---|
| ACTION_DIM / STATE_DIM | `ACTION_DIM==16` 且 `STATE_DIM==16` |
| BimanualAction 字段 | 字段为 `left_tcp_pose`/`left_gripper_width`/`right_tcp_pose`/`right_gripper_width`（TCP+width 四段，非关节/手） |
| as_vector() 段序 | 输出 16D 段序交替：左tcp7 + 左width1 + 右tcp7 + 右width1 |
| split_bimanual_action | 正确拆解 16D（与 as_vector round-trip 一致） |
| 非法维度 | 输入 15D / 17D 时抛 ValueError |
| 禁改边界 | 未修改 `pi05/`、`third_party/`、`pi05_old/`（同事源码只读） |
| 产物落点 | 源码与测试均在 `act/types/` 与 `act/tests/types/` 下，符合 `ACT代码树分层与产物落点约束.md` |

## 落点校验

| 产物 | 声明落点 | 实际是否存在 | 是否一致 |
|---|---|---|---|
| action_spec 源码 | `src/model_deploy/act/types/action_spec.py` |  |  |
| 包标记 | `src/model_deploy/act/types/__init__.py` |  |  |
| 测试包标记 | `src/model_deploy/act/tests/__init__.py`、`act/tests/types/__init__.py` |  |  |
| 单测 | `src/model_deploy/act/tests/types/test_action_spec.py` |  |  |

> 落点与声明不符时判 `FAIL_LOCAL`。

## 结论

- 验收结论：`PASS_LOCAL` / `FAIL_LOCAL` / `BLOCKED_ENV`
- 验收 sub-agent：
- 验收时间：
- 备注（若 FAIL/BLOCKED 填失败项与排查入口）：

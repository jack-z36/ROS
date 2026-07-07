# deploy_003 验收卡片

> 本卡片由验收 sub-agent 使用，配合任务文件 `03_tasks/task/active/l2-01-types/deploy_003_新建ACT_action_codec.md`。

## 验收元数据

| 字段 | 内容 |
|---|---|
| L3 编号 | deploy_003 |
| 任务 | 新建 ACT action_codec（16D 交替段序编解码） |
| 验收模式 | direct-local |
| 辅助验收模式 | 无 |
| 本地验收是否必须 | 是 |
| 最低验证层级 | unit |
| 验收运行目录 | `/home/hit/ROS` |
| L2 Git 分支 | `feat/model_deploy/l2-01-types` |
| 验收场景 | S1（Types 层维度与段序单测） |
| 验收证据落点 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/deploy_003_pytest.txt` |

## 验收对象

`src/model_deploy/act/types/action_codec.py`，重点核对：

- `ensure_action_vector(action)`：校验 size==`ACTION_DIM`(16)，返回 float32 向量。
- `ensure_action_chunk(chunk, *, action_dim=ACTION_DIM)`：校验 2D，`shape[1]==16`。
- `split_action(action)`：委托 `action_spec.split_bimanual_action(ensure_action_vector(action))`，与 `as_vector()` round-trip 一致。

## 自动化验收命令

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/types/test_action_codec.py -v
```

## 静态检查清单

| 检查项 | 通过标准 |
|---|---|
| ensure_action_vector | 校验 16D，非法维度（15D/17D）抛 ValueError；返回 float32 |
| ensure_action_chunk | 校验 2D 且 `shape[1]==16`，ndim≠2 或末维≠16 报错 |
| split_action round-trip | `split_action → as_vector()` 等于原始输入（16D 一致） |
| 委托关系 | `split_action` 委托 `action_spec.split_bimanual_action`，不重复实现段序 |
| 非法维度/ndim | 非法维度、非法 ndim、空输入抛预期异常 |
| 禁改边界 | 未修改 `action_spec.py`/`state_codec.py`、`pi05/`、`pi05_old/` |
| 产物落点 | 源码与测试均在 `act/types/` 与 `act/tests/types/` 下，符合 `ACT代码树分层与产物落点约束.md` |

## 落点校验

| 产物 | 声明落点 | 实际是否存在 | 是否一致 |
|---|---|---|---|
| action_codec 源码 | `src/model_deploy/act/types/action_codec.py` |  |  |
| 单测 | `src/model_deploy/act/tests/types/test_action_codec.py` |  |  |

> 落点与声明不符时判 `FAIL_LOCAL`。

## 结论

- 验收结论：`PASS_LOCAL` / `FAIL_LOCAL` / `BLOCKED_ENV`
- 验收 sub-agent：
- 验收时间：
- 备注（若 FAIL/BLOCKED 填失败项与排查入口）：

# L3 微元改造任务：policy_loader._build_batch + image_names 默认值

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-03 数据装配 Service 层
来源 Delta：D10（bundle 语义对齐）、D9（encoded_state 维度）
L3 编号：deploy_011
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_011_policy_loader_build_batch.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：model_deploy-l2-03-assembly
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
对应 L2 运行验收场景：[S1, S4]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_011_验收卡片.md
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs

## 3. 本次唯一目标

```text
让 policy_loader 的 _build_batch 和 image_names 默认值跟随新的 encoded_state 维度（16D）和鱼眼相机名（left_fisheye/right_fisheye），确保 observation snapshot → model batch 的映射与新 bundle 和新 codec 一致。
```

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_011
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_011_policy_loader_build_batch.md
  group: l2-03-assembly
  branch: model_deploy-l2-03-assembly
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
  acceptance_scenarios: [S1, S4]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_011_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs
  wave: 1
  parallel_group: l2-03-assembly-p1
  depends_on: [deploy_002]
  must_run_after: []
  can_run_parallel_with: [deploy_009]
  blocks: [deploy_012]
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/src/pi05/deploy/models/policy_loader.py
    modules:
      - pi05.deploy.models.policy_loader
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D10 + D9 |
| 变更对象 | Policy / Model Contract + encoded_state 维度 |
| AS-IS 契约 | `_build_batch`（policy_loader.py:80-95）用 observation.encoded_state（26D）+ image_names（默认 top/left_wrist/right_wrist）；`Pi05PolicyRuntime.__init__` image_names 默认 (top,left_wrist,right_wrist)（L43）；`_manifest_image_names` fallback 默认 (top,left_wrist,right_wrist)（L160）。 |
| TO-BE 契约 | encoded_state 自动跟随 16D（deploy_002 改 encode_bimanual_state）；image_names 默认改 (left_fisheye,right_fisheye)；_build_batch 逻辑不变（它用 observation.encoded_state 和 image_names，两者已改）。 |
| 兼容性要求 | 跟随 L2-01/L2-02。 |
| 回滚要求 | git 回退。 |

### 所属 L2 改造工作包

- L2 名称：L2-03 数据装配 Service 层
- 本 L3 在该 L2 中的位置：与 deploy_009 并行（改不同文件）。policy_loader 是 batch 构建核心。
- 本 L3 完成后解锁：deploy_012（dry-run 验证 batch 构建）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `_build_batch` | policy_loader.py:80-95 | state_normalizer.normalize(encoded_state) + 拼 observation.state/task/images | encoded_state 维度自动跟随（用 observation.encoded_state，deploy_002 已改 encode 输出 16D）；逻辑无需改 | 否（确认即可） |
| `Pi05PolicyRuntime.__init__` image_names 默认 | policy_loader.py:43 `(top,left_wrist,right_wrist)` | 默认相机名 | 改 (left_fisheye,right_fisheye) | 是 |
| `_manifest_image_names` fallback | policy_loader.py:158-164 | manifest 缺 cameras 时 fallback (top,left_wrist,right_wrist) | 改 (left_fisheye,right_fisheye) | 是 |
| `predict_action_chunk` | policy_loader.py:63-78 | 推理 + unnormalize + 维度校验 action_dim | action_dim 自动跟随（来自 config，deploy_007 改 16） | 否（确认） |
| `load_policy_runtime` | policy_loader.py:110-155 | bundle 加载 + manifest 解析 | action_dim 从 manifest 或 config（L149） | 否（确认） |

### 必须保留的现有行为

- `_build_batch` 的「state 在 CPU normalize + image 组装」流程（保留，C5 约束：state normalizer 在 CPU）。
- `predict_action_chunk` 的推理 + unnormalize + 维度校验。
- `image_names` 来自 manifest 动态绑定（set_required_image_keys 用它）。
- bundle 加载流程（manifest/experiment_config/adapter/normalizers）。

### 已知风险

- `_build_batch` 用 `observation.encoded_state`——这个值来自 collector.snapshot（deploy_009）调 encode_bimanual_state（deploy_002）。只要 deploy_002/009 改好，这里自动是 16D。**本 L3 实际改动可能很小**（只改 image_names 默认值）。
- image_names 最终来自 bundle manifest（`_manifest_image_names`），如果新 bundle 的 manifest 声明了 left_fisheye/right_fisheye，那默认值只是 fallback。但 fallback 仍要改，防止 manifest 缺 cameras 字段时用错。
- state_normalizer 维度必须与 encoded_state 一致（16D）——这由新 bundle 的 normalizers.json 保证（Q1：新 bundle 两天后到，用 16D 训练）。

## 6. 真实改造边界

### 本次允许做

- `Pi05PolicyRuntime.__init__` image_names 默认值（L43）：`(top,left_wrist,right_wrist)` → `(left_fisheye,right_fisheye)`。
- `_manifest_image_names` fallback 默认值（L160）：同上。
- 确认 `_build_batch`（L80-95）无需改逻辑（它用 observation.encoded_state，自动 16D）。
- 确认 `predict_action_chunk` 的 action_dim 校验自动跟随（来自 config/manifest，16）。

### 本次不做

- 不改 `_build_batch` 的拼装逻辑（无需改）。
- 不改 `predict_action_chunk` 的推理流程。
- 不改 bundle 加载流程。
- 不改 collector（deploy_009）/ deploy_node（deploy_010）。
- 不补单测/dry-run（deploy_012 做）。

### 明确禁止修改

- 禁止改 `_build_batch` 的 state normalize + image 组装逻辑。
- 禁止改 `predict_action_chunk` 推理流程。
- 禁止改 bundle 加载（_validate_bundle/_load_bundle_experiment_config/_load_adapter）。
- 禁止改 policy_loader.py 以外的文件。

### Adapter / 直接修改策略

```text
审查 + 默认值更新。_build_batch 逻辑自动跟随（用 observation.encoded_state）。核心改动是 image_names 默认值/fallback 改为鱼眼。如果审查发现逻辑零改动（除默认值），记录审查结论。回滚靠 git。
```

## 7. 实施步骤

1. **改 `__init__` image_names 默认**（L43）：(left_fisheye, right_fisheye)。
2. **改 `_manifest_image_names` fallback**（L160）：(left_fisheye, right_fisheye)。
3. **审查 `_build_batch`**（L80-95）：确认用 observation.encoded_state（自动 16D）+ image_names（鱼眼），逻辑无需改。
4. **审查 `predict_action_chunk`**（L63-78）：确认 action_dim 校验来自 config/manifest（16）。
5. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
src = open('src/model_deploy/pi05/deploy/src/pi05/deploy/models/policy_loader.py', encoding='utf-8').read()
# image_names 默认值改鱼眼
assert 'left_fisheye' in src and 'right_fisheye' in src
# 旧相机名在默认值位置应删除
import re
# 找 image_names 默认值附近
assert 'top' not in src.split('image_names')[1][:100] or 'left_fisheye' in src.split('image_names')[1][:200], 'image_names default should use fisheye'
# _build_batch 保留
assert '_build_batch' in src and 'observation.encoded_state' in src
print('deploy_011 验收通过: image_names→鱼眼, _build_batch保留')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 默认值断言 | 上述命令通过 |
| dry-run | 否（deploy_012 做） | — | — |

### 真机风险控制

不适用。

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/deploy/src/pi05/deploy/models/policy_loader.py`（仅 image_names 默认值 + fallback）

## 10. 禁止修改

- `_build_batch` 拼装逻辑。
- `predict_action_chunk` 推理流程。
- bundle 加载流程。
- 其他文件。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D10 + Q1 bundle 16D）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-03-数据装配Service层.md`

### 必读代码

1. `src/model_deploy/pi05/deploy/src/pi05/deploy/models/policy_loader.py`（本 L3 修改）
2. `src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py`（deploy_002 改后，确认 encode_bimanual_state 输出 16D）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_002（state_codec，encode_bimanual_state 16D）。
2. 同组：deploy_009（并行）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_002]` 已完成。

```text
审查 _build_batch（确认无需改逻辑）
→ 改 image_names 默认值
→ 验证通过
→ 记录审查结论
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] image_names 默认值改为鱼眼。
- [ ] _manifest_image_names fallback 改为鱼眼。
- [ ] _build_batch 逻辑保留（审查确认自动跟随 16D）。
- [ ] predict_action_chunk 流程保留。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- policy_loader.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、修改内容（image_names 默认值）、审查结论（_build_batch 是否零逻辑改动）、验收结果、成功标准勾选、真机影响（无）、回滚、未做事项（没改 _build_batch 逻辑/predict/bundle 加载）、后续建议（deploy_012 dry-run）。

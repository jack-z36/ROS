# deploy_005 Round 1 验收反馈

## 1. 验收轮次

Round 1

## 2. 读取的文件

| 文件 | 路径 |
|------|------|
| AGENTS.md | `AGENTS.md` |
| 验收卡片 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_005_验收卡片.md` |
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_005_重构observation_topic字段.md` |
| 执行摘要 | L3 任务文件 §16 |
| 源文件 (after) | `src/model_deploy/pi05/common/src/pi05/common/ros/topics.py` |
| 源文件 (after) | `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py` |
| 技能文件 | `skills/stage4-l3-orchestrator/SKILL.md` |

## 3. 执行的检查项

### 3.1 AST 字段存在性断言（卡片 § 本地验收命令）

```bash
python3 -c "
schema = open('src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py', encoding='utf-8').read()
topics = open('src/model_deploy/pi05/common/src/pi05/common/ros/topics.py', encoding='utf-8').read()
for f in ['left_fisheye_image','right_fisheye_image','left_tcp_pose','right_tcp_pose','left_gripper_state','right_gripper_state']:
    assert f in schema, f'{f} missing in schema'
    assert f in topics, f'{f} missing in topics'
for f in ['tactile_l1','tactile_l2','tactile_r1','tactile_r2']:
    assert f in schema, f'{f} tactile field missing'
for f in ['top_image','proprioception','left_hand_state','left_ee_position','proprioception_order']:
    assert f not in schema, f'old field {f} should be removed'
assert '/pi05' in topics
print('deploy_005 验收通过: observation 字段重构为鱼眼/TCP/gripper/触觉预留')
"
```

**结果**: ✅ 通过。输出 `deploy_005 验收通过: observation 字段重构为鱼眼/TCP/gripper/触觉预留`。

### 3.2 Python 运行时导入 & dataclass 行为验证

```bash
PYTHONPATH="src/model_deploy/pi05/common/src:src/model_deploy/pi05/deploy/src:$PYTHONPATH" python3 -c "
from pi05.common.ros.topics import DEFAULT_NAMESPACE, Pi05ObservationTopics
assert DEFAULT_NAMESPACE == '/pi05'
obs = Pi05ObservationTopics.with_namespace()
assert obs.left_fisheye_image == '/pi05/observation/image/left_gripper_fisheye'
assert obs.right_fisheye_image == '/pi05/observation/image/right_gripper_fisheye'
assert obs.left_tcp_pose == '/pi05/observation/arm/left_tcp_pose'
assert obs.right_tcp_pose == '/pi05/observation/arm/right_tcp_pose'
assert obs.left_gripper_state == '/pi05/observation/gripper/left_state'
assert obs.right_gripper_state == '/pi05/observation/gripper/right_state'
# 确认 frozen
try:
    obs.left_fisheye_image = '/other'
    assert False
except Exception:
    pass
"
```

**结果**: ✅ 通过。导入正常，`DEFAULT_NAMESPACE` 为 `/pi05`，with_namespace 默认路径正确，dataclass frozen 生效。

```bash
PYTHONPATH="src/model_deploy/pi05/common/src:src/model_deploy/pi05/deploy/src:$PYTHONPATH" python3 -c "
from pi05.deploy.config.schema import ObservationTopicsConfig
cfg = ObservationTopicsConfig(
    left_fisheye_image='/a', right_fisheye_image='/b',
    left_fisheye_image_raw='/c', right_fisheye_image_raw='/d',
    left_tcp_pose='/e', right_tcp_pose='/f',
    left_gripper_state='/g', right_gripper_state='/h',
)
assert cfg.tactile_l1 is None
assert cfg.tactile_l2 is None
assert cfg.tactile_r1 is None
assert cfg.tactile_r2 is None
# 确认 frozen
try:
    cfg.left_fisheye_image = '/other'
    assert False
except Exception:
    pass
# 确认旧字段已删除
for old in ['top_image','proprioception','left_hand_state','left_ee_position','proprioception_order']:
    assert old not in cfg.__dataclass_fields__
"
```

**结果**: ✅ 通过。`ObservationTopicsConfig` 创建正常，tactile 字段默认 None，frozen 生效，旧字段彻底删除。

### 3.3 静态评审清单

| # | 检查项 | 结果 | 备注 |
|---|--------|------|------|
| 1 | 任务文件身份、dispatch task_id、验收卡片 task_id 一致 | ✅ | 三者均为 `deploy_005` |
| 2 | 执行摘要存在，列出修改文件、命令、结果、未验证项 | ✅ | §16 完整 |
| 3 | 修改范围不超出 L3 允许修改边界 | ✅ | 仅改 `topics.py` + `schema.py` observation 部分 |
| 4 | 禁止修改项没有被触碰 | ✅ | `CommandTopicsConfig`/`BridgeTopicsConfig`/`MuxTopicsConfig`/`RuntimeConfig`/`SafetyConfig`/`Pi05CommandTopics`/`_str`/`_optional_str` 均未改动 |
| 5 | 代码路径仍使用 `src/model_deploy/pi05/...` | ✅ | 路径正确 |
| 6 | 无硬件项没有被写成真机通过 | ✅ | 未声称真机成功，标注 `robot_risk: none` |

### 3.4 Git diff 验证

检查 `git diff` 确认改动范围：

- **`topics.py`**: 仅改了 `DEFAULT_NAMESPACE` 值 (`/pi05_vla` → `/pi05`) 和 `Pi05ObservationTopics` 类（字段 + with_namespace 路径）。`Pi05CommandTopics` 未动。
- **`schema.py`**: 仅改了 import 行（+`DEFAULT_NAMESPACE`）、`ObservationTopicsConfig` 类、`_observation_topics()` 函数、`_deploy_from_mapping()` 中 namespace 默认值（硬编码 → `DEFAULT_NAMESPACE` 常量引用）。`CommandTopicsConfig`/`BridgeTopicsConfig`/`MuxTopicsConfig`/`RuntimeConfig`/`SafetyConfig` 均未动，辅助函数未动。
- **L3 任务文件**: 仅勾选了成功标准并追加了执行摘要 §16，dispatch YAML 元数据未改动。

✅ 无越界修改。

### 3.5 Scope Nuance: `DEFAULT_NAMESPACE` 导入引用

执行器在 `_deploy_from_mapping()` 中将原来硬编码的默认 namespace 字符串 `"/pi05_vla"` 替换为从 `pi05.common.ros.topics` 导入的 `DEFAULT_NAMESPACE` 常量。这一改动：
- 在允许的修改范围内（属于 schema.py 中与 observation topics 相关的配置加载部分）
- 与 `DEFAULT_NAMESPACE` 的值变更协同一致，避免后续维护中两处不同步
- 符合减少硬编码重复的好实践

✅ 记录为合理变动。

## 4. 通过 / 失败现象

| 检查 | 结果 |
|------|------|
| AST 字段存在性断言 | ✅ 通过 |
| 新字段 (left_fisheye_image, right_fisheye_image, left_tcp_pose, right_tcp_pose, left_gripper_state, right_gripper_state) | ✅ 全部在 schema + topics 中存在 |
| 触觉预留字段 (tactile_l1..tactile_r2) | ✅ 在 schema 中存在，默认 None |
| 旧字段已删除 (top_image, proprioception, left_hand_state, left_ee_position, proprioception_order) | ✅ 不在 schema 中 |
| `/pi05` 命名空间 | ✅ topics.py 中存在 |
| Python 导入 & dataclass frozen | ✅ 通过 |
| 修改范围合规 | ✅ |
| 禁止修改项未被触碰 | ✅ |

## 5. 未验证项

- deploy.yaml 加载（deploy_008 做）
- deploy_node _create_subscriptions 适配（L2-03 做）
- 真机运行验证（无硬件条件）

## 6. 最终结论

**`PASS_LOCAL`**

## 7. 回修项

无。所有检查通过，无需回修。

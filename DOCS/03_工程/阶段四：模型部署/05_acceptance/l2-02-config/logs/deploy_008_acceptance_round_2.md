# deploy_008 Acceptance Round 2

## 1. Acceptance Round

Round 2 / max 3

## 2. Files Read

- `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_008_验收卡片.md` (acceptance card)
- `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_008_deploy_yaml与单测.md` (L3 task file with round-2 execution summary)
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/deploy_008_acceptance_round_1.md` (round 1 feedback)
- `skills/stage4-l3-orchestrator/SKILL.md` (orchestrator rules)
- `src/model_deploy/pi05/tests/deploy/test_config_tcp_width.py` (test file, verified at new path)
- `src/model_deploy/pi05/tests/deploy/conftest.py` (test path helper)
- `src/model_deploy/pi05/deploy/config/deploy.yaml` (updated deploy config via git diff)

## 3. Static Review Checklist

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | 任务文件身份、dispatch task_id、验收卡片 task_id 一致 | ✅ PASS | All reference deploy_008 in l2-02-config; confirmed in task file section 2, card section 0 |
| 2 | 执行摘要存在，列出修改文件、命令、结果、未验证项 | ✅ PASS | Round-2 fix section (task file lines 312-329) documents path migration, command, 6-pass result, and unchanged items |
| 3 | 修改范围不超出 L3 的允许修改边界 | ✅ PASS | deploy.yaml changes match TO-BE requirements; test file moved within allowed paths |
| 4 | 禁止修改项没有被触碰；如触碰必须判定 FAIL_LOCAL | ✅ PASS | schema.py and topics.py changes are pre-existing from deploy_005/006/007 (not from deploy_008); confirmed via git diff |
| 5 | 当前代码路径仍使用 src/model_deploy/pi05/... | ✅ PASS | All paths under src/model_deploy/pi05/ |
| 6 | 无硬件项没有被写成真机通过 | ✅ PASS | No hardware claims; risk level is `none` |

## 4. Commands Executed

### 4.1. Acceptance card command (verbatim)

```bash
cd /home/hit/ROS/src/model_deploy/pi05 && python3 -m pytest tests/deploy/test_config_tcp_width.py -v
```

**Result: ✅ 6 passed in 0.03s**

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-7.4.4, pluggy-1.4.0
rootdir: /home/hit/ROS/src/model_deploy/pi05
collected 6 items

tests/deploy/test_config_tcp_width.py::test_load_new_config PASSED       [ 16%]
tests/deploy/test_config_tcp_width.py::test_dims_default_16 PASSED       [ 33%]
tests/deploy/test_config_tcp_width.py::test_safety_tcp_width PASSED      [ 50%]
tests/deploy/test_config_tcp_width.py::test_no_bridge_mux PASSED         [ 66%]
tests/deploy/test_config_tcp_width.py::test_tactile_optional PASSED      [ 83%]
tests/deploy/test_config_tcp_width.py::test_old_config_rejected PASSED   [100%]

============================== 6 passed in 0.03s ===============================
```

### 4.2. Git diff inspection

**deploy.yaml changes** (vs HEAD):
- Namespace `/pi05_vla` → `/pi05`
- Old realsense/proprioception/hand_state/ee_position/rpy removed
- New left/right fisheye, tcp_pose, gripper_state fields added
- Tactile commented out (optional)
- Old 4-command joint targets → single `policy_action`
- `topics.bridge_output` and `topics.mux` sections removed
- Top-level `bridge:` and `mux:` sections removed
- `action_dim`: 14 → 16, `state_dim`: 26 → 16
- `safety.max_joint_delta_rad` → `max_tcp_delta_m`
- `safety.hand_min`/`hand_max` → `gripper_width_min`/`gripper_width_max`

**Result: ✅ deploy.yaml changes remain correct from round 1.**

### 4.3. L2-03/L2-04 consumer edit check

```bash
git diff HEAD --name-only -- src/ | grep -iE "deploy_node|repo|service|data_assembly"
```

**Result: ✅ No L2-03/L2-04 consumer files modified.**

Full changed file list under `src/`:
- `src/model_deploy/pi05/deploy/config/deploy.yaml` ← deploy_008 (allowed)
- `src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py` ← pre-existing
- `src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py` ← pre-existing
- `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py` ← pre-existing
- `src/model_deploy/pi05/common/src/pi05/common/ros/topics.py` ← pre-existing
- `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py` ← pre-existing

New untracked files:
- `src/model_deploy/pi05/tests/deploy/conftest.py` ← deploy_008 (allowed, test support)
- `src/model_deploy/pi05/tests/deploy/test_config_tcp_width.py` ← deploy_008 (allowed, test file)

## 5. Detailed Findings

### 5.1. ✅ FIX VERIFIED: Test file path mismatch (round 1 issue)

The test file has been moved from `deploy/tests/test_config_tcp_width.py` to `tests/deploy/test_config_tcp_width.py`, matching the acceptance card's verbatim command path. The acceptance command now runs successfully without path correction.

### 5.2. ✅ PASS: Acceptance command succeeds verbatim

All 6 tests pass when running the exact command from the acceptance card. No path correction needed.

### 5.3. ✅ PASS: Test content unchanged from round 1 (already verified)

The 6 test cases cover all required scenarios:
1. `test_load_new_config` — loads new deploy.yaml, asserts observation/command fields
2. `test_dims_default_16` — RuntimeConfig action_dim/state_dim == 16 (with and without explicit YAML values)
3. `test_safety_tcp_width` — SafetyConfig has TCP/width fields, no hand_min/max
4. `test_no_bridge_mux` — DeployConfig has no bridge/mux attributes
5. `test_tactile_optional` — Tactile fields default to None when omitted
6. `test_old_config_rejected` — Old AS-IS fields are silently dropped via defaults

### 5.4. ✅ PASS: No forbidden file touches

All non-deploy.yaml tracked changes are pre-existing from deploy_005/006/007 (schema.py, topics.py, action_codec.py, state_codec.py, action_spec.py). deploy_008 only modified deploy.yaml and added test/conftest files.

### 5.5. ✅ PASS: deploy.yaml content is correct (re-verified)

All TO-BE transformations applied as specified and consistent with round 1 assessment.

### 5.6. ✅ PASS: No L2-03/L2-04 edits introduced

No deploy_node, repo, service, or data_assembly files were modified.

## 6. Unverified Items

- Dry-run / shadow-run / safe-run mode at runtime — belongs to L2-03
- Real robot execution — hardware not present (none risk level)
- Remaining pre-existing uncommitted diffs from deploy_005/006/007 — not part of deploy_008

## 7. Conclusion

**PASS_LOCAL**

Round 1's sole failure (test file path mismatch) has been resolved. The test file now resides at `tests/deploy/test_config_tcp_width.py`, matching the acceptance command path. The verbatim command executes successfully with 6/6 tests passing. deploy.yaml content, test logic, and boundary compliance are unchanged from round 1's verification, all of which passed. No new issues introduced.

## 8. Fix Requests

None. No fixes required.

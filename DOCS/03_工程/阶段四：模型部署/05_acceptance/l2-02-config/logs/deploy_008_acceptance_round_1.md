# deploy_008 Acceptance Round 1

## 1. Acceptance Round

Round 1 / max 3

## 2. Files Read

- `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_008_验收卡片.md` (acceptance card)
- `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_008_deploy_yaml与单测.md` (L3 task file with execution summary)
- `skills/stage4-l3-orchestrator/SKILL.md` (orchestrator rules)
- `src/model_deploy/pi05/deploy/config/deploy.yaml` (updated deploy config)
- `src/model_deploy/pi05/deploy/tests/test_config_tcp_width.py` (new test file)
- `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py` (schema - read-only verification)
- `src/model_deploy/pi05/deploy/tests/conftest.py` (test path helper)

## 3. Static Review Checklist

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | 任务文件身份、dispatch task_id、验收卡片 task_id 一致 | ✅ PASS | All reference deploy_008 in l2-02-config |
| 2 | 执行摘要存在，列出修改文件、命令、结果、未验证项 | ✅ PASS | Summary lists deploy.yaml updates, test file, pytest results, no-forbidden-touches |
| 3 | 修改范围不超出 L3 允许修改边界 | ⚠️ 见下 | deploy.yaml changes match allowed scope; test file created at `deploy/tests/` |
| 4 | 禁止修改项没有被触碰 | ✅ PASS | schema.py, topics.py, deploy_node, common code not touched by deploy_008 (diffs show pre-existing changes from deploy_005/006/007) |
| 5 | 代码路径仍使用 src/model_deploy/pi05/... | ✅ PASS | All paths under src/model_deploy/pi05/ |
| 6 | 无硬件项没有被写成真机通过 | ✅ PASS | No hardware claims |

## 4. Commands Executed

### 4.1. Acceptance card command (verbatim)

```bash
cd /home/hit/ROS/src/model_deploy/pi05 && python3 -m pytest tests/deploy/test_config_tcp_width.py -v
```

**Result: ❌ FAIL — file or directory not found: tests/deploy/test_config_tcp_width.py**

The test file was created at `deploy/tests/test_config_tcp_width.py` (per L3 section 9 "允许修改"), but the verification command in L3 section 8 and the acceptance card expect `tests/deploy/test_config_tcp_width.py`.

### 4.2. Corrected command (matching actual file location)

```bash
cd /home/hit/ROS/src/model_deploy/pi05 && python3 -m pytest deploy/tests/test_config_tcp_width.py -v
```

**Result: ✅ 6 passed in 0.03s**

```
deploy/tests/test_config_tcp_width.py::test_load_new_config PASSED
deploy/tests/test_config_tcp_width.py::test_dims_default_16 PASSED
deploy/tests/test_config_tcp_width.py::test_safety_tcp_width PASSED
deploy/tests/test_config_tcp_width.py::test_no_bridge_mux PASSED
deploy/tests/test_config_tcp_width.py::test_tactile_optional PASSED
deploy/tests/test_config_tcp_width.py::test_old_config_rejected PASSED
```

### 4.3. Git diff inspection

```bash
git diff HEAD -- src/model_deploy/pi05/deploy/config/deploy.yaml
```

**Result: ✅ deploy.yaml changes match TO-BE requirements.**

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

### 4.4. L2-03/L2-04 consumer edit check

```bash
git diff HEAD --name-only -- src/ | grep -iE "deploy_node|repo|service|data_assembly"
```

**Result: ✅ No L2-03/L2-04 consumer files modified.**

## 5. Detailed Findings

### 5.1. PASS: deploy.yaml content is correct

All TO-BE transformations applied as specified:
- Observation → fisheye + TCP pose + gripper state (tactile optional)
- Command → single policy_action
- Bridge/Mux → deleted entirely
- Dims → 16/16
- Safety → TCP/width schema

### 5.2. FAIL: Test file path mismatch

The L3 task file has a contradiction between:
- **Section 8 (自动化验收命令)**: `cd src/model_deploy/pi05 && python3 -m pytest tests/deploy/test_config_tcp_width.py -v`
- **Section 9 (允许修改)**: `src/model_deploy/pi05/deploy/tests/test_config_tcp_width.py`

The executor placed the test at `deploy/tests/test_config_tcp_width.py` (per section 9), which means the verification command from section 8 **cannot find the test file**.

The `tests/deploy/` directory already exists with `test_deploy_config.py` from earlier work; placing the new test there would match the verification command.

### 5.3. PASS: Test content is correct

All 6 required test cases exist and pass:
1. `test_load_new_config` — loads new deploy.yaml, asserts observation/command fields
2. `test_dims_default_16` — RuntimeConfig action_dim/state_dim == 16 (with and without explicit YAML values)
3. `test_safety_tcp_width` — SafetyConfig has TCP/width fields, no hand_min/max
4. `test_no_bridge_mux` — DeployConfig has no bridge/mux attributes
5. `test_tactile_optional` — Tactile fields default to None when omitted
6. `test_old_config_rejected` — Old AS-IS fields are silently dropped via defaults

### 5.4. PASS: No forbidden file touches

The uncommitted diffs in `schema.py`, `topics.py`, `action_codec.py`, `state_codec.py`, `action_spec.py` are pre-existing changes from deploy_005/006/007 (not yet committed). deploy_008 did not modify them.

### 5.5. PASS: Execution summary completeness

All required items present:
- Identity check ✅
- Branch check ✅
- Dependencies checked ✅
- Documents read ✅
- deploy.yaml update listed ✅
- Test cases enumerated ✅
- pytest result reported ✅
- No-forbidden-touches confirmed ✅
- Rollback method documented ✅

## 6. Unverified Items

- Dry-run / shadow-run / safe-run mode at runtime — belongs to L2-03
- Real robot execution — hardware not present (none risk level)
- Remaining pre-existing uncommitted diffs from deploy_005/006/007 — not part of deploy_008

## 7. Conclusion

**FAIL_LOCAL**

The test file is at `deploy/tests/test_config_tcp_width.py` but the verification command expects it at `tests/deploy/test_config_tcp_width.py`. The acceptance card's automated command cannot execute successfully as-is.

## 8. Fix Requests (for round 2)

1. **Resolve test file path**: Either
   - (a) Move the test file to `src/model_deploy/pi05/tests/deploy/test_config_tcp_width.py` (matching the verification command path), OR
   - (b) Update the verification command in the L3 task file (section 8) and acceptance card to `deploy/tests/test_config_tcp_width.py` if the `deploy/tests/` location is intentional.

2. After fixing path, re-run the acceptance card command verbatim:
   ```bash
   cd src/model_deploy/pi05 && python3 -m pytest tests/deploy/test_config_tcp_width.py -v
   ```
   and confirm 6 passed.

No other issues found. deploy.yaml content is correct. Test logic is correct. Forbidden files not touched. No L2-03/L2-04 edits present.

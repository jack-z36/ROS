# deploy_004 Acceptance — Round 1

## Metadata

| Field | Value |
|---|---|
| L3 ID | `deploy_004` |
| Acceptance Card | `deploy_004_验收卡片.md` |
| Round | 1 |
| Acceptance Mode | `direct-local` |
| Date | 2026-06-20 |
| Acceptor | Stage4 L3 Acceptance Sub-Agent |

## Files Read

1. `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_004_验收卡片.md` — acceptance card
2. `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_004_types层单测.md` — L3 task file with execution summary
3. `src/model_deploy/pi05/common/tests/test_action_spec_tcp.py` — executor-created test file (13 tests)
4. `src/model_deploy/pi05/common/tests/test_state_codec_tcp.py` — executor-created test file (12 tests)
5. `src/model_deploy/pi05/common/tests/conftest.py` — sys.path helper
6. `src/model_deploy/pi05/common/tests/__init__.py` — package marker
7. `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py` — deploy_001 source
8. `src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py` — deploy_002 source
9. `src/model_deploy/pi05/common/src/pi05/common/data/action_codec.py` — deploy_003 source
10. Git diff (`git diff HEAD`) — read-only verification of changed files

## Static Review Checklist

| # | Check | Result |
|---|---|---|
| 1 | 任务文件身份、dispatch task_id、验收卡片 task_id 一致 | ✅ All match `deploy_004` |
| 2 | 执行摘要存在，列出修改文件、实际命令、结果和未验证项 | ✅ Comprehensive summary in L3 task file section 15 |
| 3 | 修改范围不超出 L3 允许修改边界 | ✅ Only new test files + task file updates; source files modified by prior L3s |
| 4 | 禁止修改项没有被触碰 | ✅ action_spec/state_codec/action_codec not touched by deploy_004 |
| 5 | 代码路径使用 `src/model_deploy/pi05/...` | ✅ Tests under `common/tests/` |
| 6 | 无硬件项没有被写成真机通过 | ✅ No hardware claims |

## Command Execution

### Card-extracted command (stale paths — per card line 37, preferred L3 file's command)

```bash
cd src/model_deploy/pi05 && python3 -m pytest tests/deploy/test_action_spec_tcp.py pi05/common/tests/test_state_codec_tcp.py -v
```

**Issues**: `tests/deploy/test_action_spec_tcp.py` does not exist; actual path is `common/tests/test_action_spec_tcp.py`. Also missing `PYTHONPATH=common/src` needed for clean imports.

### L3 file's recorded actual command (used per card instruction)

```bash
cd src/model_deploy/pi05 && PYTHONPATH=common/src:$PYTHONPATH \
  python3 -m pytest common/tests/test_action_spec_tcp.py common/tests/test_state_codec_tcp.py -v
```

### Actual execution result

```
25 passed in 0.09s
```

All 25 test cases passed:

| Test File | Test Class | Tests |
|---|---|---|
| `test_action_spec_tcp.py` | TestActionDim | 4 (constants) |
| `test_action_spec_tcp.py` | TestBimanualActionFields | 1 (construction) |
| `test_action_spec_tcp.py` | TestAsVector | 3 (dimension, alternating order, non-left-grouped) |
| `test_action_spec_tcp.py` | TestSplit | 3 (alternating order, reject wrong dim, reject empty) |
| `test_action_spec_tcp.py` | TestRoundTrip | 2 (deterministic, random 20x) |
| `test_state_codec_tcp.py` | TestStateConstants | 1 (STATE_DIM) |
| `test_state_codec_tcp.py` | TestBimanualStateFields | 1 (construction) |
| `test_state_codec_tcp.py` | TestEncodeNoTactile | 3 (16D, values, reject wrong dim) |
| `test_state_codec_tcp.py` | TestEncodeWithTactile | 4 (32D, first-16 match, requires segments, wrong segment dim) |
| `test_state_codec_tcp.py` | TestStateActionSegmentOrder | **2 (critical state≠action regression guard)** |
| `test_state_codec_tcp.py` | TestDecodePicoteleRemoved | 1 (function removed) |

### Import verification

Confirmed `PYTHONPATH=common/src:$PYTHONPATH` allows clean import of `pi05.common.robot.action_spec` and `pi05.common.data.state_codec` without loading any `deploy` package modules. Conftest.py correctly adds `common/src` to `sys.path`.

## Command Path Discrepancy

The acceptance card's extracted command (line 40) references stale paths that differ from the actual test file locations:

- Card path: `tests/deploy/test_action_spec_tcp.py` → Actual: `common/tests/test_action_spec_tcp.py`
- Card path: `pi05/common/tests/test_state_codec_tcp.py` → Actual: `common/tests/test_state_codec_tcp.py`
- Card missing: `PYTHONPATH=common/src:$PYTHONPATH`

The L3 task file's section 15 execution summary correctly records the adjusted command. Per card line 37 instruction ("验收 agent 必须优先执行 L3 文件中记录的自动化验收命令"), the L3 command was used. This discrepancy was recorded but does not affect the PASS_LOCAL conclusion since the L3 command is authoritative.

## Failed Checks

None.

## Unverified Items

- No dry-run/shadow-run tests (out of scope per L3 task section 6 "本次不做")
- No hardware verification (N/A — `robot_risk: none`)

## Conclusion

**PASS_LOCAL**

All 25 tests pass. All static review checks pass. Modification scope is clean. No forbidden files touched. No hardware claims. No import contamination from deploy packages. The test suite covers all required aspects: dimension constants, field structure, alternating action segment order, all-left→all-right state segment order, **critical regression guard for state≠action segment order**, round-trip consistency, dimension validation, tactile toggle, and decode_picotele removal.

## Fix Requests for Execution Sub-Agent

None required. PASS_LOCAL outcome — no fixes needed.

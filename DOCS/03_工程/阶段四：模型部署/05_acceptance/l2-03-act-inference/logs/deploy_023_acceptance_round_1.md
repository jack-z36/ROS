# Acceptance Feedback: deploy_023 (Round 1)

**Timestamp**: 2026-07-10
**Acceptance Mode**: `direct-local`
**Acceptance Agent**: read-only (no source, test, dispatch, or git edits)

---

## Conclusion: PASS_LOCAL

## Evidence

### Required Command

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_action_chunk_postprocess.py -v
```

**Result**: 39 passed, 0 failed, 0 skipped in 0.97s

### PASS_LOCAL Checklist (all items satisfied)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | `action_chunk_postprocess.py` exists at correct path | PASS | `src/model_deploy/act/service/action_chunk_postprocess.py` (245 lines) |
| 2 | `postprocess_action_chunk(raw_chunk, action_normalizer, expected_chunk_size) -> ActionChunk` implemented | PASS | Lines 198-244, function signature matches exactly |
| 3a | Micro ①: Raw output structure check | PASS | `check_raw_output_structure` (line 26), 8 tests (pass + 7 rejection modes) |
| 3b | Micro ②: Batch dim removal | PASS | `remove_batch_dim` (line 79), 3 tests |
| 3c | Micro ③: Action unnormalization | PASS | `unnormalize_actions` (line 99), 5 tests; calls normalizer exactly once |
| 3d | Micro ④: CPU float32 array conversion | PASS | `to_cpu_float32_array` (line 124), 5 tests; produces contiguous C-order float32 |
| 3e | Micro ⑤: Final output contract check | PASS | `check_final_output_contract` (line 153), 7 tests; strict shape/dtype/finite |
| 3f | Micro ⑥: ActionChunk construction | PASS | Within `postprocess_action_chunk` (line 244); only `actions` set, no runtime metadata |
| 4 | No clamp/crop/pad/repeat/reorder | PASS | `test_does_not_clamp`, `test_does_not_truncate_longer_output`, `test_does_not_fill_shorter_output` all pass. Source contains no `torch.clamp`, no `[:chunk_size]`, no padding/repeat/reorder |
| 5 | No quaternion/gripper/TCP delta (L2-04) | PASS | None present in source |
| 6 | No L2-04 safety calls | PASS | No safety-related imports or calls |
| 7 | Error raw shape fails directly | PASS | Wrong rank, wrong B, wrong N, wrong D all raise without squeeze/truncate/fill |
| 8 | NaN/Inf rejected | PASS | `test_rejects_nan`, `test_rejects_inf` both pass for both raw and final checks |
| 9 | Unnormalize failure rejects | PASS | Exceptions propagate directly; no fallback to normalized values |
| 10 | pytest all pass, no skip | PASS | 39 passed, 0 skipped |
| 11 | Product paths match L3 declaration | PASS | Both files at declared paths |
| 12 | Correctly imports deploy_021 ActionChunk | PASS | `from model_deploy.act.types.action_chunk import ActionChunk` (line 17) |
| 13 | No forbidden file modifications | PASS | Only `action_chunk_postprocess.py` and `test_action_chunk_postprocess.py` are new; `src/model_deploy/pi05/`, other service files, types, config, dispatch unmodified |

### FAIL_LOCAL Checks (none triggered)

- No `torch.clamp(normalized_action, -1, 1)` -- explicitly tested and absent
- No `[:chunk_size]` truncation -- rejected, not truncated
- No padding/repeat -- rejected, not filled
- No 16D reorder -- values pass through in original order
- No runtime metadata (`obs_time`, `infer_start_time`, `ready_time`) in ActionChunk -- verified by `test_action_chunk_has_no_runtime_fields`
- All 39 tests PASS
- No forbidden files modified

### Forbidden Files Check

`git status` confirms only the two expected new files in `src/model_deploy/act/`:
- `src/model_deploy/act/service/action_chunk_postprocess.py` (new, allowed)
- `src/model_deploy/act/tests/service/test_action_chunk_postprocess.py` (new, allowed)

`src/model_deploy/pi05/` and all other layers are untouched.

---

## Action Required

The main Agent must archive the matching L3 task file:

```
from: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_023_ActionChunk后处理.md
to:   DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-03-act-inference/deploy_023_ActionChunk后处理.md
```

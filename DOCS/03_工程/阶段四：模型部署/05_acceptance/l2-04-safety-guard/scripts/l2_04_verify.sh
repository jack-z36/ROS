#!/usr/bin/env bash
# ============================================================================
# L2-04 Safety Guard 统一验收脚本（mock Gate）
#
# 按 types / config / repo / service / runtime / ui / boundary 分组输出标签：
#   PASS|FAIL|BLOCKED  LABEL  简短说明
#     file: ... / class: ... / micro-unit: ... / pytest: ... / error: ...
#   SUMMARY: N PASS / N FAIL / N BLOCKED
#
# 用法（必须在仓库根目录或任意 cwd；脚本会 cd 到仓库根）:
#     bash "DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh"
#
# 核心 C/B 标签不得因缺 ROS/hardware 标 BLOCKED。
# 任一 FAIL 退出非零。
# ============================================================================

set -o pipefail

# scripts -> l2-04-safety-guard -> 05_acceptance -> 阶段四 -> 03_工程 -> DOCS -> repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../../.." && pwd)"
cd "$REPO_ROOT" || { echo "ERROR: cannot cd to $REPO_ROOT"; exit 2; }

export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"

PASS_COUNT=0
FAIL_COUNT=0
BLOCKED_COUNT=0

GATE="src/model_deploy/act/tests/integration/test_l2_04_gate.py"
TYPES_T="src/model_deploy/act/tests/types/test_safety_result.py"
CONFIG_T="src/model_deploy/act/tests/config/test_safety_config.py"
PRIM_T="src/model_deploy/act/tests/service/test_safety_primitives.py"
GUARD_T="src/model_deploy/act/tests/service/test_safety_guard.py"
SVC_FILE="src/model_deploy/act/service/safety_guard.py"

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_emit_detail() {
    # file / class / micro-unit / pytest / error
    local file="$1" class="$2" micro="$3" pytest_sel="$4" err="$5"
    echo "    file: ${file} / class: ${class} / micro-unit: ${micro} / pytest: ${pytest_sel} / error: ${err}"
}

_run_pytest_label() {
    # $1=label $2=pytest selector $3=desc $4=file $5=class $6=micro-unit
    local label="$1" selector="$2" desc="$3" file="$4" class="$5" micro="$6"
    local out rc last_line
    if ! command -v python3 >/dev/null 2>&1; then
        echo "BLOCKED  $label  $desc"
        _emit_detail "$file" "$class" "$micro" "$selector" "python3 not found"
        BLOCKED_COUNT=$((BLOCKED_COUNT + 1))
        return
    fi
    out=$(python3 -m pytest "$selector" -v --tb=short 2>&1)
    rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "PASS  $label  $desc"
        _emit_detail "$file" "$class" "$micro" "$selector" "none"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        last_line=$(echo "$out" | grep -E 'FAILED|ERROR|ModuleNotFoundError' | tail -1 | sed 's/^[[:space:]]*//')
        if echo "$out" | grep -qE 'ModuleNotFoundError|No module named'; then
            # Missing pure-Python deps for core Gate is still FAIL (not env ROS).
            # Only treat missing pytest itself as BLOCKED.
            if echo "$out" | grep -q 'No module named .pytest'; then
                echo "BLOCKED  $label  $desc"
                _emit_detail "$file" "$class" "$micro" "$selector" "${last_line:-pytest missing}"
                BLOCKED_COUNT=$((BLOCKED_COUNT + 1))
                return
            fi
        fi
        echo "FAIL  $label  $desc"
        _emit_detail "$file" "$class" "$micro" "$selector" "${last_line:-pytest rc=$rc}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

_static_pass() {
    local label="$1" desc="$2" file="$3" class="$4" micro="$5" note="$6"
    echo "PASS  $label  $desc"
    _emit_detail "$file" "$class" "$micro" "static" "$note"
    PASS_COUNT=$((PASS_COUNT + 1))
}

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------

echo "=== L2-04 Safety Guard mock Gate 验收 ==="
echo "repo: $REPO_ROOT"
echo "PYTHONPATH=src"
echo ""

# ==================================================================
# [ types ]
# ==================================================================

echo "[ types ]"

_run_pytest_label \
    "TYPES-RESULT" \
    "${GATE}::TestTypesResult" \
    "C1-C3/C5 三种 status 字段冻结且完整" \
    "types/safety_result.py" \
    "TestTypesResult" \
    "C1-C3/C5"

_run_pytest_label \
    "TYPES-RESULT-UNIT" \
    "${TYPES_T}" \
    "types 单测全量（deploy_031）" \
    "tests/types/test_safety_result.py" \
    "unit" \
    "C1-C3/C5"

echo ""

# ==================================================================
# [ config ]
# ==================================================================

echo "[ config ]"

_run_pytest_label \
    "CONFIG-SAFETY" \
    "${CONFIG_T}" \
    "SafetyConfig ActionDomain 阈值契约（deploy_032）" \
    "config/schema.py" \
    "TestSafetyDefaults" \
    "A1-pre"

echo ""

# ==================================================================
# [ repo ]
# ==================================================================

echo "[ repo ]"

# L2-04 不拥有 repo 产物；确认 service 不依赖 repo loader。
if rg -n --no-heading 'model_deploy\.act\.repo|from model_deploy\.act import repo' \
    "$SVC_FILE" 2>/dev/null | grep -v '^\s*#' >/dev/null 2>&1; then
    echo "FAIL  REPO-PURITY  service 不得 import repo loader"
    _emit_detail "$SVC_FILE" "SafetyGuard" "A1" "static-rg" "repo import found"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    _static_pass \
        "REPO-PURITY" \
        "service 无 repo loader import（L2-04 无 repo 产物）" \
        "$SVC_FILE" \
        "SafetyGuard" \
        "A1" \
        "no repo import"
fi

echo ""

# ==================================================================
# [ service ]
# ==================================================================

echo "[ service ]"

_run_pytest_label \
    "INPUT-SHAPE" \
    "${GATE}::TestInputShape" \
    "非 (16,) → REJECTED INVALID_SHAPE" \
    "$SVC_FILE" \
    "TestInputShape" \
    "C6/B2"

_run_pytest_label \
    "INPUT-FINITE" \
    "${GATE}::TestInputFinite" \
    "NaN/Inf → REJECTED NON_FINITE" \
    "$SVC_FILE" \
    "TestInputFinite" \
    "C7/B2"

_run_pytest_label \
    "QUAT-CANDIDATE" \
    "${GATE}::TestQuatCandidate" \
    "零模拒绝，近单位可单位化" \
    "$SVC_FILE" \
    "TestQuatCandidate" \
    "C8/B2"

_run_pytest_label \
    "REFERENCE-ORDER" \
    "${GATE}::TestReferenceOrder" \
    "previous 优先于 observation" \
    "$SVC_FILE" \
    "TestReferenceOrder" \
    "C4/C9/B1"

_run_pytest_label \
    "REFERENCE-BOOTSTRAP" \
    "${GATE}::TestReferenceBootstrap" \
    "无 previous 时使用 observation" \
    "$SVC_FILE" \
    "TestReferenceBootstrap" \
    "C4/C9/B1"

_run_pytest_label \
    "REFERENCE-MISSING" \
    "${GATE}::TestReferenceMissing" \
    "两者都无 → REJECTED NO_REFERENCE" \
    "$SVC_FILE" \
    "TestReferenceMissing" \
    "C9/B1"

_run_pytest_label \
    "POSE-TRANSLATION" \
    "${GATE}::TestPoseTranslation" \
    "超阈值欧氏距离恰为阈值" \
    "$SVC_FILE" \
    "TestPoseTranslation" \
    "C10/B3"

_run_pytest_label \
    "POSE-ROTATION" \
    "${GATE}::TestPoseRotation" \
    "超阈值旋转角恰为阈值" \
    "$SVC_FILE" \
    "TestPoseRotation" \
    "C11/B3"

_run_pytest_label \
    "GRIPPER-RANGE" \
    "${GATE}::TestGripperRange" \
    "超绝对范围投影到同域 min/max" \
    "$SVC_FILE" \
    "TestGripperRange" \
    "C12/B4"

_run_pytest_label \
    "GRIPPER-STEP" \
    "${GATE}::TestGripperStep" \
    "超单步值投影到同域步长" \
    "$SVC_FILE" \
    "TestGripperStep" \
    "C13/B4"

_run_pytest_label \
    "BIMANUAL-ASSEMBLY" \
    "${GATE}::TestBimanualAssembly" \
    "左右独立调整且 16D 段序不变" \
    "$SVC_FILE" \
    "TestBimanualAssembly" \
    "C14/B5"

_run_pytest_label \
    "OUTPUT-INVARIANT" \
    "${GATE}::TestOutputInvariant" \
    "调整后动作仍合法" \
    "$SVC_FILE" \
    "TestOutputInvariant" \
    "C15/B5"

_run_pytest_label \
    "RESULT-STATUS" \
    "${GATE}::TestResultStatus" \
    "PASS/ADJUSTED/REJECTED 三种 status 正确" \
    "$SVC_FILE" \
    "TestResultStatus" \
    "B1/C5"

_run_pytest_label \
    "SERVICE-PRIMITIVES-FULL" \
    "${PRIM_T}" \
    "C4/C6-C15 纯函数全量单测（deploy_033）" \
    "$SVC_FILE" \
    "primitives" \
    "C4/C6-C15"

_run_pytest_label \
    "SERVICE-GUARD-FULL" \
    "${GUARD_T}" \
    "A1/B1-B5 编排全量单测（deploy_034）" \
    "$SVC_FILE" \
    "SafetyGuard" \
    "A1/B1-B5"

_run_pytest_label \
    "GATE-FULL" \
    "${GATE}" \
    "L2-04 mock Gate 集成测试全量" \
    "$GATE" \
    "all" \
    "A1+Gate"

echo ""

# ==================================================================
# [ runtime ]
# ==================================================================

echo "[ runtime ]"

# L2-04 无 runtime 产物；确认 service 不 import runtime。
if rg -n --no-heading 'model_deploy\.act\.runtime' "$SVC_FILE" 2>/dev/null \
    | grep -v '^\s*#' >/dev/null 2>&1; then
    echo "FAIL  RUNTIME-PURITY  service 不得 import runtime"
    _emit_detail "$SVC_FILE" "SafetyGuard" "boundary" "static-rg" "runtime import found"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    _static_pass \
        "RUNTIME-PURITY" \
        "无 runtime 层产物且 service 不 import runtime" \
        "$SVC_FILE" \
        "SafetyGuard" \
        "boundary" \
        "no runtime import"
fi

echo ""

# ==================================================================
# [ ui ]
# ==================================================================

echo "[ ui ]"

if rg -n --no-heading 'model_deploy\.act\.ui|import rclpy|import rospy' "$SVC_FILE" 2>/dev/null \
    | grep -v '^\s*#' >/dev/null 2>&1; then
    echo "FAIL  UI-PURITY  service 不得 import ui/ROS"
    _emit_detail "$SVC_FILE" "SafetyGuard" "boundary" "static-rg" "ui/ROS import found"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    _static_pass \
        "UI-PURITY" \
        "无 ui 层产物且 service 不 import ui/ROS" \
        "$SVC_FILE" \
        "SafetyGuard" \
        "boundary" \
        "no ui/ROS import"
fi

echo ""

# ==================================================================
# [ boundary ]
# ==================================================================

echo "[ boundary ]"

_run_pytest_label \
    "PURITY-IMPORT" \
    "${GATE}::TestPurityImport" \
    "无 runtime/ui/ROS/repo/hardware import；Guard 无跨 tick 状态" \
    "$SVC_FILE" \
    "TestPurityImport" \
    "A1/B/C"

echo ""

# ==================================================================
# Summary
# ==================================================================

echo "────────────────────────────────"
echo "SUMMARY: ${PASS_COUNT} PASS / ${FAIL_COUNT} FAIL / ${BLOCKED_COUNT} BLOCKED"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
exit 0

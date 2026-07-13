#!/usr/bin/env bash
# ============================================================================
# L2-05 Action Publisher 统一验收脚本 (deploy_045)
#
# 按六层 + boundary 分组，逐项运行 G01-G17 的 local/mock 验收，并以分层
# PASS/FAIL/BLOCKED 输出。FAIL 给出完整定位链；G18/G19 在 ROS/硬件缺失时
# 只记录预期 BLOCKED，绝不伪造 PASS。
#
# 用法 (cwd 必须是仓库根目录，脚本会自动定位):
#     bash src/model_deploy/act/scripts/l2_05_verify.sh
#     bash src/model_deploy/act/scripts/l2_05_verify.sh --case local
#     bash src/model_deploy/act/scripts/l2_05_verify.sh --case command-disabled
#     bash src/model_deploy/act/scripts/l2_05_verify.sh --case permit-blocked
#     bash src/model_deploy/act/scripts/l2_05_verify.sh --case topic-payloads
#     bash src/model_deploy/act/scripts/l2_05_verify.sh --case ros-message-bundle
#     bash src/model_deploy/act/scripts/l2_05_verify.sh --case command-enabled-mock
#     bash src/model_deploy/act/scripts/l2_05_verify.sh --case ros-observe
#
# 退出码:
#     0  全部 required local/mock PASS，仅预期 BLOCKED (G18/G19)
#     1  任一 required local/mock FAIL
#     2  参数或环境自检错误
# ============================================================================

set -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO_ROOT" || { echo "ERROR: cannot cd to $REPO_ROOT"; exit 2; }

export PYTHONPATH="$REPO_ROOT/src:${PYTHONPATH}"

GATE_FILE="src/model_deploy/act/tests/integration/test_l2_05_gate.py"

PASS_COUNT=0
FAIL_COUNT=0
BLOCKED_COUNT=0

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_run_tests() {
    # $1 label  $2 k-expr  $3 desc  $4 file  $5 class  $6 micro-unit
    local label="$1" kexpr="$2" desc="$3" file="$4" cls="$5" micro="$6"
    local out rc
    out=$(python3 -m pytest "$GATE_FILE" -k "$kexpr" -v --tb=short 2>&1)
    rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "  PASS  $label  $desc"
        ((PASS_COUNT++))
    else
        echo "  FAIL  $label  $desc"
        ((FAIL_COUNT++))
        echo "    file: $file"
        echo "    class: $cls"
        echo "    micro-unit: $micro"
        echo "    pytest: $GATE_FILE -k \"$kexpr\""
        local err
        err=$(echo "$out" | grep -E '^(E |FAILED|ERROR)' | tail -3 | sed 's/^[[:space:]]*//' | tr '\n' ' ')
        echo "    error: ${err:-<see full pytest output above>}"
    fi
    return $rc
}

_emit_blocked() {
    # $1 label  $2 reason
    local label="$1" reason="$2"
    echo "  BLOCKED  $label  $reason"
    ((BLOCKED_COUNT++))
}

_ros_observe() {
    # G18: observe policy/status, command silent. Keep dry-run-only: never
    # publish to a real graph. If rclpy is unavailable -> BLOCKED_ENV; if
    # available but no live observation target -> expected BLOCKED (dry-run).
    if ! python3 -c "import rclpy" >/dev/null 2>&1; then
        _emit_blocked "ROS_OBSERVE" "ROS 2 environment unavailable (BLOCKED_ENV); local/mock passed, command topics silent by contract"
        return
    fi
    _emit_blocked "ROS_OBSERVE" "rclpy importable but live ROS observation target not asserted in dry-run acceptance; command topics remain silent by contract (see mock G09/G10)"
}

_hardware_blocked() {
    # G19: real robot execution requires explicit human authorization, e-stop
    # readiness, driver readiness and ROS observation evidence. None present
    # in automated acceptance -> expected BLOCKED, never claimed PASS.
    _emit_blocked "HARDWARE" "no human authorization / e-stop / driver readiness / ROS evidence in automated acceptance (BLOCKED_HARDWARE_EXPECTED)"
}

# ------------------------------------------------------------------
# Case dispatch
# ------------------------------------------------------------------

CASE="local"
if [ "$1" = "--case" ]; then
    CASE="$2"
elif [ -n "$1" ]; then
    CASE="$1"
fi

case "$CASE" in
    local)
        echo "=== L2-05 Action Publisher 验收 (local / mock) ==="
        echo ""
        echo "[ types ]"
        _run_tests "TYPES_CONTRACT" "G01" \
            "C1-C6 frozen schema and invariants" \
            "src/model_deploy/act/types/action_publish.py" "无 class" "C1-C6 (数据)"
        echo ""
        echo "[ config ]"
        _run_tests "CLI_DEFAULT_OFF" "G02" \
            "C7 command_output_enabled=False without explicit CLI" \
            "src/model_deploy/act/config/schema.py" "CommandOutputConfig" "C7 (数据)"
        _run_tests "CLI_EXPLICIT_ON" "G03" \
            "C7 command_output_enabled=True with explicit CLI" \
            "src/model_deploy/act/config/schema.py" "CommandOutputConfig" "C7 (数据)"
        echo ""
        echo "[ service ]"
        _run_tests "B1_TOPIC_PAYLOADS" "G04 or G05 or G06" \
            "B1 build_topic_payloads: 16D -> C4 (PASS/ADJUSTED, rejects, split, gripper map)" \
            "src/model_deploy/act/service/action_output_adapter.py" "无 class" "B1 (编排)/C9-C11 (计算)"
        echo ""
        echo "[ ui ]"
        _run_tests "B2_MESSAGE_BUNDLE" "G07 or G08" \
            "B2 build_ros_messages: five messages, no status, no partial" \
            "src/model_deploy/act/ui/action_publisher.py" "无 class" "B2 (编排)/C12-C14 (计算)"
        _run_tests "B3_COMMAND_GATE" "G09 or G10 or G11 or G12 or G13 or G14 or G15 or G17" \
            "B3 publish: CLI/permit gate, PARTIAL, gripper state, status, mock integration" \
            "src/model_deploy/act/ui/action_publisher.py" "ActionPublisher" "B3 (编排)/C15-C21"
        echo ""
        echo "[ boundary ]"
        _run_tests "BOUNDARY_CLEAN" "G16" \
            "no subscription/timer/mode/accepted/TF/IK/SDK; no L2-05 artifact in repo/runtime" \
            "src/model_deploy/act/ui/action_publisher.py" "无 class" "L2-05 目标文件 (所有 class/function)"
        _run_tests "NO_RUNTIME_ARTIFACT" "G16" \
            "runtime/repo stay free of L2-05 product (scheduling not leaked into L2-05)" \
            "src/model_deploy/act/runtime/ / src/model_deploy/act/repo/" "无 L2-05 class" "无新增微元"
        echo ""
        echo "[ ros-observe / hardware (expected BLOCKED) ]"
        _ros_observe
        _hardware_blocked
        ;;
    command-disabled)
        echo "=== L2-05 验收: command-disabled ==="
        echo ""
        echo "[ config ]"
        _run_tests "CLI_DEFAULT_OFF" "G02" \
            "C7 default-off without explicit CLI" \
            "src/model_deploy/act/config/schema.py" "CommandOutputConfig" "C7 (数据)"
        echo ""
        echo "[ ui ]"
        _run_tests "B3_COMMAND_GATE_DISABLED" "G09" \
            "CLI=False, permit any -> policy/status=1, command=0, OBSERVED" \
            "src/model_deploy/act/ui/action_publisher.py" "ActionPublisher" "B3 (编排)/C15"
        ;;
    permit-blocked)
        echo "=== L2-05 验收: permit-blocked ==="
        echo ""
        echo "[ ui ]"
        _run_tests "B3_COMMAND_GATE_PERMIT_BLOCKED" "G10" \
            "CLI=True, permit=False -> command=0, BLOCKED, reason readable" \
            "src/model_deploy/act/ui/action_publisher.py" "ActionPublisher" "B3 (编排)/C15"
        ;;
    topic-payloads)
        echo "=== L2-05 验收: topic-payloads ==="
        echo ""
        echo "[ service ]"
        _run_tests "B1_TOPIC_PAYLOADS" "G04 or G05 or G06" \
            "B1: PASS/ADJUSTED -> C4; rejects; 16D split; 0/50/100 gripper map" \
            "src/model_deploy/act/service/action_output_adapter.py" "无 class" "B1 (编排)/C9-C11"
        ;;
    ros-message-bundle)
        echo "=== L2-05 验收: ros-message-bundle ==="
        echo ""
        echo "[ ui ]"
        _run_tests "B2_MESSAGE_BUNDLE" "G07 or G08" \
            "B2: five ROS messages, frame/stamp/xyzw/domain, no status, no partial" \
            "src/model_deploy/act/ui/action_publisher.py" "无 class" "B2 (编排)/C12-C14"
        ;;
    command-enabled-mock)
        echo "=== L2-05 验收: command-enabled-mock ==="
        echo ""
        echo "[ ui ]"
        _run_tests "B3_COMMAND_GATE_ENABLED" "G11 or G13 or G14" \
            "CLI=True+permit=True: PUBLISHED; nth fail -> PARTIAL; gripper deadband/interval/cache" \
            "src/model_deploy/act/ui/action_publisher.py" "ActionPublisher" "B3 (编排)/C15-C21"
        ;;
    ros-observe)
        echo "=== L2-05 验收: ros-observe ==="
        echo ""
        echo "[ ros-observe / hardware (expected BLOCKED) ]"
        _ros_observe
        _hardware_blocked
        ;;
    *)
        echo "ERROR: unknown case '$CASE'"
        echo "  allowed: local command-disabled permit-blocked topic-payloads \\"
        echo "           ros-message-bundle command-enabled-mock ros-observe"
        exit 2
        ;;
esac

# ------------------------------------------------------------------
# Summary + exit code
# ------------------------------------------------------------------

echo ""
echo "────────────────────────────────"
TOTAL=$((PASS_COUNT + FAIL_COUNT + BLOCKED_COUNT))
echo "  $PASS_COUNT PASS / $FAIL_COUNT FAIL / $BLOCKED_COUNT BLOCKED  (共 $TOTAL 标签)"

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
elif [ "$CASE" = "local" ] || [ "$CASE" = "command-disabled" ] || \
     [ "$CASE" = "permit-blocked" ] || [ "$CASE" = "topic-payloads" ] || \
     [ "$CASE" = "ros-message-bundle" ] || [ "$CASE" = "command-enabled-mock" ] || \
     [ "$CASE" = "ros-observe" ]; then
    exit 0
else
    exit 2
fi

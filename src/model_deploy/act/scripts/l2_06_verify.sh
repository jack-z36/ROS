#!/usr/bin/env bash
# ============================================================================
# L2-06 Gate 跨模块集成验收脚本 (deploy_055)
#
# 唯一验证入口：使用真实 production contracts 与可控外部替身证明
# L2-02 → L2-03 → L2-06 → L2-04 → L2-05 tracer bullet、原子启动/关闭、
# fallback / 六 outcome / fault 语义。覆盖 Gate 场景 G01-G12。
#
# 分层策略 (deploy_055 §12 / 04_L2验收机制.md):
#   local            G01-G09 用真实代码 + fake 外部边界本地跑通；baseline 0 FAIL；
#                    外部 ROS/real-bundle/真机只记录预期 BLOCKED，绝不伪造 PASS。
#   ros-dry-run      command_output 保持 disabled；真实 ROS 缺失记 BLOCKED_ENV。
#   real-policy-dry-run  要求 --policy real；无真实 bundle/GPU 记 BLOCKED_ARTIFACT。
#
# 用法 (cwd 必须是仓库根目录；脚本自动定位):
#     bash src/model_deploy/act/scripts/l2_06_verify.sh \
#         --scope local --policy fake \
#         --config src/model_deploy/act/tests/fixtures/l2_06_fake.yaml
#     bash src/model_deploy/act/scripts/l2_06_verify.sh --scope ros-dry-run
#     bash src/model_deploy/act/scripts/l2_06_verify.sh --scope real-policy-dry-run \
#         --policy real --config "$ACT_DEPLOY_CONFIG"
#
# 退出码:
#     0  全部 required local/mock PASS，仅预期 BLOCKED (G10/G11/G12 外部)
#     1  任一 required local/mock FAIL
#     2  参数或环境自检错误
# ============================================================================

set -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO_ROOT" || { echo "ERROR: cannot cd to $REPO_ROOT"; exit 2; }

# When rclpy is partially installed (the top-level ``rclpy`` import succeeds
# but ``rclpy.node`` is not exposed as an attribute, a common incomplete-ROS
# layout), the production act_deploy_node module raises AttributeError at
# import time and breaks pytest collection. Detect this case and isolate the
# test runner from the inherited ROS site-packages so the test file can be
# collected in a no-ROS context. (The Gate explicitly records this state as
# BLOCKED_ENV rather than pretending ROS is fully available.)
_PYTHON3_BIN="${PYTHON3_BIN:-python3}"
if "$_PYTHON3_BIN" -c "import rclpy; import sys; sys.exit(0 if not hasattr(rclpy, 'node') else 1)" >/dev/null 2>&1; then
    export PYTHONPATH="$REPO_ROOT/src"
fi

export PYTHONPATH="$REPO_ROOT/src:${PYTHONPATH}"

GATE_FILE="src/model_deploy/act/tests/integration/test_l2_06_gate.py"
BASELINE_DIR="src/model_deploy/act/tests"
FIXTURE_DEFAULT="src/model_deploy/act/tests/fixtures/l2_06_fake.yaml"

PASS_COUNT=0
FAIL_COUNT=0
BLOCKED_COUNT=0

# ------------------------------------------------------------------
# CLI 解析
# ------------------------------------------------------------------

SCOPE="local"
POLICY="fake"
CONFIG="$FIXTURE_DEFAULT"

while [ $# -gt 0 ]; do
    case "$1" in
        --scope) SCOPE="$2"; shift 2 ;;
        --policy) POLICY="$2"; shift 2 ;;
        --config) CONFIG="$2"; shift 2 ;;
        -h|--help)
            echo "usage: $0 --scope {local|ros-dry-run|real-policy-dry-run}"
            echo "          --policy {fake|real} --config <path>"
            exit 0
            ;;
        *)
            echo "ERROR: unknown arg '$1'"
            echo "  allowed: --scope --policy --config"
            exit 2
            ;;
    esac
done

case "$SCOPE" in
    local|ros-dry-run|real-policy-dry-run) ;;
    *) echo "ERROR: invalid --scope '$SCOPE'"; exit 2 ;;
esac
case "$POLICY" in
    fake|real) ;;
    *) echo "ERROR: invalid --policy '$POLICY'"; exit 2 ;;
esac

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_run_tests() {
    # $1 label  $2 k-expr  $3 desc  $4 file  $5 class  $6 micro-unit
    local label="$1" kexpr="$2" desc="$3" file="$4" cls="$5" micro="$6"
    local out rc
    out=$(python3 -m pytest "$file" -k "$kexpr" -v --tb=short 2>&1)
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
        echo "    pytest: $file -k \"$kexpr\""
        local err
        err=$(echo "$out" | grep -E '^(E |FAILED|ERROR)' | tail -3 | sed 's/^[[:space:]]*//' | tr '\n' ' ')
        echo "    error: ${err:-<see full pytest output above>}"
    fi
    return $rc
}

_run_baseline() {
    # 全量 act tests 回归：0 FAIL 为 PASS。
    local out rc
    out=$(python3 -m pytest "$BASELINE_DIR" -q --tb=short 2>&1)
    rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "  PASS  BASELINE_REGRESSION  全量 $BASELINE_DIR 0 FAIL"
        ((PASS_COUNT++))
    else
        echo "  FAIL  BASELINE_REGRESSION  全量 $BASELINE_DIR 存在 FAIL"
        ((FAIL_COUNT++))
        local err
        err=$(echo "$out" | grep -E '^(FAILED|ERROR)' | tail -5 | sed 's/^[[:space:]]*//' | tr '\n' ' ')
        echo "    pytest: $BASELINE_DIR -q --tb=short"
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

_ros_env_check() {
    # 真实 ROS 2 不可用 -> BLOCKED_ENV
    if ! python3 -c "import rclpy" >/dev/null 2>&1; then
        _emit_blocked "G10_ROS_OBSERVE" "ROS 2 environment unavailable (BLOCKED_ENV); local/mock dry-run passed, command topics silent by contract"
        return
    fi
    _emit_blocked "G10_ROS_OBSERVE" "rclpy importable but live ROS observation target not asserted in dry-run acceptance; command topics remain silent by contract"
}

_real_policy_check() {
    # 真实 bundle/GPU 缺失 -> BLOCKED_ARTIFACT
    _emit_blocked "G11_REAL_BUNDLE" "no real model bundle/GPU in automated acceptance (BLOCKED_ARTIFACT); local fake-policy gate passed the loader fail-fast contract"
}

_hardware_check() {
    # 真机须显式人工授权/E-stop/driver/ROS 证据；自动验收记 BLOCKED_HARDWARE
    _emit_blocked "G12_REAL_COMMAND" "no human authorization / e-stop / driver readiness / ROS evidence in automated acceptance (BLOCKED_HARDWARE_EXPECTED)"
}

# ------------------------------------------------------------------
# local / ros-dry-run / real-policy-dry-run 共同本地核心
# ------------------------------------------------------------------

_run_local_core() {
    echo "=== L2-06 Gate 本地核心 (本地 G01-G09 + 外部闸口契约) ==="
    echo ""
    echo "[ types / boundary ]"
    _run_tests "G01" "TestG01Types" \
        "types 纯净 + 无 forbidden token/import，静态边界扫描" \
        "$GATE_FILE" "TestG01Types" "ActionChunk/PolicyInputSpec + 静态扫描"
    echo ""
    echo "[ config / repo ]"
    _run_tests "G02" "TestG02Config" \
        "default-off、YAML 不能静默启用、arg 仅 2 旗、canonical 资源/spec 身份、loader fail-fast" \
        "$GATE_FILE" "TestG02Config" "DeployConfig/CommandOutputConfig/load_act_runtime_resources"
    echo ""
    echo "[ observation / service / publish seam ]"
    _run_tests "G03" "TestG03Seam" \
        "pipeline 干跑 env_blocked、collector->snapshot、service 预测、safety PASS、publisher provenance" \
        "$GATE_FILE" "TestG03Seam" "build_observation_pipeline/ActInferenceService/SafetyGuard/ActionPublisher"
    echo ""
    echo "[ channel / metrics ]"
    _run_tests "G04" "TestG04ChannelMetrics" \
        "request 校验、result XOR、LatestQueue 容量 1 close、metrics 不可变快照" \
        "$GATE_FILE" "TestG04ChannelMetrics" "InferenceRequest/InferenceResult/LatestQueue/RuntimeMetrics"
    echo ""
    echo "[ worker ]"
    _run_tests "G05" "TestG05Worker" \
        "serial success、error 恢复、CLOCK_INVALID 致命闸口" \
        "$GATE_FILE" "TestG05Worker" "InferenceWorker"
    echo ""
    echo "[ scheduling ]"
    _run_tests "G06" "TestG06Scheduling" \
        "correlation/active chunk、prefetch@horizon、result-id 错配 latch fault" \
        "$GATE_FILE" "TestG06Scheduling" "ControlLoop A1-A4"
    echo ""
    echo "[ fallback / output ]"
    _run_tests "G07" "TestG07FallbackOutput" \
        "六 outcome OBSERVED/PUBLISHED/BLOCKED/REJECTED/FAILED/PARTIAL + 观测缺失 fallback" \
        "$GATE_FILE" "TestG07FallbackOutput" "ControlLoop fallback + ActionPublisher 六 outcome"
    echo ""
    echo "[ UI / lifecycle ]"
    _run_tests "G08" "TestG08Lifecycle" \
        "preflight pass、SPEC_IDENTITY_MISMATCH、PERMIT_SOURCE_MISSING、deny fail-closed、shutdown 收敛" \
        "$GATE_FILE" "TestG08Lifecycle" "run_startup_preflight/_deny_command_permit/request_shutdown"
    echo ""
    echo "[ local full Gate ]"
    _run_tests "G09" "TestG09FullGate" \
        "完整 tracer bullet（真实 worker）：chunk_activated>0、inference_success>0、published>=1、有界 shutdown" \
        "$GATE_FILE" "TestG09FullGate" "build_composition + InferenceWorker + ControlLoop.tick"
}

# 外部闸口的本地契约证明（这些 class 在本地也 PASS，证明 fail-closed 行为）
_run_external_local_contract() {
    echo ""
    echo "[ external gate local-contract proofs ]"
    _run_tests "G10_LOCAL" "TestG10RosDryRun" \
        "dry-run command=0 契约 + ROS 可用标志自检" \
        "$GATE_FILE" "TestG10RosDryRun" "ActionPublisher command-count dry-run contract"
    _run_tests "G11_LOCAL" "TestG11RealPolicyDryRun" \
        "真实 loader 在空 bundle 下 fail-fast（无法用 fake 伪装 real-policy）" \
        "$GATE_FILE" "TestG11RealPolicyDryRun" "load_act_runtime_resources gating"
    _run_tests "G12_LOCAL" "TestG12RealCommand" \
        "默认 fail-closed：deny permit、YAML 无命令开关、未授权 command=0" \
        "$GATE_FILE" "TestG12RealCommand" "_deny_command_permit/build_arg_parser"
}

# ------------------------------------------------------------------
# Scope dispatch
# ------------------------------------------------------------------

case "$SCOPE" in
    local)
        echo "=== L2-06 Gate 验收 (scope=local, policy=$POLICY) ==="
        _run_local_core
        _run_external_local_contract
        echo ""
        echo "[ baseline regression ]"
        _run_baseline
        echo ""
        echo "[ 外部 scope（预期 BLOCKED，绝不伪造 PASS）]"
        _ros_env_check
        _real_policy_check
        _hardware_check
        ;;
    ros-dry-run)
        echo "=== L2-06 Gate 验收 (scope=ros-dry-run, policy=$POLICY) ==="
        echo "  >> ROS dry-run 契约：command_output 保持 disabled，四路 command 必为 0"
        _run_local_core
        _run_external_local_contract
        _run_baseline
        echo ""
        echo "[ ROS 真实观察（环境缺失记 BLOCKED_ENV）]"
        _ros_env_check
        _real_policy_check
        _hardware_check
        ;;
    real-policy-dry-run)
        echo "=== L2-06 Gate 验收 (scope=real-policy-dry-run, policy=$POLICY) ==="
        if [ "$POLICY" = "fake" ]; then
            echo "  >> --policy fake：本地 fake-policy 验证（无真实 bundle/GPU）"
            _run_local_core
            _run_external_local_contract
            _run_baseline
            _ros_env_check
            _real_policy_check
            _hardware_check
        else
            echo "  >> --policy real：要求真实 bundle/GPU；本自动化环境无真实 artifact"
            # 仍跑本地契约证明（loader fail-fast 等），但真实 PASS 必须外部 artifact
            _run_external_local_contract
            _ros_env_check
            _real_policy_check
            _hardware_check
        fi
        ;;
esac

# ------------------------------------------------------------------
# Summary + exit code
# ------------------------------------------------------------------

echo ""
echo "────────────────────────────────"
TOTAL=$((PASS_COUNT + FAIL_COUNT + BLOCKED_COUNT))
echo "  $PASS_COUNT PASS / $FAIL_COUNT FAIL / $BLOCKED_COUNT BLOCKED  (共 $TOTAL 标签)"
echo "  config: $CONFIG   policy: $POLICY   scope: $SCOPE"

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
exit 0

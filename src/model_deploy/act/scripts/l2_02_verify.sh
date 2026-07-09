#!/usr/bin/env bash
# ============================================================================
# L2-02 ObservationSnapshot 统一验收脚本
#
# 按 L2 Gate 12 标签逐项运行，分层分组输出 PASS/FAIL/BLOCKED。
# 用法:
#     bash src/model_deploy/act/scripts/l2_02_verify.sh
#     cwd 必须是仓库根目录
# ============================================================================

set -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO_ROOT" || { echo "ERROR: cannot cd to $REPO_ROOT"; exit 2; }

PASS_COUNT=0
FAIL_COUNT=0
BLOCKED_COUNT=0
declare -A RESULTS
declare -A FAIL_DETAIL

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_run_pytest() {
    # $1 = label, $2 = test path, $3 = description
    local label="$1" path="$2" desc="$3"
    local out rc
    out=$(python3 -m pytest "$path" -v --tb=short 2>&1)
    rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "  PASS  $label  $desc"
        RESULTS["$label"]="PASS"
        ((PASS_COUNT++))
    else
        echo "  FAIL  $label  $desc"
        FAIL_DETAIL["$label"]="$out"
        RESULTS["$label"]="FAIL"
        ((FAIL_COUNT++))
        # Print failure details
        echo "    ├─ 文件: $path"
        echo "    └─ 摘要: $(echo "$out" | tail -5 | head -1)"
    fi
}

_rg_scan() {
    # $1 = label, $2 = pattern, $3 = directory, $4 = description
    local label="$1" pat="$2" dir="$3" desc="$4"
    local matches
    matches=$(rg -n --no-heading "$pat" "$dir" 2>/dev/null || true)
    # Filter out test files and docstrings referencing boundary rules
    matches=$(echo "$matches" | grep -v 'test_' | grep -v 'FORBIDDEN' | grep -v '_verify' | grep -v 'verify.sh' || true)
    if [ -z "$matches" ]; then
        echo "  PASS  $label  $desc"
        RESULTS["$label"]="PASS"
        ((PASS_COUNT++))
    else
        echo "  FAIL  $label  $desc"
        echo "    ├─ 越界匹配:"
        echo "$matches" | while IFS= read -r line; do
            echo "    │  $line"
        done
        RESULTS["$label"]="FAIL"
        ((FAIL_COUNT++))
    fi
}

_check_ros() {
    python3 -c "import rclpy" 2>/dev/null
}

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------

echo "=== L2-02 ObservationSnapshot 验收 ==="
echo ""

# ------------------------------------------------------------------
# [ types ]
# ------------------------------------------------------------------

echo "[ types ]"

_run_pytest \
    "contract.encoded_state_dim" \
    "src/model_deploy/act/tests/types/test_observation.py" \
    "16D 维度校验"

# contract.importable: verify import via pytest
_run_pytest \
    "contract.importable" \
    "src/model_deploy/act/tests/types/test_observation.py::TestImportWithoutROS" \
    "契约可 import"

echo ""

# ------------------------------------------------------------------
# [ service ]
# ------------------------------------------------------------------

echo "[ service ]"

_run_pytest \
    "collector.mock_snapshot" \
    "src/model_deploy/act/tests/service/test_observation_collector.py::TestMockFullSnapshot" \
    "mock 全字段→snapshot"

_run_pytest \
    "collector.missing_reject" \
    "src/model_deploy/act/tests/service/test_observation_collector.py::TestMissingReject" \
    "缺字段→None"

_run_pytest \
    "collector.stale_reject" \
    "src/model_deploy/act/tests/service/test_observation_collector.py::TestStaleReject" \
    "过期→None"

_run_pytest \
    "preprocess.image" \
    "src/model_deploy/act/tests/service/test_image_preprocess.py" \
    "图像预处理"

echo ""

# ------------------------------------------------------------------
# [ runtime ]
# ------------------------------------------------------------------

echo "[ runtime ]"

_run_pytest \
    "buffer.latest_only" \
    "src/model_deploy/act/tests/runtime/test_observation_buffer.py::TestSetAndGet" \
    "覆盖语义"

_run_pytest \
    "buffer.max_age" \
    "src/model_deploy/act/tests/runtime/test_observation_buffer.py::TestSetAndGet::test_max_age_expired" \
    "max_age_s 生效"

echo ""

# ------------------------------------------------------------------
# [ ui / 边界 ]
# ------------------------------------------------------------------

echo "[ ui / 边界 ]"

# adapter.no_ros_importable
_run_pytest \
    "adapter.no_ros_importable" \
    "src/model_deploy/act/tests/ui/test_observation_ros_adapter.py::TestImportWithoutROS" \
    "无 ROS 可 import"

# boundary.no_overreach
_rg_scan \
    "boundary.no_overreach" \
    'predict_action_chunk|ActionChunk|SafetyGuard|safety_guard|publish.*hardware|send.*command|motor_control|actuator|robot_driver' \
    "src/model_deploy/act/service src/model_deploy/act/runtime src/model_deploy/act/ui" \
    "无越界"

# boundary.no_config_repo
echo -n "  "
VIOLATIONS=$(find src/model_deploy/act/config src/model_deploy/act/repo -name '*observation*' -o -name '*snapshot*' -o -name '*freshness*' 2>/dev/null || true)
if [ -z "$VIOLATIONS" ]; then
    echo "PASS  boundary.no_config_repo       config/repo 无产物"
    RESULTS["boundary.no_config_repo"]="PASS"
    ((PASS_COUNT++))
else
    echo "FAIL  boundary.no_config_repo       config/repo 无产物"
    echo "    ├─ 越界文件: $VIOLATIONS"
    RESULTS["boundary.no_config_repo"]="FAIL"
    ((FAIL_COUNT++))
fi

# adapter.real_subscription
if _check_ros; then
    echo -n "  "
    _run_pytest \
        "adapter.real_subscription" \
        "src/model_deploy/act/tests/ui/test_observation_ros_adapter.py::TestCreateSubscriptions::test_with_ros_mock_node" \
        "ROS topic 订阅"
else
    echo "  BLOCKED  adapter.real_subscription 无 ROS 环境"
    RESULTS["adapter.real_subscription"]="BLOCKED"
    ((BLOCKED_COUNT++))
fi

echo ""

# ------------------------------------------------------------------
# Integration gate
# ------------------------------------------------------------------

echo "[ integration ]"

_run_pytest \
    "gate.full_pipeline" \
    "src/model_deploy/act/tests/integration/test_l2_02_gate.py" \
    "端到端 mock 全链路"

echo ""

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

echo "────────────────────────────────"
TOTAL=$((PASS_COUNT + FAIL_COUNT + BLOCKED_COUNT))
echo "  $PASS_COUNT PASS / $FAIL_COUNT FAIL / $BLOCKED_COUNT BLOCKED  (共 $TOTAL 标签)"
echo ""

# ------------------------------------------------------------------
# Exit code
# ------------------------------------------------------------------

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
else
    exit 0
fi

#!/usr/bin/env bash
# ============================================================================
# L2-03 ACT Inference 统一验收脚本
#
# 按 L2 Gate 标签逐项运行，分层分组输出 PASS/FAIL/BLOCKED。
# 用法:
#     bash src/model_deploy/act/scripts/l2_03_verify.sh
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
        # Print failure detail per §4.2 format
        local last_line
        last_line=$(echo "$out" | grep -E 'FAILED|ERROR' | tail -1 | sed 's/^[[:space:]]*//')
        echo "    ├─ pytest: $path"
        echo "    └─ 摘要: $last_line"
    fi
}

_run_pytest_test() {
    # $1 = label, $2 = test selector (pytest path::class::method), $3 = description
    local label="$1" selector="$2" desc="$3"
    local out rc
    out=$(python3 -m pytest "$selector" -v --tb=short 2>&1)
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
        local last_line
        last_line=$(echo "$out" | grep -E 'FAILED|ERROR' | tail -1 | sed 's/^[[:space:]]*//')
        echo "    ├─ pytest: $selector"
        echo "    └─ 摘要: $last_line"
    fi
}

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------

echo "=== L2-03 ACT Inference 验收 ==="
echo ""

# ==================================================================
# [ types ]
# ==================================================================

echo "[ types ]"

_run_pytest \
    "types.action_chunk_contract" \
    "src/model_deploy/act/tests/types/test_action_chunk.py" \
    "ActionChunk 只含合法 physical actions"

echo ""

# ==================================================================
# [ config / repo ]
# ==================================================================

echo "[ config / repo ]"

echo -n "  "
VIOLATIONS=$(find src/model_deploy/act/config src/model_deploy/act/repo -name '*act_inference*' -o -name '*inference*' -o -name '*action_chunk*' -o -name '*observation_batch*' 2>/dev/null || true)
if [ -z "$VIOLATIONS" ]; then
    echo "PASS  boundary.reuse_only  未新增 config/repo 产物"
    RESULTS["boundary.reuse_only"]="PASS"
    ((PASS_COUNT++))
else
    echo "FAIL  boundary.reuse_only  未新增 config/repo 产物"
    echo "    ├─ 越界文件: $VIOLATIONS"
    RESULTS["boundary.reuse_only"]="FAIL"
    ((FAIL_COUNT++))
fi

echo ""

# ==================================================================
# [ service ]
# ==================================================================

echo "[ service ]"

_run_pytest_test \
    "service.batch.tensorize_state" \
    "src/model_deploy/act/tests/service/test_observation_batch.py::TestTensorizeState" \
    "state 表达转换"

_run_pytest_test \
    "service.batch.normalize_state" \
    "src/model_deploy/act/tests/service/test_observation_batch.py::TestNormalizeState" \
    "state 只归一化一次"

_run_pytest_test \
    "service.batch.bind_images" \
    "src/model_deploy/act/tests/service/test_observation_batch.py::TestBindImages" \
    "图像按 policy key 绑定"

_run_pytest_test \
    "service.batch.add_dimension" \
    "src/model_deploy/act/tests/service/test_observation_batch.py::TestAddBatchDim" \
    "batch 维度添加"

_run_pytest_test \
    "service.batch.assemble" \
    "src/model_deploy/act/tests/service/test_observation_batch.py::TestAssembleActBatch" \
    "ACT batch 组装"

_run_pytest_test \
    "service.batch.device" \
    "src/model_deploy/act/tests/service/test_observation_batch.py::TestAlignToDevice" \
    "设备对齐"

_run_pytest_test \
    "service.policy.predict_chunk" \
    "src/model_deploy/act/tests/service/test_act_inference.py::TestRunActInference" \
    "只调用 policy chunk API"

_run_pytest_test \
    "service.policy.error_propagation" \
    "src/model_deploy/act/tests/service/test_act_inference.py::TestFailurePropagation" \
    "前向失败传播"

_run_pytest_test \
    "service.output.raw_shape" \
    "src/model_deploy/act/tests/service/test_action_chunk_postprocess.py::TestCheckRawOutputStructure" \
    "raw 输出结构检查"

_run_pytest_test \
    "service.output.unbatch" \
    "src/model_deploy/act/tests/service/test_action_chunk_postprocess.py::TestRemoveBatchDim" \
    "batch 维移除"

_run_pytest_test \
    "service.output.unnormalize" \
    "src/model_deploy/act/tests/service/test_action_chunk_postprocess.py::TestUnnormalizeActions" \
    "action 反归一化"

_run_pytest_test \
    "service.output.float32_cpu" \
    "src/model_deploy/act/tests/service/test_action_chunk_postprocess.py::TestToCpuFloat32Array" \
    "CPU float32 转换"

_run_pytest_test \
    "service.output.final_contract" \
    "src/model_deploy/act/tests/service/test_action_chunk_postprocess.py::TestCheckFinalOutputContract" \
    "最终输出契约检查"

_run_pytest_test \
    "service.output.no_repair" \
    "src/model_deploy/act/tests/service/test_action_chunk_postprocess.py::TestPostprocessActionChunk" \
    "不裁剪、不补齐、不 clamp"

_run_pytest_test \
    "service.full_chain" \
    "src/model_deploy/act/tests/service/test_act_inference.py::TestEndToEnd" \
    "snapshot 到 ActionChunk 闭环"

_run_pytest_test \
    "service.policy.no_select_action" \
    "src/model_deploy/act/tests/service/test_act_inference.py::TestEndToEnd::test_select_action_never_called" \
    "select_action 未被调用"

# Run the full service test suites as integration validation
_run_pytest \
    "service.observation_batch_full" \
    "src/model_deploy/act/tests/service/test_observation_batch.py" \
    "阶段一批次准备全量测试"

_run_pytest \
    "service.postprocess_full" \
    "src/model_deploy/act/tests/service/test_action_chunk_postprocess.py" \
    "阶段三后处理全量测试"

_run_pytest \
    "service.inference_full" \
    "src/model_deploy/act/tests/service/test_act_inference.py" \
    "ActInferenceService 全量测试"

echo ""

# ==================================================================
# [ integration ]
# ==================================================================

echo "[ integration ]"

_run_pytest_test \
    "service.error_stops_chain" \
    "src/model_deploy/act/tests/integration/test_l2_03_gate.py::TestErrorStopsChain" \
    "各阶段失败时链停止"

_run_pytest \
    "gate.full_chain" \
    "src/model_deploy/act/tests/integration/test_l2_03_gate.py" \
    "三阶段闭环 Gate 集成测试"

echo ""

# ==================================================================
# [ runtime / ui / boundary ]
# ==================================================================

echo "[ runtime / ui / boundary ]"

_run_pytest_test \
    "boundary.no_resource_io" \
    "src/model_deploy/act/tests/integration/test_l2_03_gate.py::TestBoundary::test_no_resource_io" \
    "无 bundle/checkpoint/path 加载器"

_run_pytest_test \
    "boundary.no_runtime_state" \
    "src/model_deploy/act/tests/integration/test_l2_03_gate.py::TestBoundary::test_no_runtime_state" \
    "无 worker/queue/cursor/metrics"

_run_pytest_test \
    "boundary.no_ros_or_hardware" \
    "src/model_deploy/act/tests/integration/test_l2_03_gate.py::TestBoundary::test_no_ros_or_hardware" \
    "无 ROS/硬件交互"

_run_pytest_test \
    "boundary.no_safety_or_smoothing" \
    "src/model_deploy/act/tests/integration/test_l2_03_gate.py::TestBoundary::test_no_safety_or_smoothing" \
    "无 safety/smoothing/clamp/IK"

_run_pytest_test \
    "boundary.only_allowed_layers" \
    "src/model_deploy/act/tests/integration/test_l2_03_gate.py::TestBoundary::test_only_allowed_layers" \
    "文件只在 types/service/tests"

echo ""

# ==================================================================
# Summary
# ==================================================================

echo "────────────────────────────────"
TOTAL=$((PASS_COUNT + FAIL_COUNT + BLOCKED_COUNT))
echo "  $PASS_COUNT PASS / $FAIL_COUNT FAIL / $BLOCKED_COUNT BLOCKED  (共 $TOTAL 标签)"
echo ""

# ==================================================================
# Exit code
# ==================================================================

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
else
    exit 0
fi

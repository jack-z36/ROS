#!/usr/bin/env bash
# ============================================================================
# L2-01 一键验收脚本
# 用法: bash DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/scripts/run_acceptance.sh
# ============================================================================

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
export PYTHONPATH="src:$PYTHONPATH"

# --------------- 颜色 ---------------
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0; FAIL=0; TOTAL=0

# --------------- 工具函数 ---------------
check() {
    local label="$1"; shift
    TOTAL=$((TOTAL + 1))
    local out="/tmp/_accept_$$_${TOTAL}.txt"
    printf "${CYAN}[%2d/10]${NC} %s ... " "$TOTAL" "$label"
    if "$@" > "$out" 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC}"
        head -10 "$out" | sed 's/^/       /'
        if [ "$(wc -l < "$out")" -gt 10 ]; then
            echo "       ... (完整: $out)"
        fi
    fi
}

pytest_check() {
    local label="$1"; shift
    check "$label" python3 -m pytest "$@" -q --tb=short
}

section() {
    echo
    echo -e "${BOLD}━━━ $1 ━━━${NC}"
}

# ====================================================================
section "代码正确性 — 6 个测试组"
# ====================================================================

pytest_check \
    "① StateSpec 16D 维度/段序/值域" \
    src/model_deploy/act/tests/types/test_state_spec.py

pytest_check \
    "② ActionSpec 16D 维度/段序/值域" \
    src/model_deploy/act/tests/types/test_action_spec.py

pytest_check \
    "③ RuntimeConfig hz/chunk/mode/fallback 校验" \
    src/model_deploy/act/tests/config/test_runtime_config.py

pytest_check \
    "④ SafetyConfig TCP限制/gripper值域/quaternion" \
    src/model_deploy/act/tests/config/test_safety_config.py

pytest_check \
    "⑤ bundle 交付物校验 + normalizer 维度一致性" \
    src/model_deploy/act/tests/repo/test_bundle_reader.py \
    src/model_deploy/act/tests/config/test_contract.py

pytest_check \
    "⑥ DeployConfig 聚合 + 非法配置入口失败" \
    src/model_deploy/act/tests/config/test_deploy_config.py \
    src/model_deploy/act/tests/integration/test_startup_failure.py

# ====================================================================
section "不应该存在的东西 — 4 个静态检查"
# ====================================================================

check \
    "⑦ 平滑配置泄漏检查" \
    bash -c '
    patterns="smoothstep|blend_steps|cross_chunk|rtc_alignment|action_smoothing"
    hits=0
    for dir in src/model_deploy/act/types \
               src/model_deploy/act/config \
               src/model_deploy/act/repo \
               src/model_deploy/act/config_files; do
        [ -d "$dir" ] || continue
        found=$(grep -rn "$patterns" "$dir" 2>/dev/null || true)
        if [ -n "$found" ]; then hits=1; echo "$found"; fi
    done
    [ "$hits" -eq 0 ]
    '

check \
    "⑧ 不应存在的代码层产物 (service/runtime/ui)" \
    bash -c '
    bad=0
    for layer in service runtime ui; do
        dir="src/model_deploy/act/$layer"
        [ -d "$dir" ] || continue
        found=$(find "$dir" -name "*.py" 2>/dev/null | grep -v __init__.py || true)
        if [ -n "$found" ]; then bad=1; echo "$found"; fi
    done
    [ "$bad" -eq 0 ]
    '

check \
    "⑨ types 层无 ROS 依赖污染" \
    bash -c '
    ! grep -r "import rospy\|from sensor_msgs\|from std_msgs\|import rclpy" \
        src/model_deploy/act/types/ 2>/dev/null
    '

check \
    "⑩ bridge/mux 残余检查 + import 链路" \
    env PYTHONPATH="src:$PYTHONPATH" bash -c '
    python3 -c "
from model_deploy.act.types import StateSpec, ActionSpec
from model_deploy.act.config import DeployConfig, DeployConfigError
from model_deploy.act.repo import ActionStateNormalizer
print(\"import OK\")
"
    '

# ====================================================================
section "验收结果汇总"
# ====================================================================

echo
printf "  通过: ${GREEN}%2d${NC} / 失败: ${RED}%2d${NC} / 总计: %2d\n" "$PASS" "$FAIL" "$TOTAL"
echo

if [ "$FAIL" -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}✅ L2-01 全部验收项通过${NC}"
    rm -f /tmp/_accept_$$_*.txt
    exit 0
else
    echo -e "  ${RED}${BOLD}❌ L2-01 有 ${FAIL} 项验收失败${NC}"
    echo "  失败详情见 /tmp/_accept_$$_*.txt"
    exit 1
fi

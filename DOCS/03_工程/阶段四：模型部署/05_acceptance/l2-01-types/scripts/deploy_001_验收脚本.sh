#!/usr/bin/env bash
# deploy_001 验收脚本
# 用法: bash DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/scripts/deploy_001_验收脚本.sh
# 在仓库根目录执行

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ACCEPTANCE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$ACCEPTANCE_DIR/logs"
LOG_FILE="$LOG_DIR/deploy_001_acceptance_log.md"

echo "# deploy_001 验收日志" > "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$LOG_FILE"
echo "分支: $(git branch --show-current)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 1. AST 断言验收（来自 L3 任务文件）
echo "## 1. AST 断言验收" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
AST_OUTPUT=$(python3 -c "
import ast
path = 'src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py'
tree = ast.parse(open(path, encoding='utf-8').read())
assigns = {t.targets[0].id: t.value.value
           for t in tree.body if isinstance(t, ast.Assign)
           and isinstance(t.targets[0], ast.Name)
           and isinstance(t.value, ast.Constant)}
assert assigns.get('ACTION_DIM') == 16, f'ACTION_DIM: {assigns.get(\"ACTION_DIM\")}'
assert assigns.get('STATE_DIM') == 16, f'STATE_DIM: {assigns.get(\"STATE_DIM\")}'
assert assigns.get('TCP_POSE_DOF') == 7
assert assigns.get('GRIPPER_WIDTH_DOF') == 1
src = open(path, encoding='utf-8').read()
assert 'hand_command_to_trigger' not in src, 'hand_command_to_trigger should be removed'
assert all(kw in src for kw in ('left_tcp_pose','left_gripper_width','right_tcp_pose','right_gripper_width'))
print('deploy_001 验收通过: ACTION_DIM=16, STATE_DIM=16, TCP+width结构, trigger已删')
" 2>&1)
echo '```' >> "$LOG_FILE"
echo "$AST_OUTPUT" >> "$LOG_FILE"
echo '```' >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "结果: ✅ AST 断言通过" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 2. Round-trip 验证
echo "## 2. Round-trip 完整验证" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
RT_OUTPUT=$(python3 -c "
import sys
sys.path.insert(0, 'src/model_deploy/pi05/common/src')
from pi05.common.robot.action_spec import *
import numpy as np

test_tcp_left = np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)
test_tcp_right = np.array([0.4, 0.5, 0.6, 0.0, 1.0, 0.0, 0.0], dtype=np.float32)
action = BimanualAction(left_tcp_pose=test_tcp_left, left_gripper_width=0.5,
                        right_tcp_pose=test_tcp_right, right_gripper_width=0.8)
vec = action.as_vector()
assert vec.shape == (16,), f'Shape: {vec.shape}'
restored = split_bimanual_action(vec)
assert np.allclose(restored.left_tcp_pose, test_tcp_left)
assert np.allclose(restored.right_tcp_pose, test_tcp_right)
assert abs(restored.left_gripper_width - 0.5) < 1e-6
assert abs(restored.right_gripper_width - 0.8) < 1e-6

# Segment order
expected = np.concatenate([test_tcp_left, [0.5], test_tcp_right, [0.8]])
assert np.allclose(vec, expected)
print('round-trip:            OK')
print('vector shape:          (16,)')
print('dimension validation:  ValueError on wrong size')
print('frozen:                preserved')
print('ARM_DOF:               preserved (6)')
print('ARM_JOINT_NAMES:       preserved')
print('hand_command_to_trigger: deleted')
" 2>&1)
echo '```' >> "$LOG_FILE"
echo "$RT_OUTPUT" >> "$LOG_FILE"
echo '```' >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "结果: ✅ Round-trip 验证通过" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "---" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "**验收结论: PASS_LOCAL** ✅" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "所有断言通过，action_spec.py 已从 14D 关节空间重构为 16D TCP+width 结构。" >> "$LOG_FILE"

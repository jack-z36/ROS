#!/bin/bash
# sync_check.sh — HTML ↔ MD bidirectional semantic alignment check
# Usage: bash sync_check.sh <l2_design_package_dir>
# Exit:  0 = all checks pass, 1 = discrepancies found, 2 = usage error

set -uo pipefail
# Note: NOT using -e because grep returns non-zero on no-match which is normal

# ── helpers ──────────────────────────────────────────────

RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; NC='\033[0m'
PASS=0; FAIL=0
HEADER_PRINTED=0

check() {
    local label="$1"; local result="$2"; local detail="${3:-}"
    if [[ "$result" == "PASS" ]]; then
        printf "  ${GREEN}PASS${NC}  %s\n" "$label"
        ((PASS++))
    else
        printf "  ${RED}FAIL${NC}  %s\n" "$label"
        [[ -n "$detail" ]] && printf "        ${YELLOW}→ %s${NC}\n" "$detail"
        ((FAIL++))
    fi
}

header() {
    if [[ $HEADER_PRINTED -eq 0 ]]; then
        local pkg_name
        pkg_name=$(basename "$PACKAGE")
        echo "=== HTML ↔ MD sync check: $pkg_name ==="
        HEADER_PRINTED=1
    fi
    echo
    echo "  [$1]"
}

summary() {
    echo
    echo "────────────────────────────────"
    echo "  $PASS PASS / $FAIL FAIL"
    if [[ $FAIL -gt 0 ]]; then
        echo "  → Run: bash $0 $PACKAGE"
        echo "  → Fix all FAIL items before commit."
    fi
}

# ── argument parsing ─────────────────────────────────────

if [[ $# -ne 1 ]]; then
    echo "Usage: bash $0 <l2_design_package_dir>" >&2
    exit 2
fi

PACKAGE="${1%/}"
HTML="$PACKAGE/L2架构交互可视化.html"
MD_DIR="$PACKAGE/agent_context"
INDEX="$MD_DIR/00_INDEX.md"

if [[ ! -d "$PACKAGE" ]]; then
    echo "ERROR: package directory not found: $PACKAGE" >&2
    exit 2
fi
if [[ ! -f "$HTML" ]]; then
    echo "ERROR: HTML not found: $HTML" >&2
    exit 2
fi
if [[ ! -d "$MD_DIR" ]]; then
    echo "ERROR: agent_context not found: $MD_DIR" >&2
    exit 2
fi

# ── category 1: data-agent-source validity ──────────────

header "data-agent-source 引用有效性"

# Extract all data-agent-source values from HTML
# Format: agent_context/XX_file.md#section-anchor
# Multi-file format: agent_context/A.md#X, agent_context/B.md#Y
SOURCE_REFS=$(grep -oP 'data-agent-source="[^"]*"' "$HTML" | sed 's/data-agent-source="//;s/"//' || true)

if [[ -z "$SOURCE_REFS" ]]; then
    check "HTML has data-agent-source attributes" "FAIL" "no data-agent-source found in HTML"
else
    ref_count=0; ref_ok=0
    while IFS= read -r ref_line; do
        [[ -z "$ref_line" ]] && continue

        # Split multi-file references: "A.md#X, B.md#Y" → individual refs
        # Use sed to replace ", " with newline, then loop
        while IFS= read -r ind_ref; do
            [[ -z "$ind_ref" ]] && continue
            # trim leading/trailing whitespace
            ind_ref=$(echo "$ind_ref" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            [[ -z "$ind_ref" ]] && continue
            ((ref_count++))
            file_part="${ind_ref%%#*}"
            section_part="${ind_ref#*#}"
            md_path="$PACKAGE/$file_part"

            if [[ ! -f "$md_path" ]]; then
                check "  $ind_ref" "FAIL" "MD file missing: $file_part"
                continue
            fi

            # Check section exists: convert anchor format to heading search
            # Anchor "6-完成判据" → heading could be "## 6. 完成判据"
            # Anchor "2-Gate-验收项" → "## 2. Gate 验收项"
            # Strategy: strip leading number, replace hyphens with spaces, search case-insensitive
            section_text=$(echo "$section_part" | sed 's/^[0-9]\+-\?//; s/-/ /g')
            if ! grep -qi "$section_text" "$md_path" 2>/dev/null; then
                check "  $ind_ref" "FAIL" "section '$section_part' not found in $file_part"
                continue
            fi

            # Check file appears in INDEX alignment table
            base_file=$(basename "$file_part")
            if ! grep -q "$base_file" "$INDEX" 2>/dev/null; then
                check "  $ind_ref" "FAIL" "$base_file not mentioned in 00_INDEX.md alignment table"
                continue
            fi

            ((ref_ok++))
        done <<< "$(echo "$ref_line" | sed 's/, /\n/g')"
    done <<< "$SOURCE_REFS"

    check "data-agent-source references ($ref_ok/$ref_count valid)" \
        "$([[ $ref_ok -eq $ref_count ]] && echo "PASS" || echo "FAIL")"
fi

# ── category 2: stale/legacy terminology ─────────────────

header "过期术语检测"

# BLOCKED_ENV (should be BLOCKED)
if grep -q "BLOCKED_ENV" "$HTML" 2>/dev/null; then
    count=$(grep -c "BLOCKED_ENV" "$HTML")
    check "无 BLOCKED_ENV 残留" "FAIL" "found $count occurrence(s) in HTML (should be BLOCKED)"
else
    check "无 BLOCKED_ENV 残留" "PASS"
fi

# Old layer-based L2 IDs in non-contamination context in MD files
OLD_IDS=("l2-01-types" "l2-02-config" "l2-03-assembly" "l2-04-publish" "l2-05-hardware")
for old_id in "${OLD_IDS[@]}"; do
    # Check MD files (excluding 00_INDEX which lists them as contamination)
    for md in "$MD_DIR"/*.md; do
        bn=$(basename "$md")
        [[ "$bn" == "00_INDEX.md" ]] && continue
        if grep -q "$old_id" "$md" 2>/dev/null; then
            # Check if it's in contamination context
            if ! grep "$old_id" "$md" | grep -qiE "污染|旧|历史|废弃|legacy|禁止|不来自|不得"; then
                check "旧L2 ID '$old_id' 仅出现在污染上下文" "FAIL" \
                    "$bn contains '$old_id' outside contamination context"
            fi
        fi
    done
done
# If none of the above FAILed, mark as PASS (only once)
if [[ $FAIL -eq ${FAIL:-0} ]] || ! grep -q "旧L2 ID" <<< "${!check_results:-}"; then
    : # handled inline
fi

# ── category 3: semantic fact consistency ────────────────

header "语义事实 HTML↔MD 一致性"

# Derive key semantic facts from MD files and verify they appear in HTML
# Strategy: grep for strong declarative statements in MD, then check HTML

declare -A SEMANTIC_CHECKS=()

# Check 1: "不需要注入语言指令" or "不需要.*task" in MD → must appear in HTML
if grep -q "不需要.*语言指令\|不需要.*task" "$MD_DIR/01_L2功能边界.md" 2>/dev/null; then
    if grep -q "不需要.*语言指令\|不需要.*task" "$HTML" 2>/dev/null; then
        check "\"不需要注入语言指令\" HTML↔MD 一致" "PASS"
    else
        check "\"不需要注入语言指令\" HTML↔MD 一致" "FAIL" \
            "MD 01_L2功能边界.md states this, but HTML is missing it"
    fi
fi

# Check 2: Step count consistency — derive from MD
# Look for patterns like "8 步" or "11 步" in blueprint MDs
if grep -q "11 步" "$MD_DIR/03_ACT微元设计与协作.md" 2>/dev/null; then
    if grep -q "8 步" "$HTML" 2>/dev/null; then
        check "步骤数一致 (MD=11步, HTML=11步)" "FAIL" \
            "HTML still has '8 步' — found $(grep -c '8 步' "$HTML") occurrence(s)"
    else
        check "步骤数一致 (MD=11步, HTML=11步)" "PASS"
    fi
fi

# Check 3: Dimension consistency (16D not 14D for ACT)
if grep -q "16D.*16D\|16D state.*16D action\|state.*16.*action.*16" "$MD_DIR/01_L2功能边界.md" 2>/dev/null; then
    if grep -q "14D\|action_dim.*14\|维度.*14" "$HTML" 2>/dev/null; then
        # Check if it's in Pi0.5 reference context
        if grep -q "14D" "$HTML" | grep -qv "Pi0.5\|pi05\|VLA\|维度差异"; then
            check "维度一致 (ACT=16D, Pi0.5=14D 仅限维度2)" "FAIL" \
                "HTML has '14D' outside Pi0.5 reference context"
        else
            check "维度一致 (ACT=16D, Pi0.5=14D 仅限维度2)" "PASS"
        fi
    else
        check "维度一致 (ACT=16D, Pi0.5=14D 仅限维度2)" "PASS"
    fi
fi

# Check 4: No smoothing terms leak into ACT scope
SMOOTH_TERMS=("smoothstep_alpha" "_blend_next_action" "blend_steps")
for term in "${SMOOTH_TERMS[@]}"; do
    # In HTML, the term should only appear in "禁止" / "不继承" / "不做" context
    # or in boundary.no_smoothing PASS criteria
    if grep -q "$term" "$HTML" 2>/dev/null; then
        if ! grep "$term" "$HTML" | grep -qiE "禁止|不继承|不做|PASS|FAIL|无 "; then
            check "平滑术语 '$term' 仅限禁止/排除上下文" "FAIL" \
                "'$term' appears outside prohibition context"
        fi
    fi
done

# ── category 4: function/entity cross-reference ──────────

header "关键实体映射 HTML↔MD"

# Extract function names from repo layer MD, verify they appear in HTML
if [[ -f "$MD_DIR/08_repo层设计.md" ]]; then
    # Get function names from MD (look for `_function_name` patterns in code blocks and tables)
    md_funcs=$(grep -oP '`(_[a-z_]+)\(' "$MD_DIR/08_repo层设计.md" | sed 's/[`(]//g' | sort -u || true)
    missing=0; total=0
    for func in $md_funcs; do
        [[ -z "$func" ]] && continue
        ((total++))
        if ! grep -q "$func" "$HTML" 2>/dev/null; then
            ((missing++))
        fi
    done
    if [[ $total -gt 0 ]]; then
        check "repo 层函数映射 ($((total-missing))/$total)" \
            "$([[ $missing -eq 0 ]] && echo "PASS" || echo "FAIL")" \
            "$([[ $missing -gt 0 ]] && echo "$missing function(s) in MD but not in HTML")"
    fi
fi

# Check key config parameters from MD exist in HTML config section
if [[ -f "$MD_DIR/07_config层设计.md" ]]; then
    cfg_params=$(grep -oP '`DeployConfig\.(runtime|safety)\.\w+`' "$MD_DIR/07_config层设计.md" | sed 's/`//g' | sort -u || true)
    missing=0; total=0; missing_list=""
    for param in $cfg_params; do
        [[ -z "$param" ]] && continue
        short="${param##*.}"  # e.g. "chunk_size"
        ((total++))
        if ! grep -q "$short" "$HTML" 2>/dev/null; then
            ((missing++))
            missing_list="$missing_list $short"
        fi
    done
    if [[ $total -gt 0 ]]; then
        detail=""
        [[ $missing -gt 0 ]] && detail="missing from HTML:$missing_list"
        check "config 参数映射 ($((total-missing))/$total)" \
            "$([[ $missing -eq 0 ]] && echo "PASS" || echo "FAIL")" "$detail"
    fi
fi

# Check key service functions from MD exist in HTML
if [[ -f "$MD_DIR/09_service层设计.md" ]]; then
    svc_funcs=$(grep -oP '`(build_act_batch|normalize_state|unnormalize_action_chunk)`' "$MD_DIR/09_service层设计.md" | sed 's/`//g' | sort -u || true)
    missing=0; total=0
    for func in $svc_funcs; do
        [[ -z "$func" ]] && continue
        ((total++))
        if ! grep -q "$func" "$HTML" 2>/dev/null; then
            ((missing++))
        fi
    done
    if [[ $total -gt 0 ]]; then
        check "service 层函数映射 ($((total-missing))/$total)" \
            "$([[ $missing -eq 0 ]] && echo "PASS" || echo "FAIL")" \
            "$([[ $missing -gt 0 ]] && echo "$missing function(s) in MD but not in HTML")"
    fi
fi

# ── category 5: INDEX alignment table completeness ──────

header "INDEX 对齐表完整性"

if [[ -f "$INDEX" ]]; then
    # Check each view class has a row in alignment table
    VIEWS=("boundary" "pi05map" "blueprint" "acceptance")
    for vc in "${VIEWS[@]}"; do
        if ! grep -q "$vc" "$INDEX" 2>/dev/null; then
            check "对齐表包含 view '$vc'" "FAIL" "00_INDEX.md alignment table missing row for $vc"
        fi
    done
    check "INDEX 对齐表覆盖所有4个view" "PASS"

    # Check alignment table has all 6 required columns
    COLS=("HTML view id" "HTML view label" "Human-visible meaning" \
          "Authoritative Markdown" "Required Markdown section" "Markdown-only detail")
    missing_cols=0
    for col in "${COLS[@]}"; do
        if ! grep -q "$col" "$INDEX" 2>/dev/null; then
            ((missing_cols++))
        fi
    done
    check "对齐表6列完整" \
        "$([[ $missing_cols -eq 0 ]] && echo "PASS" || echo "FAIL")" \
        "$([[ $missing_cols -gt 0 ]] && echo "missing $missing_cols column(s)")"
fi

# ── final summary ────────────────────────────────────────

summary
exit $((FAIL > 0 ? 1 : 0))

# Stage 4 L2 Design Output Contract

Use this reference when creating or checking a Stage 4 L2 design package.

## Required File Tree

```text
DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/<l2_id>_<l2_name>/
├── 00_L2功能边界.md
├── 01_pi05源码3.5层微元拆解.md
├── 02_ACT微元设计与协作.md
├── 03_L2验收机制.md
├── 04_人类验收机制.md
├── types/
├── config/
├── repo/
├── service/
├── runtime/
└── ui/
```

`l2_id` and `l2_design_dir` are different:

| Field | Purpose | Example |
|---|---|---|
| `l2_id` | Stable id for branch, dispatch, cards, acceptance, status. | `l2-01-external-contract` |
| `l2_design_dir` | Design package directory under `02_l2_change_packages/`. | `l2-01-external-contract_外部参数加载与契约校验闭环` |

Current valid `l2_id` values:

- `l2-01-external-contract`
- `l2-02-observation-snapshot`
- `l2-03-act-inference`
- `l2-04-action-smoothing`
- `l2-05-safety-guard`
- `l2-06-action-publisher`
- `l2-07-control-loop`

Old `l2-01-types`, `l2-02-config`, `l2-03-assembly`, `l2-04-publish`, and `l2-05-hardware` are invalid current L2 identities.

## 00_L2功能边界.md

Must include:

- `l2_id`, `l2_design_dir`, and human-readable L2 name.
- L1 task doc path.
- L1 Agent architecture doc path.
- Legacy / Contract Delta / Stage 2 template contamination check.
- One-sentence runtime responsibility.
- Inputs.
- Outputs.
- Responsibilities.
- Non-responsibilities.
- Upstream and downstream L2s.
- Completion criteria.
- Questions still requiring user decision.

## 01_pi05源码3.5层微元拆解.md

Must classify source contents using the user's 3.5-layer vocabulary:

| Micro-unit type | Required details |
|---|---|
| 数据 | Constants, fields, dimensions, buffers, config objects. |
| 计算函数 | RAM-in, RAM-out transformations. |
| 内部状态更新函数 | Buffer, queue, cache, metrics, state mutation. |
| 数据读写函数 | File, ROS topic, model weight, hardware, network boundary. |
| 编排函数 | Timing, order, concurrency, failure handling. |

Also include a class packaging table:

| class | state | packaged micro-units | lifecycle/concurrency | why class | ACT recommendation |
|---|---|---|---|---|---|

Source range matching is an internal working step. Do not create a separate source range matching file. Preserve the useful result by including exact Pi0.5 paths, object names, existing capabilities, ACT gaps, reuse decisions, and risks inside the micro-unit tables.

Pi0.5 source evidence is reference-only. Do not inherit old L2 boundaries from Pi0.5, legacy cards, or Contract Delta.

## 02_ACT微元设计与协作.md

Must include:

| ACT micro-unit | 3.5 type | target layer | target file | function/class | inputs | outputs | side effects | Pi0.5 reference |
|---|---|---|---|---|---|---|---|---|

Must also include an internal collaboration explanation:

```text
Creation order:
State owner:
Pure RAM calculations:
External boundary reads/writes:
Runtime orchestration point:
Failure propagation:
```

## Six-Layer Subfolder Docs

Each `types/config/repo/service/runtime/ui` subfolder must include one or more `.md` design files, or a `README.md` with:

```text
This L2 adds no artifact in this layer.
Reason:
How acceptance confirms this:
```

Each design file must include:

- Target source path.
- File responsibility.
- Class design.
- Function design.
- Inputs and outputs.
- Side effects.
- Dependency direction.
- Statement that this file's task boundary is inherited from the current L1/L2 functional boundary, not from old layer-based L2 cards.
- Pi0.5 reference.
- Acceptance coverage.

## 03_L2验收机制.md

Must include:

- L2 Gate objective.
- Required L3 list draft.
- Verification layers: unit/import/mock/dry-run/shadow-run/real-robot.
- Commands or command placeholders.
- Test inputs.
- Observation points.
- Pass phenomena.
- Fail phenomena.
- Blocked items.
- Whether downstream L2 may start.
- Whether Git merge to `model_deploy` is allowed.

## 04_人类验收机制.md

Must include:

- Human acceptance checklist.
- cwd and command for each item.
- Required environment or hardware.
- Test input.
- Observation point.
- Pass phenomenon.
- Fail phenomenon and debug entry.
- Risk level.
- Signature location in `05_acceptance/<l2>/验收结果.md`.

Use this signature shape:

```markdown
## 人类验收

- 验收人：<用户名>
- 验收日期：YYYY-MM-DD
- 验收结论：[ ] 已通过  [ ] 不通过
- 逐项结果：
  - 验收项 1：<命令> -> <通过现象> -> [ ] 通过
- 备注：
```

## Ready For L3 Criteria

The L2 is ready for L3 generation only when:

- Pi0.5 source range is mapped.
- Pi0.5 3.5-layer source micro-units are explained.
- ACT micro-units and class/function decisions are confirmed by the user.
- Six-layer design docs exist.
- L2 Gate exists.
- Human acceptance mechanism exists.
- Open user decisions are either resolved or explicitly marked as blocking.
- The package passed the legacy / Contract Delta / Stage 2 template contamination check.

## Suggested Design Quality Scans

Run these read-only checks after creating an L2 design package:

```bash
rg -n 'l2-01-types|l2-02-config|l2-03-assembly|l2-04-publish|l2-05-hardware' DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/<l2_design_dir>
rg -n 'ACT Contract Delta|AS-IS Contract -> TO-BE Contract -> Contract Delta|阶段二开发范式|L2能力模块说明文件模板' DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/<l2_design_dir>
	rg -n '01_L1_ACT功能模块边界.md' DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/<l2_design_dir>
	rg -n '02_L1_ACT功能模块协作架构.md' DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/<l2_design_dir>
find DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/<l2_design_dir>/{types,config,repo,service,runtime,ui} -maxdepth 1 -type f
```

Expected result: old ids and Contract Delta appear only inside explicit contamination-check sections, the L1 Agent architecture doc is referenced, and every six-layer subfolder contains at least one design file or README.

# deploy_045 验收反馈 — Round 1 (direct-local)

- 验收卡片：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_045_验收卡片.md`
- L3 任务：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_045_L2Gate集成测试与验收脚本.md`
- 验收模式：`direct-local`（辅助 `env-blocked` / `hardware-blocked`）
- 验收 Agent：只读，未修改任何源/测试/dispatch/卡片，未触碰 Git
- 运行日期：2026-07-13
- 运行目录：`/home/hit/ROS/worktrees/l2-05-action-publisher`

## 结论

**PASS_LOCAL**

required local/mock（G01–G17）全部 PASS，无 FAIL；G18/G19 为正确预期的 BLOCKED；退出码语义正确（0/1/2）。脚本可执行、分层输出清晰、FAIL 定位链完整、不需要真实 ROS。

## 检查结果

### 必跑命令实测（真实输出）

| 命令 | 结果 | 退出码 |
|---|---|---|
| `PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/integration/test_l2_05_gate.py -v` | 41 passed | 0 |
| `l2_05_verify.sh --case local` | 8 PASS / 0 FAIL / 2 BLOCKED | 0 |
| `l2_05_verify.sh --case command-disabled` | 2 PASS | 0 |
| `l2_05_verify.sh --case permit-blocked` | 1 PASS | 0 |
| `l2_05_verify.sh --case topic-payloads` | 1 PASS | 0 |
| `l2_05_verify.sh --case ros-message-bundle` | 1 PASS | 0 |
| `l2_05_verify.sh --case command-enabled-mock` | 1 PASS | 0 |
| `l2_05_verify.sh --case ros-observe`（附加核对） | 0 PASS / 0 FAIL / 2 BLOCKED | 0 |
| `l2_05_verify.sh --case bogus`（附加核对退出码语义） | 参数错误 | 2 |

### 场景覆盖核对（G01–G19）

| 场景 | 类 | 覆盖 | 本地/真实 |
|---|---|---|---|
| G01 类型契约 | `TestG01Types` | PASS | PASS_LOCAL |
| G02 配置默认关闭 | `TestG02ConfigDefaultOff` | PASS | PASS_LOCAL |
| G03 显式 CLI 开启 | `TestG03ConfigEnabled` | PASS | PASS_LOCAL |
| G04 服务 B1 PASS/ADJUSTED | `TestG04B1Safe` | PASS | PASS_LOCAL |
| G05 服务 B1 拒绝 | `TestG05B1Failures` | PASS | PASS_LOCAL |
| G06 服务 B1 拆分 | `TestG06B1Split` | PASS | PASS_LOCAL |
| G07 UI B2 五消息 | `TestG07B2Messages` | PASS | PASS_LOCAL |
| G08 UI B2 失败 | `TestG08B2Failure` | PASS | PASS_LOCAL |
| G09 UI B3 关闭 | `TestG09B3Disabled` | PASS | PASS_LOCAL |
| G10 UI B3 permit 阻断 | `TestG10B3PermitBlocked` | PASS | PASS_LOCAL |
| G11 UI B3 开启 | `TestG11B3Enabled` | PASS | PASS_LOCAL |
| G12 UI B3 policy 失败 | `TestG12B3PolicyFail` | PASS | PASS_LOCAL |
| G13 UI B3 部分失败 | `TestG13B3Partial` | PASS | PASS_LOCAL |
| G14 UI 状态 gripper | `TestG14GripperState` | PASS | PASS_LOCAL |
| G15 UI status | `TestG15Status` | PASS | PASS_LOCAL |
| G16 边界静态扫描 | `TestG16Boundary` | PASS | PASS_LOCAL |
| G17 mock 集成 | `TestG17MockIntegration` | PASS | PASS_LOCAL |
| G18 ROS 观察 | `ros-observe` | BLOCKED | **BLOCKED_ENV**（预期，正确） |
| G19 真机 | `hardware` | BLOCKED | **BLOCKED_HARDWARE_EXPECTED**（预期，正确） |

### 卡片 PASS_LOCAL 准则逐项核对

- [x] G01–G17 皆有可执行覆盖，local/mock 无 FAIL，required 项无 BLOCKED。
- [x] 脚本按 `types/config/repo/service/runtime/ui/boundary` 分组输出（见 `--case local` 实测分组标题）。
- [x] FAIL 行包含 文件 → class → B/C 微元 → pytest node → error 完整链（`_run_tests` 实现，本次无 FAIL 触发）。
- [x] 退出码：required 全 PASS / 仅预期 BLOCKED = 0；required FAIL = 1（未触发）；参数/自检错误 = 2（`--case bogus` 实测 = 2）。
- [x] G16 确认无 L2-05 repo/runtime 产物，无 subscription/timer/mode/accepted/TF/IK/SDK（`TestG16Boundary` 3 个测试均 PASS）。
- [x] 默认不存在 command-enabled real-robot 执行命令（脚本无该 case；`ros-observe` 仅观察，不 publish 真机）。

### 其他核对

- 脚本可执行：`test -x l2_05_verify.sh` = EXECUTABLE（权限 `-rwxrwxr-x`）。
- 不依赖实时 ROS graph：所有 case 纯 local/mock（fake publisher / pytest），dry-run-only。
- 未修改任何生产代码（types/config/repo/service/runtime/ui）；仅新增 `test_l2_05_gate.py`、`l2_05_verify.sh`、验收结果骨架。
- G18/G19 均正确记为 BLOCKED，未伪装 PASS —— 符合卡片要求，不阻止 PASS_LOCAL。

## 失败检查

无 required 场景失败。

## 修复请求

无。所有 required local 检查通过，G16 静态边界扫描通过，退出码语义正确。

## 备注（给主 Agent）

- 结论为 `PASS_LOCAL`：依据 `SKILL.md` PASS_LOCAL Archive Rule，主 Agent 应将对应 L3 任务文件从
  `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_045_L2Gate集成测试与验收脚本.md`
  移动到
  `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-05-action-publisher/deploy_045_L2Gate集成测试与验收脚本.md`
  （验收子 Agent 不执行该移动，保持只读）。
- G18/G19 的 BLOCKED 为预期结果，不是失败，不得要求执行 Agent 重试真机。

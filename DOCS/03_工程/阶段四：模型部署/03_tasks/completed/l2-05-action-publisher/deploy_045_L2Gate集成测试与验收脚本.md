# L3 微元改造任务：L2 Gate 集成测试与验收脚本

## 1. 任务定位

阶段：阶段四：模型部署  
L1：ACT 部署程序开发  
所属 L2：`l2-05-action-publisher` 单步 Action 到执行器 Topic 适配发送闭环  
L3 编号：deploy_045  
改造类型：`test-coverage`  
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_045_L2Gate集成测试与验收脚本.md`  
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_045_验收卡片.md`  
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/`  
验收模式：`direct-local`  
辅助验收模式：[`env-blocked`, `hardware-blocked`]  
本地验收是否必须：`true`  
真机风险等级：`dry-run-only`  
L2 分支：`feat/model_deploy/l2-05-action-publisher`  
集成分支：`model_deploy`

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_045
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_045_L2Gate集成测试与验收脚本.md
  group: l2-05-action-publisher
  branch: feat/model_deploy/l2-05-action-publisher
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher
  acceptance_scenarios: [G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12, G13, G14, G15, G16, G17, G18, G19]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_045_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [env-blocked, hardware-blocked]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/logs
  wave: 4
  parallel_group: l2-05-action-publisher-p4
  depends_on: [deploy_041, deploy_042, deploy_043, deploy_044]
  must_run_after: [deploy_044]
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/tests/integration/test_l2_05_gate.py
      - src/model_deploy/act/scripts/l2_05_verify.sh
      - DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/验收结果.md
    modules:
      - model_deploy.act.tests.integration.test_l2_05_gate
    runtime_modes: []
    hardware_paths:
      - /act/policy_action
      - /act/command/status
      - /act/command/arm/left_target
      - /act/command/arm/right_target
      - /act/command/gripper/left_target
      - /act/command/gripper/right_target
  robot_risk: dry-run-only
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 Agent 只新增 Gate 测试、统一脚本与验收结果骨架；不借 Gate 任务扩大修改生产语义。
- 验收 Agent 只读。真实 ROS 不可用时 G18=`BLOCKED_ENV`；无硬件/授权时 G19=`BLOCKED_HARDWARE_EXPECTED`，都不得伪造 PASS。
- 最多 3 轮执行-验收迭代。

## 3. 本次唯一目标

```text
实现可一键执行的 L2-05 local/mock Gate：汇总 C1-C21、B1-B3、A1 与边界纯度，用分层 PASS/FAIL/BLOCKED 输出支撑 Agent 和人类验收。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 在无真实硬件的情况下，使用 types/config/service/ui/fake publisher 证明完整闭环和默认禁止 command 不变量。

### L2 不负责

- 不把 ROS publish 成功当成 driver 接受/硬件到位，不提供默认真机命令。

### 本 L3 在 L2 中的位置

```text
deploy_041-044 交付生产微元与局部测试；本 L3 是 required L3 汇总点与 L2 Gate 执行入口。
```

### 必读 L2 设计文档

- 目标 L2 `agent_context/00-11` 全部 Markdown，重点为 `03a`、`04_L2验收机制.md`、`05_人类验收机制.md`。
- L1 边界/协作只用于识别交接口；当旧语义冲突时以目标 L2 Markdown 为准。
- HTML 不是 Gate 来源。

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 类型 | 已有能力 | 差距 | 复用 |
|---|---|---|---|---|---|
| 无独立 L2-05 Gate | — | — | 旧系统仅有 node/bridge/mux 运行路径 | 缺少双门控、partial 事实和分层 mock Gate | 不复用 |

### 禁止照搬

- 不得依赖真机/ROS 才能验证核心 Gate；不把 mode/bridge/mux 行为写成 PASS 标准。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `tests/integration/test_l2_05_gate.py`，覆盖 `04_L2验收机制.md` G01-G17 required local/mock 场景。
- 新建目标 L2 Markdown 指定的统一入口 `src/model_deploy/act/scripts/l2_05_verify.sh`，支持：
  - `local`、`command-disabled`、`permit-blocked`
  - `topic-payloads`、`ros-message-bundle`、`command-enabled-mock`
  - `ros-observe`
- 按 `types/config/repo/service/runtime/ui/boundary` 分组输出 `PASS|FAIL|BLOCKED LABEL 描述`；FAIL 附文件、class、B/C 微元、pytest node 与 error。
- 退出码：required local/mock 全 PASS 且仅预期 BLOCKED=0；任一 required FAIL=1；参数/环境自检错误=2。
- 执行 G16 静态边界扫描；repo/runtime 必须显示无 L2-05 产物。
- 可初始化 `05_acceptance/l2-05-action-publisher/验收结果.md` 骨架。

### 本次不做

- 不默认执行 G18 真实 ROS 或 G19 真机；不新建 driver/launch。
- Gate 发现上游缺陷时，返回对应 L3 修正；不在本任务顺手重构生产文件。

### 函数 / class 策略

```text
测试使用 pytest fixture/fake publisher；verify 为 bash 编排入口。不新增生产 class。
```

## 7. 六层产物落点

| 层 | 涉及 | 路径 | 职责 |
|---|---|---|---|
| tests | 是 | `src/model_deploy/act/tests/integration/test_l2_05_gate.py` | G01-G17 汇总 |
| scripts | 是 | `src/model_deploy/act/scripts/l2_05_verify.sh` | L2 Markdown 指定的统一验证入口 |
| acceptance | 可选 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/验收结果.md` | 结果骨架 |
| types/config/repo/service/runtime/ui | 否 | — | 不在 Gate 任务修改生产语义 |

### 对应六层设计文档

- `04_L2验收机制.md` §3-§4：场景、label、输出格式与退出码。
- `05_人类验收机制.md` §2-§4：可执行 case、观察与证据落点。
- `06-11` 六层设计：标签对应微元和无产物边界。

## 8. 文件内 3.5 层功能微元

| 文件 | 微元 | 类型 | 输入 | 输出 | 副作用 | 验收 |
|---|---|---|---|---|---|---|
| `test_l2_05_gate.py` | Gate 场景 | 编排（测试） | mock RAM/fake publishers | assert PASS/FAIL | 仅测试状态 | G01-G17 |
| `l2_05_verify.sh` | 分层汇总 | 编排（脚本） | case+环境+pytest 退出码 | 终端摘要+进程退出码 | 启动子进程 | 人类/Gate |

## 9. 实施步骤

1. 建立 G01-G19 -> pytest/case/label 映射，先写集成测试。
2. 实现 verify 参数解析、分层输出、FAIL 定位链和退出码。
3. 运行 `local`、`command-disabled`、`permit-blocked`、`topic-payloads`、`ros-message-bundle`、`command-enabled-mock`。
4. 若 ROS 不可用，验证 `ros-observe` 输出 BLOCKED 而非假 PASS；不运行真机。

## 10. 允许修改

- `src/model_deploy/act/tests/integration/test_l2_05_gate.py`
- `src/model_deploy/act/scripts/l2_05_verify.sh`
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/验收结果.md`

## 11. 禁止修改

- 无最小缺陷证据时不得修改 deploy_041-044 生产文件。
- runtime/node/launch/driver/硬件 SDK、Pi0.5 参考源、HTML/L1 文档。
- 不得产生真机发送默认配置或真机命令。

## 12. 验证方式

```bash
bash src/model_deploy/act/scripts/l2_05_verify.sh --case local
```

```bash
bash src/model_deploy/act/scripts/l2_05_verify.sh --case command-disabled
bash src/model_deploy/act/scripts/l2_05_verify.sh --case permit-blocked
bash src/model_deploy/act/scripts/l2_05_verify.sh --case topic-payloads
bash src/model_deploy/act/scripts/l2_05_verify.sh --case ros-message-bundle
bash src/model_deploy/act/scripts/l2_05_verify.sh --case command-enabled-mock
```

| 层级 | 需要 | PASS |
|---|---|---|
| unit/import/mock | 是 | G01-G17 无 FAIL，required 项无 BLOCKED |
| ROS observation | 条件性 | 可用则观察 policy/status 且 command 静默；否则记 BLOCKED_ENV |
| real-robot | 默认否 | 无授权/急停/现场证据时必须 BLOCKED |

### 真机风险控制

- verify 默认不触发真实 driver，不包含 command-enabled real-robot case。
- 真机项必须另由现场验收卡写明人工授权、急停、driver readiness、topic 核对和回滚。

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 场景 | G01-G19（G18/G19 可预期 BLOCKED） |
| 能力 | 统一可执行 L2-05 Gate 与人类可读输出 |
| 后续 | L2 Gate 卡、人类签字及 L2-06 真实启动对接 |

## 13. 必读上下文

- 阶段四工作流、ACT 落点约束、L3 模板、目标 L2 `agent_context/00-11`。
- deploy_041-044 任务与产物；既有 L2 verify 脚本只参考输出组织。

## 14. 执行要求

- 路径、文件名、正文、dispatch 均为 `deploy_045`；deploy_041-044 已达可用终态。
- 任一 required 失败必须输出完整定位链并返回非零；BLOCKED 不得伪装 PASS。

## 15. 成功标准

- [x] G01-G17 皆有可执行测试/label，local/mock 无 FAIL。
- [x] verify 支持设计中全部人类 case，输出分层且 FAIL 定位完整。
- [x] 退出码 0/1/2 语义正确，G18/G19 环境/硬件缺失时记录预期 BLOCKED。
- [x] G16 证明无 repo/runtime/subscription/timer/mode/accepted/TF/IK/SDK 越界。
- [x] 未执行、未声称真机 PASS。

## 16. 回滚方式

```text
删除 test_l2_05_gate.py 与 l2_05_verify.sh；若初始化了验收结果骨架，只删除本 L3 新增的未签字内容。
```

## 17. 完成后交接

- 附加各 case 命令、SUMMARY、BLOCKED 理由和边界扫描证据。
- 不自行归档、commit 或 push；交由验收 Agent 判定后再进入 L2 Gate。

## 18. 执行摘要与证据（2026-07-13, direct-local）

### 18.1 实现落点（仅新增，未改生产语义）

- `src/model_deploy/act/tests/integration/test_l2_05_gate.py` — L2 Gate 集成测试，覆盖 G01-G17，驱动 deploy_041/042/043/044 公共入口端到端闭环 + G16 静态边界扫描（含 repo/runtime 无 L2-05 产物核对）。
- `src/model_deploy/act/scripts/l2_05_verify.sh` — 统一验收入口，支持 `local / command-disabled / permit-blocked / topic-payloads / ros-message-bundle / command-enabled-mock / ros-observe`；分层 PASS/FAIL/BLOCKED 输出，FAIL 给出 file→class→micro-unit→pytest→error 定位链；退出码 0/1/2。
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/验收结果.md` — 验收结果骨架（含汇总、边界扫描证据、人类签字区）。

### 18.2 验证命令与结果

| 命令 | 结果 | 退出码 |
|---|---|---|
| `PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/integration/test_l2_05_gate.py -v` | 41 passed | 0 |
| `bash src/model_deploy/act/scripts/l2_05_verify.sh --case local` | 8 PASS / 0 FAIL / 2 BLOCKED | 0 |
| `... --case command-disabled` | 2 PASS | 0 |
| `... --case permit-blocked` | 1 PASS | 0 |
| `... --case topic-payloads` | 1 PASS | 0 |
| `... --case ros-message-bundle` | 1 PASS | 0 |
| `... --case command-enabled-mock` | 1 PASS | 0 |
| `... --case ros-observe` | 0 PASS / 2 BLOCKED | 0 |
| `... --case bogus`（未知） | 参数错误 | 2 |

### 18.3 场景覆盖（G01-G19）

- G01 类型契约 → `TestG01Types`（frozen/不变式/拒绝矛盾字段） PASS
- G02 配置默认关闭 → `TestG02ConfigDefaultOff`（C7 默认 False、YAML 不能静默开启） PASS
- G03 显式 CLI 开启 → `TestG03ConfigEnabled`（C7=True） PASS
- G04 服务 B1 PASS/ADJUSTED → `TestG04B1Safe`（非空 C4、不读 `.accepted`） PASS
- G05 服务 B1 拒绝 → `TestG05B1Failures`（REJECTED/shape/NaN/爪域） PASS
- G06 服务 B1 拆分 → `TestG06B1Split`（[0:7]/[7:14]/[14]/[15]、单 frame、0/50/100） PASS
- G07 UI B2 五消息 → `TestG07B2Messages`（frame/stamp/xyzw、无 status） PASS
- G08 UI B2 失败 → `TestG08B2Failure`（无 partial、无 publish） PASS
- G09 UI B3 关闭 → `TestG09B3Disabled`（OBSERVED、command=0） PASS
- G10 UI B3 permit 阻断 → `TestG10B3PermitBlocked`（BLOCKED、reason 可读） PASS
- G11 UI B3 开启 → `TestG11B3Enabled`（PUBLISHED、四路 command） PASS
- G12 UI B3 policy 失败 → `TestG12B3PolicyFail`（FAILED、command=0） PASS
- G13 UI B3 部分失败 → `TestG13B3Partial`（PARTIAL、真实 count、停止剩余） PASS
- G14 UI 状态 gripper → `TestG14GripperState`（deadband/interval/cache 仅成功更新） PASS
- G15 UI status → `TestG15Status`（OBSERVED/BLOCKED/PARTIAL 一致、unknown=null） PASS
- G16 边界静态扫描 → `TestG16Boundary`（无越界 token/import；repo/runtime 无 L2-05 产物） PASS
- G17 mock 集成 → `TestG17MockIntegration`（多 tick 同步、partial 后恢复、无 retry/fallback） PASS
- G18 ROS 观察 → `ros-observe` 记 BLOCKED（本环境无实时观察目标，dry-run；command 静默由契约保证） BLOCKED（预期）
- G19 真机 → 默认 BLOCKED（无人工授权/急停/现场证据） BLOCKED（预期）

### 18.4 未验证项（真实 ROS / 硬件）

- 真实 ROS graph 观察（G18）：本环境 `rclpy` 可导入但未连接 graph，按 dry-run 记 BLOCKED，未启动真实 driver。
- 真实机器人执行（G19）：无人工授权/急停就绪/driver readiness/ROS 观察证据，默认 BLOCKED_HARDWARE_EXPECTED；不声称真机 PASS。

### 18.5 结论

required local/mock（G01-G17）全部 PASS，无 FAIL；G18/G19 为预期 BLOCKED；退出码语义正确（0/1/2）。未修改任何生产代码（types/config/repo/service/runtime/ui），仅新增集成测试、verify 脚本与验收结果骨架。建议下一步运行 `deploy_045_验收卡片.md` 进行验收 Agent 判定。


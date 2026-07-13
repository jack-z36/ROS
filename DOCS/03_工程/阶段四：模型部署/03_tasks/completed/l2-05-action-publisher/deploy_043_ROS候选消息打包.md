# L3 微元改造任务：ROS 候选消息打包

## 1. 任务定位

阶段：阶段四：模型部署  
L1：ACT 部署程序开发  
所属 L2：`l2-05-action-publisher` 单步 Action 到执行器 Topic 适配发送闭环  
L3 编号：deploy_043  
改造类型：`contract-adapter`  
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_043_ROS候选消息打包.md`  
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_043_验收卡片.md`  
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/`  
验收模式：`direct-local`  
辅助验收模式：[`env-blocked`]  
本地验收是否必须：`true`  
真机风险等级：`none`  
L2 分支：`feat/model_deploy/l2-05-action-publisher`  
集成分支：`model_deploy`

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_043
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_043_ROS候选消息打包.md
  group: l2-05-action-publisher
  branch: feat/model_deploy/l2-05-action-publisher
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher
  acceptance_scenarios: [G07, G08]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-action-publisher/deploy_043_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [env-blocked]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/logs
  wave: 2
  parallel_group: l2-05-action-publisher-p2
  depends_on: [deploy_041]
  must_run_after: [deploy_041]
  can_run_parallel_with: [deploy_042]
  blocks: [deploy_044, deploy_045]
  conflict_scope:
    files:
      - src/model_deploy/act/ui/action_publisher.py
      - src/model_deploy/act/tests/ui/test_action_publisher_messages.py
    modules:
      - model_deploy.act.ui.action_publisher
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 Agent 只实现 B2/C8/C12-C14 的 RAM 内 ROS message 构造与测试。
- 验收 Agent 只读；测试可用 mock message class，不得因无 ROS graph 跳过 required local 项。
- 最多 3 轮执行-验收迭代。

## 3. 本次唯一目标

```text
实现 B2 build_ros_messages，把完整 C4 一次性打包为不含 status、不产生 publish 副作用的 C8 五消息 bundle。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 将 policy16、左右臂 C3 和左右爪 `0..100` 转为标准 ROS transport 消息。

### L2 不负责

- B2 不读 CLI/permit，不做 deadband，不调 publisher，不构造最终 status。

### 本 L3 在 L2 中的位置

```text
依赖 deploy_041 的 C4；与 deploy_042 并行实现；产出 C8 供 deploy_044 B3 顺序写出。
```

### 必读 L2 设计文档

- L1 边界/协作 Markdown。
- 目标 L2 `agent_context/00_INDEX.md`、`01`、`02`、`03`、`03a`、`04`、`05`、`06_types`、`07_config`、`09_service`、`10_runtime`、`11_ui`。
- HTML 不作为实现输入。

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 类型 | 已有能力 | 差距 | 复用 |
|---|---|---|---|---|---|
| `_control_tick` 消息构造段 | `deploy/.../pi05_vla_deploy_node.py:196-212` | 编排函数 | 构造 JointState/Float64 并发布 | 边构造边发，14D joint，无完整 bundle | 仅参考消息构造位置 |
| `_joint_msg` 类似 helper | 同上 | 计算函数 | JointState 字段设置 | 当前需 PoseStamped/xyzw/frame/stamp | 不复用数值语义 |

### 必须保留的启发

- ROS message 应先在 RAM 中全部构造成功，再交给外部写出边界。

### 禁止照搬

- JointState 臂命令、14D、边构造边 publish、mode 分支和 bridge subscription。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 在 `ui/action_publisher.py` 实现模块私有 C8 `_RosMessageBundle`。
- C12 `_build_policy_msg`：长度 16 finite tuple -> `Float32MultiArray`。
- C13 `_build_arm_msg`：C3 + finite `ros_time_s` -> `PoseStamped`，保持单一 frame、xyz、xyzw。
- C14 `_build_gripper_msg`：`0..100` finite -> `Float64`。
- B2 按 C12 -> C13×2 -> C14×2 一次性构造 C8；任一失败无部分返回。
- 使用 lazy ROS import 或可注入的 message factory，使无 ROS 环境仍可 import 与 mock 测试。

### 本次不做

- 不实现 A1/B3/C15-C21，不创建 publisher，不构造 status。
- 不新增 Node/launch/subscription/timer。

### 函数 / class 策略

```text
C8 为模块私有短生命数据容器；B2/C12-C14 是无状态模块函数，不创建 class。
```

## 7. 六层产物落点

| 层 | 涉及 | 路径 | 职责 |
|---|---|---|---|
| ui | 是 | `src/model_deploy/act/ui/action_publisher.py` | B2/C8/C12-C14 RAM 消息构造 |
| tests | 是 | `src/model_deploy/act/tests/ui/test_action_publisher_messages.py` | G07/G08 |
| types | 只读 | deploy_041 C4 | transport-neutral 输入 |
| config/repo/service/runtime | 否 | — | 无产物 |

### 对应六层设计文档

| 文档 | 内容 |
|---|---|
| `11_ui层设计.md` | C8、B2、C12-C14 |
| `06_types层设计.md` | 只读 C3/C4 |
| `07_config`、`08_repo`、`09_service`、`10_runtime` | 本 L3 不新增产物 |

## 8. 文件内 3.5 层功能微元

| 文件 | 微元 | 类型 | 输入 | 输出 | 副作用 | 验收 |
|---|---|---|---|---|---|---|
| `ui/action_publisher.py` | C8 | 数据 | 5 个 message | 私有 bundle | 无 | G07 |
| 同上 | B2 | 编排函数 | C4+ROS time | C8 | 无 | G07/G08 |
| 同上 | C12 | 计算函数 | policy16 | Float32MultiArray | 无 | G07 |
| 同上 | C13 | 计算函数 | C3+time | PoseStamped | 无 | G07 |
| 同上 | C14 | 计算函数 | 0..100 | Float64 | 无 | G07 |

## 9. 实施步骤

1. 先用 mock message class 写长度、finite、frame/stamp/xyzw、爪域和无 status 字段测试。
2. 实现 C12-C14 与 C8，再实现 B2 编排。
3. 运行无 ROS import/mock 单测；环境可用时可补真实 ROS message 构造，不作 required local 前提。

## 10. 允许修改

- `src/model_deploy/act/ui/action_publisher.py`
- `src/model_deploy/act/tests/ui/test_action_publisher_messages.py`

## 11. 禁止修改

- `src/model_deploy/act/types/`、`config/`、`repo/`、`service/`、`runtime/`
- `ui/__init__.py`（B3 稳定公共导出由 deploy_044 完成）
- Pi0.5 参考源、HTML/L1 和其他 L2 文档

## 12. 验证方式

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/ui/test_action_publisher_messages.py -v
```

| 层级 | 需要 | PASS |
|---|---|---|
| unit/import/mock | 是 | C8 五消息完整、无 status、无 publish 副作用 |
| ROS graph | 否 | 缺环境可记 `BLOCKED_ENV`，不影响 required mock |
| real-robot | 否 | 本 L3 不调 publisher |

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 场景 | G07-G08 |
| 能力 | C4 -> C8 五消息完整打包 |
| 后续 | deploy_044 选择、写出并根据事实构造 status |

## 13. 必读上下文

- 阶段四工作流、ACT 落点约束、L3 模板、目标 L2 `agent_context/00-11`。
- deploy_041 产物 `types/action_publish.py`；当前 `ui/` 代码与测试约定。
- Pi0.5 deploy node 只作 publisher/message 结构参考。

## 14. 执行要求

- 路径、文件名、正文、dispatch 均核对为 `deploy_043`；`deploy_041` 已达可用终态。
- 测试优先，禁止把 publisher 或 status 便利性逻辑提前塞入 B2。

## 15. 成功标准

- [x] C12/C13/C14 正确构造五个消息，frame/stamp/xyz/xyzw/夹爪域正确。
- [x] C8 恰好包含 policy+两臂+两爪，不含 status。
- [x] 任一 builder 失败时 B2 不返回部分 bundle。
- [x] 无 ROS graph 仍可 import 和 mock 测试，没有任何 publisher 调用。

## 16. 回滚方式

```text
删除本 L3 在 action_publisher.py 中的 B2/C8/C12-C14 段落与消息单测；不影响 deploy_041/042。
```

## 17. 完成后交接

- 登记 pytest 证据和无副作用说明；不归档、commit 或 push。

## 18. 执行摘要（Execution Summary）

执行子 Agent：deploy_043（B2/C8/C12-C14 ROS 候选消息打包）。

### 改动文件

- 新增 `src/model_deploy/act/ui/action_publisher.py`：实现模块私有 C8 `_RosMessageBundle`、B2 `build_ros_messages`、C12 `_build_policy_msg`、C13 `_build_arm_msg`、C14 `_build_gripper_msg`，并带可注入 `_MessageFactory`（无 ROS 时回退纯 Python stand-in）。
- 新增 `src/model_deploy/act/tests/ui/test_action_publisher_messages.py`：G07/G08 共 15 个用例，使用注入式 mock message factory，无 ROS graph。

### 验证命令

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/ui/test_action_publisher_messages.py -v
```

### 结果

- 15 passed / 0 failed（pytest 7.4.4，Python 3.12.3，本环境无 ROS）。
- G07：C8 恰好五消息（policy Float32MultiArray + 两臂 PoseStamped + 两爪 Float64）；frame_id 单一、stamp sec/nanosec 正确、xyz/xyzw 正确、夹爪 0..100 域正确；bundle 无 status 字段。
- G08：policy 长度/非有限、frame 空、ros_time 非有限、夹爪越域均抛错；晚期 builder 失败不产生部分 C8；通过 publisher spy 确认 B2 全程无 publish 调用。
- 无 ROS 环境可 import；默认 factory 回退到纯 Python stand-in 仍可完整构造。

### 边界遵守

- 未改 `types/`、`config/`、`repo/`、`service/`、`runtime/`、`ui/__init__.py`、Pi0.5 源、HTML/L1 文档。
- 未创建 publisher / Node / launch / subscription / timer，未构造 status，未读 CLI/permit，未做 deadband。
- 未触碰 deploy_042 文件；C4 `TopicPayloadBundle` 仅作为只读输入消费，未修改 `types/action_publish.py`。

### 未验证项（Unverified）

- 真实 ROS message（rclpy / std_msgs / geometry_msgs）构造路径未在本地执行（无 ROS graph）；`_ROS_AVAILABLE=False`，默认走 mock stand-in。属 `BLOCKED_ENV` 辅助模式，不影响 required mock 验收。
- 与 deploy_044（B3/C8→C6 status）的端到端衔接未执行（由 deploy_044 负责）。
- 真机 / ROS graph 行为不在本 L3 范围（robot_risk: none，本 L3 不调 publisher）。

### Git / 归档

- 未执行任何 Git 操作，未归档、未 commit、未 push（由 main Agent 负责）。


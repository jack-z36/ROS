# L2-04 Agent 上下文索引

## 1. 定位与权威性

| 字段 | 内容 |
|---|---|
| L2 | `l2-04-safety-guard`，单步 Action 安全检查闭环 |
| 消费对象 | L2/L3 设计、实现、验收 Agent；L2-06/L2-05 集成 Agent |
| 权威来源 | 本目录 Markdown；L1 任务、边界、协作 Markdown；用户确认的 A/B/C 微元体系 |
| 人类入口 | `../L2架构交互可视化.html` |
| 本轮范围 | 重写 `agent_context/`，不生成 L3、不改源码、不改 HTML |

本目录是 L2-04 的 Agent 权威上下文。HTML 是人类投影，不能用于 L3 生成。

> [!warning] HTML 同步状态
> 本轮已把 A/B/C 编号、`xyzw`、无基准拒绝、旋转/夹爪步长检查同步到 HTML 维度3：<b>图② = A/B/C 三层功能模块总览（3 张表）</b>，<b>图③ = 六层代码落点</b>（types 层 C1-C3/C5；service 层 1 个 classbox `safety_guard.py`，按业界 Python 规范组织：模块级 dataclass C4 + 模块级纯函数 C6-C15 + class SafetyGuard A1/B1-B5）。<b>图① 运行时协作 SVG 仍为旧命名</b>（ensure_action_vector / _clamp_tcp_delta / _check_quaternion），未同步 A/B/C 编号，下次 HTML 同步处理；在那之前不要把图① 作为 A/B/C 编号权威。

## 2. 推荐读取路径

| 目的 | 必读文件 |
|---|---|
| 全局理解模块、编号与调用树 | `03a_功能微元总览与组织结构.md` |
| L2 输入、输出、负责/不负责 | `01_L2功能边界.md` |
| Pi0.5 结构参考及不可复用项 | `02_pi05源码3.5层微元拆解.md` |
| ACT 微元输入输出、状态与失败传播 | `03_ACT微元设计与协作.md` |
| AI L2 Gate 与验证标签 | `04_L2验收机制.md` |
| 人工 mock/shadow/真机验收 | `05_人类验收机制.md` |
| types 数据契约 | `06_types层设计.md` |
| config 跨 L2 协调 | `07_config层设计.md` |
| repo 层无产物原因 | `08_repo层设计.md` |
| A1/B/C 核心实现落点 | `09_service层设计.md` |
| runtime 状态/fallback 边界 | `10_runtime层设计.md` |
| ui/硬件适配边界 | `11_ui层设计.md` |

## 3. A/B/C 编号约定

```text
A（3.25 层）= 打包 B/C 的行为 Class
B（3.375 层）= 组织多个 C 微元的同步编排函数
C（3.5 层）= 不再继续拆分的数据或纯计算微元
```

当前体系固定为：`A1`、`B1-B5`、`C1-C15`。编号、总量与父子关系只在 `03a_功能微元总览与组织结构.md` 维护。

> [!note] 结构校验例外
> `03a_功能微元总览与组织结构.md` 是用户明确要求新增的全局 Agent 文档。现有 `validate_l2_design_package.py` 仍固定只接受 12 个 Markdown，因此会单独报它为 unexpected；这不是文档语义错误。后续若要将 L2-04 置为“validator-ready”，应由文档体系维护任务扩展校验器的允许文件表，而不是删除本文件。

## HTML-MD 语义对齐表

| HTML view id | HTML view label | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `boundary` | 功能边界 | L2 输入、输出、负责与不负责 | `agent_context/01_L2功能边界.md` | `## 2. Runtime 边界` | 绝对位姿、两个基准、无基准拒绝、状态所有权 |
| `pi05map` | Pi0.5 如何运作 | Pi0.5 SafetyGuard 的结构来源 | `agent_context/02_pi05源码3.5层微元拆解.md` | `## 2. Pi0.5 微元与 ACT 映射` | 不可复用的关节限位、逐轴 clip 和 fallback |
| `blueprint` | 开发蓝图 | A/B/C 组织与六层落点 | `agent_context/03a_功能微元总览与组织结构.md`、`agent_context/03_ACT微元设计与协作.md`、`agent_context/06_types层设计.md` 至 `agent_context/11_ui层设计.md` | `## 2. 总量与分层`、`## 3. 调用树`、`## 2. ACT 微元设计` | 图② = A/B/C 三层功能模块总览（3 张表：A1/B1-B5/C1-C15 各一张）；图③ = 六层落点，types classbox 标题=safety_result.py、service classbox 标题=safety_guard.py（按业界 Python 规范：模块级 C4+C6-C15 + class SafetyGuard A1/B1-B5）；图① SVG 仍为旧命名未同步 |
| `acceptance` | 人类验收标准 | 如何验证安全检查 | `agent_context/04_L2验收机制.md`、`agent_context/05_人类验收机制.md` | `## 3. 验证标签`、`## 2. 人类验收清单` | label 到 A/B/C 的映射和 blocked 规则 |

## 4. 污染与边界检查

- 当前边界只来自 L1 任务、L1 边界、L1 协作、L1 绝对位姿原子边界和用户确认。
- `pi05_old` 仅作结构参考；Pi0.5 关节限位、`max_joint_delta_rad`、桥接 fallback 不能直接迁入。
- 旧 layer-based L2、`ACT Contract Delta`、阶段二模板不得作为任务来源。
- L2-04 是纯 service：不得拥有 queue、timer、ROS、硬件、fallback、metrics 或 previous action 状态。

## 5. 实现前外部契约校验

- L2-01 必须让 SafetyConfig 阈值与部署 ActionDomain 同域：米、弧度、夹爪训练动作域。
- L2-01/L2-02/L2-05 必须共同固定内部 pose 的 `xyzw` 与同一坐标系；L2-05 才做 RM65 `wxyz` 适配。
- L2-06 必须只传新鲜 snapshot，并在 L2-05 接受输出后更新 `previous_safe_action`；该对象仍不等于硬件到位反馈。

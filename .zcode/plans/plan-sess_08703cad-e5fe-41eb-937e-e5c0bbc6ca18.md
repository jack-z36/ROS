# 重构 L2-02 HTML：在「语义表示方式」维度对齐 L2-01

## 核心目标
把 `L2架构交互可视化.html` 从「6 个英文 tab + 内联 SVG + 扁平卡片」改造成 L2-01 同款的「4 维度 + 完整组件库 + 类化 SVG」表示体系。**只改表示方式，不改语义内容**（所有 L2-02 的功能边界、Pi0.5 映射、六层落点、验收项等语义全部来自 `agent_context/*.md`，原样保留）。

## 改动文件（共 3 个）

### 文件 1：`L2架构交互可视化.html`（主体重写）

**1. 顶部骨架对齐**
- `<header>` 改为 2 列 grid（左 `<h1>L2-02 · 传感器订阅与 ObservationSnapshot 组装闭环</h1>` + `<p class="subtitle">`；右 `.note` 免责声明框「本页只是人类快速浏览入口，不作为 L3 生成依据…HTML 与 MD 冲突时以 MD 为准」）。
- 6 个英文 tab → **4 维度 tab**，每个 label 带 `<span class="n">N</span>` 圆形编号 + 选中态各自语义色：
  - `维度 1 · 功能边界`（选中色 types-teal）
  - `维度 2 · Pi0.5 如何运作`（选中色 pi-orange）
  - `维度 3 · 开发蓝图`（选中色 types-teal）
  - `维度 4 · 人类验收标准`（选中色 ctrl-dark）
- 每个维度开头加 `.reading-path`（`📖 阅读路径：…→ 维度N 图②`，跨维度跳转用 `onclick` 切 radio），结尾加 `.src` 权威来源标注。

**2. CSS 全量移植 L2-01 的 `:root` 变量与组件库**
- 6 层语义配色 + 配对 `-bg`：`--config/--types/--repo/--warn/--ok/--ctrl/--pi/--yellow/--grey`。
- 移植全部组件 class：`.card`+色变体、`.callout`+变体、`.badge/.tag`、`.figure`、`.classbox/.mu-list/.mu/.kind`(data/calc/io/orch/state)、`.lpick/.ltabs/.lpane`(6 层单选切换)、`.layer-matrix/.lcell`、`.flow/.step.s1-s4/.no/.arrow-r`、`.trace`、`.tree`、`.dict`、`.vfy-item/.vfy-section-tag/.vfy-sep`、`.cmd/.cmd-block`、`.anti-card`、`.artifact`、`details` 旋转标记、`.reading-path`、`.src`。
- SVG 类化：`.box/.band/.title/.sub/.edge/.fedge/.io/.elabel/.mono` + 共享 `<marker id="arrow">`，颜色全部走 `var(--…)`，包在 `.figure` 里。

**3. 6 维度内容映射到 4 维度**（语义不丢，来源 `agent_context/`）
- **维度1·功能边界**：①地位定位图（L2-01 上下游 → L2-02 snapshot/buffer → L2-03/L2-06 消费）；②**负责 vs 不负责边界墙**（绿✓:订阅/转 image/收 TCP pose+gripper/缓存字段/齐全检查/新鲜度/调 L2-01 编 16D/写 latest buffer/暴露诊断；红✗:不调模型/不组 batch/不碰 ActionChunk/不决推理节奏/不管 ControlLoop tick/不做 safety/不发硬件）；③输入输出契约（6 个 `/act/observation/*` topic → `ObservationSnapshot(images, ObservationState, encoded_state[16], captured_at_s)` → `ObservationBuffer.latest_observation`）。dataflow 的数据流 SVG 并入这里。
- **维度2·Pi0.5 如何运作**：白话三件套（collector/buffer/node 各自干什么）+ `.dict` 术语词典（callback/snapshot/latest-only/max_age_s/monotonic stamp 等，对应认知框架层）+ `.trace` 跟一个字段（如 left TCP pose 从 topic → decode → collector.update_tcp_pose → snapshot → buffer）+ Pi0.5→ACT 差异 `.callout.pi`（26D→16D、topics 改名、ObservationSnapshot 移到 types/、不照搬 SharedBuffer 整体）。
- **维度3·开发蓝图**：①装配时序图（L2-01 DeployConfig/codec → types 定义契约 → service collector 组装 → runtime buffer latest-only → ui adapter 转消息）；②**6 层落点单选切换器** `.lpick`（types/service/runtime/ui = 有产物，config/repo = 无产物并解释原因：复用 L2-01 配置 / 不读 bundle）；③每个有产物层用 `.classbox + .mu-list` 拆解微元（types: `ObservationState`/`ObservationSnapshot`/`ObservationFreshnessResult`；service: `ObservationCollector.update_*/snapshot/missing_fields` + `preprocess_observation_image`；runtime: `ObservationBuffer`/`ObservationMetrics`；ui: `ObservationRosAdapter`/`decode_image_message`/`handle_*_callback`）。
- **维度4·人类验收标准**：用 `.vfy-item` 卡（编号 + 做什么 + `.cmd-block` 命令 + 绿✅通过/红❌失败 + `📎 对应维度1/3 §X` 回溯链）。两组：**代码正确性**（合法 mock snapshot shape==(16,)、缺字段拒绝、stale 拒绝、latest-only A→B、ROS adapter 边界 import、L2 边界 `rg` 越界检查）+ **不应该存在的东西**（无模型推理/ActionChunk 消费/safety/硬件发送）。`BLOCKED_ENV`/`BLOCKED_HARDWARE_EXPECTED` 用 `.callout.warn`。

### 文件 2：`agent_context/00_INDEX.md`（同步第 33-42 行）
- 「HTML-MD 语义对齐表」表头从 `HTML view id / label` 改为 `HTML 维度 / 维度名`，6 行重映射为 4 行（`维度1功能边界`/`维度2 Pi0.5`/`维度3开发蓝图`/`维度4人类验收标准`），每行的 Authoritative Markdown 和 Required section 沿用原 6 行内容合并（无信息丢失）。

### 文件 3：`agent_context/05_人类验收机制.md`（同步第 20 行）
- 第 4 项「HTML 对齐检查」通过现象从 `能看到 overview/dataflow/runtime/failure/metrics/boundary` 改为 `每个维度有 data-agent-source，能看到维度1/维度2/维度3/维度4`。

## 执行约束
- **只动表示方式**：所有 class 名、文件路径、维度值、topic 名、验收命令、blocked 分类、Pi0.5 参考对象等语义，严格取自 `agent_context/*.md`，不增删 L2-02 的实际职责或验收标准。
- **L2-01 仅作表示参考**：移植的是组件库、配色、叙事骨架（reading-path/图①②/回溯链/vfy-item），不引入 L2-01 的业务语义（如 16D state 段序细节、bridge/mux、blend_steps 等）。
- 单文件 HTML，无外部依赖，`<details>`/radio 切换保持纯 CSS+最小 inline JS（跨维度跳转用 `document.getElementById('vN').click()`）。

## 验证方式
重写后在浏览器打开核对：4 维度 tab 切换正常、6 层选择器联动、SVG 配色统一、每个维度有 `.src` 来源、`rg data-agent-source` 命中 4 个维度。
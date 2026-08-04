# Web 控制中心 — 程序架构知识

## 定位

Web 控制中心为 ACT 推理程序提供浏览器图形化控制面板。它采用**双层进程架构**，外层管理推理进程生命周期，内层嵌入只读 Web 服务暴露运行时数据。

本文件面向 Agent 消费，描述 Web 控制中心在六架构层（types / config / repo / service / runtime / ui）中的位置和内部结构。

## 架构层归属

| 文件 | 架构层 | 职责 |
|---|---|---|
| `act/ui/web_launcher.py` | **ui** | 外层进程管理器 + FastAPI Web 服务（端口 8080） |
| `act/ui/runtime_bridge.py` | **ui** | Web UI 与 ACT 运行时的只读桥梁，封装对 node 内部状态的线程安全只读访问 |
| `act/ui/static/dashboard.html` | **ui** | 浏览器端图形化控制面板（Vue 3 + Tailwind + ECharts） |
| `act/runtime/debug_observer.py` | **runtime** | Observation 旁路采集层，从 ObservationBuffer 回调中捕获图像和状态数值 |
| `act/runtime/action_debug_recorder.py` | **runtime** | Action 三阶段数据记录器（推理输出 → 安全过滤 → 发布结果） |

## 双层进程架构

```
浏览器 (http://host:8080)
    │
    ▼
┌─────────────────────────────────────────────────┐
│  外层: web_launcher.py  (FastAPI, 端口 8080)     │
│                                                   │
│  - ActProcessManager: 管理推理子进程生命周期       │
│  - REST API: /api/start, /api/stop, /api/status   │
│  - WebSocket: /ws/metrics (1 Hz 广播)             │
│  - 代理转发: 图像流、Observation、Action 数据      │
│  - 静态文件: dashboard.html                        │
└──────────────┬────────────────────────────────────┘
               │ subprocess.Popen (python -m model_deploy.act.ui.act_deploy_node)
               ▼
┌─────────────────────────────────────────────────┐
│  内层: act_deploy_node.py  (daemon 线程, 端口 8081)│
│                                                   │
│  - FastAPI 应用（仅监听 127.0.0.1）                │
│  - RuntimeBridge: 只读访问 node 内部状态           │
│  - DebugObserver: Observation 旁路采集             │
│  - ActionDebugRecorder: Action 三阶段记录          │
│  - REST + WebSocket 端点暴露运行时数据             │
└─────────────────────────────────────────────────┘
```

### 外层 API 端点

| 端点 | 类型 | 说明 |
|---|---|---|
| `GET /` | 静态文件 | 返回 dashboard.html |
| `GET /api/status` | REST | 推理进程状态（running/pid/mode/bundle_dir/events） |
| `POST /api/start` | REST | 启动推理进程，可选 mode 和 bundle_dir |
| `POST /api/stop` | REST | 优雅停止推理进程（SIGINT → 10s → SIGKILL） |
| `POST /api/mode` | REST | 切换 dry-run / real-run 模式并重启 |
| `POST /api/bundle_dir` | REST | 切换模型权重路径并重启 |
| `GET /stream/image/{side}` | MJPEG 流 | 代理转发内层图像流（side: left/right） |
| `GET /api/action/latest` | REST | 代理转发最新 Action 记录 |
| `GET /api/action/history` | REST | 代理转发 Action 历史记录 |
| `GET /api/action/record/{step_id}` | REST | 代理转发单条 Action 记录 |
| `GET /api/action/stats` | REST | 代理转发 Action 统计信息 |
| `WS /ws/metrics` | WebSocket | 1 Hz 实时 metrics 广播 |
| `WS /ws/observation` | WebSocket | 10 Hz Observation 状态推送（代理转发） |
| `WS /ws/action` | WebSocket | Action 数据实时推送（代理转发） |

### 内层 API 端点（仅 127.0.0.1:8081）

| 端点 | 类型 | 说明 |
|---|---|---|
| `GET /internal/metrics` | REST | RuntimeMetrics 快照 |
| `GET /internal/status` | REST | RuntimeBridge 状态摘要 |
| `GET /internal/stream/image/{side}` | MJPEG 流 | DebugObserver 缓存的 JPEG 帧 |
| `GET /internal/observer/state` | REST | 当前 Observation 状态数值 |
| `GET /internal/observer/stats` | REST | DebugObserver 统计信息 |
| `GET /internal/api/action/latest` | REST | 最新 Action 记录 |
| `GET /internal/api/action/history` | REST | Action 历史记录 |
| `GET /internal/api/action/record/{step_id}` | REST | 单条 Action 记录 |
| `GET /internal/api/action/stats` | REST | Action 统计信息 |
| `WS /internal/ws/observation` | WebSocket | Observation 实时推送 |
| `WS /internal/ws/action` | WebSocket | Action 实时推送 |

## 回调钩子注入点与数据流

Web 控制中心通过**回调钩子**将数据采集层注入到现有推理流程中，不修改主流程逻辑：

### Observation 旁路采集

```
ObservationBuffer.add()
    │
    ├─ 原有逻辑: 写入 buffer，供推理使用
    │
    └─ 回调钩子: on_observation(snapshot)
         │
         ▼
    DebugObserver.on_observation()
         │
         ├─ 提取 images → CHW→HWC → JPEG 编码 → 缓存最新帧
         │
         └─ 提取 state → tcp_position/orientation/gripper → 缓存 + 历史
```

- 注入点：`observation_buffer.py` 的 `set_on_observation_callback()` 方法
- 注入时机：`act_deploy_node.py` 的 `_start_internal_web_server()` 中
- 限频：10 FPS（`_min_capture_interval = 0.1`）
- 异常隔离：所有异常被 try/except 吞掉，绝不影响主推理

### Action 三阶段记录

```
ControlLoop._run_inference()
    │
    ├─ 原有逻辑: 推理得到 action vector
    │
    └─ 回调钩子: on_inference_result(action_values)
         │
         ▼
    ActionDebugRecorder.record_inference_result() → 返回 step_id
         │
         ... (安全过滤阶段) ...
         
SafetyGuard / ControlLoop
    │
    └─ 回调钩子: on_safety_result(step_id, verdict, filtered_values)
         │
         ▼
    ActionDebugRecorder.record_safety_result()
         │
         ... (发布阶段) ...

ActionPublisher.publish()
    │
    └─ 回调钩子: on_publish_result(step_id, outcome, command_values)
         │
         ▼
    ActionDebugRecorder.record_publish_result() → 写入 ring buffer
```

- 注入点：
  - `control_loop.py` 构造参数 `on_inference_result` / `on_safety_result`
  - `action_publisher.py` 构造参数 `on_publish_result`
  - `observation_buffer.py` 方法 `set_on_observation_callback()`
- 注入时机：`act_deploy_node.py` 在构造 ControlLoop 和 ActionPublisher 时传入回调
- 数据存储：`collections.deque(maxlen=1000)` ring buffer，线程安全

## 启动方式

### 外层启动（推荐）

```bash
python -m model_deploy.act.ui.web_launcher \
    --config /path/to/deploy.yaml \
    [--port 8080] \
    [--host 0.0.0.0] \
    [--auto-start] \
    [--mode dry-run|real-run]
```

- `--auto-start`：启动时自动运行推理进程
- `--mode`：初始运行模式（默认 dry-run）

### 内层独立启动（调试用）

```bash
python -m model_deploy.act.ui.act_deploy_node \
    --config /path/to/deploy.yaml \
    [--bundle-dir /path/to/bundle] \
    [--enable-command-output]
```

内层启动后自动在 daemon 线程中启动 FastAPI 服务（端口 8081，仅 127.0.0.1）。

## 前端面板功能模块

`dashboard.html` 是单文件 SPA，技术栈：Vue 3 + Tailwind CSS + ECharts。

| 模块 | 说明 | 数据来源 |
|---|---|---|
| 标题栏 | 运行状态指示灯（running/stopped/starting）、PID | `/api/status` |
| 控制面板 | 启动/停止按钮、模式切换（dry-run/real-run）、权重路径输入 | `/api/start`, `/api/stop`, `/api/mode`, `/api/bundle_dir` |
| 运行指标 | Tick 计数、推理成功/失败、安全拒绝、推理延迟、运行状态、回退次数 | `WS /ws/metrics` |
| 事件日志 | 最近 20 条进程事件（start/stop/mode_switch/bundle_change） | `/api/status` |
| Observation 数据 | 左/右摄像头 MJPEG 画面、左/右臂 TCP 位姿数值、左/右夹爪开合度 | `GET /stream/image/{side}`, `WS /ws/observation` |
| Action 数据流 | 统计（总步数/PASS/ADJUSTED/REJECTED）、最新一步三阶段对比、历史表格 | `GET /api/action/*`, `WS /ws/action` |
| Action 趋势图 | 可选维度的 Raw vs Filtered 对比折线图（ECharts） | `WS /ws/action` |

## 关键接口摘要

### RuntimeBridge（ui 层）

```python
class RuntimeBridge:
    def __init__(self, node: ActDeployNode) -> None
    def get_status(self) -> dict      # 运行状态摘要
    def get_metrics(self) -> dict     # RuntimeMetrics 快照
    def get_mode(self) -> str         # 'dry-run' | 'real-run'
    def get_permit_state(self) -> str # 许可状态
    def get_bundle_dir(self) -> str   # 当前 bundle 路径
```

线程安全策略：`RuntimeMetrics.snapshot()` 内部有 lock；`DeployConfig` 是 frozen dataclass；permit_provider 的简单属性读取由 Python GIL 保证原子性；node 状态标记通过 `lifecycle_lock` 保护。

### DebugObserver（runtime 层）

```python
class DebugObserver:
    def on_observation(self, snapshot) -> None  # 回调入口
    def get_latest_jpeg(self, side: str) -> Optional[bytes]
    def get_latest_state(self) -> Optional[dict]
    def get_state_history(self, n: int = 50) -> list
    def get_stats(self) -> dict
```

所有公开方法线程安全，永不抛异常。

### ActionDebugRecorder（runtime 层）

```python
class ActionDebugRecorder:
    def record_inference_result(self, action_values: list) -> int  # 返回 step_id
    def record_safety_result(self, step_id, verdict, filtered_values, details=None)
    def record_publish_result(self, step_id, outcome, command_values)
    def get_latest(self) -> Optional[dict]
    def get_history(self, n: int = 50) -> list
    def get_record(self, step_id: int) -> Optional[dict]
    def get_stats(self) -> dict
```

使用 `deque(maxlen=1000)` 作为 ring buffer，`_pending` dict 关联同一 step 的三个阶段数据，阶段 3 完成后写入 buffer。

## 依赖

- `fastapi`：Web 框架（外层 + 内层）
- `uvicorn`：ASGI 服务器
- `requests`：外层代理转发内层 REST 接口
- `numpy`、`cv2`：DebugObserver 图像编码
- `vue@3`、`tailwindcss`、`echarts@5`：前端（CDN 加载）

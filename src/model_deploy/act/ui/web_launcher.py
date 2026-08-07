"""ACT 推理程序 Web 控制中心 — 外层进程管理器。

双层架构：
- 外层（本模块）：常驻 Web 服务，管理推理进程生命周期
- 内层（act_deploy_node）：推理进程，可被启停/重启

启动方式：
    python -m model_deploy.act.ui.web_launcher --config deploy.yaml [--port 8080]
"""

from __future__ import annotations

import asyncio
import collections
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("act.web_launcher")


# ---------------------------------------------------------------------------
# Pydantic-free request bodies (plain dicts via Query / Body)
# ---------------------------------------------------------------------------

class _StartRequest:
    """Schema for /api/start body."""
    mode: Optional[str] = None
    checkpoint_dir: Optional[str] = None
    bundle_dir: Optional[str] = None


# ---------------------------------------------------------------------------
# ActProcessManager
# ---------------------------------------------------------------------------


class ActProcessManager:
    """管理 act_deploy_node 子进程的生命周期。

    职责：
      - 启动 / 停止 / 重启 act_deploy_node 子进程
      - 维护当前 mode / checkpoint_dir 状态
      - 从内层 Web（端口 8081）轮询 metrics 并通过 WebSocket 广播
      - 记录最近事件供 REST API 查询
    """

    def __init__(
        self,
        config_path: str,
        default_bundle_dir: Optional[str] = None,
        default_checkpoint_dir: Optional[str] = None,
    ) -> None:
        self._config_path = config_path
        self._process: Optional[subprocess.Popen] = None
        self._mode = "dry-run"
        self._checkpoint_dir = default_checkpoint_dir or default_bundle_dir or ""
        self._lock = threading.Lock()
        self._event_log: list[dict] = []
        # 临时 deploy.yaml 路径（覆盖 checkpoint_dir/mode 时生成），stop 后清理。
        self._temp_configs: list[str] = []

        # WebSocket 广播相关
        self._ws_clients: set[WebSocket] = set()
        self._ws_lock = asyncio.Lock()
        self._metrics_loop: Optional[threading.Thread] = None
        self._metrics_stop = threading.Event()
        # 保存 asyncio 事件循环引用，供后台线程 schedule coroutine
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # 子进程输出捕获：避免 stdout/stderr PIPE 写满 64KB 缓冲区导致子进程
        # 在 write() 上永久阻塞（表现为推理进程启动后不久"假死"）。stdout+stderr
        # 全部沉淀到有界 ring buffer，供 Dashboard 实时日志面板展示（启动到哪一步、
        # 模型加载是否卡住、推理是否报错）。_log_seq 单调递增，供前端断线续传去重。
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._log_tail: collections.deque[dict] = collections.deque(maxlen=800)
        self._log_seq: int = 0
        self._log_cond = threading.Condition()
        self._exit_code: Optional[int] = None
        self._exit_time: Optional[float] = None

    # -- 公开 API -----------------------------------------------------------

    def start(
        self,
        mode: Optional[str] = None,
        checkpoint_dir: Optional[str] = None,
        bundle_dir: Optional[str] = None,
    ) -> dict:
        """启动推理进程（一次拉起全部节点）。

        通过 ``ros2 launch act_system act_system.launch.py`` 启动，由 launch 文件
        统一拉起 RM65 双臂 / 大象夹爪 / 双鱼眼相机 / ACT 部署节点 4 个进程。这样
        ACT 节点订阅的 observation topic 才有 publisher，observation 面板才有数据
        （原来只起 ACT 单进程，没有任何硬件 publisher，故 observation 永远为空）。

        安全（双闸门，已验证 fail-closed）：
          - dry-run：临时配置 runtime.mode=dry-run + launch 不加 enable_command_output
            → 不下发电机指令，真机硬件在跑也安全。
          - real-run：临时配置 runtime.mode=real-run + launch 加 enable_command_output:=true
            → 两个闸门同时满足才下发。
        """
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return {"ok": False, "error": "Process already running"}

            if mode:
                self._mode = mode
            if checkpoint_dir and bundle_dir:
                return {"ok": False, "error": "Use either checkpoint_dir or bundle_dir"}
            if checkpoint_dir:
                self._checkpoint_dir = checkpoint_dir
            elif bundle_dir:
                self._checkpoint_dir = bundle_dir

            # 1) 解析 ACT 节点用的 Python（需含 torch 的 model_deploy conda 环境）。
            act_python = self._resolve_act_python()

            # 2) 生成（可能的）临时 deploy.yaml：覆盖 checkpoint_dir / runtime.mode。
            #    launch 文件只有 act_config（整份 yaml）参数，没有单独的 checkpoint_dir /
            #    mode 参数，所以这里物化一份临时配置交给 launch。
            config_path = self._materialize_config()

            # 3) 组装 ros2 launch 命令。launch 文件内部已处理相机 topic remap、
            #    PYTHONPATH 前缀（src + lerobot）、可执行文件缺失跳过告警。
            cmd = [
                "ros2", "launch", "act_system", "act_system.launch.py",
                f"act_python:={act_python}",
                f"act_config:={config_path}",
            ]
            if self._mode == "real-run":
                cmd.append("enable_command_output:=true")

            # 4) env 继承父进程（start_web_launcher.sh 已 source ROS/workspace setup
            #    并导出 FASTDDS_BUILTIN_TRANSPORTS）。子进程必须继承 DDS 大图传输
            #    配置，否则相机 30Hz 帧会丢。
            env = os.environ.copy()

            # 5) 启动子进程（新进程组，便于整组清理）。launch 主进程收到 SIGINT 会
            #    优雅停止它拉起的全部子节点。stdout/stderr 接 PIPE 由 reader 线程
            #    排空——所有 4 个节点的日志（output='screen'）都会汇集到此。
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None,
                env=env,
            )

            # 重置上一轮退出诊断，启动两个 daemon 线程排空管道并捕获日志。
            self._exit_code = None
            self._exit_time = None
            with self._log_cond:
                self._log_tail.clear()
                self._log_seq = 0
            self._stdout_thread = threading.Thread(
                target=self._drain_stream,
                args=(self._process.stdout, "stdout"),
                daemon=True,
                name="child-stdout-drain",
            )
            self._stderr_thread = threading.Thread(
                target=self._drain_stream,
                args=(self._process.stderr, "stderr"),
                daemon=True,
                name="child-stderr-drain",
            )
            self._stdout_thread.start()
            self._stderr_thread.start()

            self._log_event(
                "start",
                f"Launch started (PID={self._process.pid}, mode={self._mode}, "
                f"config={config_path})",
            )
            self._start_metrics_forwarder()

            return {"ok": True, "pid": self._process.pid, "mode": self._mode}

    def stop(self) -> dict:
        """优雅停止推理进程（SIGINT → 10 s → SIGKILL）。"""
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                return {"ok": False, "error": "No process running"}

            pid = self._process.pid
            self._stop_metrics_forwarder()

            try:
                os.killpg(os.getpgid(pid), signal.SIGINT)
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Process %d did not exit in 10 s, sending SIGKILL", pid)
                os.killpg(os.getpgid(pid), signal.SIGKILL)
                self._process.wait(timeout=5)
            except ProcessLookupError:
                pass  # 进程已退出

            self._log_event("stop", f"Process stopped (PID={pid})")
            self._process = None
            # 清理本轮生成的临时配置文件
            self._cleanup_temp_configs()
            return {"ok": True}

    def restart(
        self,
        mode: Optional[str] = None,
        checkpoint_dir: Optional[str] = None,
        bundle_dir: Optional[str] = None,
    ) -> dict:
        """重启推理进程（用于模式切换或权重切换）。"""
        self.stop()
        time.sleep(1)  # 等待端口释放
        return self.start(
            mode=mode, checkpoint_dir=checkpoint_dir, bundle_dir=bundle_dir
        )

    def get_status(self) -> dict:
        """获取当前状态摘要。

        关键诊断字段：
          - node_ready: 内层 :8081 Web 是否已响应。:8081 是 ActDeployNode.__init__
            的最后一步才起来的——只要它没好，说明进程还卡在启动早期（模型加载、
            rclpy.init、观测管线装配等），这时 observation/metrics 都不会有数据。
          - obs_frame_count: DebugObserver 已捕获的观测帧数。>0 表示 ROS 订阅确有
            完整快照流入；=0 表示上游（硬件节点未发布/字段不全/cv2 缺失）没数据。
        两个 probe 失败都静默置 None/False，不影响主状态展示。
        """
        running = self._process is not None and self._process.poll() is None
        # 仅在子进程存活时探测内层，避免对已死进程无谓等待。
        node_ready = False
        obs_frame_count: Optional[int] = None
        if running:
            node_ready, obs_frame_count = self._probe_inner()
        return {
            "running": running,
            "pid": self._process.pid if running else None,
            "mode": self._mode,
            "checkpoint_dir": self._checkpoint_dir,
            # Compatibility field consumed by older dashboards/scripts.
            "bundle_dir": self._checkpoint_dir,
            "config_path": self._config_path,
            "events": self._event_log[-20:],
            # 退出诊断：仅在子进程已停止时有意义，供 Dashboard 展示真实原因。
            "exit_code": self._exit_code,
            "exit_time": self._exit_time,
            "log_tail": list(self._log_tail)[-20:],
            # 启动/数据可见性诊断（运行中才探测）。
            "node_ready": node_ready,
            "obs_frame_count": obs_frame_count,
        }

    def _probe_inner(self) -> tuple[bool, Optional[int]]:
        """探测内层 :8081 是否就绪 + observation 帧数。快速失败，不抛异常。

        返回 (node_ready, obs_frame_count)。node_ready=False 表示 :8081 还没起来
        （启动早期）；True 但 obs_frame_count=0 表示起来了但还没收到观测数据。
        校验响应确实含 frame_count/history_size 两个字段——避免代理/沙箱返回的
        任意 200 响应被误判为就绪。
        """
        import requests as _requests

        try:
            resp = _requests.get(
                "http://127.0.0.1:8081/internal/observer/stats", timeout=1.0
            )
            if resp.ok:
                stats = resp.json()
                if isinstance(stats, dict) and "frame_count" in stats and "history_size" in stats:
                    return True, stats.get("frame_count")
        except Exception:
            pass
        return False, None

    def _resolve_act_python(self) -> str:
        """解析 ACT 节点用的 Python 解释器（需含 torch 的 model_deploy conda 环境）。

        镜像 start_act_system.sh 的探测顺序：miniforge3 → miniconda3 → anaconda3
        → 回退 python3。launch 文件本身不把 conda 环境加进 PYTHONPATH，所以
        act_python 必须直指已装好 torch 的解释器。
        """
        home = os.path.expanduser("~")
        for cand in (
            f"{home}/miniforge3/envs/model_deploy/bin/python3",
            f"{home}/miniconda3/envs/model_deploy/bin/python3",
            f"{home}/anaconda3/envs/model_deploy/bin/python3",
        ):
            if os.path.exists(cand):
                return cand
        return "python3"

    def _materialize_config(self) -> str:
        """生成（可能的）临时 deploy.yaml 并返回其路径。

        只有当需要覆盖 bundle_dir 或 runtime.mode 时才物化临时文件；否则直接用
        原始 config_path（launch 文件内部也会把 act_config 默认指向它，但显式传入
        更明确）。临时文件登记到 _temp_configs，stop() 后清理。

        覆盖规则：
          - checkpoint_dir：非空则覆盖 model.checkpoint_dir，并清空旧 bundle。
          - mode：dry-run/real-run 均显式写入 runtime.mode（real-run 才真正下发，
            配合 launch 的 enable_command_output 双闸门）。
        用 PyYAML 安全加载/转储，保留原配置结构；若无 yaml 则回退原路径并告警。
        """
        # 是否需要物化：有 checkpoint 覆盖、或当前 mode 与原配置 mode 不一致。
        need_checkpoint = bool(self._checkpoint_dir and self._checkpoint_dir.strip())
        need_mode = self._mode in ("dry-run", "real-run")
        if not (need_checkpoint or need_mode):
            return self._config_path

        try:
            import yaml
        except ImportError:
            logger.warning(
                "PyYAML 不可用，无法生成临时配置；将直接使用 %s（checkpoint_dir/mode "
                "覆盖不生效）", self._config_path
            )
            return self._config_path

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            if not isinstance(cfg, dict):
                logger.warning("配置根不是映射，跳过临时配置生成：%s", self._config_path)
                return self._config_path
            if need_checkpoint:
                cfg.setdefault("model", {})["checkpoint_dir"] = self._checkpoint_dir.strip()
                cfg.setdefault("bundle", {})["bundle_dir"] = None
            if need_mode:
                cfg.setdefault("runtime", {})["mode"] = self._mode
            # command_output.enabled 绝不写入（schema 禁止，它是 CLI 启动决策）。
            import tempfile

            fd, tmp_path = tempfile.mkstemp(prefix="act_deploy_", suffix=".yaml")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
            self._temp_configs.append(tmp_path)
            logger.info("生成临时配置: %s (mode=%s)", tmp_path, self._mode)
            return tmp_path
        except Exception as e:
            logger.warning("生成临时配置失败 (%s)，回退原配置 %s", e, self._config_path)
            return self._config_path

    def _cleanup_temp_configs(self) -> None:
        """清理 _materialize_config 生成的临时配置文件。"""
        while self._temp_configs:
            tmp = self._temp_configs.pop()
            try:
                os.remove(tmp)
            except OSError:
                pass

    def set_mode(self, mode: str) -> dict:
        """设置模式并重启。"""
        if mode not in ("dry-run", "real-run"):
            return {"ok": False, "error": f"Invalid mode: {mode}"}
        self._log_event("mode_switch", f"Switching to {mode}")
        return self.restart(mode=mode)

    def set_checkpoint_dir(self, checkpoint_dir: str) -> dict:
        """设置 checkpoint 路径并重启。"""
        self._log_event("checkpoint_change", f"Switching checkpoint to {checkpoint_dir}")
        return self.restart(checkpoint_dir=checkpoint_dir)

    def set_bundle_dir(self, bundle_dir: str) -> dict:
        """Legacy alias for setting the model source path and restarting."""
        self._log_event("bundle_change", f"Switching bundle to {bundle_dir}")
        return self.restart(bundle_dir=bundle_dir)

    # -- WebSocket 广播 -----------------------------------------------------

    async def broadcast_metrics(self, data: dict) -> None:
        """将 metrics 数据广播给所有已连接的 WebSocket 客户端。"""
        if not self._ws_clients:
            return
        payload = json.dumps(data, ensure_ascii=False)
        async with self._ws_lock:
            dead: list[WebSocket] = []
            for ws in self._ws_clients:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._ws_clients.discard(ws)

    # -- 内部方法 -----------------------------------------------------------

    def _log_event(self, event_type: str, message: str) -> None:
        entry = {
            "type": event_type,
            "message": message,
            "timestamp": time.time(),
        }
        self._event_log.append(entry)
        logger.info("[%s] %s", event_type, message)

    def _drain_stream(self, stream, name: str) -> None:
        """后台线程：逐行读取子进程 stdout/stderr。

        作用有二：
        1. 持续排空 PIPE，避免 64KB 内核缓冲区写满后子进程 write() 阻塞。
        2. 每行（stdout+stderr 全收）沉淀进有界 ring buffer（_log_tail），带
           单调 seq + stream 标记 + 时间戳，供 Dashboard 实时日志面板展示，定位
           "启动卡在哪一步"；同时转发到外层终端便于现场排障。
        """
        if stream is None:
            return
        while True:
            try:
                line = stream.readline()
            except (ValueError, OSError):
                break  # 管道已关闭
            if not line:
                break
            try:
                text = line.decode("utf-8", errors="replace").rstrip("\n")
            except Exception:
                text = repr(line)
            if not text.strip():
                continue
            with self._log_cond:
                self._log_seq += 1
                self._log_tail.append(
                    {
                        "seq": self._log_seq,
                        "stream": name,
                        "ts": time.time(),
                        "text": text,
                    }
                )
                self._log_cond.notify_all()
            # stderr 更可能含报错，用 info 顶到终端；stdout 用 debug 避免刷屏
            (logger.info if name == "stderr" else logger.debug)(
                "[child:%s] %s", name, text
            )

    def get_logs_after(self, after_seq: int = 0, limit: int = 200) -> list[dict]:
        """返回 seq > after_seq 的日志条目（供前端断线续传），最多 limit 条。"""
        with self._log_cond:
            out = [e for e in self._log_tail if e["seq"] > after_seq][-limit:]
            return out

    def wait_for_new_logs(self, after_seq: int, timeout: float = 15.0) -> list[dict]:
        """阻塞等待 seq > after_seq 的新日志；超时返回空列表。供长轮询 WS 使用。"""
        with self._log_cond:
            if not any(e["seq"] > after_seq for e in self._log_tail):
                self._log_cond.wait(timeout=timeout)
            return [e for e in self._log_tail if e["seq"] > after_seq][-200:]

    # -- Metrics 转发（后台线程 + requests）---------------------------------

    def _start_metrics_forwarder(self) -> None:
        """启动从内层 Web（8081）拉取 metrics 的后台线程。"""
        if self._metrics_loop is not None and self._metrics_loop.is_alive():
            return
        self._metrics_stop.clear()
        self._metrics_loop = threading.Thread(
            target=self._metrics_forward_loop,
            daemon=True,
            name="metrics-forwarder",
        )
        self._metrics_loop.start()

    def _stop_metrics_forwarder(self) -> None:
        """停止 metrics 转发线程。"""
        self._metrics_stop.set()
        if self._metrics_loop is not None:
            self._metrics_loop.join(timeout=3)
            self._metrics_loop = None

    def _metrics_forward_loop(self) -> None:
        """后台线程：1 Hz 从内层 Web 拉取 metrics，通过 asyncio 广播。"""
        import requests as _requests

        url = "http://127.0.0.1:8081/internal/metrics"
        while not self._metrics_stop.is_set():
            # 检查子进程是否存活
            if self._process is None or self._process.poll() is not None:
                # 子进程已退出：沉淀退出码/时间/日志尾部，供 get_status() 返回。
                # 只记一次——用 _exit_code 为 None 判定本轮尚未登记。
                if self._process is not None and self._exit_code is None:
                    self._exit_code = self._process.returncode
                    self._exit_time = time.time()
                    tail = [e["text"] for e in self._log_tail][-12:]
                    self._log_event(
                        "exit",
                        f"Process exited rc={self._exit_code}"
                        + (f" | log tail: {' || '.join(tail)}" if tail else ""),
                    )
                break
            try:
                resp = _requests.get(url, timeout=2)
                if resp.ok:
                    data = resp.json()
                    # 调度到 asyncio 事件循环进行 WebSocket 广播
                    if self._loop is not None:
                        asyncio.run_coroutine_threadsafe(
                            self.broadcast_metrics(data), self._loop
                        )
            except Exception:
                pass  # 内层 Web 可能尚未就绪或已关闭
            self._metrics_stop.wait(timeout=1.0)


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------

app = FastAPI(title="ACT Web Control Center")

# 全局进程管理器（在 main 中初始化）
_process_manager: Optional[ActProcessManager] = None


@app.on_event("startup")
async def _on_startup() -> None:
    """记录 asyncio 事件循环引用，供后台 metrics 线程 schedule 广播。"""
    if _process_manager is not None:
        _process_manager._loop = asyncio.get_running_loop()


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    """Stop the launch group before the outer Web process exits.

    ``ActProcessManager`` intentionally gives the launch process its own
    session so one stop request can clean up all ROS children.  That also means
    it survives if this outer process exits unless we explicitly stop it here.
    Run the synchronous stop sequence in a worker so shutdown does not block
    the ASGI loop while it waits for ROS processes to exit.
    """
    if _process_manager is not None:
        await asyncio.to_thread(_process_manager.stop)


# -- REST API ---------------------------------------------------------------


@app.get("/api/status")
async def api_status() -> dict:
    """获取推理进程状态。"""
    return _process_manager.get_status()


@app.post("/api/start")
async def api_start(
    mode: Optional[str] = None,
    checkpoint_dir: Optional[str] = None,
    bundle_dir: Optional[str] = None,
) -> dict:
    """启动推理进程。"""
    return _process_manager.start(
        mode=mode, checkpoint_dir=checkpoint_dir, bundle_dir=bundle_dir
    )


@app.post("/api/stop")
async def api_stop() -> dict:
    """停止推理进程。"""
    return _process_manager.stop()


@app.post("/api/mode")
async def api_mode(mode: str) -> dict:
    """切换模式（dry-run / real-run）并重启。"""
    return _process_manager.set_mode(mode)


@app.post("/api/checkpoint_dir")
async def api_checkpoint_dir(checkpoint_dir: str) -> dict:
    """切换 checkpoint 路径并重启。"""
    return _process_manager.set_checkpoint_dir(checkpoint_dir)


@app.post("/api/bundle_dir")
async def api_bundle_dir(bundle_dir: str) -> dict:
    """Legacy alias for switching the model source path."""
    return _process_manager.set_bundle_dir(bundle_dir)


# -- WebSocket: metrics 广播 ------------------------------------------------


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket) -> None:
    """浏览器通过此端点接收实时 metrics 推送。"""
    await websocket.accept()
    assert _process_manager is not None
    _process_manager._ws_clients.add(websocket)
    try:
        # 保持连接；客户端可发送心跳，服务端忽略
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _process_manager._ws_clients.discard(websocket)


# -- 子进程实时日志：REST 拉取 + WebSocket 推送 ------------------------------
# 用于在浏览器看到推理进程"启动到哪一步"——尤其是模型加载（torch/lerobot）可能
# 卡数十秒且期间无任何日志，有了它就能直接定位是卡住还是正常加载。


@app.get("/api/logs")
async def api_logs(after: int = 0, limit: int = 200) -> dict:
    """获取子进程日志。after=seq 做断线续传（只返回 seq > after 的条目）。

    返回 {logs: [...], last_seq: <最新 seq>}。
    """
    assert _process_manager is not None
    logs = _process_manager.get_logs_after(after_seq=after, limit=limit)
    return {
        "logs": logs,
        "last_seq": logs[-1]["seq"] if logs else after,
    }


async def _wait_for_new_logs(manager: ActProcessManager, after: int) -> list[dict]:
    """Await the manager's blocking log long-poll without blocking ASGI."""
    return await asyncio.to_thread(manager.wait_for_new_logs, after, timeout=15.0)


@app.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket) -> None:
    """子进程日志实时推送（长轮询式：阻塞等待新日志，再 send_text(JSON 数组)）。

    客户端发起点可带首条消息 `{"after": <seq>}` 指定续传起点；否则从 0 开始。
    """
    await websocket.accept()
    assert _process_manager is not None
    after = 0
    # 可选：客户端首发续传起点（2s 等待窗口，超时即从 0 开始）
    try:
        first = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
        try:
            payload = json.loads(first)
            after = int(payload.get("after", 0))
        except Exception:
            pass
    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        return
    try:
        while True:
            # ``wait_for_new_logs`` uses ``threading.Condition.wait``.  Calling
            # it directly in this async handler blocks uvicorn's event loop for
            # up to 15 seconds whenever the child is quiet, which also freezes
            # every REST endpoint (including / and /api/start).  Keep the
            # long-poll wait in a worker thread; WebSocket sends remain on the
            # ASGI event loop.
            new_logs = await _wait_for_new_logs(_process_manager, after)
            if not new_logs:
                # 周期性发心跳，让前端区分"无新日志"与"断线"
                await websocket.send_text(json.dumps({"heartbeat": True}))
                continue
            after = new_logs[-1]["seq"]
            await websocket.send_text(json.dumps({"logs": new_logs}))
    except WebSocketDisconnect:
        pass


# -- 代理转发：图像流 + Observation WebSocket -------------------------------


@app.get("/stream/image/{side}")
async def proxy_image(side: str):
    """代理转发内层 MJPEG 图像流。"""
    if side not in ("left", "right"):
        return {"error": "side must be 'left' or 'right'"}

    import requests as _requests

    def generate():
        try:
            resp = _requests.get(
                f"http://127.0.0.1:8081/internal/stream/image/{side}",
                stream=True,
                timeout=5,
            )
            for chunk in resp.iter_content(chunk_size=8192):
                yield chunk
        except Exception:
            pass

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.websocket("/ws/observation")
async def ws_observation_proxy(websocket: WebSocket) -> None:
    """代理转发内层 observation WebSocket。

    外层 WebSocket 接收浏览器连接，后台线程从内层 REST 接口轮询
    observation 数据并推送给客户端。无需额外 websockets 库。
    """
    await websocket.accept()
    import requests as _requests

    stop_event = threading.Event()

    def _poll_inner() -> None:
        """后台线程：~3 Hz 从内层 REST 接口拉取 observation 数据。

        三种状态分别给前端不同 reason，避免"一直转圈不知道为什么没数据"：
          - 内层 :8081 连不上：进程仍在启动（模型加载等），还没起 Web
          - 连得上但 data=={}：起来了，但 ROS 还没收到完整观测快照
            （硬件节点未运行 / 主题名不对 / 字段不全 / cv2 缺失）
          - data 有内容：正常推送
        """
        url = "http://127.0.0.1:8081/internal/observer/state"
        last_signal = None
        while not stop_event.is_set():
            signal = None
            try:
                resp = _requests.get(url, timeout=1.0)
                if resp.ok and _process_manager is not None:
                    data = resp.json()
                    if data and _process_manager._loop is not None:
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_json(data),
                            _process_manager._loop,
                        )
                        last_signal = "data"
                        signal = "data"
                    elif _process_manager._loop is not None:
                        # 内层就绪但无数据：限频下发状态，避免刷屏
                        signal = "no_data"
                        if last_signal != "no_data":
                            asyncio.run_coroutine_threadsafe(
                                websocket.send_json(
                                    {"_reason": "no_observation",
                                     "_hint": "推理进程已就绪但未收到完整观测：请确认硬件节点(相机/双臂/夹爪)正在运行"}
                                ),
                                _process_manager._loop,
                            )
            except Exception:
                # 内层 Web 尚未就绪：仅在状态翻转时提示一次，避免每秒刷屏
                signal = "inner_down"
                if last_signal != "inner_down" and _process_manager is not None and _process_manager._loop is not None:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_json(
                            {"_reason": "inner_starting",
                             "_hint": "推理进程仍在启动中（加载模型/初始化ROS），内层服务尚未就绪"}
                        ),
                        _process_manager._loop,
                    )
            last_signal = signal
            stop_event.wait(timeout=0.3)

    poller = threading.Thread(target=_poll_inner, daemon=True)
    poller.start()
    try:
        while True:
            # 保持连接活跃，接收客户端心跳
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        stop_event.set()
        poller.join(timeout=2)


# -- 代理转发：Action 数据流 REST + WebSocket --------------------------------


def _proxy_action_get(path: str) -> dict:
    """代理 GET 请求到内层 Web (8081)。"""
    import requests as _requests
    try:
        resp = _requests.get(f"http://127.0.0.1:8081{path}", timeout=2)
        return resp.json()
    except Exception:
        return {}


@app.get("/api/action/latest")
async def proxy_action_latest():
    """代理转发最新 Action 记录。"""
    return _proxy_action_get("/internal/api/action/latest")


@app.get("/api/action/history")
async def proxy_action_history(n: int = 50):
    """代理转发 Action 历史记录。"""
    return _proxy_action_get(f"/internal/api/action/history?n={n}")


@app.get("/api/action/record/{step_id}")
async def proxy_action_record(step_id: int):
    """代理转发单条 Action 记录。"""
    return _proxy_action_get(f"/internal/api/action/record/{step_id}")


@app.get("/api/action/stats")
async def proxy_action_stats():
    """代理转发 Action 统计信息。"""
    return _proxy_action_get("/internal/api/action/stats")


@app.websocket("/ws/action")
async def ws_action_proxy(websocket: WebSocket) -> None:
    """代理转发内层 Action WebSocket。"""
    await websocket.accept()
    import requests as _requests

    stop_event = threading.Event()

    def _poll_inner() -> None:
        """后台线程：10 Hz 从内层拉取最新 Action 数据。"""
        url = "http://127.0.0.1:8081/internal/api/action/latest"
        while not stop_event.is_set():
            try:
                resp = _requests.get(url, timeout=2)
                if resp.ok and _process_manager is not None:
                    data = resp.json()
                    if data and _process_manager._loop is not None:
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_json(data),
                            _process_manager._loop,
                        )
            except Exception:
                pass
            stop_event.wait(timeout=0.1)

    poller = threading.Thread(target=_poll_inner, daemon=True)
    poller.start()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        stop_event.set()
        poller.join(timeout=2)


# -- 静态文件 / Dashboard ---------------------------------------------------

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def serve_dashboard() -> FileResponse:
    """根路径返回 dashboard.html。"""
    return FileResponse(STATIC_DIR / "dashboard.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def main() -> None:
    # 确保 src/ 在 sys.path 中（直接运行脚本时不走 __init__.py）
    src_dir = str(Path(__file__).resolve().parent.parent.parent.parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    import argparse

    parser = argparse.ArgumentParser(
        prog="act_web_launcher",
        description="ACT Web Control Center — 外层进程管理器",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to deploy.yaml",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Web 服务端口（默认 8080）",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Web 服务监听地址（默认 0.0.0.0）",
    )
    parser.add_argument(
        "--auto-start",
        action="store_true",
        help="启动时自动运行推理进程",
    )
    parser.add_argument(
        "--mode",
        default="dry-run",
        choices=["dry-run", "real-run"],
        help="初始运行模式（默认 dry-run）",
    )
    args = parser.parse_args()

    # 从 deploy.yaml 读取默认 checkpoint_dir（供面板输入框预填）+ 初始 mode。
    default_checkpoint = ""
    try:
        import yaml
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        default_checkpoint = str(
            (cfg.get("model") or {}).get("checkpoint_dir")
            or (cfg.get("bundle") or {}).get("bundle_dir")
            or ""
        )
    except Exception:
        logger.warning("读取 %s 的 checkpoint_dir 失败，面板权重输入框将为空", args.config)

    global _process_manager
    _process_manager = ActProcessManager(
        config_path=args.config,
        default_checkpoint_dir=default_checkpoint,
    )

    if args.auto_start:
        result = _process_manager.start(mode=args.mode)
        if not result.get("ok"):
            logger.error("Auto-start failed: %s", result.get("error"))

    # ws="auto" 让 uvicorn 自动选择可用的 WebSocket 协议实现。基础版 uvicorn 不含
    # 任何 ws 库，若库缺失则回退到"无 WebSocket 支持"，导致所有 /ws/* 端点返回 404
    # （observation/metrics/action 实时推送全部失效）。依赖 websockets 包
    # （见 requirements.txt）；ws="auto" 会在装了 websockets 后自动启用，未装也不报错。
    uvicorn.run(
        app, host=args.host, port=args.port, log_level="info", ws="auto"
    )


if __name__ == "__main__":
    main()

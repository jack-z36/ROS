"""RuntimeBridge: Web UI 与 ACT 运行时之间的唯一桥梁。

封装对 ActDeployNode 内部运行状态的只读访问，供内部 FastAPI 服务调用。
所有方法均为线程安全只读操作（Web 线程调用，ROS 主线程运行）。

Micro-units:
  - RuntimeBridge (Web <-> ACT runtime read-only facade)
"""

from __future__ import annotations

import dataclasses
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model_deploy.act.ui.act_deploy_node import ActDeployNode


class RuntimeBridge:
    """Web UI 与 ACT 运行时之间的唯一桥梁。

    在构造时捕获对 node 内部运行时组件的引用，之后所有访问均为只读。
    RuntimeMetrics.snapshot() 本身是线程安全的（内部有 lock），
    DeployConfig 是 frozen dataclass，天然线程安全。

    线程安全策略：
      - _runtime_metrics: RuntimeMetrics.snapshot() 内部有 lock，跨线程安全。
      - _config: frozen dataclass，不可变，天然线程安全。
      - _permit_provider: 构造时捕获引用；其 state/reason_code 为简单属性读取，
        由 ROS 主线程写入，Web 线程读取，Python GIL 保证原子性。
      - _started/_shutdown: 通过 node 的 lifecycle_lock 保护读取。
    """

    def __init__(self, node: ActDeployNode) -> None:
        # 持有 node 引用，仅用于读取 _started/_shutdown 状态标记
        self._node = node
        # 捕获对 node 内部运行时组件的引用（构造时一次性绑定，之后不再变动）
        self._runtime_metrics = node._runtime_metrics
        self._config = node._config
        self._permit_provider = node._permit_provider
        # 记录桥创建时间，用于 uptime 计算
        self._created_at_s = time.monotonic()

    def get_status(self) -> dict:
        """运行状态摘要：running/stopped, mode, permit_state, uptime 等。

        返回一个 JSON-serializable dict，包含：
          - runtime_status: 当前运行状态（STARTING / RUNNING / SHUTDOWN 等）
          - mode: 'dry-run' 或 'real-run'
          - permit_state: 许可状态字符串
          - permit_reason_code: 许可原因码
          - uptime_s: 桥创建以来的秒数（近似 uptime）
          - started: 节点是否已完成初始化
          - shutdown: 节点是否已进入关闭流程
        """
        # RuntimeMetrics.snapshot() 是线程安全的（内部有 lock）
        snap = self._runtime_metrics.snapshot()

        # 许可状态（Python GIL 保证简单属性读取的原子性）
        if self._permit_provider is not None:
            permit_state = getattr(self._permit_provider, "state", "UNKNOWN")
            permit_reason_code = getattr(self._permit_provider, "reason_code", "UNKNOWN")
        else:
            permit_state = "DISABLED"
            permit_reason_code = "COMMAND_OUTPUT_DISABLED"

        # 通过 lifecycle_lock 安全读取 node 状态标记
        with self._node._lifecycle_lock:
            started = self._node._started
            shutdown = self._node._shutdown

        return {
            "runtime_status": snap.runtime_status,
            "mode": self._config.runtime.mode,
            "permit_state": permit_state,
            "permit_reason_code": permit_reason_code,
            "uptime_s": round(time.monotonic() - self._created_at_s, 3),
            "started": started,
            "shutdown": shutdown,
        }

    def get_metrics(self) -> dict:
        """RuntimeMetrics 快照，调用 runtime_metrics.snapshot() 并转为 dict。

        返回的 dict 与 RuntimeMetricsSnapshot 字段完全一致，
        所有 tuple 字段转为 list 以便 JSON 序列化。
        """
        snap = self._runtime_metrics.snapshot()
        result = dataclasses.asdict(snap)
        # 将 tuple 值转为 list 以支持 JSON 序列化
        for key, value in result.items():
            if isinstance(value, tuple):
                result[key] = list(value)
        return result

    def get_mode(self) -> str:
        """当前模式: 'dry-run' 或 'real-run'。"""
        return self._config.runtime.mode

    def get_permit_state(self) -> str:
        """许可状态字符串。

        返回 permit_provider.state（若存在），否则返回 'DISABLED'。
        """
        if self._permit_provider is not None:
            return getattr(self._permit_provider, "state", "UNKNOWN")
        return "DISABLED"

    def get_bundle_dir(self) -> str:
        """当前 bundle_dir 路径字符串。

        返回 bundle_dir 的字符串表示；若为 None 则返回空字符串。
        """
        bundle_dir = self._config.bundle.bundle_dir
        if bundle_dir is None:
            return ""
        return str(bundle_dir)

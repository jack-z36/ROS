"""ActionDebugRecorder: 线程安全的 ring buffer，记录推理数据流三阶段数据。

阶段 1: 推理输出 (ActionChunk 原始值)
阶段 2: 安全过滤结果 (SafetyResult verdict + filtered values)
阶段 3: 最终发布结果 (ActionPublishResult outcome + command values)

所有方法线程安全，失败不影响主推理流程。
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ActionDebugRecord:
    """单步推理数据流的完整记录。"""

    step_id: int = 0
    timestamp: float = 0.0
    raw_action: list[float] = field(default_factory=list)
    safety_verdict: str = ""
    filtered_action: list[float] = field(default_factory=list)
    publish_outcome: str = ""
    command_action: list[float] = field(default_factory=list)
    safety_details: Optional[dict] = None

    def to_dict(self) -> dict:
        """转换为可序列化字典。"""
        result = {
            "step_id": self.step_id,
            "timestamp": self.timestamp,
            "raw_action": list(self.raw_action),
            "safety_verdict": self.safety_verdict,
            "filtered_action": list(self.filtered_action),
            "publish_outcome": self.publish_outcome,
            "command_action": list(self.command_action),
        }
        if self.safety_details is not None:
            result["safety_details"] = self.safety_details
        return result


class ActionDebugRecorder:
    """线程安全的 ring buffer，关联三阶段数据。

    使用 ``collections.deque(maxlen=1000)`` 作为 ring buffer，
    ``threading.Lock`` 保护并发访问。``_pending`` dict 关联同一
    step 的三个阶段数据，直到阶段 3 完成后写入 buffer。
    """

    def __init__(self, maxlen: int = 1000) -> None:
        self._buffer: deque[ActionDebugRecord] = deque(maxlen=maxlen)
        self._pending: dict[int, ActionDebugRecord] = {}
        self._lock = threading.Lock()
        self._step_counter: int = 0

    # -- 阶段 1: 推理输出 --------------------------------------------------

    def record_inference_result(self, action_values: list) -> int:
        """阶段 1: 记录推理输出的原始 action 值，返回 step_id。"""
        with self._lock:
            self._step_counter += 1
            step_id = self._step_counter
            record = ActionDebugRecord(
                step_id=step_id,
                timestamp=time.time(),
                raw_action=list(action_values),
            )
            self._pending[step_id] = record
            return step_id

    # -- 阶段 2: 安全过滤结果 -----------------------------------------------

    def record_safety_result(
        self,
        step_id: int,
        verdict: str,
        filtered_values: list,
        details: dict = None,
    ) -> None:
        """阶段 2: 记录安全过滤结果。"""
        with self._lock:
            record = self._pending.get(step_id)
            if record is None:
                return
            record.safety_verdict = verdict
            record.filtered_action = list(filtered_values)
            if details is not None:
                record.safety_details = details

    # -- 阶段 3: 发布结果 ---------------------------------------------------

    def record_publish_result(
        self,
        step_id: int,
        outcome: str,
        command_values: list,
    ) -> None:
        """阶段 3: 完成记录，写入 ring buffer。"""
        with self._lock:
            record = self._pending.pop(step_id, None)
            if record is None:
                return
            record.publish_outcome = outcome
            record.command_action = list(command_values)
            self._buffer.append(record)

    # -- 查询接口 -----------------------------------------------------------

    def get_latest(self) -> Optional[dict]:
        """返回最新一条完整记录。"""
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[-1].to_dict()

    def get_history(self, n: int = 50) -> list:
        """返回最近 n 条完整记录（最新在前）。"""
        with self._lock:
            items = list(self._buffer)
            return [r.to_dict() for r in items[-n:]][::-1]

    def get_record(self, step_id: int) -> Optional[dict]:
        """按 step_id 查询记录。"""
        with self._lock:
            # 先在 buffer 中查找
            for record in self._buffer:
                if record.step_id == step_id:
                    return record.to_dict()
            # 再在 pending 中查找
            record = self._pending.get(step_id)
            if record is not None:
                return record.to_dict()
            return None

    def get_stats(self) -> dict:
        """返回统计信息。"""
        with self._lock:
            total = len(self._buffer)
            pass_count = sum(
                1 for r in self._buffer if r.safety_verdict == "PASS"
            )
            adjusted_count = sum(
                1 for r in self._buffer if r.safety_verdict == "ADJUSTED"
            )
            rejected_count = sum(
                1 for r in self._buffer if r.safety_verdict == "REJECTED"
            )
            published_count = sum(
                1 for r in self._buffer
                if r.publish_outcome in ("PUBLISHED", "OBSERVED")
            )
            return {
                "total_steps": total,
                "buffer_size": len(self._buffer),
                "buffer_maxlen": self._buffer.maxlen,
                "pending_steps": len(self._pending),
                "pass_count": pass_count,
                "adjusted_count": adjusted_count,
                "rejected_count": rejected_count,
                "published_count": published_count,
            }


__all__ = ["ActionDebugRecord", "ActionDebugRecorder"]

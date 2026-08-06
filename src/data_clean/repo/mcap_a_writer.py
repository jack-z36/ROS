from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mcap.reader import make_reader
from mcap.records import Channel, Schema
from mcap.writer import CompressionType, Writer

from repo.ros2_codec import Ros2DynamicCodec, inject_pose_fields, inject_tactile_fields, select_alignment_timestamp
from schemas.mcap_a_writer import (
    MCAP_A_MessageReplacement,
    MCAP_A_OutputContract,
    MCAP_A_WritePlan,
    MCAP_A_WriterConfig,
    MCAP_A_WriterResult,
)
from schemas.reliability import SignalSampleRef


class MCAP_A_Writer:
    """Stream-copy an MCAP while replacing exactly addressed source messages."""

    def __init__(self, config: MCAP_A_WriterConfig, plan: MCAP_A_WritePlan | None = None) -> None:
        self.config = config
        self.plan = plan

    def execute_write_plan(
        self,
        plan: MCAP_A_WritePlan | None = None,
        replacements: Iterable[MCAP_A_MessageReplacement] | None = None,
    ) -> MCAP_A_WriterResult:
        active_plan = plan or self.plan
        if active_plan is None:
            fallback = MCAP_A_WritePlan(source_mcap="missing", output_mcap=self.config.output_path, operations=[])
            return self._failed_result(fallback, "missing_write_plan")

        output_path = Path(active_plan.output_mcap)
        temp_path = output_path.with_name(f".{output_path.name}.tmp")
        try:
            self._validate_required_input_refs(active_plan)
            replacement_by_key = self._index_replacements(replacements or [])
            source_records, source_counts, hit_counts = self._stream_copy(
                Path(active_plan.source_mcap), temp_path, replacement_by_key
            )
            missing_hits = [key for key, count in hit_counts.items() if count != 1]
            if missing_hits:
                raise ValueError(f"stable_message_reference_hit_mismatch: {missing_hits}")
            contract = self._validate_output(temp_path, source_records)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.replace(output_path)
            self._write_summary(
                active_plan,
                contract,
                source_counts,
                list(replacement_by_key.values()),
                status="completed",
                failure_reason=None,
            )
            return MCAP_A_WriterResult(plan=active_plan, contract=contract, success=True)
        except Exception as exc:
            if temp_path.exists():
                temp_path.unlink()
            failed = self._failed_result(active_plan, str(exc))
            self._write_summary(active_plan, failed.contract, {}, [], status="failed", failure_reason=str(exc))
            return failed

    def _validate_required_input_refs(self, plan: MCAP_A_WritePlan) -> None:
        refs = plan.output_sequence_refs
        if not isinstance(refs, Mapping):
            raise ValueError("missing_signal_repair_result")
        for key, error in (
            ("signal_repair_result_ref", "missing_signal_repair_result"),
            ("pose_filter_result_ref", "missing_pose_filter_result"),
            ("tactile_filter_result_ref", "missing_tactile_filter_result"),
        ):
            if not refs.get(key):
                raise ValueError(error)

    def _index_replacements(
        self,
        replacements: Iterable[MCAP_A_MessageReplacement],
    ) -> dict[tuple[str, int], MCAP_A_MessageReplacement]:
        indexed: dict[tuple[str, int], MCAP_A_MessageReplacement] = {}
        for replacement in replacements:
            key = (replacement.sample_ref.topic, replacement.sample_ref.message_index)
            if key in indexed:
                raise ValueError(f"duplicate_stable_message_replacement: {key}")
            ref = replacement.sample_ref
            if None in (ref.log_time_ns, ref.publish_time_ns, ref.sequence, ref.source_channel_id):
                raise ValueError(f"incomplete_stable_message_reference: {key}")
            indexed[key] = replacement
        return indexed

    def _stream_copy(
        self,
        source_path: Path,
        output_path: Path,
        replacements: Mapping[tuple[str, int], MCAP_A_MessageReplacement],
    ) -> tuple[list[tuple[Any, ...]], dict[str, int], dict[tuple[str, int], int]]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        topic_indexes: dict[str, int] = defaultdict(int)
        topic_counts: dict[str, int] = defaultdict(int)
        hit_counts = {key: 0 for key in replacements}
        source_records: list[tuple[Any, ...]] = []
        schema_map: dict[int, int] = {}
        channel_map: dict[int, int] = {}
        codec = Ros2DynamicCodec()

        with source_path.open("rb") as source_fh, output_path.open("wb") as output_fh:
            reader = make_reader(source_fh)
            writer = Writer(output_fh, chunk_size=self.config.chunk_size, compression=self._compression_type())
            writer.start()
            for schema, channel, message in reader.iter_messages(log_time_order=False):
                topic = channel.topic
                index = topic_indexes[topic]
                topic_indexes[topic] += 1
                topic_counts[topic] += 1
                output_channel_id = self._output_channel_id(writer, schema, channel, schema_map, channel_map)
                replacement = replacements.get((topic, index))
                payload = message.data
                if replacement is not None:
                    self._validate_identity(replacement.sample_ref, channel, message, schema, codec)
                    payload = self._encode_replacement(replacement, schema, message, codec)
                    hit_counts[(topic, index)] += 1
                source_records.append(self._record_signature(schema, channel, message))
                writer.add_message(
                    channel_id=output_channel_id,
                    log_time=message.log_time,
                    publish_time=message.publish_time,
                    sequence=message.sequence,
                    data=payload,
                )
            writer.finish()
        return source_records, dict(topic_counts), hit_counts

    def _validate_identity(self, ref: SignalSampleRef, channel: Channel, message: Any, schema: Schema | None, codec: Ros2DynamicCodec) -> None:
        observed = (int(message.log_time), int(message.publish_time), int(message.sequence), int(channel.id))
        expected = (ref.log_time_ns, ref.publish_time_ns, ref.sequence, ref.source_channel_id)
        if observed != expected:
            raise ValueError(f"stable_message_identity_mismatch: topic={ref.topic} index={ref.message_index}")
        if schema is None:
            raise ValueError(f"schema missing for replacement topic {ref.topic}")
        decoded = codec.decode(schema, message)
        selected = select_alignment_timestamp(schema, message, codec=codec, decoded_message=decoded)
        if (selected.timestamp_ns, selected.time_domain) != (ref.timestamp, ref.time_domain):
            raise ValueError(f"stable_message_signal_time_mismatch: topic={ref.topic} index={ref.message_index}")

    def _encode_replacement(
        self,
        replacement: MCAP_A_MessageReplacement,
        schema: Schema | None,
        message: Any,
        codec: Ros2DynamicCodec,
    ) -> bytes:
        if schema is None:
            raise ValueError("replacement message has no schema")
        decoded = codec.decode(schema, message)
        unit = replacement.replacement_unit
        value = replacement.value
        if unit == "pose":
            position, orientation = value["position"], value["orientation"]
            injected = inject_pose_fields(
                decoded,
                schema.name,
                tuple(float(position[key]) for key in ("x", "y", "z"))
                + tuple(float(orientation[key]) for key in ("x", "y", "z", "w")),
            )
        elif unit == "tactile.frame":
            matrix = [[min(65535, max(0, int(round(cell)))) for cell in row] for row in value]
            injected = inject_tactile_fields(decoded, matrix)
        elif unit == "gripper.value":
            decoded.data = float(value)
            injected = decoded
        else:
            raise ValueError(f"unsupported_replacement_unit: {unit}")
        return codec.encode(schema, injected)

    def _validate_output(self, output_path: Path, source_records: list[tuple[Any, ...]]) -> MCAP_A_OutputContract:
        output_records: list[tuple[Any, ...]] = []
        topics: list[str] = []
        seen_topics: set[str] = set()
        start_time: int | None = None
        end_time: int | None = None
        with output_path.open("rb") as fh:
            reader = make_reader(fh)
            for schema, channel, message in reader.iter_messages(log_time_order=False):
                output_records.append(self._record_signature(schema, channel, message))
                if channel.topic not in seen_topics:
                    topics.append(channel.topic)
                    seen_topics.add(channel.topic)
                start_time = message.log_time if start_time is None else min(start_time, message.log_time)
                end_time = message.log_time if end_time is None else max(end_time, message.log_time)
        if output_records != source_records:
            raise ValueError("mcap_a_preservation_contract_mismatch")
        return MCAP_A_OutputContract(
            topic_list=topics,
            message_count=len(output_records),
            start_time=start_time,
            end_time=end_time,
            checksum=f"sha256:{self._checksum(output_path)}",
        )

    @staticmethod
    def _record_signature(schema: Schema | None, channel: Channel, message: Any) -> tuple[Any, ...]:
        return (
            channel.topic,
            schema.name if schema is not None else None,
            schema.encoding if schema is not None else None,
            channel.message_encoding,
            int(message.log_time),
            int(message.publish_time),
            int(message.sequence),
        )

    def _output_channel_id(
        self,
        writer: Writer,
        schema: Schema | None,
        channel: Channel,
        schema_map: dict[int, int],
        channel_map: dict[int, int],
    ) -> int:
        if channel.id in channel_map:
            return channel_map[channel.id]
        schema_id = 0
        if schema is not None:
            schema_id = schema_map.get(schema.id, 0)
            if schema_id == 0:
                schema_id = writer.register_schema(schema.name, schema.encoding, schema.data)
                schema_map[schema.id] = schema_id
        channel_id = writer.register_channel(
            topic=channel.topic,
            message_encoding=channel.message_encoding,
            schema_id=schema_id,
            metadata=channel.metadata,
        )
        channel_map[channel.id] = channel_id
        return channel_id

    def _write_summary(
        self,
        plan: MCAP_A_WritePlan,
        contract: MCAP_A_OutputContract,
        source_counts: Mapping[str, int],
        replacements: list[MCAP_A_MessageReplacement],
        *,
        status: str,
        failure_reason: str | None,
    ) -> None:
        replaced_by_modality: dict[str, int] = defaultdict(int)
        replaced_by_topic: dict[str, int] = defaultdict(int)
        for replacement in replacements:
            replaced_by_modality[replacement.sample_ref.modality] += 1
            replaced_by_topic[replacement.sample_ref.topic] += 1
        refs = plan.output_sequence_refs if isinstance(plan.output_sequence_refs, Mapping) else {}
        run_context = asdict(plan.run_context) if is_dataclass(plan.run_context) else plan.run_context
        summary = {
            "input_cleaned_mcap": plan.source_mcap,
            "output_mcap_a": plan.output_mcap if status == "completed" else None,
            "signal_repair_result_ref": refs.get("signal_repair_result_ref"),
            "pose_filter_result_ref": refs.get("pose_filter_result_ref"),
            "tactile_filter_result_ref": refs.get("tactile_filter_result_ref"),
            "replaced_topic_stats": dict(replaced_by_topic),
            "replaced_modality_stats": dict(replaced_by_modality),
            "copied_topic_stats": {
                topic: count - replaced_by_topic.get(topic, 0) for topic, count in source_counts.items()
            },
            "timestamp_policy": plan.timestamp_policy,
            "topic_policy": self.config.topic_policy,
            "status": status,
            "failure_reason": failure_reason,
            "created_at": datetime.now().isoformat(),
            "run_id": plan.run_id,
            "run_context": run_context,
            "config_snapshot": run_context.get("config_snapshot") if isinstance(run_context, dict) else None,
            "contract": {
                "topic_list": contract.topic_list,
                "message_count": contract.message_count,
                "start_time": contract.start_time,
                "end_time": contract.end_time,
                "checksum": contract.checksum,
            },
        }
        summary_path = Path(plan.output_mcap).parent / "mcap_a_write_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    def _compression_type(self) -> CompressionType:
        value = self.config.compression.lower()
        if value == "none":
            return CompressionType.NONE
        if value == "lz4":
            return CompressionType.LZ4
        if value == "zstd":
            return CompressionType.ZSTD
        raise ValueError(f"unsupported compression: {self.config.compression}")

    @staticmethod
    def _failed_result(plan: MCAP_A_WritePlan, error: str) -> MCAP_A_WriterResult:
        contract = MCAP_A_OutputContract([], 0, None, None, "")
        return MCAP_A_WriterResult(plan=plan, contract=contract, success=False, error_log=[error])

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

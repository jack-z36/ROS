from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path

from mcap.reader import make_reader
from mcap.records import Channel, Schema
from mcap.writer import CompressionType, Writer

from schemas.mcap_a_writer import MCAP_A_OutputContract, MCAP_A_WritePlan, MCAP_A_WriterConfig, MCAP_A_WriterResult


class MCAP_A_Writer:
    def __init__(self, config: MCAP_A_WriterConfig, plan: MCAP_A_WritePlan | None = None) -> None:
        self.config = config
        self.plan = plan

    def copy_original_topic(self, mcap_path: str | Path, topic: str) -> MCAP_A_OutputContract:
        output_path = Path(self.config.output_path)
        self._write_mcap(Path(mcap_path), output_path, selected_topics={topic}, replacements={})
        return self._build_output_contract(output_path)

    def replace_topic(
        self,
        mcap_path: str | Path,
        topic: str,
        new_content: Iterable[bytes],
    ) -> MCAP_A_OutputContract:
        output_path = Path(self.config.output_path)
        self._write_mcap(Path(mcap_path), output_path, selected_topics={topic}, replacements={topic: list(new_content)})
        return self._build_output_contract(output_path)

    def execute_write_plan(
        self,
        plan: MCAP_A_WritePlan | None = None,
        replacement_content: Mapping[str, Sequence[bytes]] | None = None,
    ) -> MCAP_A_WriterResult:
        active_plan = plan or self.plan
        if active_plan is None:
            fallback_plan = MCAP_A_WritePlan(source_mcap="missing", output_mcap=self.config.output_path, operations=[])
            return self._failed_result(fallback_plan, "missing_write_plan")

        output_path = Path(active_plan.output_mcap)
        temp_path = output_path.with_name(f"{output_path.name}.tmp")
        try:
            self._validate_required_input_refs(active_plan)
            replacements = self._replacement_payloads(active_plan, replacement_content or {})
            source_counts = self._topic_message_counts(Path(active_plan.source_mcap))
            self._validate_replacement_counts(source_counts, replacements)
            self._write_mcap(Path(active_plan.source_mcap), temp_path, selected_topics=None, replacements=replacements)
            contract = self._build_output_contract(temp_path)
            source_contract = self._build_output_contract(Path(active_plan.source_mcap))
            self._verify_preserved_contract(source_contract, contract)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.replace(output_path)
            self._write_summary(active_plan, contract, source_counts, replacements, status="completed", failure_reason=None)
            return MCAP_A_WriterResult(plan=active_plan, contract=contract, success=True)
        except Exception as exc:
            if temp_path.exists():
                temp_path.unlink()
            if output_path.exists():
                output_path.unlink()
            failed = self._failed_result(active_plan, str(exc))
            self._write_summary(active_plan, failed.contract, {}, {}, status="failed", failure_reason=str(exc))
            return failed

    def _validate_required_input_refs(self, plan: MCAP_A_WritePlan) -> None:
        refs = plan.output_sequence_refs
        if not isinstance(refs, Mapping):
            raise ValueError("missing_signal_repair_result")
        required_refs = (
            ("signal_repair_result_ref", "missing_signal_repair_result"),
            ("pose_filter_result_ref", "missing_pose_filter_result"),
            ("tactile_filter_result_ref", "missing_tactile_filter_result"),
        )
        for key, error in required_refs:
            if not refs.get(key):
                raise ValueError(error)

    def _replacement_payloads(
        self,
        plan: MCAP_A_WritePlan,
        replacement_content: Mapping[str, Sequence[bytes]],
    ) -> dict[str, list[bytes]]:
        replacements: dict[str, list[bytes]] = {}
        for operation in plan.operations:
            if operation["operation"] != "replace":
                continue
            topic = operation.get("topic")
            if not topic:
                raise ValueError("replace operations must include topic")
            if topic not in replacement_content:
                raise ValueError(f"missing replacement content for {topic}")
            replacements[topic] = list(replacement_content[topic])
        return replacements

    def _validate_replacement_counts(
        self,
        topic_counts: Mapping[str, int],
        replacements: Mapping[str, Sequence[bytes]],
    ) -> None:
        for topic, payloads in replacements.items():
            expected_count = topic_counts.get(topic)
            if expected_count is None:
                raise ValueError(f"topic_or_sample_count_mismatch: {topic} not found in source MCAP")
            if expected_count != len(payloads):
                raise ValueError(
                    f"topic_or_sample_count_mismatch: {topic} expected {expected_count} replacement messages, "
                    f"got {len(payloads)}"
                )

    def _write_mcap(
        self,
        source_path: Path,
        output_path: Path,
        *,
        selected_topics: set[str] | None,
        replacements: Mapping[str, Sequence[bytes]],
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        replacement_indexes = {topic: 0 for topic in replacements}
        schema_map: dict[int, int] = {}
        channel_map: dict[int, int] = {}

        with source_path.open("rb") as source_fh, output_path.open("wb") as output_fh:
            reader = make_reader(source_fh)
            writer = Writer(output_fh, chunk_size=self.config.chunk_size, compression=self._compression_type())
            writer.start()
            for schema, channel, message in reader.iter_messages(log_time_order=False):
                if selected_topics is not None and channel.topic not in selected_topics:
                    continue

                channel_id = self._output_channel_id(writer, schema, channel, schema_map, channel_map)
                payload = message.data
                if channel.topic in replacements:
                    payload = replacements[channel.topic][replacement_indexes[channel.topic]]
                    replacement_indexes[channel.topic] += 1

                writer.add_message(
                    channel_id=channel_id,
                    log_time=message.log_time,
                    publish_time=message.publish_time,
                    sequence=message.sequence,
                    data=payload,
                )
            writer.finish()

        for topic, payloads in replacements.items():
            if replacement_indexes[topic] != len(payloads):
                raise ValueError(
                    f"topic_or_sample_count_mismatch: {topic} expected {replacement_indexes[topic]} source messages, "
                    f"got {len(payloads)} replacement messages"
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

    def _build_output_contract(self, path: Path) -> MCAP_A_OutputContract:
        topics: list[str] = []
        seen_topics: set[str] = set()
        message_count = 0
        start_time: int | None = None
        end_time: int | None = None
        with path.open("rb") as fh:
            reader = make_reader(fh)
            for _, channel, message in reader.iter_messages(log_time_order=True):
                if channel.topic not in seen_topics:
                    seen_topics.add(channel.topic)
                    topics.append(channel.topic)
                message_count += 1
                start_time = message.log_time if start_time is None else min(start_time, message.log_time)
                end_time = message.log_time if end_time is None else max(end_time, message.log_time)
        return MCAP_A_OutputContract(
            topic_list=topics,
            message_count=message_count,
            start_time=start_time,
            end_time=end_time,
            checksum=f"sha256:{self._checksum(path)}",
        )

    def _topic_message_counts(self, path: Path) -> dict[str, int]:
        counts: dict[str, int] = {}
        with path.open("rb") as fh:
            reader = make_reader(fh)
            for _, channel, _ in reader.iter_messages(log_time_order=False):
                counts[channel.topic] = counts.get(channel.topic, 0) + 1
        return counts

    def _verify_preserved_contract(
        self,
        source_contract: MCAP_A_OutputContract,
        output_contract: MCAP_A_OutputContract,
    ) -> None:
        if source_contract.topic_list != output_contract.topic_list:
            raise ValueError("topic_or_sample_count_mismatch: output topic list does not match source")
        if source_contract.message_count != output_contract.message_count:
            raise ValueError("topic_or_sample_count_mismatch: output message count does not match source")
        if source_contract.start_time != output_contract.start_time or source_contract.end_time != output_contract.end_time:
            raise ValueError("topic_or_sample_count_mismatch: output time range does not match source")


    def _write_summary(
        self,
        plan: MCAP_A_WritePlan,
        contract: MCAP_A_OutputContract,
        source_counts: Mapping[str, int],
        replacements: Mapping[str, Sequence[bytes]],
        *,
        status: str,
        failure_reason: str | None,
    ) -> None:
        output_path = Path(plan.output_mcap)
        replaced_topic_stats = {topic: len(payloads) for topic, payloads in replacements.items()}
        copied_topic_stats = {
            topic: count for topic, count in source_counts.items() if topic not in replaced_topic_stats
        }
        refs = plan.output_sequence_refs if isinstance(plan.output_sequence_refs, Mapping) else {}
        summary = {
            "input_cleaned_mcap": plan.source_mcap,
            "output_mcap_a": plan.output_mcap if status == "completed" else None,
            "write_config_ref": self.config.output_path,
            "signal_repair_result_ref": refs.get("signal_repair_result_ref"),
            "pose_filter_result_ref": refs.get("pose_filter_result_ref"),
            "tactile_filter_result_ref": refs.get("tactile_filter_result_ref"),
            "replaced_topic_stats": replaced_topic_stats,
            "copied_topic_stats": copied_topic_stats,
            "timestamp_policy": plan.timestamp_policy,
            "topic_policy": self.config.topic_policy,
            "status": status,
            "failure_reason": failure_reason,
            "created_at": datetime.now().isoformat(),
            "run_id": None,
            "contract": {
                "topic_list": contract.topic_list,
                "message_count": contract.message_count,
                "start_time": contract.start_time,
                "end_time": contract.end_time,
                "checksum": contract.checksum,
            },
        }
        summary_path = output_path.parent / "mcap_a_write_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    def _compression_type(self) -> CompressionType:
        compression = self.config.compression.lower()
        if compression == "none":
            return CompressionType.NONE
        if compression == "lz4":
            return CompressionType.LZ4
        if compression == "zstd":
            return CompressionType.ZSTD
        raise ValueError(f"unsupported compression: {self.config.compression}")

    def _failed_result(self, plan: MCAP_A_WritePlan, error: str) -> MCAP_A_WriterResult:
        contract = MCAP_A_OutputContract(topic_list=[], message_count=0, start_time=None, end_time=None, checksum="")
        return MCAP_A_WriterResult(plan=plan, contract=contract, success=False, error_log=[error])

    def _checksum(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

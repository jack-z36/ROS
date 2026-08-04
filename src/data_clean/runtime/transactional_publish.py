"""Crash-recoverable same-filesystem directory publication."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
from typing import Any

from repo.job_store import JobStore


class PublishTransactionError(RuntimeError):
    """Raised when atomic publication cannot preserve old-or-new completeness."""


class TransactionalPublisher:
    def __init__(self, store: JobStore):
        self.store = store

    def publish_directory(
        self,
        *,
        job_id: str,
        staging_path: str | Path,
        target_path: str | Path,
    ) -> dict[str, Any]:
        staging = Path(staging_path).expanduser().resolve()
        target = Path(target_path).expanduser().resolve()
        if not staging.is_dir():
            raise PublishTransactionError(f"staging directory is missing: {staging}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if staging.stat().st_dev != target.parent.stat().st_dev:
            raise PublishTransactionError(
                f"staging and target must share a filesystem: {staging} -> {target}"
            )
        backup = target.parent / f".data-clean-backup.{job_id}.{target.name}"
        if backup.exists():
            raise PublishTransactionError(f"publish backup already exists: {backup}")
        transaction_id = self.store.create_publish_transaction(
            job_id=job_id,
            target_path=target,
            staging_path=staging,
            backup_path=backup,
            target_existed=target.exists(),
        )
        try:
            if target.exists():
                os.replace(target, backup)
            self.store.update_publish_transaction(transaction_id, "old_backed_up")
            os.replace(staging, target)
            self.store.update_publish_transaction(transaction_id, "new_installed")
            self.store.update_publish_transaction(transaction_id, "committed")
            self._discard_backup(backup)
        except Exception as exc:
            self._recover_one(self.store.publish_transaction(transaction_id))
            raise PublishTransactionError(
                f"publish transaction failed: {type(exc).__name__}: {exc}"
            ) from exc
        return self.store.publish_transaction(transaction_id)

    def recover_incomplete(self) -> list[dict[str, Any]]:
        results = []
        for transaction in self.store.incomplete_publish_transactions():
            results.append(self._recover_one(transaction))
        for transaction in self.store.committed_publish_transactions():
            self._finalize_committed(transaction)
        return results

    def _finalize_committed(self, transaction: dict[str, Any]) -> None:
        target = Path(transaction["target_path"])
        backup = Path(transaction["backup_path"])
        if target.is_dir():
            self._discard_backup(backup)
            return
        if backup.is_dir():
            os.replace(backup, target)
            self.store.update_publish_transaction(
                str(transaction["transaction_id"]),
                "rolled_back",
                error="committed target was missing; restored the complete backup",
            )
            return
        raise PublishTransactionError(
            f"committed publish target is missing and has no backup: {target}"
        )

    def _recover_one(self, transaction: dict[str, Any]) -> dict[str, Any]:
        transaction_id = str(transaction["transaction_id"])
        target = Path(transaction["target_path"])
        staging = Path(transaction["staging_path"])
        backup = Path(transaction["backup_path"])
        status = str(transaction["status"])
        target_existed = bool(transaction["target_existed"])

        try:
            # Infer an fs operation that completed just before its SQLite state update.
            if status == "prepared" and backup.exists() and not target.exists():
                status = "old_backed_up"
                self.store.update_publish_transaction(transaction_id, status)
            if status in {"prepared", "old_backed_up"} and target.exists() and backup.exists() and not staging.exists():
                status = "new_installed"
                self.store.update_publish_transaction(transaction_id, status)

            if status == "prepared":
                if staging.is_dir():
                    if target.exists():
                        os.replace(target, backup)
                    self.store.update_publish_transaction(transaction_id, "old_backed_up")
                    status = "old_backed_up"
                elif target.exists():
                    self.store.update_publish_transaction(transaction_id, "rolled_back")
                    return self.store.publish_transaction(transaction_id)
                else:
                    raise PublishTransactionError("prepared transaction lost staging and target")

            if status == "old_backed_up":
                if staging.is_dir():
                    os.replace(staging, target)
                    self.store.update_publish_transaction(transaction_id, "new_installed")
                    status = "new_installed"
                elif not target.exists() and target_existed and backup.exists():
                    os.replace(backup, target)
                    self.store.update_publish_transaction(transaction_id, "rolled_back")
                    return self.store.publish_transaction(transaction_id)
                elif target.exists():
                    status = "new_installed"
                    self.store.update_publish_transaction(transaction_id, status)
                else:
                    raise PublishTransactionError("old_backed_up transaction has no recoverable directory")

            if status == "new_installed":
                if target.is_dir():
                    self.store.update_publish_transaction(transaction_id, "committed")
                    self._discard_backup(backup)
                elif target_existed and backup.is_dir():
                    os.replace(backup, target)
                    self.store.update_publish_transaction(transaction_id, "rolled_back")
                else:
                    raise PublishTransactionError("new_installed target is missing")
        except Exception as exc:
            self.store.update_publish_transaction(
                transaction_id,
                "failed",
                error=f"{type(exc).__name__}: {exc}",
            )
            raise
        return self.store.publish_transaction(transaction_id)

    @staticmethod
    def _discard_backup(path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

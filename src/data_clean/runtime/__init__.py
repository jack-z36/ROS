"""Pipeline orchestration — batch processing and CLI entry points."""

from .run_context_attach import (
    RunContextAttachError,
    attach_run_directory,
    build_context_with_run_dir,
)
from .run_directory_creator import RunDirectoryCreationError, create_run_directory

__all__ = [
    "RunContextAttachError",
    "RunDirectoryCreationError",
    "attach_run_directory",
    "build_context_with_run_dir",
    "create_run_directory",
]

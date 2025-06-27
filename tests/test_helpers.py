"""
Test helpers for JuliaPkgTemplatesCLI
"""

import shutil
import tempfile
from pathlib import Path
from typing import Generator
import pytest


@pytest.fixture
def isolated_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory outside any Git repository for integration tests.

    This allows testing Git-related functionality without conflicts with the
    development repository.
    """
    # Create temporary directory in system temp location
    temp_dir = Path(tempfile.mkdtemp(prefix="jtc_test_"))

    # Ensure we're not in a Git repository by checking parent directories
    current = temp_dir
    while current != current.parent:
        git_dir = current / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
        current = current.parent

    try:
        yield temp_dir
    finally:
        # Clean up
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

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


@pytest.fixture
def mock_git_not_in_repo():
    """Mock Git detection to return False (not in Git repo)"""
    from unittest.mock import patch
    with patch('juliapkgtemplates.generator.JuliaPackageGenerator._is_in_git_repository', return_value=False):
        yield


@pytest.fixture
def mock_git_in_repo():
    """Mock Git detection to return True (in Git repo)"""
    from unittest.mock import patch
    with patch('juliapkgtemplates.generator.JuliaPackageGenerator._is_in_git_repository', return_value=True):
        yield


def create_test_git_repo(path: Path) -> Path:
    """
    Create a test Git repository at the given path.
    
    Args:
        path: Directory where to create the Git repository
        
    Returns:
        Path to the created Git repository
    """
    import subprocess
    
    path.mkdir(parents=True, exist_ok=True)
    
    # Initialize Git repository
    subprocess.run(['git', 'init'], cwd=path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=path, check=True, capture_output=True)
    
    # Create initial commit
    readme = path / "README.md"
    readme.write_text("# Test Repository")
    subprocess.run(['git', 'add', 'README.md'], cwd=path, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=path, check=True, capture_output=True)
    
    return path


@pytest.fixture
def test_git_repo(isolated_dir: Path) -> Path:
    """Create a test Git repository in an isolated directory"""
    return create_test_git_repo(isolated_dir / "test_repo")
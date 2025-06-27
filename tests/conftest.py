"""
Pytest configuration and fixtures for JuliaPkgTemplatesCLI tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for Julia calls"""
    with patch('subprocess.run') as mock_run:
        # Default successful run
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Package created successfully",
            stderr=""
        )
        yield mock_run


@pytest.fixture
def cli_runner():
    """Click CLI runner for testing commands"""
    return CliRunner()


@pytest.fixture
def sample_config():
    """Sample configuration data"""
    return {
        "default": {
            "author": "Test Author",
            "license": "MIT",
            "template": "standard"
        }
    }


@pytest.fixture
def mock_julia_dependencies():
    """Mock successful dependency checks"""
    return {
        "julia": True,
        "pkgtemplates": True,
        "mise": True
    }


@pytest.fixture
def isolated_dir():
    """
    Create a temporary directory outside any Git repository for integration tests.
    
    This allows testing Git-related functionality without conflicts with the
    development repository.
    """
    import subprocess
    from typing import Generator
    
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
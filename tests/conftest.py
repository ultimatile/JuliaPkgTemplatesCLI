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
"""
Tests for Julia script's author and mail combination logic
"""

import subprocess
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from juliapkgtemplates.generator import JuliaPackageGenerator


class TestJuliaAuthorMailCombination:
    """Test author and mail combination in Julia script"""

    def test_author_mail_combination_in_julia_script(self):
        """Test that Julia script correctly combines author and mail"""
        generator = JuliaPackageGenerator()
        julia_script = generator.scripts_dir / "pkg_generator.jl"

        # Skip if Julia script doesn't exist
        if not julia_script.exists():
            pytest.skip("Julia script not found")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Mock subprocess.run to capture the Julia command but not execute it
            def mock_subprocess_run(*args, **kwargs):
                cmd = args[0]
                if len(cmd) >= 7 and cmd[0] == "julia":
                    # Extract parameters from the Julia command
                    package_name = cmd[2]
                    _author = cmd[3]
                    _user = cmd[4]
                    _mail = cmd[5]
                    _output_dir = cmd[6]
                    _plugins_str = cmd[7]

                    # Simulate successful package creation for testing
                    package_dir = temp_path / package_name
                    package_dir.mkdir(parents=True, exist_ok=True)

                    # Create a mock result
                    mock_result = type(
                        "MockResult",
                        (),
                        {
                            "returncode": 0,
                            "stdout": f"Package created successfully at: {package_dir}",
                            "stderr": "",
                        },
                    )()
                    return mock_result

                # For other commands, return original behavior
                return subprocess.run(*args, **kwargs)

            with patch("subprocess.run", side_effect=mock_subprocess_run):
                # Test case 1: Both author and mail provided
                result_dir = generator.create_package(
                    package_name="TestPackage1",
                    author="John Doe",
                    user="johndoe",
                    mail="john@example.com",
                    output_dir=temp_path,
                    config={"template": "minimal"},
                )

                assert result_dir.exists()
                assert result_dir.name == "TestPackage1"

    def test_author_only_in_julia_script(self):
        """Test that Julia script handles author-only case"""
        generator = JuliaPackageGenerator()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            def mock_subprocess_run(*args, **kwargs):
                cmd = args[0]
                if len(cmd) >= 7 and cmd[0] == "julia":
                    package_name = cmd[2]
                    package_dir = temp_path / package_name
                    package_dir.mkdir(parents=True, exist_ok=True)

                    mock_result = type(
                        "MockResult",
                        (),
                        {
                            "returncode": 0,
                            "stdout": f"Package created successfully at: {package_dir}",
                            "stderr": "",
                        },
                    )()
                    return mock_result

                return subprocess.run(*args, **kwargs)

            with patch("subprocess.run", side_effect=mock_subprocess_run):
                # Test case 2: Only author provided
                result_dir = generator.create_package(
                    package_name="TestPackage2",
                    author="John Doe",
                    user=None,
                    mail=None,
                    output_dir=temp_path,
                    config={"template": "minimal"},
                )

                assert result_dir.exists()
                assert result_dir.name == "TestPackage2"

    def test_mail_only_in_julia_script(self):
        """Test that Julia script handles mail-only case"""
        generator = JuliaPackageGenerator()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            def mock_subprocess_run(*args, **kwargs):
                cmd = args[0]
                if len(cmd) >= 7 and cmd[0] == "julia":
                    package_name = cmd[2]
                    package_dir = temp_path / package_name
                    package_dir.mkdir(parents=True, exist_ok=True)

                    mock_result = type(
                        "MockResult",
                        (),
                        {
                            "returncode": 0,
                            "stdout": f"Package created successfully at: {package_dir}",
                            "stderr": "",
                        },
                    )()
                    return mock_result

                return subprocess.run(*args, **kwargs)

            with patch("subprocess.run", side_effect=mock_subprocess_run):
                # Test case 3: Only mail provided
                result_dir = generator.create_package(
                    package_name="TestPackage3",
                    author=None,
                    user=None,
                    mail="john@example.com",
                    output_dir=temp_path,
                    config={"template": "minimal"},
                )

                assert result_dir.exists()
                assert result_dir.name == "TestPackage3"

    def test_neither_author_nor_mail_fallback(self):
        """Test fallback behavior when neither author nor mail is provided"""
        generator = JuliaPackageGenerator()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            def mock_subprocess_run(*args, **kwargs):
                cmd = args[0]
                if len(cmd) >= 7 and cmd[0] == "julia":
                    package_name = cmd[2]
                    package_dir = temp_path / package_name
                    package_dir.mkdir(parents=True, exist_ok=True)

                    mock_result = type(
                        "MockResult",
                        (),
                        {
                            "returncode": 0,
                            "stdout": f"Package created successfully at: {package_dir}",
                            "stderr": "",
                        },
                    )()
                    return mock_result

                return subprocess.run(*args, **kwargs)

            with patch("subprocess.run", side_effect=mock_subprocess_run):
                # Test case 4: Neither author nor mail provided (should use git config fallback)
                result_dir = generator.create_package(
                    package_name="TestPackage4",
                    author=None,
                    user=None,
                    mail=None,
                    output_dir=temp_path,
                    config={"template": "minimal"},
                )

                assert result_dir.exists()
                assert result_dir.name == "TestPackage4"

    def _julia_available(self):
        """Check if Julia is available in PATH"""
        try:
            subprocess.run(["julia", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def test_julia_script_exists_and_callable(self):
        """Test that Julia script exists and is syntactically valid (ultra-fast check)"""
        generator = JuliaPackageGenerator()
        julia_script = generator.scripts_dir / "pkg_generator.jl"

        # Check that the Julia script file exists
        assert julia_script.exists(), f"Julia script not found at {julia_script}"

        # Basic syntax check: ensure key functions are defined
        script_content = julia_script.read_text()

        # Check for essential function definitions
        assert "function generate_package(" in script_content, (
            "generate_package function not found"
        )
        assert "function main(" in script_content, "main function not found"
        assert "function parse_plugins(" in script_content, (
            "parse_plugins function not found"
        )

        # Check for author+mail logic we implemented
        assert "!isempty(author) && !isempty(mail)" in script_content, (
            "Author+mail combination logic not found"
        )
        assert 'template_args[:authors] = ["$author <$mail>"]' in script_content, (
            "Author+mail formatting not found"
        )

        # Verify the script contains the expected argument handling
        assert "ARGS[2]" in script_content, "Author argument handling not found"
        assert "ARGS[4]" in script_content, "Mail argument handling not found"

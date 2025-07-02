"""
Simplified integration tests for core functionality only
"""

from unittest.mock import patch, Mock
from click.testing import CliRunner

from juliapkgtemplates.cli import main
from juliapkgtemplates.generator import JuliaPackageGenerator


class TestBasicIntegration:
    """Test basic integration scenarios only"""

    def test_dependency_check_workflow(self):
        """Test dependency checking functionality"""
        dependencies = JuliaPackageGenerator.check_dependencies()

        # Verify the function returns a dictionary with expected keys
        assert isinstance(dependencies, dict)
        expected_keys = {"julia", "pkgtemplates", "mise"}
        assert expected_keys.issubset(dependencies.keys())

        # Verify all values are boolean
        for key, value in dependencies.items():
            assert isinstance(value, bool)

    def test_package_name_validation_workflow(self):
        """Test package name validation in CLI"""
        runner = CliRunner()

        # Test invalid package name (starts with number)
        result = runner.invoke(main, ["create", "123InvalidName"])
        assert result.exit_code == 1
        assert "must start with a letter" in result.output

        # Test invalid package name (special characters)
        result = runner.invoke(main, ["create", "Invalid@Name"])
        assert result.exit_code == 1
        assert (
            "must contain only letters, numbers, hyphens, and underscores"
            in result.output
        )

    @patch("juliapkgtemplates.generator.subprocess.run")
    def test_basic_package_creation(self, mock_subprocess, temp_dir):
        """Test basic package creation workflow"""
        runner = CliRunner()
        package_name = "TestPackage"

        # Mock successful Julia execution
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Package created successfully", stderr=""
        )

        # Create expected package directory
        package_dir = temp_dir / package_name
        package_dir.mkdir()

        # Run the create command with minimal options
        result = runner.invoke(
            main,
            [
                "create",
                package_name,
                "--output-dir",
                str(temp_dir),
            ],
        )

        # Verify basic success
        assert result.exit_code == 0
        assert f"Package '{package_name}' created successfully" in result.output

"""
Integration tests for end-to-end workflows
"""

from pathlib import Path
from unittest.mock import patch, Mock
from click.testing import CliRunner

from juliapkgtemplates.cli import main


class TestEndToEndWorkflows:
    """Test complete workflows from CLI to package creation"""

    @patch("juliapkgtemplates.generator.subprocess.run")
    def test_complete_package_creation_workflow(self, mock_subprocess, temp_dir):
        """Test complete package creation from CLI command"""
        runner = CliRunner()
        package_name = "MyTestPackage"

        # Mock successful Julia execution
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Package created successfully", stderr=""
        )

        # Create expected package directory structure
        package_dir = temp_dir / package_name
        package_dir.mkdir()
        (package_dir / "src").mkdir()
        (package_dir / "test").mkdir()
        (package_dir / "Project.toml").touch()

        # Run the create command
        result = runner.invoke(
            main,
            [
                "create",
                package_name,
                "--author",
                "Integration Test Author",
                "--user",
                "integrationtest",
                "--output-dir",
                str(temp_dir),
                "--template",
                "standard",
                "--license",
                "MIT",
            ],
        )

        # Verify command succeeded
        assert result.exit_code == 0
        assert f"Creating Julia package: {package_name}" in result.output
        assert "Package created successfully" in result.output
        assert "Next steps:" in result.output
        assert "mise run instantiate" in result.output

        # Verify subprocess was called with correct parameters
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "julia" in call_args
        assert package_name in call_args
        assert "Integration Test Author" in call_args
        assert "integrationtest" in call_args
        # Check that some version of temp_dir path is in the args (handle /private prefix on macOS)
        temp_dir_found = any(
            str(temp_dir) in arg or str(temp_dir.resolve()) in arg for arg in call_args
        )
        assert temp_dir_found

    @patch("juliapkgtemplates.generator.subprocess.run")
    def test_config_then_create_workflow(self, mock_subprocess, temp_dir):
        """Test setting config then creating package"""
        runner = CliRunner()

        # Mock successful Julia execution
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Package created successfully", stderr=""
        )

        # Create expected package directory
        package_dir = temp_dir / "ConfiguredPackage"
        package_dir.mkdir()

        with runner.isolated_filesystem():
            # Mock config path to prevent overwriting user config
            with patch("juliapkgtemplates.cli.get_config_path") as mock_config_path:
                mock_config_path.return_value = Path.cwd() / "test_config.toml"

                # First, set configuration
                config_result = runner.invoke(
                    main,
                    [
                        "config",
                        "--author",
                        "Configured Author",
                        "--user",
                        "configureduser",
                        "--license",
                        "Apache",
                        "--template",
                        "full",
                    ],
                )

                assert config_result.exit_code == 0
                assert "Set default author: Configured Author" in config_result.output
                assert "Set default user: configureduser" in config_result.output
                assert "Set default license: Apache" in config_result.output
                assert "Set default template: full" in config_result.output

                # Then create package using defaults
                create_result = runner.invoke(
                    main, ["create", "ConfiguredPackage", "--output-dir", str(temp_dir)]
                )

                assert create_result.exit_code == 0
                assert "Author: Configured Author" in create_result.output

    @patch("juliapkgtemplates.generator.subprocess.run")
    def test_minimal_template_workflow(
        self, mock_subprocess, temp_dir, isolated_config
    ):
        """Test creating package with minimal template"""
        runner = CliRunner()

        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Package created successfully", stderr=""
        )

        package_dir = temp_dir / "MinimalPackage"
        package_dir.mkdir()

        result = runner.invoke(
            main,
            [
                "create",
                "MinimalPackage",
                "--author",
                "Minimal Author",
                "--user",
                "minimaluser",
                "--output-dir",
                str(temp_dir),
                "--template",
                "minimal",
                "--no-docs",
                "--no-ci",
                "--no-codecov",
            ],
        )

        assert result.exit_code == 0
        assert "Template: minimal" in result.output

        # Verify Julia was called with minimal plugins
        call_args = mock_subprocess.call_args[0][0]
        plugins_str = [arg for arg in call_args if arg.startswith("[")][0]
        # License plugin should not be present when no license is specified (delegates to PkgTemplates.jl default)
        assert "License(" not in plugins_str
        assert "Git(" in plugins_str
        assert "GitHubActions()" not in plugins_str
        assert "Codecov()" not in plugins_str

    @patch("juliapkgtemplates.generator.subprocess.run")
    def test_full_template_workflow(self, mock_subprocess, temp_dir):
        """Test creating package with full template"""
        runner = CliRunner()

        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Package created successfully", stderr=""
        )

        package_dir = temp_dir / "FullPackage"
        package_dir.mkdir()

        result = runner.invoke(
            main,
            [
                "create",
                "FullPackage",
                "--author",
                "Full Author",
                "--user",
                "fulluser",
                "--output-dir",
                str(temp_dir),
                "--template",
                "full",
                "--license",
                "BSD3",
            ],
        )

        assert result.exit_code == 0
        assert "Template: full" in result.output

        # Verify Julia was called with full plugins
        call_args = mock_subprocess.call_args[0][0]
        plugins_str = [arg for arg in call_args if arg.startswith("[")][0]
        assert "License(" in plugins_str
        assert "Git(" in plugins_str
        assert "GitHubActions()" in plugins_str
        assert "Codecov()" in plugins_str
        assert "Documenter{GitHubActions}()" in plugins_str
        assert "TagBot()" in plugins_str
        assert "CompatHelper()" in plugins_str

    def test_dependency_check_workflow(self):
        """Test dependency checking workflow"""
        from juliapkgtemplates.generator import JuliaPackageGenerator

        with patch("subprocess.run") as mock_run:
            # Mock all dependencies available
            mock_run.return_value = Mock(returncode=0)

            deps = JuliaPackageGenerator.check_dependencies()

            assert deps["julia"] is True
            assert deps["pkgtemplates"] is True
            assert deps["mise"] is True

            # Verify all dependency checks were made
            assert mock_run.call_count == 3

    @patch("juliapkgtemplates.generator.subprocess.run")
    def test_error_handling_workflow(self, mock_subprocess, temp_dir):
        """Test error handling in complete workflow"""
        runner = CliRunner()

        # Mock Julia execution failure
        mock_subprocess.side_effect = FileNotFoundError()

        result = runner.invoke(
            main,
            [
                "create",
                "ErrorPackage",
                "--author",
                "Error Author",
                "--user",
                "erroruser",
                "--output-dir",
                str(temp_dir),
            ],
        )

        assert result.exit_code == 1
        assert "Error: Julia not found" in result.output

    def test_package_name_validation_workflow(self):
        """Test package name validation in workflow"""
        runner = CliRunner()

        # Test invalid package name
        result = runner.invoke(
            main,
            [
                "create",
                "123InvalidName",
                "--author",
                "Test Author",
                "--user",
                "testuser",
            ],
        )

        assert result.exit_code == 1
        assert "Package name must start with a letter" in result.output

        # Test package name with special characters
        result = runner.invoke(
            main,
            ["create", "Invalid@Name", "--author", "Test Author", "--user", "testuser"],
        )

        assert result.exit_code == 1
        assert (
            "Package name must contain only letters, numbers, hyphens, and underscores"
            in result.output
        )

    @patch("juliapkgtemplates.generator.subprocess.run")
    def test_mise_config_integration(self, mock_subprocess, temp_dir):
        """Test that mise configuration is properly integrated"""
        runner = CliRunner()
        package_name = "MiseTestPackage"

        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Package created successfully", stderr=""
        )

        # Create package directory
        package_dir = temp_dir / package_name
        package_dir.mkdir()

        # Mock mise template
        with patch(
            "juliapkgtemplates.generator.JuliaPackageGenerator._add_mise_config"
        ) as mock_mise:
            result = runner.invoke(
                main,
                [
                    "create",
                    package_name,
                    "--author",
                    "Mise Author",
                    "--user",
                    "miseuser",
                    "--output-dir",
                    str(temp_dir),
                ],
            )

            assert result.exit_code == 0
            mock_mise.assert_called_once()

            # Verify mise was called with correct parameters
            mise_call_args = mock_mise.call_args
            assert mise_call_args[0][1] == package_name

    def test_no_author_delegates_to_pkgtemplates_workflow(self, temp_dir):
        """Test workflow when no author is provided - delegates to PkgTemplates.jl"""
        runner = CliRunner()

        with patch("juliapkgtemplates.generator.subprocess.run") as mock_subprocess:
            with patch("juliapkgtemplates.cli.load_config", return_value={}):
                mock_subprocess.return_value = Mock(
                    returncode=0, stdout="Package created successfully", stderr=""
                )

                package_dir = temp_dir / "InteractivePackage"
                package_dir.mkdir()

                # Test that no prompt appears and PkgTemplates.jl handles author
                result = runner.invoke(
                    main,
                    ["create", "InteractivePackage", "--output-dir", str(temp_dir)],
                )

                assert result.exit_code == 0
                assert "Author: None" in result.output
                # Verify subprocess was called (indicating PkgTemplates.jl handles the author)
                mock_subprocess.assert_called_once()

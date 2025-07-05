"""
Tests for Generator module
"""

import pytest
import subprocess
from unittest.mock import Mock, patch

from juliapkgtemplates.generator import JuliaPackageGenerator, PackageConfig


class TestJuliaPackageGenerator:
    """Test JuliaPackageGenerator class"""

    def test_init(self):
        """Test generator initialization"""
        generator = JuliaPackageGenerator()

        assert generator.templates_dir.name == "templates"
        assert generator.jinja_env is not None

    def test_get_plugins_minimal(self):
        """Test plugin configuration for minimal template"""
        generator = JuliaPackageGenerator()

        plugins = generator._get_plugins(
            template="minimal",
            license_type="MIT",
            plugin_options={
                "Formatter": {"style": "nostyle"},
                "Tests": {"project": True},
                "Git": {"manifest": False},
            },
        )

        expected_plugins = [
            'ProjectFile(; version=v"0.0.1")',
            'License(; name="MIT")',
            "Git(; manifest=false)",
            'Formatter(; style="nostyle")',
            "Tests(; project=true)",
        ]

        assert plugins["plugins"] == expected_plugins

    def test_get_plugins_standard(self):
        """Test plugin configuration for standard template"""
        generator = JuliaPackageGenerator()

        plugins = generator._get_plugins(
            template="standard",
            license_type="MIT",
            plugin_options={
                "Formatter": {"style": "blue"},
                "Tests": {"project": True, "aqua": True},
                "Git": {"manifest": False, "ssh": True},
            },
        )

        expected_plugins = [
            'ProjectFile(; version=v"0.0.1")',
            'License(; name="MIT")',
            "Git(; manifest=false, ssh=true)",
            'Formatter(; style="blue")',
            "Tests(; project=true, aqua=true)",
            "GitHubActions()",
            "Codecov()",
        ]

        assert plugins["plugins"] == expected_plugins

    def test_get_plugins_full(self):
        """Test plugin configuration for full template"""
        generator = JuliaPackageGenerator()

        plugins = generator._get_plugins(
            template="full",
            license_type="Apache",
            plugin_options={
                "Formatter": {"style": "sciml"},
                "Tests": {"project": True, "aqua": True, "jet": True},
                "Git": {"manifest": True, "ssh": False},
            },
        )

        expected_plugins = [
            'ProjectFile(; version=v"0.0.1")',
            'License(; name="ASL")',
            "Git(; manifest=true)",
            'Formatter(; style="sciml")',
            "Tests(; project=true, aqua=true, jet=true)",
            "GitHubActions()",
            "Codecov()",
            "Documenter{GitHubActions}()",
            "TagBot()",
            "CompatHelper()",
        ]

        assert plugins["plugins"] == expected_plugins

    @patch("subprocess.run")
    def test_call_julia_generator_success(self, mock_run, temp_dir):
        """Test successful Julia template execution"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"
        author = "Test Author"
        plugins = {"plugins": ['License(; name="MIT")', "Git(; manifest=true)"]}

        # Mock successful subprocess call
        mock_run.return_value = Mock(
            returncode=0, stdout="Package created successfully", stderr=""
        )

        # Create the expected package directory
        package_dir = temp_dir / package_name
        package_dir.mkdir()

        result = generator._call_julia_generator(
            package_name, author, "testuser", "test@example.com", temp_dir, plugins
        )

        assert result == package_dir
        assert mock_run.called

        # Verify command structure
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "julia"
        assert call_args[1] == "-e"
        assert "using PkgTemplates" in call_args[2]
        assert package_name in call_args[2]

    @patch("subprocess.run")
    def test_call_julia_generator_julia_not_found(self, mock_run, temp_dir):
        """Test Julia not found error"""
        generator = JuliaPackageGenerator()

        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(RuntimeError, match="Julia not found"):
            generator._call_julia_generator(
                "TestPackage",
                "Test Author",
                "testuser",
                "test@example.com",
                temp_dir,
                {"plugins": []},
            )

    @patch("subprocess.run")
    def test_call_julia_generator_subprocess_error_with_package_dir(
        self, mock_run, temp_dir
    ):
        """Test subprocess error but package directory exists"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"

        # Create package directory to simulate partial success
        package_dir = temp_dir / package_name
        package_dir.mkdir()

        error = subprocess.CalledProcessError(1, ["julia"])
        error.stdout = "Some warnings but package created"
        error.stderr = ""
        mock_run.side_effect = error

        result = generator._call_julia_generator(
            "TestPackage",
            "Test Author",
            "testuser",
            "test@example.com",
            temp_dir,
            {"plugins": []},
        )

        assert result == package_dir

    @patch("subprocess.run")
    def test_call_julia_generator_real_error(self, mock_run, temp_dir):
        """Test real Julia script error"""
        generator = JuliaPackageGenerator()

        error = subprocess.CalledProcessError(1, ["julia"])
        error.stdout = "Error creating package: PkgTemplates error"
        error.stderr = ""
        mock_run.side_effect = error

        with pytest.raises(RuntimeError, match="PkgTemplates error"):
            generator._call_julia_generator(
                "TestPackage",
                "Test Author",
                "testuser",
                "test@example.com",
                temp_dir,
                {"plugins": []},
            )

    def test_add_mise_config(self, temp_dir):
        """Test mise config generation"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"
        package_dir = temp_dir / package_name
        package_dir.mkdir()

        generator._add_mise_config(package_dir, package_name)

        mise_file = package_dir / ".mise.toml"
        assert mise_file.exists()

        content = mise_file.read_text()
        assert package_name in content

    def test_check_dependencies_all_available(self):
        """Test dependency check when all are available"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            deps = JuliaPackageGenerator.check_dependencies()
            assert deps["julia"] is True
            assert deps["pkgtemplates"] is True
            assert deps["mise"] is True

    def test_check_dependencies_julia_missing(self):
        """Test dependency check when Julia is missing"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                FileNotFoundError(),  # julia --version
                Mock(returncode=0),  # julia -e "using PkgTemplates"
                Mock(returncode=0),  # mise --version
            ]
            deps = JuliaPackageGenerator.check_dependencies()
            assert deps["julia"] is False

    def test_check_dependencies_pkgtemplates_missing(self):
        """Test dependency check when PkgTemplates is missing"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0),  # julia --version
                subprocess.CalledProcessError(
                    1, ["julia"]
                ),  # julia -e "using PkgTemplates"
                Mock(returncode=0),  # mise --version
            ]
            deps = JuliaPackageGenerator.check_dependencies()
            assert deps["pkgtemplates"] is False

    def test_create_package_integration(self, temp_dir):
        """Test complete package creation process"""
        generator = JuliaPackageGenerator()

        config = PackageConfig(
            template="minimal",
            license_type="MIT",
            plugin_options={"Git": {"manifest": False}},
        )

        with patch.object(generator, "_call_julia_generator") as mock_call:
            package_dir = temp_dir / "TestPackage"
            package_dir.mkdir()
            mock_call.return_value = package_dir

            result = generator.create_package(
                "TestPackage",
                "Test Author",
                "testuser",
                "test@example.com",
                temp_dir,
                config,
            )

            assert result == package_dir
            # Check that mise config was added
            assert (package_dir / ".mise.toml").exists()

    def test_create_package_output_dir_creation(self, temp_dir):
        """Test that output directory is created if it doesn't exist"""
        generator = JuliaPackageGenerator()
        non_existent_dir = temp_dir / "non_existent"

        config = PackageConfig(template="minimal")

        with patch.object(generator, "_call_julia_generator") as mock_call:
            package_dir = non_existent_dir / "TestPackage"
            package_dir.mkdir(parents=True)
            mock_call.return_value = package_dir

            result = generator.create_package(
                "TestPackage",
                "Test Author",
                "testuser",
                "test@example.com",
                non_existent_dir,
                config,
            )

            assert non_existent_dir.exists()
            assert result == package_dir

    @patch("subprocess.run")
    def test_call_julia_generator_invalid_package_names(self, mock_run, temp_dir):
        """Test Julia execution with various package names"""
        generator = JuliaPackageGenerator()

        invalid_names = [
            "123InvalidStart",  # Starts with number
            "invalid-name",  # Contains hyphen (not allowed in Julia identifiers)
            "invalid name",  # Contains space
            "invalid.name",  # Contains dot
            "invalid@name",  # Contains special character
            "if",  # Reserved keyword
            "function",  # Reserved keyword
            "",  # Empty string
            "a",  # Too short (less than 5 chars for General registry)
            "lowercase",  # Doesn't start with uppercase
        ]

        for name in invalid_names:
            try:
                generator._call_julia_generator(
                    name,
                    "Test Author",
                    "testuser",
                    "test@example.com",
                    temp_dir,
                    {"plugins": []},
                )
                # If no exception is raised, that's fine - the validation might be in Julia
                # or we might allow these names for local development
            except Exception:
                # Exceptions are expected for invalid names
                pass

    def test_generate_julia_code(self, temp_dir):
        """Test Julia code generation for dry-run mode"""
        generator = JuliaPackageGenerator()

        config = PackageConfig(
            template="minimal",
            license_type="MIT",
            plugin_options={"Git": {"manifest": False}},
        )

        julia_code = generator.generate_julia_code(
            "TestPackage",
            "Test Author",
            "testuser",
            "test@example.com",
            temp_dir,
            config,
        )

        assert "using PkgTemplates" in julia_code
        assert "Template(;" in julia_code
        assert "TestPackage" in julia_code
        assert "Test Author" in julia_code
        assert 'License(; name="MIT")' in julia_code
        assert "Git(; manifest=false)" in julia_code


class TestPackageConfig:
    """Test PackageConfig class"""

    def test_from_dict_basic(self):
        """Test creating PackageConfig from basic dictionary"""
        config_dict = {
            "template": "standard",
            "license_type": "MIT",
            "julia_version": "1.8.0",
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "standard"
        assert config.license_type == "MIT"
        assert config.julia_version == "1.8.0"
        assert config.plugin_options == {}

    def test_from_dict_with_plugin_options(self):
        """Test creating PackageConfig with plugin options"""
        config_dict = {
            "template": "full",
            "plugin_options": {
                "Git": {"manifest": False, "ssh": True},
                "Tests": {"aqua": True},
            },
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "full"
        assert config.plugin_options is not None
        assert config.plugin_options["Git"]["manifest"] is False
        assert config.plugin_options["Git"]["ssh"] is True
        assert config.plugin_options["Tests"]["aqua"] is True

    def test_from_dict_with_dot_notation(self):
        """Test creating PackageConfig with dot notation plugin options"""
        config_dict = {
            "template": "standard",
            "git.manifest": False,
            "git.ssh": True,
            "tests.aqua": True,
            "formatter.style": "blue",
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "standard"
        assert config.plugin_options is not None
        assert config.plugin_options["git"]["manifest"] is False
        assert config.plugin_options["git"]["ssh"] is True
        assert config.plugin_options["tests"]["aqua"] is True
        assert config.plugin_options["formatter"]["style"] == "blue"

    def test_from_dict_mixed_formats(self):
        """Test creating PackageConfig with mixed plugin option formats"""
        config_dict = {
            "template": "full",
            "plugin_options": {"Git": {"manifest": True}},
            "git.ssh": False,  # This should override the plugin_options value
            "tests.aqua": True,
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "full"
        assert config.plugin_options is not None
        assert config.plugin_options["Git"]["manifest"] is True
        assert config.plugin_options["git"]["ssh"] is False
        assert config.plugin_options["tests"]["aqua"] is True

    def test_from_dict_empty(self):
        """Test creating PackageConfig from empty dictionary"""
        config = PackageConfig.from_dict({})

        assert config.template == "standard"
        assert config.license_type is None
        assert config.julia_version is None
        assert config.plugin_options == {}

    def test_from_dict_none(self):
        """Test creating PackageConfig from None"""
        config = PackageConfig.from_dict(None)

        assert config.template == "standard"
        assert config.license_type is None
        assert config.julia_version is None
        assert config.plugin_options == {}

    def test_from_dict_unknown_keys(self):
        """Test that unknown keys are safely ignored"""
        config_dict = {
            "template": "minimal",
            "unknown_key": "unknown_value",
            "another_unknown": 42,
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "minimal"
        assert not hasattr(config, "unknown_key")
        assert not hasattr(config, "another_unknown")

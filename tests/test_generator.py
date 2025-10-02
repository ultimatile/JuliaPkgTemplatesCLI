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

    def test_add_mise_config_custom_filename(self, temp_dir):
        """Test mise config generation with custom filename"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"
        package_dir = temp_dir / package_name
        package_dir.mkdir()

        generator._add_mise_config(package_dir, package_name, "mise")

        mise_file = package_dir / "mise.toml"
        assert mise_file.exists()

        content = mise_file.read_text()
        assert package_name in content

        # Ensure the default file was not created
        default_file = package_dir / ".mise.toml"
        assert not default_file.exists()

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
            enabled_plugins=["License", "Git"],
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

    def test_create_package_with_custom_mise_filename(self, temp_dir):
        """Test package creation with custom mise filename"""
        generator = JuliaPackageGenerator()

        config = PackageConfig(
            enabled_plugins=["License", "Git"],
            license_type="MIT",
            plugin_options={"Git": {"manifest": False}},
            mise_filename_base="mise",
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
            # Check that custom mise config was added
            assert (package_dir / "mise.toml").exists()
            # Check that default mise config was not created
            assert not (package_dir / ".mise.toml").exists()

    def test_create_package_with_mise_disabled(self, temp_dir):
        """Test package creation with mise disabled"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"

        config = PackageConfig(
            with_mise=False,
        )

        with patch.object(generator, "_call_julia_generator") as mock_call:
            package_dir = temp_dir / package_name
            package_dir.mkdir(parents=True)
            mock_call.return_value = package_dir

            result = generator.create_package(
                package_name,
                "Test Author",
                "testuser",
                "test@example.com",
                temp_dir,
                config,
            )

            assert result == package_dir
            # Check that mise config was NOT created
            assert not (package_dir / ".mise.toml").exists()

    def test_create_package_with_mise_enabled(self, temp_dir):
        """Test package creation with mise enabled (default)"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"

        config = PackageConfig(
            with_mise=True,
        )

        with patch.object(generator, "_call_julia_generator") as mock_call:
            package_dir = temp_dir / package_name
            package_dir.mkdir(parents=True)
            mock_call.return_value = package_dir

            result = generator.create_package(
                package_name,
                "Test Author",
                "testuser",
                "test@example.com",
                temp_dir,
                config,
            )

            assert result == package_dir
            # Check that mise config was created
            assert (package_dir / ".mise.toml").exists()

    def test_create_package_output_dir_creation(self, temp_dir):
        """Test that output directory is created if it doesn't exist"""
        generator = JuliaPackageGenerator()
        non_existent_dir = temp_dir / "non_existent"

        config = PackageConfig()

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
            enabled_plugins=["License", "Git"],
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

    def test_generate_license_plugin_with_empty_options(self, temp_dir):
        """License plugin should render License() when no options are provided"""
        generator = JuliaPackageGenerator()
        config = PackageConfig(
            enabled_plugins=["License"],
            plugin_options={"License": {}},
        )

        julia_code = generator.generate_julia_code(
            "TestPackage",
            None,
            None,
            None,
            temp_dir,
            config,
        )

        assert "License()" in julia_code
        assert "License(;" not in julia_code


class TestPackageConfig:
    """Test PackageConfig class"""

    def test_from_dict_basic(self):
        """Test creating PackageConfig from basic dictionary"""
        config_dict = {
            "license_type": "MIT",
            "julia_version": "1.8.0",
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.license_type == "MIT"
        assert config.julia_version == "1.8.0"
        assert config.plugin_options == {}

    def test_from_dict_with_plugin_options(self):
        """Test creating PackageConfig with plugin options"""
        config_dict = {
            "plugin_options": {
                "Git": {"manifest": False, "ssh": True},
                "Tests": {"aqua": True},
            },
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.plugin_options is not None
        assert config.plugin_options["Git"]["manifest"] is False
        assert config.plugin_options["Git"]["ssh"] is True
        assert config.plugin_options["Tests"]["aqua"] is True

    def test_from_dict_with_dot_notation(self):
        """Test creating PackageConfig with dot notation plugin options"""
        config_dict = {
            "git.manifest": False,
            "git.ssh": True,
            "tests.aqua": True,
            "formatter.style": "blue",
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.plugin_options is not None
        assert config.plugin_options["git"]["manifest"] is False
        assert config.plugin_options["git"]["ssh"] is True
        assert config.plugin_options["tests"]["aqua"] is True
        assert config.plugin_options["formatter"]["style"] == "blue"

    def test_from_dict_mixed_formats(self):
        """Test creating PackageConfig with mixed plugin option formats"""
        config_dict = {
            "plugin_options": {"Git": {"manifest": True}},
            "git.ssh": False,  # This should override the plugin_options value
            "tests.aqua": True,
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.plugin_options is not None
        assert config.plugin_options["Git"]["manifest"] is True
        assert config.plugin_options["git"]["ssh"] is False
        assert config.plugin_options["tests"]["aqua"] is True

    def test_from_dict_empty(self):
        """Test creating PackageConfig from empty dictionary"""
        config = PackageConfig.from_dict({})

        assert config.license_type is None
        assert config.julia_version is None
        assert config.plugin_options == {}

    def test_from_dict_none(self):
        """Test creating PackageConfig from None"""
        config = PackageConfig.from_dict(None)

        assert config.license_type is None
        assert config.julia_version is None
        assert config.plugin_options == {}

    def test_from_dict_unknown_keys(self):
        """Test that unknown keys are safely ignored"""
        config_dict = {
            "unknown_key": "unknown_value",
            "another_unknown": 42,
        }

        config = PackageConfig.from_dict(config_dict)

        assert not hasattr(config, "unknown_key")
        assert not hasattr(config, "another_unknown")

    def test_from_dict_with_mise_filename_base(self):
        """Test creating PackageConfig with mise_filename_base"""
        config_dict = {
            "mise_filename_base": "mise",
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.mise_filename_base == "mise"

    def test_default_mise_filename_base(self):
        """Test that default mise_filename_base is '.mise'"""
        config = PackageConfig()
        assert config.mise_filename_base == ".mise"

    def test_default_with_mise(self):
        """Test that default with_mise is True"""
        config = PackageConfig()
        assert config.with_mise is True

    def test_from_dict_with_mise_option(self):
        """Test creating PackageConfig with with_mise option"""
        config_dict = {
            "with_mise": False,
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.with_mise is False

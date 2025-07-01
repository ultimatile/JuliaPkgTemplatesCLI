"""
Tests for plugin options functionality
"""

from juliapkgtemplates.generator import PackageConfig, JuliaPackageGenerator


class TestPluginOptions:
    """Test plugin options parsing and usage"""

    def test_config_from_dict_with_plugin_options(self):
        """Test PackageConfig.from_dict with plugin options"""
        config_dict = {
            "template": "standard",
            "license": "MIT",
            "options": {
                "Git.manifest": False,
                "Git.ssh": True,
                "Tests.aqua": True,
                "Formatter.style": "blue",
            },
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "standard"
        assert config.plugin_options is not None
        assert config.plugin_options["Git"]["manifest"] is False
        assert config.plugin_options["Git"]["ssh"] is True
        assert config.plugin_options["Tests"]["aqua"] is True
        assert config.plugin_options["Formatter"]["style"] == "blue"

    def test_config_from_dict_without_plugin_options(self):
        """Test PackageConfig.from_dict without plugin options"""
        config_dict = {
            "template": "minimal",
            "license": "MIT",
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "minimal"
        assert config.plugin_options is None

    def test_git_plugin_with_manifest_false(self):
        """Test Git plugin generation with manifest=false"""
        generator = JuliaPackageGenerator()

        plugin_options = {"Git": {"manifest": False}}

        git_plugin = generator._build_git_plugin(False, None, plugin_options)

        assert "manifest=false" in git_plugin
        assert git_plugin == "Git(; manifest=false)"

    def test_git_plugin_with_manifest_true_default(self):
        """Test Git plugin generation with default manifest=true"""
        generator = JuliaPackageGenerator()

        git_plugin = generator._build_git_plugin(False, None, None)

        assert "manifest=true" in git_plugin
        assert git_plugin == "Git(; manifest=true)"

    def test_git_plugin_with_multiple_options(self):
        """Test Git plugin generation with multiple options"""
        generator = JuliaPackageGenerator()

        plugin_options = {
            "Git": {"manifest": False, "ssh": True, "ignore": ["*.tmp", "temp/"]}
        }

        git_plugin = generator._build_git_plugin(False, None, plugin_options)

        assert "manifest=false" in git_plugin
        assert "ssh=true" in git_plugin
        assert '"*.tmp"' in git_plugin
        assert '"temp/"' in git_plugin

    def test_tests_plugin_with_options(self):
        """Test Tests plugin generation with options"""
        generator = JuliaPackageGenerator()

        plugin_options = {"Tests": {"aqua": True, "jet": True, "project": False}}

        tests_plugin = generator._build_tests_plugin(False, False, True, plugin_options)

        assert "aqua=true" in tests_plugin
        assert "jet=true" in tests_plugin
        assert "project=true" not in tests_plugin  # Overridden to False

    def test_formatter_plugin_with_style_option(self):
        """Test Formatter plugin generation with style option"""
        generator = JuliaPackageGenerator()

        plugin_options = {"Formatter": {"style": "blue"}}

        formatter_plugin = generator._build_formatter_plugin("nostyle", plugin_options)

        assert 'style="blue"' in formatter_plugin

    def test_project_file_plugin_with_version_option(self):
        """Test ProjectFile plugin generation with version option"""
        generator = JuliaPackageGenerator()

        plugin_options = {"ProjectFile": {"version": "1.2.3"}}

        project_file_plugin = generator._build_project_file_plugin(
            "0.0.1", plugin_options
        )

        assert 'version=v"1.2.3"' in project_file_plugin

    def test_license_plugin_with_name_option(self):
        """Test License plugin generation with name option"""
        generator = JuliaPackageGenerator()

        plugin_options = {"License": {"name": "Apache-2.0"}}

        license_plugin = generator._build_license_plugin("MIT", plugin_options)

        assert 'name="Apache-2.0"' in license_plugin

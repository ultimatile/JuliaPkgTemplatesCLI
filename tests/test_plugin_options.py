"""
Tests for plugin options functionality
"""

from juliapkgtemplates.generator import PackageConfig, JuliaPackageGenerator


class TestPluginOptions:
    """Test plugin options parsing and usage"""

    def test_config_from_dict_with_plugin_options(self):
        """Test PackageConfig.from_dict with plugin options using dot notation"""
        config_dict = {
            "template": "standard",
            "license_type": "MIT",
            "Git.manifest": False,
            "Git.ssh": True,
            "Tests.aqua": True,
            "Formatter.style": "blue",
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "standard"
        assert config.license_type == "MIT"
        assert config.plugin_options is not None
        assert config.plugin_options["Git"]["manifest"] is False
        assert config.plugin_options["Git"]["ssh"] is True
        assert config.plugin_options["Tests"]["aqua"] is True
        assert config.plugin_options["Formatter"]["style"] == "blue"

    def test_config_from_dict_without_plugin_options(self):
        """Test PackageConfig.from_dict without plugin options"""
        config_dict = {
            "template": "minimal",
            "license_type": "MIT",
        }

        config = PackageConfig.from_dict(config_dict)

        assert config.template == "minimal"
        assert config.license_type == "MIT"
        assert config.plugin_options == {}

    def test_git_plugin_with_manifest_false(self):
        """Test Git plugin generation with manifest=false"""
        generator = JuliaPackageGenerator()

        plugin_options = {"Git": {"manifest": False}}

        git_plugin = generator._build_git_plugin(plugin_options)

        assert "manifest=false" in git_plugin
        assert git_plugin == "Git(; manifest=false)"

    def test_git_plugin_with_manifest_false_default(self):
        """Test Git plugin generation with default manifest=false"""
        generator = JuliaPackageGenerator()

        git_plugin = generator._build_git_plugin(None)

        assert "manifest=false" in git_plugin
        assert git_plugin == "Git(; manifest=false)"

    def test_git_plugin_with_multiple_options(self):
        """Test Git plugin generation with multiple options"""
        generator = JuliaPackageGenerator()

        plugin_options = {
            "Git": {"manifest": False, "ssh": True, "ignore": ["*.tmp", "temp/"]}
        }

        git_plugin = generator._build_git_plugin(plugin_options)

        assert "manifest=false" in git_plugin
        assert "ssh=true" in git_plugin
        assert '"*.tmp"' in git_plugin
        assert '"temp/"' in git_plugin

    def test_tests_plugin_with_options(self):
        """Test Tests plugin generation with options"""
        generator = JuliaPackageGenerator()

        plugin_options = {"Tests": {"aqua": True, "jet": True, "project": False}}

        tests_plugin = generator._build_tests_plugin(plugin_options)

        assert "aqua=true" in tests_plugin
        assert "jet=true" in tests_plugin
        assert "project=true" not in tests_plugin  # Overridden to False

    def test_formatter_plugin_with_style_option(self):
        """Test Formatter plugin generation with style option"""
        generator = JuliaPackageGenerator()

        plugin_options = {"Formatter": {"style": "blue"}}

        formatter_plugin = generator._build_formatter_plugin(plugin_options)

        assert 'style="blue"' in formatter_plugin

    def test_project_file_plugin_with_version_option(self):
        """Test ProjectFile plugin generation with version option"""
        generator = JuliaPackageGenerator()

        plugin_options = {"ProjectFile": {"version": "1.2.3"}}

        project_file_plugin = generator._build_project_file_plugin(plugin_options)

        assert 'version=v"1.2.3"' in project_file_plugin

    def test_license_plugin_with_name_option(self):
        """Test License plugin generation with name option"""
        generator = JuliaPackageGenerator()

        plugin_options = {"License": {"name": "Apache-2.0"}}

        license_plugin = generator._build_license_plugin("MIT", plugin_options)

        assert 'name="Apache-2.0"' in license_plugin

    def test_plugin_options_simple_usage(self):
        """Test simple plugin options usage"""
        generator = JuliaPackageGenerator()

        plugin_options = {"Git": {"ssh": False, "manifest": True}}

        git_plugin = generator._build_git_plugin(plugin_options)

        assert "manifest=true" in git_plugin
        assert "ssh=true" not in git_plugin  # ssh=False, so not included

    def test_new_config_format(self):
        """Test new flat configuration format"""
        config_dict = {
            "template": "standard",
            "license_type": "MIT",
            "Git.ssh": False,
            "Git.manifest": False,
            "Tests.aqua": True,
        }

        config = PackageConfig.from_dict(config_dict)
        generator = JuliaPackageGenerator()

        git_plugin = generator._build_git_plugin(config.plugin_options)
        tests_plugin = generator._build_tests_plugin(config.plugin_options)

        assert "manifest=false" in git_plugin
        assert "ssh=true" not in git_plugin
        assert "aqua=true" in tests_plugin

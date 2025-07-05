"""
Tests for CLI plugin options functionality
"""

from click.testing import CliRunner

from juliapkgtemplates.cli import (
    main,
    parse_plugin_option_value,
    parse_plugin_options_from_cli,
    load_config,
)


class TestPluginOptionParsing:
    """Test plugin option value parsing"""

    def test_parse_boolean_values(self):
        """Test parsing boolean values"""
        assert parse_plugin_option_value("true") is True
        assert parse_plugin_option_value("True") is True
        assert parse_plugin_option_value("yes") is True
        assert parse_plugin_option_value("1") is True

        assert parse_plugin_option_value("false") is False
        assert parse_plugin_option_value("False") is False
        assert parse_plugin_option_value("no") is False
        assert parse_plugin_option_value("0") is False

    def test_parse_list_values(self):
        """Test parsing list values"""
        assert parse_plugin_option_value("[]") == []
        assert parse_plugin_option_value("[item1,item2]") == ["item1", "item2"]
        assert parse_plugin_option_value('["item1", "item2"]') == ["item1", "item2"]

    def test_parse_string_values(self):
        """Test parsing string values"""
        assert parse_plugin_option_value("blue") == "blue"
        assert parse_plugin_option_value("1.2.3") == "1.2.3"

    def test_parse_integer_values(self):
        """Test parsing integer values"""
        assert parse_plugin_option_value("123") == 123

    def test_parse_plugin_options_from_cli(self):
        """Test parsing plugin options from CLI kwargs"""
        kwargs = {
            "git": "manifest=false ssh=true",
            "tests": "aqua=true project=false",
            "formatter": "style=blue",
        }

        result = parse_plugin_options_from_cli(**kwargs)

        expected = {
            "Git": {"manifest": False, "ssh": True},
            "Tests": {"aqua": True, "project": False},
            "Formatter": {"style": "blue"},
        }

        assert result == expected

    def test_plugin_option_override_scenarios(self):
        """Test plugin option override scenarios (corner cases)"""
        # Test same plugin with conflicting options (last one wins)
        kwargs = {
            "git": "ssh=true ssh=false manifest=true",
        }
        result = parse_plugin_options_from_cli(**kwargs)
        expected = {
            "Git": {"ssh": False, "manifest": True},  # ssh=false overrides ssh=true
        }
        assert result == expected

    def test_empty_plugin_options(self):
        """Test empty and None plugin options"""
        kwargs = {
            "git": "",
            "tests": None,
        }
        result = parse_plugin_options_from_cli(**kwargs)
        assert result == {}  # Empty options should result in empty dict

    def test_malformed_plugin_options(self):
        """Test malformed plugin option strings"""
        kwargs = {
            "git": "manifest",  # Missing value (no =)
            "tests": "aqua=",  # Empty value
            "formatter": "=blue",  # Missing key
        }
        result = parse_plugin_options_from_cli(**kwargs)
        expected = {
            "Tests": {"aqua": ""},  # Empty value becomes empty string
            "Formatter": {"": "blue"},  # Missing key becomes empty string
        }
        assert result == expected

    def test_quoted_values_with_spaces(self):
        """Test quoted values containing spaces"""
        kwargs = {
            "git": 'ignore="*.tmp file with spaces.log"',
        }
        result = parse_plugin_options_from_cli(**kwargs)
        expected = {
            "Git": {"ignore": "*.tmp file with spaces.log"},
        }
        assert result == expected


class TestCLICommands:
    """Test CLI commands with plugin options"""

    def test_create_with_conflicting_plugin_options_same_arg(self, mock_subprocess):
        """Test create command with conflicting plugin options in same argument"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--git",
                "ssh=false ssh=true manifest=true",  # Conflicting ssh values in same arg
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        # Last value should win, ssh=true should appear in output
        assert "ssh=true" in result.output
        assert "manifest=true" in result.output

    def test_create_with_conflicting_plugin_options_separate_args(
        self, mock_subprocess
    ):
        """Test create command with conflicting plugin options in separate arguments (full override)"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--git",
                "ssh=true manifest=false",
                "--git",
                "ssh=false manifest=true",  # Second --git arg should override conflicting keys
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        # Second argument should override conflicting keys
        assert "manifest=true" in result.output
        # ssh=false is default, so it might not appear in output

    def test_create_with_partial_plugin_override_separate_args(self, mock_subprocess):
        """Test create command with separate plugin args - should do key-level merge"""
        runner = CliRunner()

        # Use isolated config to avoid interference from user settings
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "create",
                    "TestPkg",
                    "--git",
                    "ssh=true manifest=false",
                    "--git",
                    "manifest=true",  # Only manifest specified, ssh should be preserved (key-level merge)
                    "--dry-run",
                ],
                env={"XDG_CONFIG_HOME": "."},  # Use isolated config
            )

            assert result.exit_code == 0
            # Should do key-level merge: ssh=true should survive from first argument
            assert "ssh=true" in result.output
            # manifest=true should override manifest=false
            assert "manifest=true" in result.output

    def test_create_with_complex_list_options(self, mock_subprocess):
        """Test create command with complex list plugin options"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--git",
                'ignore=["*.tmp","*.log","build/"]',
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert '"*.tmp"' in result.output
        assert '"*.log"' in result.output
        assert '"build/"' in result.output

    def test_create_with_empty_plugin_options(self, mock_subprocess):
        """Test create command with empty plugin options"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--git",
                "",  # Empty git options
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        # Should still work but not include empty plugin options

    def test_create_with_quoted_spaces_plugin_options(self, mock_subprocess):
        """Test create command with quoted values containing spaces"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--git",
                'ignore="*.tmp file with spaces.log"',
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "*.tmp file with spaces.log" in result.output

    def test_config_command_with_conflicting_plugin_options(self, isolated_config):
        """Test config command with conflicting plugin options (corner case)"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "config",
                "set",
                "--git",
                "ssh=true ssh=false manifest=true",  # Conflicting ssh values
            ],
        )

        assert result.exit_code == 0
        assert "Set default Git.ssh: False" in result.output  # Last value wins
        assert "Set default Git.manifest: True" in result.output
        assert "Configuration saved" in result.output

        # Verify the config was saved correctly
        config_data = load_config()
        assert config_data["default"]["Git"]["ssh"] is False
        assert config_data["default"]["Git"]["manifest"] is True

    def test_config_command_with_malformed_options(self, isolated_config):
        """Test config command with malformed plugin options"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "config",
                "set",
                "--git",
                "manifest=",  # Empty value
                "--tests",
                "aqua",  # Missing value
            ],
        )

        assert result.exit_code == 0
        assert "Set default Git.manifest:" in result.output  # Empty value
        # malformed options without '=' are ignored
        assert "Configuration saved" in result.output

        # Verify the config was saved correctly
        config_data = load_config()
        assert config_data["default"]["Git"]["manifest"] == ""  # Empty string

    def test_config_command_with_separate_plugin_args(self, isolated_config):
        """Test config command with separate plugin arguments (full override)"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "config",
                "set",
                "--git",
                "ssh=true manifest=false",
                "--git",
                "ssh=false manifest=true",  # Second --git should override conflicting keys
            ],
        )

        assert result.exit_code == 0
        assert "Set default Git.ssh: False" in result.output  # Last value wins
        assert "Set default Git.manifest: True" in result.output  # Last value wins
        assert "Configuration saved" in result.output

        # Verify the config was saved correctly
        config_data = load_config()
        assert config_data["default"]["Git"]["ssh"] is False
        assert config_data["default"]["Git"]["manifest"] is True

    def test_config_command_with_partial_plugin_override(self, isolated_config):
        """Test config command with separate plugin args - should do key-level merge"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "config",
                "set",
                "--git",
                "ssh=true manifest=false",
                "--git",
                "manifest=true",  # Only manifest specified, ssh should be preserved (key-level merge)
            ],
        )

        assert result.exit_code == 0
        # Should do key-level merge: both ssh and manifest should be set
        assert "Set default Git.ssh: True" in result.output
        assert "Set default Git.manifest: True" in result.output
        assert "Configuration saved" in result.output

        # Verify the config was saved correctly
        config_data = load_config()
        # Both keys should be present after merge
        assert config_data["default"]["Git"]["ssh"] is True
        assert config_data["default"]["Git"]["manifest"] is True

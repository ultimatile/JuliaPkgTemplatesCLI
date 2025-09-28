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

        assert result["options"] == expected

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
        assert result["options"] == expected

    def test_empty_plugin_options(self):
        """Test empty and None plugin options"""
        kwargs = {
            "git": "",
            "tests": None,
        }
        result = parse_plugin_options_from_cli(**kwargs)
        # Empty string enables plugin with no options, None doesn't enable
        assert result["options"] == {"Git": {}}

    def test_malformed_plugin_options(self):
        """Test malformed plugin option strings"""
        kwargs = {
            "git": "manifest",  # Missing value (no =)
            "tests": "aqua=",  # Empty value
            "formatter": "=blue",  # Missing key
        }
        result = parse_plugin_options_from_cli(**kwargs)
        expected = {
            "Git": {},  # "manifest" without = just enables plugin
            "Tests": {"aqua": ""},  # Empty value becomes empty string
            "Formatter": {"": "blue"},  # Missing key becomes empty string
        }
        assert result["options"] == expected

    def test_quoted_values_with_spaces(self):
        """Test quoted values containing spaces"""
        kwargs = {
            "git": 'ignore="*.tmp file with spaces.log"',
        }
        result = parse_plugin_options_from_cli(**kwargs)
        expected = {
            "Git": {"ignore": "*.tmp file with spaces.log"},
        }
        assert result["options"] == expected


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
        """Test create command with separate plugin args - last option wins"""
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
                    "manifest=true",  # Last option wins, only manifest=true is kept
                    "--dry-run",
                ],
                env={"XDG_CONFIG_HOME": "."},  # Use isolated config
            )

            assert result.exit_code == 0
            # Last option wins: only manifest=true should be present
            assert "manifest=true" in result.output
            # ssh option from first argument should not be present
            assert "ssh=true" not in result.output

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
                "--config-file",
                str(isolated_config),
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
                "--config-file",
                str(isolated_config),
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
                "--config-file",
                str(isolated_config),
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
        """Test config command with separate plugin args - last option wins"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                "ssh=true manifest=false",
                "--git",
                "manifest=true",  # Last option wins, only manifest=true is kept
            ],
        )

        assert result.exit_code == 0
        # Last option wins: only manifest should be set
        assert "Set default Git.manifest: True" in result.output
        assert "Configuration saved" in result.output
        # ssh should not be set since last option doesn't include it
        assert "Set default Git.ssh:" not in result.output

        # Verify the config was saved correctly
        config_data = load_config()
        # Only manifest should be present since last option wins
        assert config_data["default"]["Git"]["manifest"] is True
        # ssh should not be present since it was only in the first option
        assert "ssh" not in config_data["default"]["Git"]

    def test_config_command_multiple_ignore_executions(self, isolated_config):
        """Test multiple config set executions with git ignore - should merge or override"""
        runner = CliRunner()

        # First execution: set ignore to "*.tmp"
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.tmp"',
            ],
        )
        assert result1.exit_code == 0
        assert "Set default Git.ignore:" in result1.output and "*.tmp" in result1.output
        assert "Configuration saved" in result1.output

        # Verify first config
        config_data = load_config()
        assert config_data["default"]["Git"]["ignore"] == "*.tmp"

        # Second execution: set ignore to "*.log"
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.log"',
            ],
        )
        assert result2.exit_code == 0
        assert "Set default Git.ignore:" in result2.output and "*.log" in result2.output
        assert "Configuration saved" in result2.output

        # Verify final config - check if it merges or overrides
        config_data = load_config()
        final_ignore = config_data["default"]["Git"]["ignore"]

        # Current behavior: auto-merge for git ignore
        assert isinstance(final_ignore, list)
        assert "*.tmp" in final_ignore
        assert "*.log" in final_ignore

        # Test package creation to see if this works correctly
        result3 = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--dry-run",
            ],
        )

        # Should work since result is array format now
        assert result3.exit_code == 0
        assert "*.tmp" in result3.output
        assert "*.log" in result3.output

    def test_config_command_multiple_ignore_array_executions(self, isolated_config):
        """Test multiple config set executions with array format git ignore"""
        runner = CliRunner()

        # First execution: set ignore to array with one item
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore=["*.tmp"]',
            ],
        )
        assert result1.exit_code == 0
        assert "Configuration saved" in result1.output

        # Verify first config
        config_data = load_config()
        assert config_data["default"]["Git"]["ignore"] == ["*.tmp"]

        # Second execution: set ignore to array with different item
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore=["*.log"]',
            ],
        )
        assert result2.exit_code == 0
        assert "Configuration saved" in result2.output

        # Verify final config - should merge
        config_data = load_config()
        final_ignore = config_data["default"]["Git"]["ignore"]

        # Current behavior: auto-merge for git ignore
        assert isinstance(final_ignore, list)
        assert "*.tmp" in final_ignore
        assert "*.log" in final_ignore

        # Test package creation - this should work since it's proper array format
        result3 = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--dry-run",
            ],
        )

        assert result3.exit_code == 0
        assert '"*.tmp"' in result3.output
        assert '"*.log"' in result3.output

    def test_config_command_explicit_merge_with_plus_equals(self, isolated_config):
        """Test config set with explicit += merge syntax"""
        runner = CliRunner()

        # First execution: set ignore to initial value
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.tmp"',
            ],
        )
        assert result1.exit_code == 0

        # Second execution: use += to explicitly merge
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore+="*.log"',
            ],
        )
        assert result2.exit_code == 0
        assert "Merged Git.ignore:" in result2.output

        # Verify final config - should merge
        config_data = load_config()
        final_ignore = config_data["default"]["Git"]["ignore"]

        assert isinstance(final_ignore, list)
        assert "*.tmp" in final_ignore
        assert "*.log" in final_ignore

    def test_config_command_explicit_merge_array_with_plus_equals(
        self, isolated_config
    ):
        """Test config set with explicit += merge syntax for arrays"""
        runner = CliRunner()

        # First execution: set ignore to array
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore=["*.tmp", "*.log"]',
            ],
        )
        assert result1.exit_code == 0

        # Second execution: use += to explicitly merge more items
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore+=["*.bak", "*.swp"]',
            ],
        )
        assert result2.exit_code == 0
        assert "Merged Git.ignore:" in result2.output

        # Verify final config - should merge all items
        config_data = load_config()
        final_ignore = config_data["default"]["Git"]["ignore"]

        assert isinstance(final_ignore, list)
        assert "*.tmp" in final_ignore
        assert "*.log" in final_ignore
        assert "*.bak" in final_ignore
        assert "*.swp" in final_ignore

    def test_config_command_mixed_regular_and_merge_syntax(self, isolated_config):
        """Test mixing regular = and += syntax in same command"""
        runner = CliRunner()

        # First execution: set initial values
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.tmp" ssh=true',
            ],
        )
        assert result1.exit_code == 0

        # Second execution: mix override and merge operations
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore+="*.log" ssh=false',  # Merge ignore, override ssh
            ],
        )
        assert result2.exit_code == 0

        # Verify final config
        config_data = load_config()
        git_config = config_data["default"]["Git"]

        # ignore should be merged
        assert isinstance(git_config["ignore"], list)
        assert "*.tmp" in git_config["ignore"]
        assert "*.log" in git_config["ignore"]

        # ssh should be overridden
        assert git_config["ssh"] is False

    def test_config_command_merge_with_no_existing_value(self, isolated_config):
        """Test += syntax when no existing value exists (should behave like first-time setting)"""
        runner = CliRunner()

        # First execution: use += with no existing value
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore+="*.tmp"',
            ],
        )
        assert result1.exit_code == 0
        assert "Set default Git.ignore:" in result1.output and "*.tmp" in result1.output

        # Verify config - should be set as if it was a normal assignment
        config_data = load_config()
        ignore = config_data["default"]["Git"]["ignore"]

        assert ignore == "*.tmp"  # Should be single value, not array

        # Second execution: now add more with +=
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore+="*.log"',
            ],
        )
        assert result2.exit_code == 0
        assert "Merged Git.ignore:" in result2.output

        # Verify final config - should now be merged into array
        config_data = load_config()
        final_ignore = config_data["default"]["Git"]["ignore"]

        assert isinstance(final_ignore, list)
        assert "*.tmp" in final_ignore
        assert "*.log" in final_ignore

    def test_config_command_merge_array_with_no_existing_value(self, isolated_config):
        """Test += syntax with array value when no existing value exists"""
        runner = CliRunner()

        # First execution: use += with array and no existing value
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore+=["*.tmp", "*.log"]',
            ],
        )
        assert result1.exit_code == 0
        assert "Set default Git.ignore:" in result1.output

        # Verify config - should be set as array
        config_data = load_config()
        ignore = config_data["default"]["Git"]["ignore"]

        assert isinstance(ignore, list)
        assert "*.tmp" in ignore
        assert "*.log" in ignore

    # NOTE: Complex nested array parsing is not yet implemented
    # def test_config_command_complex_nested_array_merge(self, isolated_config):
    #     """Test merging complex nested arrays (Vector{Vector} preservation)"""
    #     # This feature requires more sophisticated array parsing
    #     # Currently only simple arrays and gitignore auto-merge are supported
    #     pass

    def test_config_command_scalar_mixed_with_array_merge(self, isolated_config):
        """Test merging scalar values with arrays using universal strategy"""
        runner = CliRunner()

        # First execution: set a scalar value
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--formatter",
                "style=blue",
            ],
        )
        assert result1.exit_code == 0

        # Second execution: try to merge with a different scalar - should create array
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--formatter",
                "style+=red",
            ],
        )
        assert result2.exit_code == 0

        # Verify final config - should create array from scalars
        config_data = load_config()
        style = config_data["default"]["Formatter"]["style"]

        assert isinstance(style, list)
        assert "blue" in style
        assert "red" in style

    def test_config_command_boolean_and_string_merge(self, isolated_config):
        """Test merging boolean with string values"""
        runner = CliRunner()

        # First execution: set a boolean value
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                "ssh=true",
            ],
        )
        assert result1.exit_code == 0

        # Second execution: merge with a string value
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ssh+="custom"',
            ],
        )
        assert result2.exit_code == 0

        # Verify final config - should create array from boolean and string
        config_data = load_config()
        ssh = config_data["default"]["Git"]["ssh"]

        assert isinstance(ssh, list)
        assert True in ssh
        assert "custom" in ssh

    def test_config_command_comma_separated_string_expansion(self, isolated_config):
        """Test that comma-separated strings are properly expanded in merge operations"""
        runner = CliRunner()

        # First execution: set initial ignore pattern
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.tmp"',
            ],
        )
        assert result1.exit_code == 0

        # Second execution: merge comma-separated patterns
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore+="*.log,*.bak,*.swp"',
            ],
        )
        assert result2.exit_code == 0

        # Verify final config - comma-separated should be expanded
        config_data = load_config()
        ignore = config_data["default"]["Git"]["ignore"]

        assert isinstance(ignore, list)
        assert "*.tmp" in ignore
        assert "*.log" in ignore
        assert "*.bak" in ignore
        assert "*.swp" in ignore
        assert len(ignore) == 4

    def test_config_command_array_then_string_ignore_merge(self, isolated_config):
        """Test config set: array first, then string - should merge into array"""
        runner = CliRunner()

        # First execution: set ignore to array
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore=["*.tmp", "*.log"]',
            ],
        )
        assert result1.exit_code == 0

        # Second execution: add string ignore - should merge
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.backup"',
            ],
        )
        assert result2.exit_code == 0

        # Verify final config - should merge into array
        config_data = load_config()
        final_ignore = config_data["default"]["Git"]["ignore"]

        # Should merge: existing array + new string
        assert isinstance(final_ignore, list)
        assert "*.tmp" in final_ignore
        assert "*.log" in final_ignore
        assert "*.backup" in final_ignore
        assert len(final_ignore) == 3

        # Test package creation - should work since result is array
        result3 = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--dry-run",
            ],
        )

        assert result3.exit_code == 0
        assert '"*.tmp"' in result3.output
        assert '"*.log"' in result3.output
        assert '"*.backup"' in result3.output

    def test_config_command_string_then_array_ignore_merge(self, isolated_config):
        """Test config set: string first, then array - should merge into array"""
        runner = CliRunner()

        # First execution: set ignore to string
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.tmp"',
            ],
        )
        assert result1.exit_code == 0

        # Second execution: add array ignore - should merge
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore=["*.log", "*.backup"]',
            ],
        )
        assert result2.exit_code == 0

        # Verify final config - should merge into array
        config_data = load_config()
        final_ignore = config_data["default"]["Git"]["ignore"]

        # Should merge: existing string + new array
        assert isinstance(final_ignore, list)
        assert "*.tmp" in final_ignore
        assert "*.log" in final_ignore
        assert "*.backup" in final_ignore
        assert len(final_ignore) == 3

        # Test package creation - should work since result is array
        result3 = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--dry-run",
            ],
        )

        assert result3.exit_code == 0
        assert '"*.tmp"' in result3.output
        assert '"*.log"' in result3.output
        assert '"*.backup"' in result3.output

    def test_config_command_string_then_string_ignore_merge(self, isolated_config):
        """Test config set: string first, then string - should merge into array"""
        runner = CliRunner()

        # First execution: set ignore to string
        result1 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.tmp"',
            ],
        )
        assert result1.exit_code == 0

        # Second execution: add another string ignore - should merge
        result2 = runner.invoke(
            main,
            [
                "config",
                "set",
                "--config-file",
                str(isolated_config),
                "--git",
                'ignore="*.log"',
            ],
        )
        assert result2.exit_code == 0

        # Verify final config - should merge into array
        config_data = load_config()
        final_ignore = config_data["default"]["Git"]["ignore"]

        # Should merge: string + string = array
        assert isinstance(final_ignore, list)
        assert "*.tmp" in final_ignore
        assert "*.log" in final_ignore
        assert len(final_ignore) == 2

        # Test package creation - should work since result is array
        result3 = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--dry-run",
            ],
        )

        assert result3.exit_code == 0
        assert '"*.tmp"' in result3.output
        assert '"*.log"' in result3.output

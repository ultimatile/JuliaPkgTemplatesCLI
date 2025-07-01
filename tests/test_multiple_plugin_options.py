"""
Test the new multiple plugin option syntax
"""

import pytest
from click.testing import CliRunner

from juliapkgtemplates.cli import (
    parse_multiple_key_value_pairs,
    parse_plugin_options_from_cli,
    main,
)


class TestMultiplePluginOptionsParser:
    """Test the parser for multiple key=value pairs"""

    def test_parse_simple_pairs(self):
        """Test parsing simple key=value pairs"""
        result = parse_multiple_key_value_pairs("manifest=false ssh=true")
        expected = {"manifest": False, "ssh": True}
        assert result == expected

    def test_parse_quoted_values(self):
        """Test parsing quoted values"""
        result = parse_multiple_key_value_pairs('name="My Package" version="1.0.0"')
        expected = {"name": "My Package", "version": "1.0.0"}
        assert result == expected

    def test_parse_mixed_types(self):
        """Test parsing mixed value types"""
        result = parse_multiple_key_value_pairs("count=42 enabled=true name=test")
        expected = {"count": 42, "enabled": True, "name": "test"}
        assert result == expected

    def test_parse_list_values(self):
        """Test parsing list values"""
        result = parse_multiple_key_value_pairs("ignore=[*.tmp,*.log] enabled=true")
        expected = {"ignore": ["*.tmp", "*.log"], "enabled": True}
        assert result == expected

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = parse_multiple_key_value_pairs("")
        assert result == {}

    def test_parse_single_pair(self):
        """Test parsing single key=value pair"""
        result = parse_multiple_key_value_pairs("manifest=false")
        expected = {"manifest": False}
        assert result == expected

    def test_parse_extra_spaces(self):
        """Test parsing with extra spaces"""
        result = parse_multiple_key_value_pairs("  manifest=false   ssh=true  ")
        expected = {"manifest": False, "ssh": True}
        assert result == expected


class TestPluginOptionsFromCLI:
    """Test CLI plugin option parsing with new syntax"""

    def test_new_format_git_options(self):
        """Test new format for Git plugin options"""
        kwargs = {"gitoption": "manifest=false ssh=true"}
        result = parse_plugin_options_from_cli(**kwargs)
        expected = {"Git": {"manifest": False, "ssh": True}}
        assert result == expected

    def test_old_format_still_works(self):
        """Test that old format still works"""
        kwargs = {"git_option": ["manifest=false", "ssh=true"]}
        result = parse_plugin_options_from_cli(**kwargs)
        expected = {"Git": {"manifest": False, "ssh": True}}
        assert result == expected

    def test_multiple_plugins_new_format(self):
        """Test multiple plugins with new format"""
        kwargs = {
            "gitoption": "manifest=false ssh=true",
            "testsoption": "aqua=true jet=false",
        }
        result = parse_plugin_options_from_cli(**kwargs)
        expected = {
            "Git": {"manifest": False, "ssh": True},
            "Tests": {"aqua": True, "jet": False},
        }
        assert result == expected

    def test_priority_old_over_new(self):
        """Test that old format takes priority over new format"""
        kwargs = {
            "git_option": ["manifest=true"],
            "gitoption": "manifest=false ssh=true",
        }
        result = parse_plugin_options_from_cli(**kwargs)
        # Old format should take priority
        expected = {"Git": {"manifest": True}}
        assert result == expected


class TestCLIIntegration:
    """Test CLI integration with new plugin option syntax"""

    def test_new_syntax_help_text(self):
        """Test that help text includes new syntax"""
        runner = CliRunner()
        result = runner.invoke(main, ["create", "--help"])

        # Should contain both old and new syntax help
        assert "--git-option" in result.output
        assert "--gitoption" in result.output
        assert "space-separated" in result.output

    @pytest.mark.parametrize("plugin", ["git", "tests", "formatter"])
    def test_plugin_options_available(self, plugin):
        """Test that plugin options are available for known plugins"""
        runner = CliRunner()
        result = runner.invoke(main, ["create", "--help"])

        # Both old and new format should be available
        assert f"--{plugin}-option" in result.output
        assert f"--{plugin}option" in result.output

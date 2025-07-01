"""
Tests for CLI plugin options functionality
"""

from click.testing import CliRunner

from juliapkgtemplates.cli import (
    main,
    parse_plugin_option_value,
    parse_plugin_options_from_cli,
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
            "git_option": ["manifest=false", "ssh=true"],
            "tests_option": ["aqua=true", "project=false"],
            "formatter_option": ["style=blue"],
        }

        result = parse_plugin_options_from_cli(**kwargs)

        expected = {
            "Git": {"manifest": False, "ssh": True},
            "Tests": {"aqua": True, "project": False},
            "Formatter": {"style": "blue"},
        }

        assert result == expected


class TestCLICommands:
    """Test CLI commands with plugin options"""

    def test_create_with_git_options(self, mock_subprocess):
        """Test create command with Git plugin options"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--git-option",
                "manifest=false",
                "--git-option",
                "ssh=true",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "manifest=false" in result.output
        assert "ssh=true" in result.output

    def test_create_with_tests_options(self, mock_subprocess):
        """Test create command with Tests plugin options"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--tests-option",
                "aqua=true",
                "--tests-option",
                "jet=true",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "aqua=true" in result.output
        assert "jet=true" in result.output

    def test_create_with_formatter_options(self, mock_subprocess):
        """Test create command with Formatter plugin options"""
        runner = CliRunner()

        result = runner.invoke(
            main, ["create", "TestPkg", "--formatter-option", "style=blue", "--dry-run"]
        )

        assert result.exit_code == 0
        assert 'style="blue"' in result.output

    def test_create_with_multiple_plugin_options(self, mock_subprocess):
        """Test create command with multiple plugin options"""
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "create",
                "TestPkg",
                "--git-option",
                "manifest=false",
                "--tests-option",
                "aqua=true",
                "--formatter-option",
                "style=blue",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "manifest=false" in result.output
        assert "aqua=true" in result.output
        assert 'style="blue"' in result.output

    def test_config_command(self, temp_config_dir):
        """Test config command"""
        runner = CliRunner()

        result = runner.invoke(main, ["config", "template", "minimal"])

        assert result.exit_code == 0
        assert "Set template = minimal" in result.output

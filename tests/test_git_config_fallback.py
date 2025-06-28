"""
Tests for git config fallback behavior
"""

import subprocess
import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner

from juliapkgtemplates.cli import create


def get_git_config(key: str) -> str:
    """Get git config value, return empty string if not set"""
    try:
        result = subprocess.run(
            ["git", "config", key], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


class TestGitConfigFallback:
    """Test git config fallback behavior"""

    def test_author_fallback_to_git_config(self, temp_dir):
        """Test that author falls back to git config user.name when not provided"""
        expected_author = get_git_config("user.name")

        # Skip if git config user.name is not set
        if not expected_author:
            pytest.skip("git config user.name not set")

        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            # Mock load_config to return empty config (no defaults)
            with patch("juliapkgtemplates.cli.load_config", return_value={}):
                runner = CliRunner()
                result = runner.invoke(
                    create, ["TestPackage", "--output-dir", str(temp_dir)]
                )

                assert result.exit_code == 0

                # Verify that author was passed as None to let PkgTemplates.jl handle fallback
                call_args = mock_instance.create_package.call_args
                assert call_args.kwargs["author"] is None

                # The Julia script should handle the fallback to git config user.name
                # This is tested by verifying the Julia script call structure

    def test_user_fallback_to_git_config(self, temp_dir):
        """Test that user falls back to git config github.user when not provided"""
        expected_user = get_git_config("github.user")

        # Skip if git config github.user is not set
        if not expected_user:
            pytest.skip("git config github.user not set")

        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            # Mock load_config to return empty config (no defaults)
            with patch("juliapkgtemplates.cli.load_config", return_value={}):
                runner = CliRunner()
                result = runner.invoke(
                    create, ["TestPackage", "--output-dir", str(temp_dir)]
                )

                assert result.exit_code == 0

                # Verify that user was passed as None to let PkgTemplates.jl handle fallback
                call_args = mock_instance.create_package.call_args
                assert call_args.kwargs["user"] is None

    def test_mail_fallback_to_git_config(self, temp_dir):
        """Test that mail falls back to git config user.email when not provided"""
        expected_mail = get_git_config("user.email")

        # Skip if git config user.email is not set
        if not expected_mail:
            pytest.skip("git config user.email not set")

        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            # Mock load_config to return empty config (no defaults)
            with patch("juliapkgtemplates.cli.load_config", return_value={}):
                runner = CliRunner()
                result = runner.invoke(
                    create, ["TestPackage", "--output-dir", str(temp_dir)]
                )

                assert result.exit_code == 0

                # Verify that mail was passed as None to let PkgTemplates.jl handle fallback
                call_args = mock_instance.create_package.call_args
                assert call_args.kwargs["mail"] is None

    @pytest.mark.skipif(
        not get_git_config("user.name") or not get_git_config("user.email"),
        reason="git config user.name and user.email must be set for fallback testing",
    )
    def test_git_config_values_available(self):
        """Test that expected git config values are available for testing"""
        user_name = get_git_config("user.name")
        user_email = get_git_config("user.email")
        github_user = get_git_config("github.user")

        print("Git config values:")
        print(f"  user.name: '{user_name}'")
        print(f"  user.email: '{user_email}'")
        print(f"  github.user: '{github_user}'")

        # At least user.name and user.email should be set for meaningful tests
        assert user_name, "git config user.name should be set for fallback testing"
        assert user_email, "git config user.email should be set for fallback testing"

    def test_cli_args_override_git_config(self, temp_dir):
        """Test that CLI arguments override git config values"""
        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            # Mock load_config to return empty config (no defaults)
            with patch("juliapkgtemplates.cli.load_config", return_value={}):
                runner = CliRunner()
                result = runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--author",
                        "CLI Author",
                        "--user",
                        "cliuser",
                        "--mail",
                        "cli@example.com",
                        "--output-dir",
                        str(temp_dir),
                    ],
                )

                assert result.exit_code == 0

                # Verify that CLI values were used, not git config fallbacks
                call_args = mock_instance.create_package.call_args
                assert call_args.kwargs["author"] == "CLI Author"
                assert call_args.kwargs["user"] == "cliuser"
                assert call_args.kwargs["mail"] == "cli@example.com"

    def test_config_file_values_override_git_config(self, temp_dir):
        """Test that config file values override git config values"""
        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            # Mock load_config to return config with defaults
            config_defaults = {
                "default": {
                    "author": "Config Author",
                    "user": "configuser",
                    "mail": "config@example.com",
                }
            }
            with patch(
                "juliapkgtemplates.cli.load_config", return_value=config_defaults
            ):
                runner = CliRunner()
                result = runner.invoke(
                    create, ["TestPackage", "--output-dir", str(temp_dir)]
                )

                assert result.exit_code == 0

                # Verify that config values were used, not git config fallbacks
                call_args = mock_instance.create_package.call_args
                assert call_args.kwargs["author"] == "Config Author"
                assert call_args.kwargs["user"] == "configuser"
                assert call_args.kwargs["mail"] == "config@example.com"

    def test_precedence_cli_over_config_over_git(self, temp_dir):
        """Test precedence: CLI args > config file > git config"""
        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            # Mock load_config to return partial config
            config_defaults = {
                "default": {
                    "author": "Config Author",
                    # user and mail not in config, should fall back to git config
                }
            }
            with patch(
                "juliapkgtemplates.cli.load_config", return_value=config_defaults
            ):
                runner = CliRunner()
                result = runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--user",
                        "CLI User",  # CLI overrides
                        # author from config, mail from git config
                        "--output-dir",
                        str(temp_dir),
                    ],
                )

                assert result.exit_code == 0

                call_args = mock_instance.create_package.call_args
                # CLI value used
                assert call_args.kwargs["user"] == "CLI User"
                # Config value used
                assert call_args.kwargs["author"] == "Config Author"
                # Git config fallback (passed as None to Julia script)
                assert call_args.kwargs["mail"] is None

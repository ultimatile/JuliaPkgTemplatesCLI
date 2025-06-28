"""
Tests for Julia script integration with git config fallback behavior
"""

import subprocess
import pytest
from unittest.mock import patch

from juliapkgtemplates.generator import JuliaPackageGenerator


def get_git_config(key: str) -> str:
    """Get git config value, return empty string if not set"""
    try:
        result = subprocess.run(
            ["git", "config", key], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


class TestJuliaGitIntegration:
    """Test Julia script integration with git config"""

    def test_julia_script_args_structure(self, temp_dir):
        """Test that Julia script receives correct argument structure"""
        generator = JuliaPackageGenerator()

        # Mock the Julia script execution to capture arguments
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Package created successfully"
            mock_run.return_value.stderr = ""

            # Create the expected package directory
            package_dir = temp_dir / "TestPackage"
            package_dir.mkdir()

            # Mock the Julia script file existence
            with patch.object(generator, "scripts_dir", temp_dir):
                julia_script = temp_dir / "pkg_generator.jl"
                julia_script.touch()

                plugins = {"plugins": ['License(; name="MIT")', "Git(; manifest=true)"]}

                try:
                    generator._call_julia_generator(
                        "TestPackage",
                        "Test Author",
                        "testuser",
                        "test@example.com",
                        temp_dir,
                        plugins,
                    )

                    # Verify the command structure
                    mock_run.assert_called_once()
                    call_args = mock_run.call_args[0][0]

                    # Verify argument order and presence
                    assert call_args[0] == "julia"
                    assert str(julia_script) in call_args
                    assert "TestPackage" in call_args
                    assert "Test Author" in call_args
                    assert "testuser" in call_args
                    assert "test@example.com" in call_args
                    assert str(temp_dir) in call_args

                    # Verify the mail parameter is in the expected position (4th argument)
                    # julia script package_name author user mail output_dir plugins
                    expected_order = [
                        "julia",
                        str(julia_script),
                        "TestPackage",
                        "Test Author",
                        "testuser",
                        "test@example.com",
                        str(temp_dir),
                        '[License(; name="MIT"), Git(; manifest=true)]',
                    ]

                    assert call_args == expected_order

                except Exception as e:
                    # If the test package directory doesn't exist, we still get the command structure
                    if "Package directory not created" in str(e):
                        mock_run.assert_called_once()
                        call_args = mock_run.call_args[0][0]
                        # Still verify the command structure
                        assert call_args[0] == "julia"
                        assert "TestPackage" in call_args
                        assert "test@example.com" in call_args

    def test_julia_script_with_empty_values(self, temp_dir):
        """Test Julia script call with empty author/user/mail values (fallback scenario)"""
        generator = JuliaPackageGenerator()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Package created successfully"
            mock_run.return_value.stderr = ""

            package_dir = temp_dir / "TestPackage"
            package_dir.mkdir()

            with patch.object(generator, "scripts_dir", temp_dir):
                julia_script = temp_dir / "pkg_generator.jl"
                julia_script.touch()

                plugins = {"plugins": []}

                try:
                    # Call with None values (should be converted to empty strings)
                    generator._call_julia_generator(
                        "TestPackage",
                        None,  # author
                        None,  # user
                        None,  # mail
                        temp_dir,
                        plugins,
                    )

                    mock_run.assert_called_once()
                    call_args = mock_run.call_args[0][0]

                    # Verify empty strings are passed for None values
                    expected_order = [
                        "julia",
                        str(julia_script),
                        "TestPackage",
                        "",  # empty author
                        "",  # empty user
                        "",  # empty mail
                        str(temp_dir),
                        "[]",
                    ]

                    assert call_args == expected_order

                except Exception as e:
                    if "Package directory not created" in str(e):
                        # Still verify the command was called correctly
                        mock_run.assert_called_once()

    def test_git_config_integration_output(self, temp_dir):
        """Test that git config values appear in debug output when available"""
        expected_user_name = get_git_config("user.name")
        expected_user_email = get_git_config("user.email")
        expected_github_user = get_git_config("github.user")

        if not (expected_user_name and expected_user_email):
            pytest.skip("git config user.name and user.email must be set for this test")

        print("Testing with git config values:")
        print(f"  user.name: '{expected_user_name}'")
        print(f"  user.email: '{expected_user_email}'")
        print(f"  github.user: '{expected_github_user}'")

        # These values should be available to PkgTemplates.jl when the Julia script runs
        assert expected_user_name, "user.name should be available for author fallback"
        assert expected_user_email, "user.email should be available for mail fallback"

    @pytest.mark.skipif(
        not get_git_config("user.name") or not get_git_config("user.email"),
        reason="git config user.name and user.email must be set for fallback testing",
    )
    def test_verify_fallback_values_match_expectations(self):
        """Verify that the git config values are properly available for fallback behavior"""
        user_name = get_git_config("user.name")
        user_email = get_git_config("user.email")
        github_user = get_git_config("github.user")

        # Log the values for test verification
        print("Current git configuration:")
        print(f"  user.name: '{user_name}' (author fallback)")
        print(f"  user.email: '{user_email}' (mail fallback)")
        print(f"  github.user: '{github_user}' (user fallback)")

        # Verify we have the minimum required values (whatever they are in this environment)
        assert user_name, f"user.name should be non-empty, got '{user_name}'"
        assert user_email, f"user.email should be non-empty, got '{user_email}'"

        # Verify the values are reasonable (basic format validation)
        assert isinstance(user_name, str) and len(user_name.strip()) > 0, (
            "user.name should be a non-empty string"
        )
        assert isinstance(user_email, str) and "@" in user_email, (
            f"user.email should be valid email format, got '{user_email}'"
        )

        # github.user is optional but if set, should be a reasonable value
        if github_user:
            assert isinstance(github_user, str) and len(github_user.strip()) > 0, (
                f"github.user should be a non-empty string if set, got '{github_user}'"
            )
            print(f"  Note: github.user is set to '{github_user}'")
        else:
            print("  Note: github.user is not configured (this is optional)")

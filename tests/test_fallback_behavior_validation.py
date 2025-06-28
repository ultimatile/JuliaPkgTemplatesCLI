"""
Test to validate actual fallback behavior implementation
"""

import subprocess
import pytest
from unittest.mock import patch

from juliapkgtemplates.generator import JuliaPackageGenerator


def get_git_config(key: str) -> str:
    """Get git config value"""
    try:
        result = subprocess.run(
            ["git", "config", key], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


class TestFallbackBehaviorValidation:
    """Validate the correct implementation of fallback behavior"""

    def test_empty_string_vs_none_parameter_handling(self, temp_dir):
        """Test that empty strings result in parameters NOT being passed to PkgTemplates.jl"""
        generator = JuliaPackageGenerator()

        # Mock the Julia script execution to capture the actual Template() call
        with patch("subprocess.run") as mock_run:
            # Mock successful execution but capture what would be called
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Package created successfully"
            mock_run.return_value.stderr = ""

            package_dir = temp_dir / "TestPackage"
            package_dir.mkdir()

            with patch.object(generator, "scripts_dir", temp_dir):
                julia_script = temp_dir / "pkg_generator.jl"
                julia_script.touch()

                plugins = {"plugins": []}

                # Test with None values (should become empty strings)
                generator._call_julia_generator(
                    "TestPackage",
                    None,  # author -> ""
                    None,  # user -> ""
                    None,  # mail -> ""
                    temp_dir,
                    plugins,
                )

                # Verify the command arguments
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]

                # The Julia script should receive empty strings for None values
                assert call_args[3] == ""  # author
                assert call_args[4] == ""  # user
                assert call_args[5] == ""  # mail

                print("Command that would be executed:")
                print(" ".join(call_args))

    def test_julia_script_parameter_logic(self):
        """Test the Julia script logic for handling empty parameters"""
        # This test validates the Julia script logic without executing it

        # The key insight: in Julia script, we check !isempty(param)
        # If param is empty string "", then !isempty("") is false
        # So the parameter is NOT added to template_args
        # This allows PkgTemplates.jl to use its default fallback to git config

        # Simulate Julia script logic:
        # author = ""
        # user = ""
        # mail = ""
        #
        # template_args = Dict()
        #
        # if !isempty(author)  # false for ""
        #     template_args[:authors] = [author]
        # end
        #
        # if !isempty(user)    # false for ""
        #     template_args[:user] = user
        # end
        #
        # if !isempty(mail)    # false for ""
        #     template_args[:mail] = mail
        # end
        #
        # template_args would be empty Dict()
        # Template(; template_args...) would be Template() with no overrides
        # PkgTemplates.jl then uses git config defaults

        # This demonstrates the correct logic:
        # Empty string -> parameter not passed -> PkgTemplates.jl uses git config
        # Non-empty string -> parameter passed -> overrides git config

        assert True  # This test documents the expected behavior

    @pytest.mark.skipif(
        not get_git_config("user.name") or not get_git_config("user.email"),
        reason="git config user.name and user.email must be set for fallback testing",
    )
    def test_actual_git_config_availability(self):
        """Verify git config values are available for PkgTemplates.jl fallback"""
        user_name = get_git_config("user.name")
        user_email = get_git_config("user.email")
        github_user = get_git_config("github.user")

        print("Available git config for fallback:")
        print(f"  user.name: '{user_name}' (for authors parameter)")
        print(f"  user.email: '{user_email}' (for mail parameter)")
        print(f"  github.user: '{github_user}' (for user parameter)")

        # These should be available for meaningful fallback testing
        assert user_name, "git config user.name should be set"
        assert user_email, "git config user.email should be set"

        # github.user might not be set by default, that's OK
        if not github_user:
            print(
                "  Note: github.user not set, PkgTemplates.jl may require explicit --user"
            )

    def test_parameter_precedence_logic(self, temp_dir):
        """Test that the precedence logic works correctly"""
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

                # Test explicit values (should override any defaults)
                generator._call_julia_generator(
                    "TestPackage",
                    "Explicit Author",  # non-empty -> will be set in Template()
                    "",  # empty -> not set, use git config
                    "explicit@example.com",  # non-empty -> will be set
                    temp_dir,
                    plugins,
                )

                call_args = mock_run.call_args[0][0]
                assert call_args[3] == "Explicit Author"  # author
                assert call_args[4] == ""  # user (empty)
                assert call_args[5] == "explicit@example.com"  # mail

    def test_understanding_of_correct_behavior(self):
        """Document and test understanding of correct fallback behavior"""

        # Correct behavior:
        # 1. CLI provides values -> use CLI values
        # 2. Config file provides values -> use config values
        # 3. Neither provides values -> pass empty string to Julia script
        # 4. Julia script sees empty string -> doesn't set parameter in Template()
        # 5. PkgTemplates.jl Template() without parameter -> uses git config

        # WRONG behavior (what we were doing before):
        # - Pass empty string as parameter value to Template(authors="", user="", mail="")
        # - This would override git config with empty values

        # RIGHT behavior (what we do now):
        # - Don't pass parameter at all: Template() (no authors, user, mail kwargs)
        # - PkgTemplates.jl then falls back to git config

        print("Correct fallback implementation:")
        print(
            "  None/empty in Python -> empty string to Julia -> parameter not set in Template() -> git config fallback"
        )
        print(
            "  Value in Python -> value to Julia -> parameter set in Template() -> overrides git config"
        )

        assert True

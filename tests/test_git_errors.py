"""
Test Git error handling and force flag behavior
"""

import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner

from juliapkgtemplates.cli import main
from juliapkgtemplates.generator import JuliaPackageGenerator


class TestGitErrorHandling:
    """Test error handling for Git repository conflicts"""
    
    def test_generator_raises_error_in_git_repo(self, tmp_path):
        """Test that generator raises error when in Git repo without force flag"""
        generator = JuliaPackageGenerator()
        
        with patch.object(generator, '_is_in_git_repository', return_value=True):
            with pytest.raises(RuntimeError) as exc_info:
                generator.create_package(
                    package_name="TestPackage",
                    author="Test Author",
                    output_dir=tmp_path,
                    force_in_git_repo=False
                )
            
            error_message = str(exc_info.value)
            assert "Cannot create package inside existing Git repository" in error_message
            assert "--force-in-git-repo" in error_message
    
    def test_generator_succeeds_with_force_flag(self, tmp_path):
        """Test that generator succeeds with force flag even in Git repo"""
        generator = JuliaPackageGenerator()
        
        with patch.object(generator, '_is_in_git_repository', return_value=True):
            with patch.object(generator, '_call_julia_generator') as mock_julia:
                # Mock successful Julia execution
                mock_julia.return_value = tmp_path / "TestPackage"
                
                with patch.object(generator, '_add_mise_config'):
                    result = generator.create_package(
                        package_name="TestPackage",
                        author="Test Author",
                        output_dir=tmp_path,
                        force_in_git_repo=True
                    )
                    
                    assert result == tmp_path / "TestPackage"
                    # Should have called Julia generator
                    mock_julia.assert_called_once()
    
    @patch('juliapkgtemplates.generator.subprocess.run')
    def test_cli_error_message_in_git_repo(self, mock_subprocess, tmp_path):
        """Test CLI shows proper error message in Git repo"""
        runner = CliRunner()
        
        # Mock being in a Git repository
        with patch('juliapkgtemplates.generator.JuliaPackageGenerator._is_in_git_repository', return_value=True):
            result = runner.invoke(main, [
                'create', 'TestPackage',
                '--author', 'Test Author',
                '--output-dir', str(tmp_path),
                '--license', 'MIT'
            ])
            
            assert result.exit_code == 1
            assert "Cannot create package inside existing Git repository" in result.output
            assert "--force-in-git-repo" in result.output
            
            # Should not have called Julia
            mock_subprocess.assert_not_called()
    
    @patch('juliapkgtemplates.generator.subprocess.run')
    def test_cli_succeeds_with_force_flag(self, mock_subprocess, tmp_path):
        """Test CLI succeeds with --force-in-git-repo flag"""
        runner = CliRunner()
        
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Package created successfully",
            stderr=""
        )
        
        # Create package directory for mock
        package_dir = tmp_path / "TestPackage"
        package_dir.mkdir()
        
        # Mock being in a Git repository
        with patch('juliapkgtemplates.generator.JuliaPackageGenerator._is_in_git_repository', return_value=True):
            result = runner.invoke(main, [
                'create', 'TestPackage',
                '--author', 'Test Author',
                '--output-dir', str(tmp_path),
                '--license', 'MIT',
                '--force-in-git-repo'
            ])
            
            assert result.exit_code == 0
            assert "Package created successfully" in result.output
            
            # Should have called Julia
            mock_subprocess.assert_called_once()
    
    def test_force_flag_enables_git_plugins(self):
        """Test that force flag enables Git plugins even in Git repo"""
        generator = JuliaPackageGenerator()
        
        # Test without force flag in Git repo
        plugins_no_force = generator._get_plugins(
            template="standard",
            license_type="MIT",
            with_docs=True,
            with_ci=True,
            with_codecov=True,
            formatter_style="nostyle",
            ssh=False,
            ignore_patterns=None,
            tests_aqua=False,
            tests_jet=False,
            tests_project=True,
            project_version=None,
            is_in_git_repo=True,
            force_in_git_repo=False
        )
        
        # Test with force flag in Git repo
        plugins_with_force = generator._get_plugins(
            template="standard",
            license_type="MIT",
            with_docs=True,
            with_ci=True,
            with_codecov=True,
            formatter_style="nostyle",
            ssh=False,
            ignore_patterns=None,
            tests_aqua=False,
            tests_jet=False,
            tests_project=True,
            project_version=None,
            is_in_git_repo=True,
            force_in_git_repo=True
        )
        
        # Without force: no Git-related plugins
        no_force_text = ' '.join(plugins_no_force["plugins"])
        assert 'Git(' not in no_force_text
        assert 'GitHubActions()' not in no_force_text
        assert 'Codecov()' not in no_force_text
        
        # With force: Git-related plugins included
        with_force_text = ' '.join(plugins_with_force["plugins"])
        assert 'Git(' in with_force_text
        assert 'GitHubActions()' in with_force_text
        assert 'Codecov()' in with_force_text
    
    def test_error_message_content(self, tmp_path):
        """Test that error message contains helpful information"""
        generator = JuliaPackageGenerator()
        
        with patch.object(generator, '_is_in_git_repository', return_value=True):
            with pytest.raises(RuntimeError) as exc_info:
                generator.create_package(
                    package_name="TestPackage",
                    author="Test Author",
                    output_dir=tmp_path,
                    force_in_git_repo=False
                )
            
            error_message = str(exc_info.value)
            
            # Check all expected parts of error message
            assert "Cannot create package inside existing Git repository" in error_message
            assert "PkgTemplates.jl" in error_message
            assert "--force-in-git-repo" in error_message
            assert "not recommended" in error_message
            assert "output directory outside" in error_message
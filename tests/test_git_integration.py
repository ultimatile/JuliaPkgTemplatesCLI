"""
Integration tests for Git-related functionality
"""

from unittest.mock import patch, Mock
from click.testing import CliRunner

from juliapkgtemplates.cli import main
from juliapkgtemplates.generator import JuliaPackageGenerator


class TestGitIntegration:
    """Test Git-related functionality with actual Git operations where possible"""
    
    def test_git_detection_outside_repo(self, isolated_dir):
        """Test Git detection works correctly outside Git repository"""
        generator = JuliaPackageGenerator()
        
        # Should not detect Git repo in isolated directory
        is_git = generator._is_in_git_repository(isolated_dir)
        assert not is_git
    
    def test_git_detection_inside_repo(self, test_git_repo):
        """Test Git detection works correctly inside Git repository"""
        generator = JuliaPackageGenerator()
        
        # Should detect Git repo
        is_git = generator._is_in_git_repository(test_git_repo)
        assert is_git
        
        # Should also detect Git repo in subdirectory
        subdir = test_git_repo / "subdir"
        subdir.mkdir()
        is_git_subdir = generator._is_in_git_repository(subdir)
        assert is_git_subdir
    
    @patch('juliapkgtemplates.generator.subprocess.run')
    def test_error_when_in_git_repo(self, mock_subprocess, test_git_repo):
        """Test that package creation fails in Git repository by default"""
        runner = CliRunner()
        
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Package created successfully",
            stderr=""
        )
        
        result = runner.invoke(main, [
            'create', 'TestPackage',
            '--author', 'Test Author',
            '--output-dir', str(test_git_repo),
            '--license', 'MIT'
        ])
        
        assert result.exit_code != 0
        assert "Cannot create package inside existing Git repository" in result.output
        assert "--force-in-git-repo" in result.output
    
    @patch('juliapkgtemplates.generator.subprocess.run')
    def test_force_flag_allows_git_repo_creation(self, mock_subprocess, test_git_repo):
        """Test that --force-in-git-repo allows creation in Git repository"""
        runner = CliRunner()
        
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Package created successfully",
            stderr=""
        )
        
        # Create package directory for mock
        package_dir = test_git_repo / "TestPackage"
        package_dir.mkdir()
        
        result = runner.invoke(main, [
            'create', 'TestPackage',
            '--author', 'Test Author',
            '--output-dir', str(test_git_repo),
            '--license', 'MIT',
            '--force-in-git-repo'
        ])
        
        assert result.exit_code == 0
        assert "Package created successfully" in result.output
        
        # Verify Julia was called with Git plugins
        call_args = mock_subprocess.call_args[0][0]
        plugins_str = [arg for arg in call_args if arg.startswith('[')][0]
        assert 'Git(' in plugins_str
    
    @patch('juliapkgtemplates.generator.subprocess.run')
    def test_git_options_in_isolated_environment(self, mock_subprocess, isolated_dir):
        """Test Git options work correctly in isolated environment"""
        runner = CliRunner()
        
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Package created successfully",
            stderr=""
        )
        
        # Create package directory for mock
        package_dir = isolated_dir / "TestPackage"
        package_dir.mkdir()
        
        result = runner.invoke(main, [
            'create', 'TestPackage',
            '--author', 'Test Author',
            '--output-dir', str(isolated_dir),
            '--license', 'MIT',
            '--ssh',
            '--ignore-patterns', '.vscode,.DS_Store',
            '--julia-version', 'v"1.10.9"',
            '--tests-aqua',
            '--tests-jet'
        ])
        
        assert result.exit_code == 0
        
        # Verify Julia was called with all requested options
        call_args = mock_subprocess.call_args[0][0]
        plugins_str = [arg for arg in call_args if arg.startswith('[')][0]
        
        # Check Git plugin with SSH and ignore patterns
        assert 'Git(' in plugins_str
        assert 'ssh=true' in plugins_str
        assert '.vscode' in plugins_str
        assert '.DS_Store' in plugins_str
        
        # Check Tests plugin with aqua and jet
        assert 'Tests(' in plugins_str
        assert 'aqua=true' in plugins_str
        assert 'jet=true' in plugins_str
        
        # Check Julia version was passed
        julia_version_arg = [arg for arg in call_args if arg.startswith('v"')]
        assert len(julia_version_arg) == 1
        assert julia_version_arg[0] == 'v"1.10.9"'
    
    def test_git_plugin_configuration_outside_repo(self):
        """Test that Git plugins are configured correctly outside Git repo"""
        generator = JuliaPackageGenerator()
        
        plugins = generator._get_plugins(
            template="full",
            license_type="MIT",
            with_docs=True,
            with_ci=True,
            with_codecov=True,
            formatter_style="nostyle",
            ssh=True,
            ignore_patterns=".vscode,.DS_Store",
            tests_aqua=True,
            tests_jet=True,
            tests_project=True,
            project_version="v0.1.0",
            is_in_git_repo=False,
            force_in_git_repo=False
        )
        
        plugin_strings = plugins["plugins"]
        plugin_text = ' '.join(plugin_strings)
        
        # Should include all plugins
        assert any('Git(' in p for p in plugin_strings)
        assert 'ssh=true' in plugin_text
        assert '.vscode' in plugin_text
        assert '.DS_Store' in plugin_text
        assert 'GitHubActions()' in plugin_text
        assert 'Codecov()' in plugin_text
        assert 'TagBot()' in plugin_text
        assert 'CompatHelper()' in plugin_text
        assert 'aqua=true' in plugin_text
        assert 'jet=true' in plugin_text
    
    def test_git_plugin_configuration_inside_repo_with_force(self):
        """Test that Git plugins work with force flag in Git repo"""
        generator = JuliaPackageGenerator()
        
        plugins = generator._get_plugins(
            template="full",
            license_type="MIT",
            with_docs=True,
            with_ci=True,
            with_codecov=True,
            formatter_style="nostyle",
            ssh=True,
            ignore_patterns=".vscode,.DS_Store",
            tests_aqua=True,
            tests_jet=True,
            tests_project=True,
            project_version="v0.1.0",
            is_in_git_repo=True,
            force_in_git_repo=True
        )
        
        plugin_strings = plugins["plugins"]
        plugin_text = ' '.join(plugin_strings)
        
        # Should include all plugins when forced
        assert any('Git(' in p for p in plugin_strings)
        assert 'ssh=true' in plugin_text
        assert 'GitHubActions()' in plugin_text
        assert 'Codecov()' in plugin_text
        assert 'TagBot()' in plugin_text
        assert 'CompatHelper()' in plugin_text
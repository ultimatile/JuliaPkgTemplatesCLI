"""
Tests for Generator module
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from jugen.generator import JuliaPackageGenerator


class TestJuliaPackageGenerator:
    """Test JuliaPackageGenerator class"""
    
    def test_init(self):
        """Test generator initialization"""
        generator = JuliaPackageGenerator()
        
        assert generator.templates_dir.name == "templates"
        assert generator.scripts_dir.name == "scripts"
        assert generator.jinja_env is not None
    
    def test_get_plugins_minimal(self):
        """Test plugin configuration for minimal template"""
        generator = JuliaPackageGenerator()
        
        plugins = generator._get_plugins(
            template="minimal",
            license_type="MIT",
            with_docs=True,
            with_ci=True,
            with_codecov=True
        )
        
        expected_plugins = [
            'License(; name="MIT")',
            "Git(; manifest=true)"
        ]
        
        assert plugins["plugins"] == expected_plugins
        assert plugins["license_type"] == "MIT"
        assert plugins["with_docs"] is True
    
    def test_get_plugins_standard(self):
        """Test plugin configuration for standard template"""
        generator = JuliaPackageGenerator()
        
        plugins = generator._get_plugins(
            template="standard",
            license_type="Apache-2.0",
            with_docs=True,
            with_ci=True,
            with_codecov=True
        )
        
        expected_plugins = [
            'License(; name="Apache-2.0")',
            "Git(; manifest=true)",
            "GitHubActions()",
            "Codecov()"
        ]
        
        assert plugins["plugins"] == expected_plugins
        assert plugins["license_type"] == "Apache-2.0"
    
    def test_get_plugins_standard_no_ci_codecov(self):
        """Test standard template without CI and Codecov"""
        generator = JuliaPackageGenerator()
        
        plugins = generator._get_plugins(
            template="standard",
            license_type="MIT",
            with_docs=True,
            with_ci=False,
            with_codecov=False
        )
        
        expected_plugins = [
            'License(; name="MIT")',
            "Git(; manifest=true)"
        ]
        
        assert plugins["plugins"] == expected_plugins
    
    def test_get_plugins_full(self):
        """Test plugin configuration for full template"""
        generator = JuliaPackageGenerator()
        
        plugins = generator._get_plugins(
            template="full",
            license_type="BSD-3-Clause",
            with_docs=True,
            with_ci=True,
            with_codecov=True
        )
        
        expected_plugins = [
            'License(; name="BSD-3-Clause")',
            "Git(; manifest=true)",
            "GitHubActions()",
            "Codecov()",
            "Documenter{GitHubActions}()",
            "TagBot()",
            "CompatHelper()"
        ]
        
        assert plugins["plugins"] == expected_plugins
    
    def test_get_plugins_full_no_docs(self):
        """Test full template without docs"""
        generator = JuliaPackageGenerator()
        
        plugins = generator._get_plugins(
            template="full",
            license_type="MIT",
            with_docs=False,
            with_ci=True,
            with_codecov=True
        )
        
        # Should not include Documenter
        assert "Documenter{GitHubActions}()" not in plugins["plugins"]
        assert "TagBot()" in plugins["plugins"]
        assert "CompatHelper()" in plugins["plugins"]
    
    def test_get_plugins_invalid_template(self):
        """Test invalid template raises error"""
        generator = JuliaPackageGenerator()
        
        with pytest.raises(ValueError, match="Unknown template type: invalid"):
            generator._get_plugins(
                template="invalid",
                license_type="MIT",
                with_docs=True,
                with_ci=True,
                with_codecov=True
            )
    
    @patch('subprocess.run')
    def test_call_julia_generator_success(self, mock_run, temp_dir):
        """Test successful Julia script call"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"
        author = "Test Author"
        plugins = {"plugins": ['License(; name="MIT")', "Git(; manifest=true)"]}
        
        # Mock successful subprocess call
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Package created successfully",
            stderr=""
        )
        
        # Create the expected package directory
        package_dir = temp_dir / package_name
        package_dir.mkdir()
        
        with patch.object(generator, 'scripts_dir', temp_dir):
            # Create mock Julia script
            julia_script = temp_dir / "pkg_generator.jl"
            julia_script.touch()
            
            result = generator._call_julia_generator(
                package_name, author, temp_dir, plugins
            )
            
            assert result == package_dir
            mock_run.assert_called_once()
            
            # Verify command structure
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "julia"
            assert str(julia_script) in call_args
            assert package_name in call_args
            assert author in call_args
    
    @patch('subprocess.run')
    def test_call_julia_generator_script_not_found(self, mock_run, temp_dir):
        """Test Julia script not found error"""
        generator = JuliaPackageGenerator()
        
        with patch.object(generator, 'scripts_dir', temp_dir):
            with pytest.raises(FileNotFoundError, match="Julia script not found"):
                generator._call_julia_generator(
                    "TestPackage", "Author", temp_dir, {"plugins": []}
                )
    
    @patch('subprocess.run')
    def test_call_julia_generator_julia_not_found(self, mock_run, temp_dir):
        """Test Julia not found error"""
        generator = JuliaPackageGenerator()
        
        mock_run.side_effect = FileNotFoundError()
        
        with patch.object(generator, 'scripts_dir', temp_dir):
            julia_script = temp_dir / "pkg_generator.jl"
            julia_script.touch()
            
            with pytest.raises(RuntimeError, match="Julia not found"):
                generator._call_julia_generator(
                    "TestPackage", "Author", temp_dir, {"plugins": []}
                )
    
    @patch('subprocess.run')
    def test_call_julia_generator_subprocess_error_with_package_dir(self, mock_run, temp_dir):
        """Test subprocess error but package directory exists"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"
        
        # Mock subprocess error
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["julia"], stdout="", stderr="Some warning"
        )
        
        # Create the package directory (successful despite stderr)
        package_dir = temp_dir / package_name
        package_dir.mkdir()
        
        with patch.object(generator, 'scripts_dir', temp_dir):
            julia_script = temp_dir / "pkg_generator.jl"
            julia_script.touch()
            
            result = generator._call_julia_generator(
                package_name, "Author", temp_dir, {"plugins": []}
            )
            
            assert result == package_dir
    
    @patch('subprocess.run')
    def test_call_julia_generator_real_error(self, mock_run, temp_dir):
        """Test real Julia script error"""
        generator = JuliaPackageGenerator()
        
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["julia"], stdout="Error creating package: PkgTemplates error", stderr=""
        )
        
        with patch.object(generator, 'scripts_dir', temp_dir):
            julia_script = temp_dir / "pkg_generator.jl"
            julia_script.touch()
            
            with pytest.raises(RuntimeError, match="Julia script failed"):
                generator._call_julia_generator(
                    "TestPackage", "Author", temp_dir, {"plugins": []}
                )
    
    def test_add_mise_config(self, temp_dir):
        """Test adding mise configuration"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"
        package_dir = temp_dir / f"{package_name}.jl"
        package_dir.mkdir()
        
        # Mock the Jinja2 template
        mock_template = Mock()
        mock_template.render.return_value = "[build]\ncommand = 'julia --project=. -e \"using Pkg; Pkg.test()\"'"
        
        with patch.object(generator.jinja_env, 'get_template', return_value=mock_template):
            generator._add_mise_config(package_dir, package_name)
        
        # Verify mise file was created
        mise_file = package_dir / ".mise.toml"
        assert mise_file.exists()
        
        # Verify template was called correctly
        mock_template.render.assert_called_once_with(
            package_name=package_name, 
            project_dir="."
        )
    
    @patch('subprocess.run')
    def test_check_dependencies_all_available(self, mock_run):
        """Test dependency check when all dependencies are available"""
        # Mock all commands to succeed
        mock_run.return_value = Mock(returncode=0)
        
        deps = JuliaPackageGenerator.check_dependencies()
        
        assert deps["julia"] is True
        assert deps["pkgtemplates"] is True
        assert deps["mise"] is True
        
        # Verify all expected commands were called
        assert mock_run.call_count == 3
    
    @patch('subprocess.run')
    def test_check_dependencies_julia_missing(self, mock_run):
        """Test dependency check when Julia is missing"""
        def side_effect(*args, **kwargs):
            if args[0][0] == "julia" and args[0][1] == "--version":
                raise FileNotFoundError()
            return Mock(returncode=0)
        
        mock_run.side_effect = side_effect
        
        deps = JuliaPackageGenerator.check_dependencies()
        
        assert deps["julia"] is False
        assert deps["pkgtemplates"] is True
        assert deps["mise"] is True
    
    @patch('subprocess.run')
    def test_check_dependencies_pkgtemplates_missing(self, mock_run):
        """Test dependency check when PkgTemplates.jl is missing"""
        def side_effect(*args, **kwargs):
            if "using PkgTemplates" in args[0]:
                raise subprocess.CalledProcessError(1, args[0])
            return Mock(returncode=0)
        
        mock_run.side_effect = side_effect
        
        deps = JuliaPackageGenerator.check_dependencies()
        
        assert deps["julia"] is True
        assert deps["pkgtemplates"] is False
        assert deps["mise"] is True
    
    @patch('jugen.generator.JuliaPackageGenerator._call_julia_generator')
    @patch('jugen.generator.JuliaPackageGenerator._add_mise_config')
    def test_create_package_integration(self, mock_mise, mock_julia, temp_dir):
        """Test full create_package workflow"""
        generator = JuliaPackageGenerator()
        package_name = "TestPackage"
        author = "Test Author"
        package_dir = temp_dir / f"{package_name}.jl"
        
        # Mock Julia generator to return package directory
        mock_julia.return_value = package_dir
        
        result = generator.create_package(
            package_name=package_name,
            author=author,
            output_dir=temp_dir,
            template="standard",
            license_type="MIT",
            with_docs=True,
            with_ci=True,
            with_codecov=True
        )
        
        assert result == package_dir
        
        # Verify Julia generator was called
        mock_julia.assert_called_once()
        call_args = mock_julia.call_args
        assert call_args[0][0] == package_name
        assert call_args[0][1] == author
        assert call_args[0][2] == temp_dir.resolve()
        
        # Verify plugins were configured correctly
        plugins = call_args[0][3]
        assert 'License(; name="MIT")' in plugins["plugins"]
        assert "GitHubActions()" in plugins["plugins"]
        assert "Codecov()" in plugins["plugins"]
        
        # Verify mise config was added
        mock_mise.assert_called_once_with(package_dir, package_name)
    
    def test_create_package_output_dir_creation(self, temp_dir):
        """Test that output directory is created if it doesn't exist"""
        generator = JuliaPackageGenerator()
        nonexistent_dir = temp_dir / "new_dir"
        
        with patch.object(generator, '_call_julia_generator') as mock_julia:
            with patch.object(generator, '_add_mise_config'):
                mock_julia.return_value = nonexistent_dir / "TestPackage.jl"
                
                generator.create_package(
                    package_name="TestPackage",
                    author="Author",
                    output_dir=nonexistent_dir
                )
                
                assert nonexistent_dir.exists()
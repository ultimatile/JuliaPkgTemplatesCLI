"""
Tests for CLI module
"""

import os
from pathlib import Path
from unittest.mock import patch, Mock

from juliapkgtemplates.cli import (
    main, 
    get_config_path, 
    load_config, 
    save_config,
    create,
    config as config_cmd
)


class TestConfigFunctions:
    """Test configuration-related functions"""
    
    def test_get_config_path_with_xdg_config_home(self, temp_config_dir):
        """Test config path with XDG_CONFIG_HOME set"""
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(temp_config_dir)}):
            config_path = get_config_path()
            assert config_path == temp_config_dir / "jtc" / "config.toml"
    
    def test_get_config_path_without_xdg_config_home(self):
        """Test config path without XDG_CONFIG_HOME"""
        with patch.dict(os.environ, {}, clear=True):
            config_path = get_config_path()
            expected = Path.home() / ".config" / "jtc" / "config.toml"
            assert config_path == expected

    def test_load_config_existing_file(self, temp_config_dir):
        """Test loading existing config file"""
        config_content = b'[default]\nauthor = "Test Author"\nlicense = "MIT"\n'
        config_file = temp_config_dir / "jtc.toml"
        config_file.write_bytes(config_content)
        
        with patch('juliapkgtemplates.cli.get_config_path', return_value=config_file):
            config = load_config()
            assert config["default"]["author"] == "Test Author"
            assert config["default"]["license"] == "MIT"
    
    def test_load_config_no_file(self, temp_config_dir):
        """Test loading config when file doesn't exist"""
        config_file = temp_config_dir / "nonexistent.toml"
        
        with patch('juliapkgtemplates.cli.get_config_path', return_value=config_file):
            config = load_config()
            assert config == {}
    
    def test_load_config_invalid_file(self, temp_config_dir, capsys):
        """Test loading invalid config file"""
        config_file = temp_config_dir / "invalid.toml"
        config_file.write_text("invalid toml content [")
        
        with patch('juliapkgtemplates.cli.get_config_path', return_value=config_file):
            config = load_config()
            assert config == {}
            captured = capsys.readouterr()
            assert "Warning: Error loading config file" in captured.err
    
    def test_save_config_with_tomli_w(self, temp_config_dir):
        """Test saving config with tomli_w"""
        config_file = temp_config_dir / "jtc.toml"
        test_config = {"default": {"author": "Test Author", "license": "MIT"}}
        
        with patch('juliapkgtemplates.cli.get_config_path', return_value=config_file):
            save_config(test_config)
            
        # Verify file was created and contains expected content
        assert config_file.exists()
        content = config_file.read_text()
        assert "author" in content
        assert "Test Author" in content
    
    def test_save_config_fallback(self, temp_config_dir):
        """Test saving config with fallback method"""
        config_file = temp_config_dir / "jtc.toml"
        test_config = {"default": {"author": "Test Author", "license": "MIT"}}
        
        with patch('juliapkgtemplates.cli.get_config_path', return_value=config_file):
            with patch('tomli_w.dump', side_effect=ImportError):
                save_config(test_config)
        
        # Verify fallback file was created
        assert config_file.exists()
        content = config_file.read_text()
        assert 'author = "Test Author"' in content
        assert 'license = "MIT"' in content


class TestCreateCommand:
    """Test create command"""
    
    def test_create_with_valid_package_name(self, cli_runner, temp_dir):
        """Test create command with valid package name"""
        with patch('juliapkgtemplates.cli.JuliaPackageGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance
            
            result = cli_runner.invoke(create, [
                'TestPackage',
                '--author', 'Test Author',
                '--output-dir', str(temp_dir)
            ])
            
            assert result.exit_code == 0
            assert "Creating Julia package: TestPackage" in result.output
            assert "Package created successfully" in result.output
            mock_instance.create_package.assert_called_once()
    
    def test_create_invalid_package_name_non_alpha_start(self, cli_runner):
        """Test create command with invalid package name (doesn't start with letter)"""
        result = cli_runner.invoke(create, [
            '123InvalidName',
            '--author', 'Test Author'
        ])
        
        assert result.exit_code == 1
        assert "Package name must start with a letter" in result.output
    
    def test_create_invalid_package_name_special_chars(self, cli_runner):
        """Test create command with invalid package name (special characters)"""
        result = cli_runner.invoke(create, [
            'Invalid@Name',
            '--author', 'Test Author'
        ])
        
        assert result.exit_code == 1
        assert "Package name must contain only letters, numbers, hyphens, and underscores" in result.output
    
    def test_create_with_config_defaults(self, cli_runner, temp_dir):
        """Test create command using config defaults"""
        with patch('juliapkgtemplates.cli.load_config') as mock_load_config:
            mock_load_config.return_value = {
                "default": {
                    "author": "Config Author",
                    "license": "Apache",
                    "template": "full"
                }
            }
            
            with patch('juliapkgtemplates.cli.JuliaPackageGenerator') as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance
                
                result = cli_runner.invoke(create, [
                    'TestPackage',
                    '--output-dir', str(temp_dir)
                ])
                
                assert result.exit_code == 0
                assert "Author: Config Author" in result.output
                mock_instance.create_package.assert_called_once()
                
                # Check that config values were used
                call_args = mock_instance.create_package.call_args
                assert call_args[1]['author'] == "Config Author"
                assert call_args[1]['license_type'] == "Apache"
                assert call_args[1]['template'] == "full"
    
    def test_create_no_author_delegates_to_pkgtemplates(self, cli_runner, temp_dir):
        """Test create command delegates to PkgTemplates.jl when no author provided"""
        with patch('juliapkgtemplates.cli.load_config', return_value={}):
            with patch('juliapkgtemplates.cli.JuliaPackageGenerator') as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance
                
                result = cli_runner.invoke(create, [
                    'TestPackage',
                    '--output-dir', str(temp_dir)
                ])
                
                assert result.exit_code == 0
                assert "Author: None" in result.output
                # Verify that create_package was called with author=None, letting PkgTemplates.jl handle it
                mock_instance.create_package.assert_called_once()
                call_args = mock_instance.create_package.call_args
                assert call_args.kwargs['author'] is None
    
    def test_create_generator_error(self, cli_runner, temp_dir):
        """Test create command handles generator errors"""
        with patch('juliapkgtemplates.cli.JuliaPackageGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.side_effect = RuntimeError("Julia not found")
            mock_generator.return_value = mock_instance
            
            result = cli_runner.invoke(create, [
                'TestPackage',
                '--author', 'Test Author',
                '--output-dir', str(temp_dir)
            ])
            
            assert result.exit_code == 1
            assert "Error: Julia not found" in result.output


class TestConfigCommand:
    """Test config command"""
    
    def test_config_set_author(self, cli_runner, temp_config_dir):
        """Test config command sets author"""
        config_file = temp_config_dir / "jtc.toml"
        
        with patch('juliapkgtemplates.cli.get_config_path', return_value=config_file):
            with patch('juliapkgtemplates.cli.load_config', return_value={}):
                result = cli_runner.invoke(config_cmd, [
                    '--author', 'New Author'
                ])
                
                assert result.exit_code == 0
                assert "Set default author: New Author" in result.output
                assert "Configuration saved" in result.output
    
    def test_config_set_multiple_options(self, cli_runner, temp_config_dir):
        """Test config command sets multiple options"""
        config_file = temp_config_dir / "jtc.toml"
        
        with patch('juliapkgtemplates.cli.get_config_path', return_value=config_file):
            with patch('juliapkgtemplates.cli.load_config', return_value={}):
                result = cli_runner.invoke(config_cmd, [
                    '--author', 'New Author',
                    '--license', 'Apache',
                    '--template', 'full'
                ])
                
                assert result.exit_code == 0
                assert "Set default author: New Author" in result.output
                assert "Set default license: Apache" in result.output
                assert "Set default template: full" in result.output
    
    def test_config_update_existing_config(self, cli_runner, temp_config_dir):
        """Test config command updates existing configuration"""
        config_file = temp_config_dir / "jtc.toml"
        existing_config = {
            "default": {
                "author": "Old Author",
                "license": "MIT"
            }
        }
        
        with patch('juliapkgtemplates.cli.get_config_path', return_value=config_file):
            with patch('juliapkgtemplates.cli.load_config', return_value=existing_config):
                with patch('juliapkgtemplates.cli.save_config') as mock_save:
                    result = cli_runner.invoke(config_cmd, [
                        '--author', 'Updated Author'
                    ])
                    
                    assert result.exit_code == 0
                    mock_save.assert_called_once()
                    saved_config = mock_save.call_args[0][0]
                    assert saved_config["default"]["author"] == "Updated Author"
                    assert saved_config["default"]["license"] == "MIT"  # preserved


class TestMainCommand:
    """Test main command group"""
    
    def test_main_version(self, cli_runner):
        """Test main command shows version"""
        result = cli_runner.invoke(main, ['--version'])
        assert result.exit_code == 0
    
    def test_main_help(self, cli_runner):
        """Test main command shows help"""
        result = cli_runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Julia package generator" in result.output
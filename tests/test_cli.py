"""
Tests for CLI module
"""

import os
from unittest.mock import patch, Mock

from juliapkgtemplates.cli import (
    main,
    get_config_path,
    load_config,
    save_config,
    create,
    config as config_cmd,
)


class TestConfigFunctions:
    """Test configuration-related functions"""

    def test_get_config_path_with_xdg_config_home(self, temp_config_dir):
        """Test config path with XDG_CONFIG_HOME set"""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(temp_config_dir)}):
            config_path = get_config_path()
            assert config_path == temp_config_dir / "jtc" / "config.toml"

    def test_get_config_path_without_xdg_config_home(self, temp_config_dir):
        """Test config path without XDG_CONFIG_HOME"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.home", return_value=temp_config_dir):
                config_path = get_config_path()
                expected = temp_config_dir / ".config" / "jtc" / "config.toml"
                assert config_path == expected

    def test_load_config_existing_file(self, temp_config_dir):
        """Test loading existing config file"""
        config_content = b'[default]\nauthor = "Test Author"\nlicense = "MIT"\n'
        config_file = temp_config_dir / "config.toml"
        config_file.write_bytes(config_content)

        with patch("juliapkgtemplates.cli.get_config_path", return_value=config_file):
            config = load_config()
            assert config["default"]["author"] == "Test Author"
            assert config["default"]["license"] == "MIT"

    def test_load_config_no_file(self, temp_config_dir):
        """Test loading config when file doesn't exist"""
        config_file = temp_config_dir / "nonexistent.toml"

        with patch("juliapkgtemplates.cli.get_config_path", return_value=config_file):
            config = load_config()
            assert config == {}

    def test_load_config_invalid_file(self, temp_config_dir, capsys):
        """Test loading invalid config file"""
        config_file = temp_config_dir / "invalid.toml"
        config_file.write_text("invalid toml content [")

        with patch("juliapkgtemplates.cli.get_config_path", return_value=config_file):
            config = load_config()
            assert config == {}
            captured = capsys.readouterr()
            assert "Warning: Error loading config file" in captured.err

    def test_save_config_with_tomli_w(self, temp_config_dir):
        """Test saving config with tomli_w"""
        config_file = temp_config_dir / "config.toml"
        test_config = {"default": {"author": "Test Author", "license": "MIT"}}

        with patch("juliapkgtemplates.cli.get_config_path", return_value=config_file):
            save_config(test_config)

        # Verify file was created and contains expected content
        assert config_file.exists()
        content = config_file.read_text()
        assert "author" in content
        assert "Test Author" in content

    def test_save_config_fallback(self, temp_config_dir):
        """Test saving config with fallback method"""
        config_file = temp_config_dir / "config.toml"
        test_config = {"default": {"author": "Test Author", "license": "MIT"}}

        with patch("juliapkgtemplates.cli.get_config_path", return_value=config_file):
            with patch("tomli_w.dump", side_effect=ImportError):
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
        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            result = cli_runner.invoke(
                create,
                [
                    "TestPackage",
                    "--author",
                    "Test Author",
                    "--user",
                    "testuser",
                    "--mail",
                    "test@example.com",
                    "--output-dir",
                    str(temp_dir),
                ],
            )

            assert result.exit_code == 0
            assert "Package 'TestPackage' created successfully" in result.output
            mock_instance.create_package.assert_called_once()

    def test_create_invalid_package_name_non_alpha_start(self, cli_runner):
        """Test create command with invalid package name (doesn't start with letter)"""
        result = cli_runner.invoke(
            create,
            [
                "123InvalidName",
                "--author",
                "Test Author",
                "--user",
                "testuser",
                "--mail",
                "test@example.com",
            ],
        )

        assert result.exit_code == 1
        assert "Package name must start with a letter" in result.output

    def test_create_invalid_package_name_special_chars(self, cli_runner):
        """Test create command with invalid package name (special characters)"""
        result = cli_runner.invoke(
            create,
            [
                "Invalid@Name",
                "--author",
                "Test Author",
                "--user",
                "testuser",
                "--mail",
                "test@example.com",
            ],
        )

        assert result.exit_code == 1
        assert (
            "Package name must contain only letters, numbers, hyphens, and underscores"
            in result.output
        )

    def test_create_with_jl_suffix(self, cli_runner, temp_dir):
        """Test create command with valid package name ending in .jl"""
        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            result = cli_runner.invoke(
                create,
                [
                    "TestPackage.jl",
                    "--author",
                    "Test Author",
                    "--user",
                    "testuser",
                    "--mail",
                    "test@example.com",
                    "--output-dir",
                    str(temp_dir),
                ],
            )

            assert result.exit_code == 0
            assert "Package 'TestPackage.jl' created successfully" in result.output
            mock_instance.create_package.assert_called_once()

    def test_create_invalid_jl_suffix_name(self, cli_runner):
        """Test create command with invalid base name but .jl suffix"""
        result = cli_runner.invoke(
            create,
            [
                "123Invalid.jl",
                "--author",
                "Test Author",
                "--user",
                "testuser",
                "--mail",
                "test@example.com",
            ],
        )

        assert result.exit_code == 1
        assert "Package name must start with a letter" in result.output

    def test_create_with_config_defaults(self, cli_runner, temp_dir):
        """Test create command using config defaults"""
        with patch("juliapkgtemplates.cli.load_config") as mock_load_config:
            mock_load_config.return_value = {
                "default": {
                    "author": "Config Author",
                    "user": "configuser",
                    "mail": "config@example.com",
                    "license": "Apache",
                }
            }

            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create, ["TestPackage", "--output-dir", str(temp_dir)]
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Check that config values were used
                call_args = mock_instance.create_package.call_args
                assert call_args[0][1] == "Config Author"  # author (position 1)
                assert call_args[0][2] == "configuser"  # user (position 2)
                assert call_args[0][3] == "config@example.com"  # mail (position 3)
                # License is now handled as plugin option, not license_type field
                config = call_args[0][5]  # PackageConfig is position 5
                assert "License" in config.plugin_options
                assert config.plugin_options["License"]["name"] == "Apache"

    def test_create_no_author_delegates_to_pkgtemplates(self, cli_runner, temp_dir):
        """Test create command delegates to PkgTemplates.jl when no author provided"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create, ["TestPackage", "--output-dir", str(temp_dir)]
                )

                assert result.exit_code == 0
                # Verify that create_package was called with author=None, user=None, and mail=None, letting PkgTemplates.jl handle it
                mock_instance.create_package.assert_called_once()
                call_args = mock_instance.create_package.call_args
                assert call_args[0][1] is None  # author (position 1)
                assert call_args[0][2] is None  # user (position 2)
                assert call_args[0][3] is None  # mail (position 3)

    def test_create_with_cli_license_option(self, cli_runner, temp_dir):
        """Test create command with --license option (using non-MIT license to verify it works)"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--license",
                        "Apache",
                        "--output-dir",
                        str(temp_dir),
                    ],
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Check that license was passed correctly
                call_args = mock_instance.create_package.call_args
                config = call_args[0][5]  # PackageConfig is position 5
                # License is now handled as plugin option
                assert "License" in config.plugin_options
                assert config.plugin_options["License"]["name"] == "Apache"

    def test_create_with_cli_license_ptj_native(self, cli_runner, temp_dir):
        """Test create command with PkgTemplates.jl native license identifier"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--license",
                        "GPL-3.0+",
                        "--output-dir",
                        str(temp_dir),
                    ],
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Check that PTJ native license passes through
                call_args = mock_instance.create_package.call_args
                config = call_args[0][5]  # PackageConfig is position 5
                # License is now handled as plugin option
                assert "License" in config.plugin_options
                assert config.plugin_options["License"]["name"] == "GPL-3.0+"

    def test_create_with_config_license_generates_license_plugin(
        self, cli_runner, temp_dir, isolated_config
    ):
        """Test that config file license setting actually generates License plugin in Julia code"""
        from juliapkgtemplates.cli import save_config
        from juliapkgtemplates.generator import JuliaPackageGenerator, PackageConfig

        # Set license in isolated config
        config_data = {"default": {"license_type": "Apache"}}
        save_config(config_data)

        # Create package and check generated Julia code
        generator = JuliaPackageGenerator()
        julia_code = generator.generate_julia_code(
            "TestPackage",
            None,
            None,
            None,
            temp_dir,
            PackageConfig.from_dict({"license_type": "Apache"}),
        )

        # Verify License plugin is generated
        assert 'License(; name="ASL")' in julia_code

    def test_create_with_license_simple_format(self, cli_runner, temp_dir):
        """Test create command with --license simple format (direct license name)"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--license",
                        "Apache",
                        "--output-dir",
                        str(temp_dir),
                    ],
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Check that License plugin options were set correctly
                call_args = mock_instance.create_package.call_args
                config = call_args[0][5]  # PackageConfig is position 5
                assert "License" in config.plugin_options
                assert config.plugin_options["License"]["name"] == "Apache"

    def test_create_with_license_keyvalue_format(self, cli_runner, temp_dir):
        """Test create command with --license key=value format"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--license",
                        "name=MIT path=./my-license.txt",
                        "--output-dir",
                        str(temp_dir),
                    ],
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Check that License plugin options were set correctly
                call_args = mock_instance.create_package.call_args
                config = call_args[0][5]  # PackageConfig is position 5
                assert "License" in config.plugin_options
                assert config.plugin_options["License"]["name"] == "MIT"
                assert config.plugin_options["License"]["path"] == "./my-license.txt"

    def test_create_license_plugin_generation_simple_format(self, temp_dir):
        """Test that simple license format generates correct License plugin in Julia code"""
        from juliapkgtemplates.generator import JuliaPackageGenerator, PackageConfig

        # Test simple format
        generator = JuliaPackageGenerator()
        config = PackageConfig.from_dict(
            {"plugin_options": {"License": {"name": "Apache"}}}
        )
        julia_code = generator.generate_julia_code(
            "TestPackage", None, None, None, temp_dir, config
        )

        # Verify License plugin is generated with correct mapping
        assert 'License(; name="ASL")' in julia_code

    def test_create_license_plugin_generation_keyvalue_format(self, temp_dir):
        """Test that key=value license format generates correct License plugin in Julia code"""
        from juliapkgtemplates.generator import JuliaPackageGenerator, PackageConfig

        # Test key=value format with multiple options
        generator = JuliaPackageGenerator()
        config = PackageConfig.from_dict(
            {
                "plugin_options": {
                    "License": {
                        "name": "MIT",
                        "path": "./my-license.txt",
                        "destination": "LICENSE.txt",
                    }
                }
            }
        )
        julia_code = generator.generate_julia_code(
            "TestPackage", None, None, None, temp_dir, config
        )

        # Verify License plugin is generated with all options
        assert (
            'License(; name="MIT", path="./my-license.txt", destination="LICENSE.txt")'
            in julia_code
        )

    def test_create_with_custom_mise_filename_base(self, cli_runner, temp_dir):
        """Test create command with custom mise filename base"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--output-dir",
                        str(temp_dir),
                        "--mise-filename-base",
                        "mise",
                    ],
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Check that custom mise filename base was passed in config
                call_args = mock_instance.create_package.call_args
                config = call_args[0][5]  # PackageConfig (position 5)
                assert config.mise_filename_base == "mise"

    def test_create_with_no_mise(self, cli_runner, temp_dir):
        """Test create command with --no-mise option"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--output-dir",
                        str(temp_dir),
                        "--no-mise",
                    ],
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Check that mise is disabled in config
                call_args = mock_instance.create_package.call_args
                config = call_args[0][5]  # PackageConfig (position 5)
                assert config.with_mise is False

    def test_create_with_mise_enabled(self, cli_runner, temp_dir):
        """Test create command with --with-mise option (default behavior)"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage"
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--output-dir",
                        str(temp_dir),
                        "--with-mise",
                    ],
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Check that mise is enabled in config
                call_args = mock_instance.create_package.call_args
                config = call_args[0][5]  # PackageConfig (position 5)
                assert config.with_mise is True


class TestConfigCommand:
    """Test config command"""

    def test_config_set_author(self, cli_runner, isolated_config):
        """Test config set command sets author"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(config_cmd, ["set", "--author", "New Author"])

            assert result.exit_code == 0
            assert "Set default author: New Author" in result.output
            assert "Configuration saved" in result.output

    def test_config_set_user(self, cli_runner, isolated_config):
        """Test config set command sets user"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(config_cmd, ["set", "--user", "newuser"])

            assert result.exit_code == 0
            assert "Set default user: newuser" in result.output
            assert "Configuration saved" in result.output

    def test_config_set_mail(self, cli_runner, isolated_config):
        """Test config set command sets mail"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(config_cmd, ["set", "--mail", "new@example.com"])

            assert result.exit_code == 0
            assert "Set default mail: new@example.com" in result.output
            assert "Configuration saved" in result.output

    def test_config_set_mise_filename_base(self, cli_runner, isolated_config):
        """Test config set command sets mise filename base"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(
                config_cmd, ["set", "--mise-filename-base", "mise"]
            )

            assert result.exit_code == 0
            assert "Set default mise_filename_base: mise" in result.output
            assert "Configuration saved" in result.output

    def test_config_set_with_mise(self, cli_runner, isolated_config):
        """Test config set command sets with_mise option"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(config_cmd, ["set", "--with-mise"])

            assert result.exit_code == 0
            assert "Set default with_mise: True" in result.output
            assert "Configuration saved" in result.output

    def test_config_set_no_mise(self, cli_runner, isolated_config):
        """Test config set command sets no_mise option"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(config_cmd, ["set", "--no-mise"])

            assert result.exit_code == 0
            assert "Set default with_mise: False" in result.output
            assert "Configuration saved" in result.output

    def test_config_show(self, cli_runner, isolated_config):
        """Test config show command displays configuration"""
        mock_config = {"default": {"author": "Test Author", "license_type": "MIT"}}
        with patch("juliapkgtemplates.cli.load_config", return_value=mock_config):
            result = cli_runner.invoke(config_cmd, ["show"])

            assert result.exit_code == 0
            assert "Current configuration:" in result.output
            assert "author: 'Test Author'" in result.output
            assert "license_type: 'MIT'" in result.output

    def test_config_bare_command_shows_config(self, cli_runner, isolated_config):
        """Test bare config command shows configuration (alias for show)"""
        mock_config = {"default": {"author": "Test Author", "license_type": "MIT"}}
        with patch("juliapkgtemplates.cli.load_config", return_value=mock_config):
            result = cli_runner.invoke(config_cmd, [])

            assert result.exit_code == 0
            assert "Current configuration:" in result.output
            assert "author: 'Test Author'" in result.output
            assert "license_type: 'MIT'" in result.output

    def test_config_with_options_sets_config(self, cli_runner, isolated_config):
        """Test config command with options behaves like config set"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(config_cmd, ["--author", "New Author"])

            assert result.exit_code == 0
            assert "Set default author: New Author" in result.output
            assert "Configuration saved" in result.output

    def test_config_with_plugin_options_sets_config(self, cli_runner, isolated_config):
        """Test config command with plugin options behaves like config set"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(config_cmd, ["--git", "ssh=true"])

            assert result.exit_code == 0
            assert "Set default Git.ssh: True" in result.output
            assert "Configuration saved" in result.output


class TestMainCommand:
    """Test main command group"""

    def test_main_version(self, cli_runner):
        """Test main command shows version"""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_main_help(self, cli_runner):
        """Test main command shows help"""
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Julia package generator" in result.output

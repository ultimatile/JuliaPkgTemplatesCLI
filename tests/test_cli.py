"""
Tests for CLI module
"""

import os
from unittest.mock import patch, Mock

from juliapkgtemplates.cli import (
    main,
    get_config_file_path,
    load_config,
    save_config,
    create,
    config as config_cmd,
    set_config_file,
)


class TestConfigFunctions:
    """Test configuration-related functions"""

    def test_get_config_file_path_with_xdg_config_home(self, temp_config_dir):
        """Test config file with XDG_CONFIG_HOME set"""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(temp_config_dir)}):
            config_path = get_config_file_path()
            assert config_path == temp_config_dir / "jtc" / "config.toml"

    def test_get_config_file_path_without_xdg_config_home(self, temp_config_dir):
        """Test config file without XDG_CONFIG_HOME"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.home", return_value=temp_config_dir):
                config_path = get_config_file_path()
                expected = temp_config_dir / ".config" / "jtc" / "config.toml"
                assert config_path == expected

    def test_load_config_existing_file(self, temp_config_dir):
        """Test loading existing config file"""
        config_content = b'[default]\nauthor = "Test Author"\nlicense = "MIT"\n'
        config_file = temp_config_dir / "config.toml"
        config_file.write_bytes(config_content)

        with patch(
            "juliapkgtemplates.cli.get_config_file_path", return_value=config_file
        ):
            config = load_config()
            assert config["default"]["author"] == "Test Author"
            assert config["default"]["license"] == "MIT"

    def test_load_config_no_file(self, temp_config_dir):
        """Test loading config when file doesn't exist"""
        config_file = temp_config_dir / "nonexistent.toml"

        with patch(
            "juliapkgtemplates.cli.get_config_file_path", return_value=config_file
        ):
            config = load_config()
            assert config == {}

    def test_load_config_invalid_file(self, temp_config_dir, capsys):
        """Test loading invalid config file"""
        config_file = temp_config_dir / "invalid.toml"
        config_file.write_text("invalid toml content [")

        with patch(
            "juliapkgtemplates.cli.get_config_file_path", return_value=config_file
        ):
            config = load_config()
            assert config == {}
            captured = capsys.readouterr()
            assert "Warning: Error loading config file" in captured.err

    def test_save_config_with_tomli_w(self, temp_config_dir):
        """Test saving config with tomli_w"""
        config_file = temp_config_dir / "config.toml"
        test_config = {"default": {"author": "Test Author", "license": "MIT"}}

        with patch(
            "juliapkgtemplates.cli.get_config_file_path", return_value=config_file
        ):
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

        with patch(
            "juliapkgtemplates.cli.get_config_file_path", return_value=config_file
        ):
            with patch("tomli_w.dump", side_effect=ImportError):
                save_config(test_config)

        # Verify fallback file was created
        assert config_file.exists()
        content = config_file.read_text()
        assert 'author = "Test Author"' in content
        assert 'license = "MIT"' in content

    def test_set_config_file(self, temp_config_dir):
        """Test setting custom config file"""
        custom_config_file = temp_config_dir / "custom.toml"

        # Set custom path
        set_config_file(str(custom_config_file))

        # Verify custom path is returned when requesting config location
        config_path = get_config_file_path()
        assert config_path.resolve() == custom_config_file.resolve()

    def test_set_config_file_none(self, temp_config_dir):
        """Test resetting config file to default"""
        custom_config_file = temp_config_dir / "custom.toml"

        # Set custom path first
        set_config_file(str(custom_config_file))

        # Reset to default
        set_config_file(None)

        # Confirm fallback to standard XDG location when custom path is cleared
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(temp_config_dir)}):
            config_path = get_config_file_path()
            assert config_path == temp_config_dir / "jtc" / "config.toml"

    def test_save_config_with_custom_path(self, temp_config_dir):
        """Test saving config to custom path creates parent directories"""
        custom_dir = temp_config_dir / "custom" / "subdir"
        custom_config_file = custom_dir / "my-config.toml"
        test_config = {"default": {"author": "Test Author"}}

        # Set custom path
        set_config_file(str(custom_config_file))

        # Exercise directory creation logic when saving to non-existent path
        save_config(test_config)

        # Confirm config file exists at expected location with correct content
        assert custom_config_file.exists()
        content = custom_config_file.read_text()
        assert 'author = "Test Author"' in content


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
                assert call_args[0][1] == [
                    "Config Author"
                ]  # author (position 1) - now a list
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

    def test_create_with_config_plugin_options_no_cli_args(self, cli_runner, temp_dir):
        """Test create command applies plugin options from config when no CLI plugin args provided"""
        mock_config = {
            "default": {
                "author": "Config Author",
                # Plugin options in nested format (like real config files)
                "formatter": {"indent": 4, "margin": 120},
                "git": {"ssh": True, "manifest": False},
                "documenter": {
                    "logo": "path/to/logo.png",
                    "canonical_url": "https://example.com",
                },
            }
        }

        with patch("juliapkgtemplates.cli.load_config", return_value=mock_config):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
                mock_generator.return_value = mock_instance

                # Call create WITHOUT any plugin CLI args - should use config values
                result = cli_runner.invoke(
                    create,
                    ["TestPackage", "--output-dir", str(temp_dir)],
                )

                assert result.exit_code == 0
                mock_instance.create_package.assert_called_once()

                # Verify that config plugin options were applied
                call_args = mock_instance.create_package.call_args
                config = call_args[0][5]  # PackageConfig is position 5

                # Check that plugin options from config were loaded
                assert "formatter" in config.plugin_options
                assert config.plugin_options["formatter"]["indent"] == 4
                assert config.plugin_options["formatter"]["margin"] == 120

                assert "git" in config.plugin_options
                assert config.plugin_options["git"]["ssh"]
                assert not config.plugin_options["git"]["manifest"]

                assert "documenter" in config.plugin_options
                assert config.plugin_options["documenter"]["logo"] == "path/to/logo.png"
                assert (
                    config.plugin_options["documenter"]["canonical_url"]
                    == "https://example.com"
                )

    def test_create_dry_run_with_config_defaults(self, cli_runner, temp_dir):
        """Test dry-run command applies config defaults properly"""
        mock_config = {
            "default": {
                "author": "Config Author",
                "user": "configuser",
                "mail": "config@example.com",
                "license": "Apache",
                "julia_version": "1.10.9",
                # Plugin options in nested format
                "formatter": {"indent": 4, "margin": 120},
            }
        }

        with patch("juliapkgtemplates.cli.load_config", return_value=mock_config):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.generate_julia_code.return_value = (
                    "# Mock Julia code with config values"
                )
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    ["TestPackage", "--dry-run", "--output-dir", str(temp_dir)],
                )

                assert result.exit_code == 0
                assert "# Mock Julia code with config values" in result.output

                # Verify that generate_julia_code was called with config values
                mock_instance.generate_julia_code.assert_called_once()
                call_args = mock_instance.generate_julia_code.call_args

                # Check that config values were used
                assert call_args[0][1] == ["Config Author"]  # author - now a list
                assert call_args[0][2] == "configuser"  # user
                assert call_args[0][3] == "config@example.com"  # mail
                # output_dir is position 4, PackageConfig is position 5

                # Check PackageConfig contains config values
                config = call_args[0][5]  # PackageConfig is position 5
                assert config.julia_version == "1.10.9"  # julia_version in config
                assert "License" in config.plugin_options
                assert config.plugin_options["License"]["name"] == "Apache"
                assert "formatter" in config.plugin_options
                assert config.plugin_options["formatter"]["indent"] == 4
                assert config.plugin_options["formatter"]["margin"] == 120

    def test_create_dry_run_cli_overrides_config_defaults(self, cli_runner, temp_dir):
        """Test dry-run command CLI options override config defaults"""
        mock_config = {
            "default": {
                "author": "Config Author",
                "license": "GPL3",
            }
        }

        with patch("juliapkgtemplates.cli.load_config", return_value=mock_config):
            with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
                mock_instance = Mock()
                mock_instance.generate_julia_code.return_value = (
                    "# Mock Julia code with CLI overrides"
                )
                mock_generator.return_value = mock_instance

                result = cli_runner.invoke(
                    create,
                    [
                        "TestPackage",
                        "--dry-run",
                        "--author",
                        "CLI Author",
                        "--license",
                        "MIT",
                        "--output-dir",
                        str(temp_dir),
                    ],
                )

                assert result.exit_code == 0

                # Verify that CLI values override config values
                call_args = mock_instance.generate_julia_code.call_args
                assert call_args[0][1] == [
                    "CLI Author"
                ]  # author overridden - now a list

                config = call_args[0][5]
                assert (
                    config.plugin_options["License"]["name"] == "MIT"
                )  # license overridden

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

    def test_dry_run_with_license_flag_only(self, cli_runner, temp_dir):
        """Dry-run should allow --license without value and emit License() plugin"""
        with patch("juliapkgtemplates.cli.load_config", return_value={}):
            result = cli_runner.invoke(
                create,
                [
                    "TestPackage",
                    "--dry-run",
                    "--license",
                    "--output-dir",
                    str(temp_dir),
                ],
            )

        assert result.exit_code == 0
        assert "License()" in result.output
        assert "License(;" not in result.output

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

    def test_create_with_custom_config_file(self, cli_runner, temp_dir):
        """Test create command with custom config file"""
        custom_config_file = temp_dir / "custom-config.toml"
        custom_config_file.write_text(
            '[default]\nauthor = "Custom Author"\nuser = "custom-user"\n'
        )

        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_generator:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_generator.return_value = mock_instance

            result = cli_runner.invoke(
                create,
                [
                    "TestPackage",
                    "--config-file",
                    str(custom_config_file),
                    "--output-dir",
                    str(temp_dir),
                ],
            )

            assert result.exit_code == 0
            assert "Package 'TestPackage' created successfully" in result.output
            mock_instance.create_package.assert_called_once()

            # Confirm values from custom config file are applied to package creation
            call_args = mock_instance.create_package.call_args
            author_arg = call_args[0][1]  # author argument (position 1)
            user_arg = call_args[0][2]  # user argument (position 2)
            assert author_arg == ["Custom Author"]
            assert user_arg == "custom-user"


class TestConfigCommand:
    """Test config command"""

    def test_config_set_author(self, cli_runner, isolated_config):
        """Test config set command sets author"""
        result = cli_runner.invoke(
            config_cmd,
            ["set", "--config-file", str(isolated_config), "--author", "New Author"],
        )

        assert result.exit_code == 0
        assert "Set default author: New Author" in result.output
        assert "Configuration saved" in result.output
        config = load_config()
        assert config["default"]["author"] == "New Author"

    def test_config_set_user(self, cli_runner, isolated_config):
        """Test config set command sets user"""
        result = cli_runner.invoke(
            config_cmd,
            ["set", "--config-file", str(isolated_config), "--user", "newuser"],
        )

        assert result.exit_code == 0
        assert "Set default user: newuser" in result.output
        assert "Configuration saved" in result.output
        config = load_config()
        assert config["default"]["user"] == "newuser"

    def test_config_set_mail(self, cli_runner, isolated_config):
        """Test config set command sets mail"""
        result = cli_runner.invoke(
            config_cmd,
            [
                "set",
                "--config-file",
                str(isolated_config),
                "--mail",
                "new@example.com",
            ],
        )

        assert result.exit_code == 0
        assert "Set default mail: new@example.com" in result.output
        assert "Configuration saved" in result.output
        config = load_config()
        assert config["default"]["mail"] == "new@example.com"

    def test_config_set_mise_filename_base(self, cli_runner, isolated_config):
        """Test config set command sets mise filename base"""
        result = cli_runner.invoke(
            config_cmd,
            [
                "set",
                "--config-file",
                str(isolated_config),
                "--mise-filename-base",
                "mise",
            ],
        )

        assert result.exit_code == 0
        assert "Set default mise_filename_base: mise" in result.output
        assert "Configuration saved" in result.output
        config = load_config()
        assert config["default"]["mise_filename_base"] == "mise"

    def test_config_set_with_mise(self, cli_runner, isolated_config):
        """Test config set command sets with_mise option"""
        result = cli_runner.invoke(
            config_cmd,
            ["set", "--config-file", str(isolated_config), "--with-mise"],
        )

        assert result.exit_code == 0
        assert "Set default with_mise: True" in result.output
        assert "Configuration saved" in result.output
        config = load_config()
        assert config["default"]["with_mise"] is True

    def test_config_set_no_mise(self, cli_runner, isolated_config):
        """Test config set command sets no_mise option"""
        result = cli_runner.invoke(
            config_cmd,
            ["set", "--config-file", str(isolated_config), "--no-mise"],
        )

        assert result.exit_code == 0
        assert "Set default with_mise: False" in result.output
        assert "Configuration saved" in result.output
        config = load_config()
        assert config["default"]["with_mise"] is False

    def test_config_show(self, cli_runner, isolated_config):
        """Test config show command displays configuration"""
        isolated_config.write_text(
            '[default]\nauthor = "Test Author"\nlicense_type = "MIT"\n'
        )

        result = cli_runner.invoke(
            config_cmd, ["show", "--config-file", str(isolated_config)]
        )

        assert result.exit_code == 0
        assert "Current configuration:" in result.output
        assert "author: 'Test Author'" in result.output
        assert "license_type: 'MIT'" in result.output

    def test_config_bare_command_shows_config(self, cli_runner, isolated_config):
        """Test bare config command shows configuration (alias for show)"""
        isolated_config.write_text(
            '[default]\nauthor = "Test Author"\nlicense_type = "MIT"\n'
        )

        result = cli_runner.invoke(config_cmd, ["--config-file", str(isolated_config)])

        assert result.exit_code == 0
        assert "Current configuration:" in result.output
        assert "author: 'Test Author'" in result.output
        assert "license_type: 'MIT'" in result.output

    def test_config_with_options_sets_config(self, cli_runner, isolated_config):
        """Test config command with options behaves like config set"""
        result = cli_runner.invoke(
            config_cmd,
            ["--config-file", str(isolated_config), "--author", "New Author"],
        )

        assert result.exit_code == 0
        assert "Set default author: New Author" in result.output
        assert "Configuration saved" in result.output
        config = load_config()
        assert config["default"]["author"] == "New Author"

    def test_config_with_plugin_options_sets_config(self, cli_runner, isolated_config):
        """Test config command with plugin options behaves like config set"""
        result = cli_runner.invoke(
            config_cmd,
            ["--config-file", str(isolated_config), "--git", "ssh=true"],
        )

        assert result.exit_code == 0
        assert "Set default Git.ssh: True" in result.output
        assert "Configuration saved" in result.output
        config = load_config()
        assert config["default"]["Git"]["ssh"] is True

    def test_config_set_with_custom_config_file(self, cli_runner, temp_dir):
        """Test config set command with custom config file"""
        custom_config_file = temp_dir / "custom-config.toml"

        result = cli_runner.invoke(
            config_cmd,
            [
                "set",
                "--config-file",
                str(custom_config_file),
                "--author",
                "Custom Author",
            ],
        )

        assert result.exit_code == 0
        assert "Set default author: Custom Author" in result.output
        assert "Configuration saved" in result.output

        # Confirm configuration written to specified custom location with expected content
        assert custom_config_file.exists()
        content = custom_config_file.read_text()
        assert 'author = "Custom Author"' in content

    def test_config_show_with_custom_config_file(self, cli_runner, temp_dir):
        """Test config show command with custom config file"""
        custom_config_file = temp_dir / "custom-config.toml"
        custom_config_file.write_text(
            '[default]\nauthor = "Custom Author"\nuser = "custom-user"\n'
        )

        result = cli_runner.invoke(
            config_cmd,
            [
                "show",
                "--config-file",
                str(custom_config_file),
            ],
        )

        assert result.exit_code == 0
        assert "Current configuration:" in result.output
        assert "author: 'Custom Author'" in result.output
        assert "user: 'custom-user'" in result.output

    def test_config_group_with_custom_config_file(self, cli_runner, temp_dir):
        """Test config group command with custom config file and options"""
        custom_config_file = temp_dir / "custom-config.toml"

        result = cli_runner.invoke(
            config_cmd,
            [
                "--config-file",
                str(custom_config_file),
                "--author",
                "Custom Author",
            ],
        )

        assert result.exit_code == 0
        assert "Set default author: Custom Author" in result.output
        assert "Configuration saved" in result.output

        # Confirm configuration written to specified custom location with expected content
        assert custom_config_file.exists()
        content = custom_config_file.read_text()
        assert 'author = "Custom Author"' in content

    def test_config_set_argumentless_plugin(self, cli_runner, isolated_config):
        """Test setting argumentless plugin with flag only"""
        result = cli_runner.invoke(
            config_cmd,
            ["set", "--config-file", str(isolated_config), "--srcdir"],
        )
        assert result.exit_code == 0
        assert "Enabled argumentless plugin: SrcDir" in result.output
        assert "Configuration saved" in result.output

        # Verify config content
        config = load_config()
        assert config["default"]["SrcDir"] is True

    def test_config_set_multiple_argumentless_plugins(
        self, cli_runner, isolated_config
    ):
        """Test setting multiple argumentless plugins"""
        result = cli_runner.invoke(
            config_cmd,
            [
                "set",
                "--config-file",
                str(isolated_config),
                "--srcdir",
                "--gitlabci",
            ],
        )
        assert result.exit_code == 0
        assert "Enabled argumentless plugin: SrcDir" in result.output
        assert "Enabled argumentless plugin: GitLabCI" in result.output
        assert "Configuration saved" in result.output

        # Verify config content
        config = load_config()
        assert config["default"]["SrcDir"] is True
        assert config["default"]["GitLabCI"] is True

    def test_config_set_argumentless_and_argument_plugins(
        self, cli_runner, isolated_config
    ):
        """Test setting both argumentless and argument plugins together"""
        result = cli_runner.invoke(
            config_cmd,
            [
                "set",
                "--config-file",
                str(isolated_config),
                "--srcdir",
                "--formatter",
                "style=blue",
            ],
        )
        assert result.exit_code == 0
        assert "Enabled argumentless plugin: SrcDir" in result.output
        assert (
            "Set default Formatter.style:" in result.output and "blue" in result.output
        )
        assert "Configuration saved" in result.output

        # Verify config content
        config = load_config()
        assert config["default"]["SrcDir"] is True
        assert config["default"]["Formatter"]["style"] == "blue"

    @patch("juliapkgtemplates.cli.JuliaPackageGenerator")
    def test_create_with_argumentless_plugin_config(
        self, mock_gen, cli_runner, temp_dir, isolated_config
    ):
        """Test create command loads argumentless plugin from config"""
        # Set up config with argumentless plugin
        cli_runner.invoke(
            config_cmd,
            ["set", "--config-file", str(isolated_config), "--srcdir"],
        )

        # Mock generator
        mock_instance = Mock()
        mock_instance.create_package.return_value = temp_dir / "TestPackage"
        mock_gen.return_value = mock_instance

        # Create package
        result = cli_runner.invoke(create, ["TestPackage", "--author", "Test Author"])

        assert result.exit_code == 0

        # Verify SrcDir plugin was enabled
        mock_instance.create_package.assert_called_once()
        call_args = mock_instance.create_package.call_args
        package_config = call_args[0][5]  # PackageConfig parameter

        assert "SrcDir" in package_config.enabled_plugins
        assert package_config.plugin_options["SrcDir"] == {}


class TestMultipleAuthors:
    """Test unified author handling supporting both single and multiple authors

    Design rationale: These tests verify the unified author interface that replaced
    the separate --authors option, ensuring backward compatibility while providing
    more intuitive user experience through consistent --author option usage.
    """

    def test_create_with_multiple_author_options(
        self, cli_runner, temp_dir, mock_subprocess
    ):
        """Test create command with multiple --author options

        Verifies that multiple --author options are properly parsed and passed
        as a list to the generator, maintaining the unified author interface.
        """
        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_gen:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_gen.return_value = mock_instance

            result = cli_runner.invoke(
                create,
                [
                    "TestPackage",
                    "--author",
                    "Author One",
                    "--author",
                    "Author Two <author2@example.com>",
                    "--author",
                    "Author Three",
                    "--output-dir",
                    str(temp_dir),
                ],
            )

            assert result.exit_code == 0
            mock_instance.create_package.assert_called_once()

            # Verify multiple authors are passed correctly
            call_args = mock_instance.create_package.call_args
            authors_arg = call_args[0][1]  # authors argument (position 1)
            assert isinstance(authors_arg, list)
            assert len(authors_arg) == 3
            assert "Author One" in authors_arg
            assert "Author Two <author2@example.com>" in authors_arg
            assert "Author Three" in authors_arg

    def test_create_with_comma_separated_authors(
        self, cli_runner, temp_dir, mock_subprocess
    ):
        """Test create command with comma-separated authors in single --author option

        Validates the flexible parsing that allows users to specify multiple authors
        within a single --author option using comma separation for convenience.
        """
        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_gen:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_gen.return_value = mock_instance

            result = cli_runner.invoke(
                create,
                [
                    "TestPackage",
                    "--author",
                    "Author One, Author Two <author2@example.com>, Author Three",
                    "--output-dir",
                    str(temp_dir),
                ],
            )

            assert result.exit_code == 0
            mock_instance.create_package.assert_called_once()

            # Verify comma-separated authors are parsed correctly
            call_args = mock_instance.create_package.call_args
            authors_arg = call_args[0][1]  # authors argument (position 1)
            assert isinstance(authors_arg, list)
            assert len(authors_arg) == 3
            assert "Author One" in authors_arg
            assert "Author Two <author2@example.com>" in authors_arg
            assert "Author Three" in authors_arg

    def test_single_author_option_converted_to_list(
        self, cli_runner, temp_dir, mock_subprocess
    ):
        """Test that single --author is converted to list format"""
        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_gen:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_gen.return_value = mock_instance

            result = cli_runner.invoke(
                create,
                [
                    "TestPackage",
                    "--author",
                    "Single Author",
                    "--output-dir",
                    str(temp_dir),
                ],
            )

            assert result.exit_code == 0
            mock_instance.create_package.assert_called_once()

            # Verify single author is passed as list
            call_args = mock_instance.create_package.call_args
            authors_arg = call_args[0][1]  # authors argument (position 1)
            assert isinstance(authors_arg, list)
            assert len(authors_arg) == 1
            assert authors_arg[0] == "Single Author"

    def test_config_file_author_array_support(
        self, cli_runner, temp_dir, temp_config_dir, mock_subprocess
    ):
        """Test config file support for author array

        Ensures backward compatibility with existing config files that store
        multiple authors as arrays under the 'author' key.
        """
        config_file = temp_config_dir / "config.toml"
        with config_file.open("w", encoding="utf-8") as f:
            f.write(
                "[default]\n"
                'author = ["Config Author One", "Config Author Two <author2@example.com>"]\n'
                'license_type = "MIT"\n'
            )

        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_gen:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_gen.return_value = mock_instance

            result = cli_runner.invoke(
                create,
                [
                    "TestPackage",
                    "--config-file",
                    str(config_file),
                    "--output-dir",
                    str(temp_dir),
                ],
                env={"XDG_CONFIG_HOME": str(temp_config_dir.parent)},
            )

            assert result.exit_code == 0
            mock_instance.create_package.assert_called_once()

            # Verify config authors are used correctly
            call_args = mock_instance.create_package.call_args
            authors_arg = call_args[0][1]  # authors argument (position 1)
            assert isinstance(authors_arg, list)
            assert len(authors_arg) == 2
            assert "Config Author One" in authors_arg
            assert "Config Author Two <author2@example.com>" in authors_arg

    def test_config_file_author_comma_separated_string(
        self, cli_runner, temp_dir, temp_config_dir, mock_subprocess
    ):
        """Test config file support for comma-separated author string

        Validates flexible config file format supporting comma-separated authors
        in string format, providing users multiple ways to specify authors.
        """
        config_file = temp_config_dir / "config.toml"
        with config_file.open("w", encoding="utf-8") as f:
            f.write(
                "[default]\n"
                'author = "Author One, Author Two <author2@example.com>, Author Three"\n'
                'license_type = "MIT"\n'
            )

        with patch("juliapkgtemplates.cli.JuliaPackageGenerator") as mock_gen:
            mock_instance = Mock()
            mock_instance.create_package.return_value = temp_dir / "TestPackage.jl"
            mock_gen.return_value = mock_instance

            result = cli_runner.invoke(
                create,
                [
                    "TestPackage",
                    "--config-file",
                    str(config_file),
                    "--output-dir",
                    str(temp_dir),
                ],
                env={"XDG_CONFIG_HOME": str(temp_config_dir.parent)},
            )

            assert result.exit_code == 0
            mock_instance.create_package.assert_called_once()

            # Verify comma-separated authors are parsed correctly
            call_args = mock_instance.create_package.call_args
            authors_arg = call_args[0][1]  # authors argument (position 1)
            assert isinstance(authors_arg, list)
            assert len(authors_arg) == 3
            assert "Author One" in authors_arg
            assert "Author Two <author2@example.com>" in authors_arg
            assert "Author Three" in authors_arg


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

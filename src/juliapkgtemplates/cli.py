"""
New CLI interface with dynamic plugin options
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click

from .generator import JuliaPackageGenerator, PackageConfig


def get_config_path() -> Path:
    """Get the configuration file path using XDG_CONFIG_HOME"""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_dir = Path(xdg_config_home)
    else:
        config_dir = Path.home() / ".config"

    app_config_dir = config_dir / "jtc"
    app_config_dir.mkdir(parents=True, exist_ok=True)
    return app_config_dir / "config.toml"


def load_config() -> dict:
    """Load configuration from config.toml"""
    config_path = get_config_path()
    config = {}

    if config_path.exists():
        try:
            import tomllib

            with open(config_path, "rb") as f:
                config = tomllib.load(f)
        except Exception as e:
            click.echo(
                f"Warning: Error loading config file {config_path}: {e}", err=True
            )

    return config


def save_config(config: dict) -> None:
    """Save configuration to config.toml"""
    config_path = get_config_path()
    try:
        import tomli_w

        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)
    except ImportError:
        # Fallback to manual TOML writing if tomli_w is not available
        content = "[default]\n"
        defaults = config.get("default", {})
        for key, value in defaults.items():
            content += f'{key} = "{value}"\n'
        with open(config_path, "w") as f:
            f.write(content)
    except Exception as e:
        click.echo(f"Error saving configuration: {e}", err=True)
        sys.exit(1)


def get_help_with_default(
    description: str, config_key: str, fallback_default: str
) -> str:
    """Generate help text with actual default value from config"""
    config = load_config()
    defaults = config.get("default", {})
    actual_default = defaults.get(config_key, fallback_default)
    return f"{description} (default: {actual_default})"


def get_help_with_fallback(
    base_description: str, config_key: str, fallback_text: Optional[str] = None
) -> str:
    """Generate help text with config default or fallback text"""
    config = load_config()
    defaults = config.get("default", {})
    value = defaults.get(config_key)

    if value and value.strip():
        return f"{base_description} (default: {value})"
    elif fallback_text:
        return f"{base_description} ({fallback_text})"
    else:
        return base_description


def get_author_help() -> str:
    """Generate help text for author option with config fallback"""
    return get_help_with_fallback(
        "Author name for the package (corresponds to PkgTemplates.jl 'authors' parameter)",
        "author",
        "defaults to git config user.name if not set in config or CLI",
    )


def get_user_help() -> str:
    """Generate help text for user option with config or PkgTemplates.jl fallback"""
    return get_help_with_fallback(
        "Git hosting username for repository URLs and CI (corresponds to PkgTemplates.jl 'user' parameter)",
        "user",
        "defaults to git config github.user if not set in config or CLI",
    )


def get_mail_help() -> str:
    """Generate help text for mail option with config or PkgTemplates.jl fallback"""
    return get_help_with_fallback(
        "Email address for package metadata (corresponds to PkgTemplates.jl 'mail' parameter)",
        "mail",
        "defaults to git config user.email if not set in config or CLI",
    )


def parse_plugin_option_value(value_str: str):
    """Convert string values to appropriate Python types for Julia interop"""
    if value_str.lower() in ("true", "yes", "1"):
        return True
    elif value_str.lower() in ("false", "no", "0"):
        return False
    elif value_str.startswith("[") and value_str.endswith("]"):
        # Simple list parsing: [item1,item2,item3]
        content = value_str[1:-1].strip()
        if not content:
            return []
        return [item.strip().strip("\"'") for item in content.split(",")]
    elif value_str.isdigit():
        return int(value_str)
    else:
        return value_str


def parse_multiple_key_value_pairs(option_string: str) -> dict:
    """Extract configuration options from space-separated key=value format"""
    options = {}
    if not option_string:
        return options

    # Preserve quoted strings containing spaces during tokenization
    parts = []
    current_part = ""
    in_quotes = False
    quote_char = None

    for char in option_string:
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
            current_part += char
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
            current_part += char
        elif char == " " and not in_quotes:
            if current_part.strip():
                parts.append(current_part.strip())
            current_part = ""
        else:
            current_part += char

    if current_part.strip():
        parts.append(current_part.strip())

    # Convert string tokens to typed values
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            # Remove quotes from value if present
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            options[key.strip()] = parse_plugin_option_value(value)

    return options


def parse_plugin_options_from_cli(**kwargs) -> dict:
    """Transform CLI plugin arguments into structured configuration dict"""
    plugin_options = {}

    for plugin in JuliaPackageGenerator.KNOWN_PLUGINS:
        # Support legacy and current CLI option formats for backward compatibility
        old_option_key = f"{plugin.lower()}_option"
        new_option_key = f"{plugin.lower()}option"

        # Handle old format (multiple occurrences)
        if old_option_key in kwargs and kwargs[old_option_key]:
            plugin_options[plugin] = {}
            for option_pair in kwargs[old_option_key]:
                if "=" in option_pair:
                    key, value = option_pair.split("=", 1)
                    plugin_options[plugin][key.strip()] = parse_plugin_option_value(
                        value.strip()
                    )

        # Handle new format (single string with multiple key=value pairs)
        elif new_option_key in kwargs and kwargs[new_option_key]:
            options = parse_multiple_key_value_pairs(kwargs[new_option_key])
            if options:
                plugin_options[plugin] = options

    return plugin_options


def create_dynamic_plugin_options(cmd):
    """Programmatically register Click options for all known PkgTemplates.jl plugins"""
    for plugin in JuliaPackageGenerator.KNOWN_PLUGINS:
        # Add old format option (multiple occurrences)
        old_option_name = f"--{plugin.lower()}-option"
        old_help_text = (
            f"Set {plugin} plugin options as key=value pairs (e.g., manifest=false)"
        )

        # Add new format option (single string with multiple pairs)
        new_option_name = f"--{plugin.lower()}option"
        new_help_text = f"Set {plugin} plugin options as space-separated key=value pairs (e.g., 'manifest=false ssh=true')"

        def add_old_option(plugin_name=plugin):
            return click.option(old_option_name, multiple=True, help=old_help_text)

        def add_new_option(plugin_name=plugin):
            return click.option(new_option_name, help=new_help_text)

        cmd = add_old_option()(cmd)
        cmd = add_new_option()(cmd)

    return cmd


@click.group()
@click.version_option(package_name="JuliaPkgTemplatesCLI")
def main():
    """jtc - Julia package generator with PkgTemplates.jl and mise tasks integration"""
    pass


@main.command()
@click.argument("package_name")
@click.option("--author", "-a", help=get_author_help())
@click.option("--user", "-u", help=get_user_help())
@click.option("--mail", "-m", help=get_mail_help())
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Output directory (default: current directory)",
)
@click.option(
    "--template",
    "-t",
    type=click.Choice(["minimal", "standard", "full"]),
    help=get_help_with_default("Template type", "template", "standard"),
)
@click.option(
    "--license",
    type=click.Choice(
        [
            "MIT",
            "Apache",
            "BSD2",
            "BSD3",
            "GPL2",
            "GPL3",
            "MPL",
            "ISC",
            "LGPL2",
            "LGPL3",
            "AGPL3",
            "EUPL",
        ]
    ),
    help=get_help_with_fallback(
        "License type", "license_type", "uses PkgTemplates.jl default if not set"
    ),
)
@click.option(
    "--julia-version",
    help='Julia version constraint (e.g., v"1.10.9") for Template constructor',
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what Julia Template function would be executed without actually running it",
)
@create_dynamic_plugin_options
@click.pass_context
def create(
    ctx: click.Context,
    package_name: str,
    author: Optional[str],
    user: Optional[str],
    mail: Optional[str],
    output_dir: str,
    template: Optional[str],
    license: Optional[str],
    julia_version: Optional[str],
    dry_run: bool,
    **kwargs,
):
    """Create a new Julia package"""

    # Strip .jl suffix for validation while preserving original name for generation
    name_to_check = package_name
    if package_name.endswith(".jl"):
        name_to_check = package_name[:-3]

    # Enforce Julia package naming conventions
    if not name_to_check.replace("_", "").replace("-", "").isalnum():
        click.echo(
            "Error: Package name must contain only letters, numbers, hyphens, and underscores (optionally ending with .jl)",
            err=True,
        )
        sys.exit(1)

    if not package_name[0].isalpha():
        click.echo("Error: Package name must start with a letter", err=True)
        sys.exit(1)

    # Establish configuration precedence: CLI args > config file > built-in defaults
    config = load_config()
    defaults = config.get("default", {})

    cli_plugin_options = parse_plugin_options_from_cli(**kwargs)

    # Build final configuration with proper precedence
    final_config = {}
    final_config["template"] = template or defaults.get("template", "standard")
    final_config["license_type"] = license or defaults.get("license_type")
    final_config["julia_version"] = julia_version or defaults.get("julia_version")

    # Merge plugin options (CLI overrides config)
    config_plugin_options = defaults.copy()
    # Isolate plugin-specific configuration from general package settings
    for key in ["template", "license_type", "julia_version"]:
        config_plugin_options.pop(key, None)

    # Transform dot-notation config keys (e.g., Git.manifest) into nested structure
    config_plugin_dict = {}
    for key, value in config_plugin_options.items():
        if "." in key:
            plugin_name, option_name = key.split(".", 1)
            if plugin_name not in config_plugin_dict:
                config_plugin_dict[plugin_name] = {}
            config_plugin_dict[plugin_name][option_name] = value

    # Apply CLI overrides to maintain precedence hierarchy
    for plugin, options in cli_plugin_options.items():
        if plugin not in config_plugin_dict:
            config_plugin_dict[plugin] = {}
        config_plugin_dict[plugin].update(options)

    final_config["plugin_options"] = config_plugin_dict if config_plugin_dict else {}

    # Create PackageConfig
    package_config = PackageConfig.from_dict(final_config)

    # Create generator and run
    generator = JuliaPackageGenerator()

    if dry_run:
        # Preview Julia Template function without package creation side effects
        julia_code = generator.generate_julia_code(
            package_name, author, user, mail, Path(output_dir), package_config
        )
        click.echo("Would execute the following Julia code:")
        click.echo("=" * 50)
        click.echo(julia_code)
        click.echo("=" * 50)
        return

    try:
        package_dir = generator.create_package(
            package_name, author, user, mail, Path(output_dir), package_config
        )
        click.echo(f"Package '{package_name}' created successfully at {package_dir}")
    except Exception as e:
        click.echo(f"Error creating package: {e}", err=True)
        sys.exit(1)


@main.command("plugin-info")
@click.argument("plugin_name", required=False)
def plugin_info(plugin_name: Optional[str]):
    """Show information about plugins or a specific plugin"""
    if plugin_name is None:
        click.echo("Available plugins:")
        click.echo("=" * 40)
        for p in JuliaPackageGenerator.KNOWN_PLUGINS:
            click.echo(f"  {p}")
        click.echo(
            "\nUse 'jtc plugin-info <plugin_name>' to see options for a specific plugin."
        )
        click.echo("Example: jtc plugin-info Git")
        return

    plugin_name_title = plugin_name.title()

    if plugin_name_title not in JuliaPackageGenerator.KNOWN_PLUGINS:
        available = ", ".join(JuliaPackageGenerator.KNOWN_PLUGINS)
        click.echo(f"Unknown plugin: {plugin_name}")
        click.echo(f"Available plugins: {available}")
        sys.exit(1)

    click.echo(f"Help for {plugin_name_title} plugin:")
    click.echo("=" * 40)

    if plugin_name_title == "Git":
        click.echo("Options:")
        click.echo(
            "  manifest=true/false  - Include/exclude Manifest.toml (default: false)"
        )
        click.echo(
            "  ssh=true/false       - Use SSH for Git operations (default: false)"
        )
        click.echo("  ignore=[pattern,...]  - Git ignore patterns (default: none)")
        click.echo("\nExample:")
        click.echo(
            "  jtc create MyPkg --git-option manifest=false --git-option ssh=true"
        )

    elif plugin_name_title == "Tests":
        click.echo("Options:")
        click.echo(
            "  project=true/false   - Separate project for tests (default: true)"
        )
        click.echo("  aqua=true/false      - Enable Aqua.jl testing (default: false)")
        click.echo("  jet=true/false       - Enable JET.jl testing (default: false)")
        click.echo("\nExample:")
        click.echo(
            "  jtc create MyPkg --tests-option aqua=true --tests-option jet=true"
        )

    elif plugin_name_title == "Formatter":
        click.echo("Options:")
        click.echo(
            "  style=nostyle/blue/sciml/yas  - JuliaFormatter style (default: nostyle)"
        )
        click.echo("\nExample:")
        click.echo("  jtc create MyPkg --formatter-option style=blue")

    elif plugin_name_title == "ProjectFile":
        click.echo("Options:")
        click.echo("  version=x.y.z        - Initial package version (default: 0.0.1)")
        click.echo("\nExample:")
        click.echo("  jtc create MyPkg --projectfile-option version=1.0.0")

    elif plugin_name_title == "License":
        click.echo("Options:")
        click.echo("  name=license_name    - License identifier")
        click.echo("\nExample:")
        click.echo("  jtc create MyPkg --license-option name=Apache-2.0")
        click.echo(
            "\nNote: Use --license for common licenses, --license-option for custom ones"
        )

    else:
        click.echo(f"No specific help available for {plugin_name_title} plugin.")
        click.echo("This plugin typically has no configurable options.")


@main.command()
@click.argument("key")
@click.argument("value")
def config(key: str, value: str):
    """Set configuration values"""
    config_data = load_config()
    if "default" not in config_data:
        config_data["default"] = {}

    config_data["default"][key] = value
    save_config(config_data)
    click.echo(f"Set {key} = {value}")


if __name__ == "__main__":
    main()

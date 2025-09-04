"""
New CLI interface with dynamic plugin options
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

import click
from jinja2 import Environment, PackageLoader

from .generator import JuliaPackageGenerator, PackageConfig, JuliaDependencyError


def check_julia_dependencies():
    """Check Julia dependencies early and exit if not available"""
    try:
        JuliaPackageGenerator.get_available_plugins()
    except JuliaDependencyError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


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


def flatten_config_for_backward_compatibility(config: dict) -> dict:
    """Convert nested config structure to flat dot-notation for backward compatibility"""
    if "default" not in config:
        return config

    defaults = config["default"].copy()
    flattened_defaults = {}

    for key, value in defaults.items():
        if isinstance(value, dict):
            for plugin_key, plugin_value in value.items():
                flattened_defaults[f"{key}.{plugin_key}"] = plugin_value
        else:
            flattened_defaults[key] = value

    return {"default": flattened_defaults}


def save_config(config: dict) -> None:
    """Save configuration to config.toml"""
    config_path = get_config_path()
    try:
        import tomli_w

        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)
    except ImportError:
        # Manual TOML generation when tomli_w is unavailable
        content = ""
        defaults = config.get("default", {})

        basic_values = {}
        plugin_values = {}

        for key, value in defaults.items():
            if "." in key:
                plugin_name, option_name = key.split(".", 1)
                if plugin_name not in plugin_values:
                    plugin_values[plugin_name] = {}
                plugin_values[plugin_name][option_name] = value
            else:
                basic_values[key] = value

        if basic_values or plugin_values:
            content += "[default]\n"
            for key, value in basic_values.items():
                if isinstance(value, str):
                    content += f'{key} = "{value}"\n'
                elif isinstance(value, bool):
                    content += f"{key} = {str(value).lower()}\n"
                elif isinstance(value, (int, float)):
                    content += f"{key} = {value}\n"
                elif isinstance(value, list):
                    content += f"{key} = {value}\n"

            for plugin_name, options in plugin_values.items():
                content += f"\n[default.{plugin_name}]\n"
                for option_key, option_value in options.items():
                    if isinstance(option_value, str):
                        content += f'{option_key} = "{option_value}"\n'
                    elif isinstance(option_value, bool):
                        content += f"{option_key} = {str(option_value).lower()}\n"
                    elif isinstance(option_value, (int, float)):
                        content += f"{option_key} = {option_value}\n"
                    elif isinstance(option_value, list):
                        content += f"{option_key} = {option_value}\n"

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
    flat_config = flatten_config_for_backward_compatibility(config)
    defaults = flat_config.get("default", {})
    actual_default = defaults.get(config_key, fallback_default)
    return f"{description} (default: {actual_default})"


def get_help_with_fallback(
    base_description: str, config_key: str, fallback_text: Optional[str] = None
) -> str:
    """Generate help text with config default or fallback text"""
    config = load_config()
    flat_config = flatten_config_for_backward_compatibility(config)
    defaults = flat_config.get("default", {})
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
        content = value_str[1:-1].strip()
        if not content:
            return []
        return [item.strip().strip("\"'") for item in content.split(",")]
    elif value_str.isdigit():
        return int(value_str)
    else:
        return value_str


def ensure_list(value):
    """Normalize value to a list for consistent iteration"""
    if isinstance(value, (list, tuple)):
        return value
    return [value]


def parse_multiple_key_value_pairs(option_string: str) -> dict:
    """Extract configuration options from space-separated key=value format"""
    options = {}
    if not option_string:
        return options

    # Parse quoted strings to preserve spaces in option values
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

    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            options[key.strip()] = parse_plugin_option_value(value)

    return options


def handle_license_option(license_value: str) -> dict:
    """Parse license option supporting both simple and key=value formats"""
    if "=" in license_value:
        return parse_multiple_key_value_pairs(license_value)
    else:
        return {"name": license_value}


def parse_plugin_options_from_cli(**kwargs) -> dict:
    """Transform CLI plugin arguments into structured configuration dict"""
    plugin_options = {}

    option_to_plugin = {
        "git": "Git",
        "tests": "Tests",
        "formatter": "Formatter",
        "projectfile": "ProjectFile",
        "srcdir": "SrcDir",
        "readme": "Readme",
        "githubactions": "GitHubActions",
        "appveyor": "AppVeyor",
        "cirrusci": "CirrusCI",
        "droneci": "DroneCI",
        "gitlabci": "GitLabCI",
        "travisci": "TravisCI",
        "codecov": "Codecov",
        "coveralls": "Coveralls",
        "documenter": "Documenter",
        "tagbot": "TagBot",
        "compathelper": "CompatHelper",
        "dependabot": "Dependabot",
        "bluestylebadge": "BlueStyleBadge",
        "colpracbadge": "ColPracBadge",
        "pkgevalbadge": "PkgEvalBadge",
        "develop": "Develop",
        "citation": "Citation",
        "registeraction": "RegisterAction",
        "codeowners": "CodeOwners",
        "pkgbenchmark": "PkgBenchmark",
        "runic": "Runic",
    }

    for option_key, plugin_name in option_to_plugin.items():
        if option_key in kwargs and kwargs[option_key] is not None:
            option_string = kwargs[option_key]

            if plugin_name not in plugin_options:
                plugin_options[plugin_name] = {}

            if option_string:
                options = parse_multiple_key_value_pairs(option_string)
                if options:
                    plugin_options[plugin_name].update(options)

    # License uses different CLI option format than other plugins
    if "license" in kwargs and kwargs["license"] is not None:
        license_value = kwargs["license"]
        if license_value:
            plugin_options["License"] = handle_license_option(license_value)

    return plugin_options


def create_dynamic_plugin_options(cmd):
    """Programmatically register Click options for all known PkgTemplates.jl plugins"""

    plugin_option_names = {
        # Core plugins
        "Git": "--git",
        "Tests": "--tests",
        "Formatter": "--formatter",
        "ProjectFile": "--projectfile",
        "SrcDir": "--srcdir",
        "Readme": "--readme",
        # CI/CD plugins
        "GitHubActions": "--githubactions",
        "AppVeyor": "--appveyor",
        "CirrusCI": "--cirrusci",
        "DroneCI": "--droneci",
        "GitLabCI": "--gitlabci",
        "TravisCI": "--travisci",
        # Code coverage plugins
        "Codecov": "--codecov",
        "Coveralls": "--coveralls",
        # Documentation plugins
        "Documenter": "--documenter",
        # Automation plugins
        "TagBot": "--tagbot",
        "CompatHelper": "--compathelper",
        "Dependabot": "--dependabot",
        # Badge plugins
        "BlueStyleBadge": "--bluestylebadge",
        "ColPracBadge": "--colpracbadge",
        "PkgEvalBadge": "--pkgevalbadge",
        # Miscellaneous plugins
        "Develop": "--develop",
        "Citation": "--citation",
        "RegisterAction": "--registeraction",
        "CodeOwners": "--codeowners",
        "PkgBenchmark": "--pkgbenchmark",
        "Runic": "--runic",
    }

    available_plugins = JuliaPackageGenerator.get_available_plugins()

    for plugin in available_plugins:
        if plugin == "License":
            continue

        option_name = plugin_option_names.get(plugin, f"--{plugin.lower()}")

        def add_option(plugin_name=plugin, opt_name=option_name):
            return click.option(
                opt_name,
                is_flag=False,
                flag_value="",  # --plugin only → empty string (enable with defaults)
                default=None,  # not specified → None (disabled)
                help=f"Enable {plugin} plugin (empty for defaults, or key=value pairs)",
            )

        cmd = add_option()(cmd)

    return cmd


@click.group()
@click.version_option(package_name="JuliaPkgTemplatesCLI")
def main():
    """jtc - Julia package generator with PkgTemplates.jl and mise tasks integration"""
    check_julia_dependencies()


@main.command()
@click.argument("package_name")
@click.option("--author", "-a", help=get_author_help())
@click.option("--user", "-u", help=get_user_help())
@click.option("--mail", "-m", help=get_mail_help())
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output directory (default: current directory)",
)
@click.option(
    "--license",
    help=get_help_with_fallback(
        "License type (common: MIT, Apache, BSD2, BSD3, GPL2, GPL3, MPL, ISC, LGPL2, LGPL3, AGPL3, EUPL; or any PkgTemplates.jl license identifier)",
        "license_type",
        "uses PkgTemplates.jl default if not set",
    ),
)
@click.option(
    "--julia-version",
    help='Julia version constraint (e.g., "1.10.9") for Template constructor',
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    default=False,
    help="Show what Julia Template function would be executed without actually running it",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output for debugging",
)
@click.option(
    "--mise-filename-base",
    help=get_help_with_default(
        "Base name for mise config file (e.g., '.mise' creates '.mise.toml', 'mise' creates 'mise.toml')",
        "mise_filename_base",
        ".mise",
    ),
)
@click.option(
    "--with-mise/--no-mise",
    default=True,
    help=get_help_with_default(
        "Enable/disable mise task file generation",
        "with_mise",
        "enabled",
    ),
)
@create_dynamic_plugin_options
@click.pass_context
def create(
    ctx: click.Context,
    package_name: str,
    author: Optional[str],
    user: Optional[str],
    mail: Optional[str],
    output_dir: Optional[str],
    license: Optional[str],
    julia_version: Optional[str],
    dry_run: bool,
    verbose: bool,
    mise_filename_base: Optional[str],
    with_mise: bool,
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
    # Flatten nested structure for backward compatibility with existing code
    flat_config = flatten_config_for_backward_compatibility(config)
    defaults = flat_config.get("default", {})

    cli_plugin_options = parse_plugin_options_from_cli(license=license, **kwargs)

    # Extract enabled plugins from plugin options
    # Plugins are enabled when their options are specified (not None)
    enabled_plugins = []

    for plugin_name, options in cli_plugin_options.items():
        # Plugin is enabled if options are provided (including empty string for defaults)
        enabled_plugins.append(plugin_name)

    # Apply config defaults if CLI arguments not provided
    final_author = author or defaults.get("author")
    final_user = user or defaults.get("user")
    final_mail = mail or defaults.get("mail")
    final_output_dir = output_dir or defaults.get("output_dir", ".")
    final_mise_filename_base = mise_filename_base or defaults.get(
        "mise_filename_base", ".mise"
    )
    final_with_mise = (
        with_mise if with_mise is not None else defaults.get("with_mise", True)
    )

    # Display configuration being used

    # Build final configuration with proper precedence
    final_config = {}
    final_config["enabled_plugins"] = enabled_plugins
    final_config["julia_version"] = julia_version or defaults.get("julia_version")
    final_config["mise_filename_base"] = final_mise_filename_base
    final_config["with_mise"] = final_with_mise

    # Only apply plugin options for explicitly enabled plugins
    final_plugin_options = {}

    # Apply CLI plugin options (these are the enabled plugins)
    for plugin, options in cli_plugin_options.items():
        final_plugin_options[plugin] = options.copy()

    # Handle legacy license_type from config for backward compatibility
    config_license = defaults.get("license_type") or defaults.get("license")
    if config_license and "License" not in final_plugin_options:
        # Add config license as License plugin option if no CLI license specified
        final_plugin_options["License"] = {"name": config_license}

    # Then, apply config file options only for CLI-enabled plugins
    if enabled_plugins:  # Only if there are CLI-enabled plugins
        config_plugin_options = defaults.copy()
        # Remove non-plugin configuration
        for key in [
            "enabled_plugins",
            "license_type",
            "julia_version",
            "mise_filename_base",
            "with_mise",
            "user",
            "author",
            "mail",
            "output_dir",
        ]:
            config_plugin_options.pop(key, None)

        # Transform dot-notation config keys for enabled plugins only
        for key, value in config_plugin_options.items():
            if "." in key:
                plugin_name, option_name = key.split(".", 1)
                if plugin_name in enabled_plugins:
                    if plugin_name not in final_plugin_options:
                        final_plugin_options[plugin_name] = {}
                    # CLI options take precedence over config file
                    if option_name not in final_plugin_options[plugin_name]:
                        final_plugin_options[plugin_name][option_name] = value

    final_config["plugin_options"] = final_plugin_options

    # Create PackageConfig
    package_config = PackageConfig.from_dict(final_config)

    # Create generator and run
    generator = JuliaPackageGenerator()

    if dry_run:
        # Preview Julia Template function without package creation side effects
        julia_code = generator.generate_julia_code(
            package_name,
            final_author,
            final_user,
            final_mail,
            Path(final_output_dir),
            package_config,
        )
        click.echo("Would execute the following Julia code:")
        click.echo("=" * 50)
        click.echo(julia_code)
        click.echo("=" * 50)
        return

    try:
        package_dir = generator.create_package(
            package_name,
            final_author,
            final_user,
            final_mail,
            Path(final_output_dir),
            package_config,
            verbose=verbose,
        )
        click.echo(f"Package '{package_name}' created successfully at {package_dir}")
    except Exception as e:
        click.echo(f"Error creating package: {e}", err=True)
        sys.exit(1)


@main.command("plugin-info")
@click.argument("plugin_name", required=False)
def plugin_info(plugin_name: Optional[str]):
    """Show information about plugins or a specific plugin"""
    # Get available plugins dynamically from Julia
    available_plugins = _get_plugins_from_julia()

    if plugin_name is None:
        click.echo("Available PkgTemplates.jl plugins:")
        click.echo("=" * 40)

        # Group plugins by category for better readability
        core_plugins = [
            "Git",
            "Tests",
            "Formatter",
            "ProjectFile",
            "SrcDir",
            "Readme",
            "License",
        ]
        ci_plugins = [
            "GitHubActions",
            "AppVeyor",
            "CirrusCI",
            "DroneCI",
            "GitLabCI",
            "TravisCI",
        ]
        coverage_plugins = ["Codecov", "Coveralls"]
        doc_plugins = ["Documenter"]
        automation_plugins = ["TagBot", "CompatHelper", "Dependabot", "RegisterAction"]
        badge_plugins = ["BlueStyleBadge", "ColPracBadge", "PkgEvalBadge"]
        dev_plugins = ["Citation", "CodeOwners", "PkgBenchmark", "Develop"]
        formatting_plugins = ["Runic"]

        categories = [
            ("Core", core_plugins),
            ("CI/CD", ci_plugins),
            ("Coverage", coverage_plugins),
            ("Documentation", doc_plugins),
            ("Automation", automation_plugins),
            ("Badges", badge_plugins),
            ("Development", dev_plugins),
            ("Formatting", formatting_plugins),
        ]

        for category, plugin_list in categories:
            available_in_category = [p for p in plugin_list if p in available_plugins]
            if available_in_category:
                click.echo(f"\n{category}:")
                for p in available_in_category:
                    click.echo(f"  {p}")

        # Show any remaining plugins not categorized
        categorized = set()
        for _, plugin_list in categories:
            categorized.update(plugin_list)
        uncategorized = [p for p in available_plugins if p not in categorized]
        if uncategorized:
            click.echo("\nOther:")
            for p in uncategorized:
                click.echo(f"  {p}")

        click.echo(
            "\nUse 'jtc plugin-info <plugin_name>' to see options for a specific plugin."
        )
        click.echo("Example: jtc plugin-info Git")
        return

    # Find matching plugin name (case-insensitive search)
    plugin_name_matched = None
    for known_plugin in available_plugins:
        if known_plugin.lower() == plugin_name.lower():
            plugin_name_matched = known_plugin
            break

    if plugin_name_matched is None:
        available = ", ".join(available_plugins)
        click.echo(f"Unknown plugin: {plugin_name}")
        click.echo(f"Available plugins: {available}")
        sys.exit(1)

    click.echo(f"Help for {plugin_name_matched} plugin:")
    click.echo("=" * 40)

    # Delegate to Julia's documentation system
    try:
        julia_doc_cmd = [
            "julia",
            "-e",
            f"using REPL, Markdown, PkgTemplates; "
            f"Markdown.term(IOContext(stdout, :color=>true), "
            f'Base.Docs.doc(Base.Docs.Binding(PkgTemplates, Symbol("{plugin_name_matched}"))))',
        ]

        result = subprocess.run(
            julia_doc_cmd, capture_output=True, text=True, check=True
        )
        click.echo(result.stdout)

        # Add usage examples specific to jtc CLI
        _add_jtc_plugin_examples(plugin_name_matched)

    except subprocess.CalledProcessError as e:
        # Fallback to basic message if Julia doc system fails
        click.echo(
            f"Could not retrieve documentation for {plugin_name_matched} plugin from Julia."
        )
        click.echo(
            "This may indicate that Julia or PkgTemplates.jl is not properly installed."
        )
        click.echo(
            f"\nError details: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        )

        # Provide basic usage info as fallback
        click.echo("\nBasic usage:")
        plugin_option_name = _get_plugin_cli_option_name(plugin_name_matched)
        click.echo(f"  jtc create MyPkg {plugin_option_name}")
        click.echo(f"  jtc create MyPkg {plugin_option_name} 'key=value'")
    except FileNotFoundError:
        click.echo(
            "Julia not found. Please install Julia and ensure it's in your PATH."
        )
        sys.exit(1)


def _get_plugin_cli_option_name(plugin_name: str) -> str:
    """Get CLI option name for a plugin"""
    plugin_option_names = {
        # Core plugins
        "Git": "--git",
        "Tests": "--tests",
        "Formatter": "--formatter",
        "ProjectFile": "--projectfile",
        "SrcDir": "--srcdir",
        "Readme": "--readme",
        # CI/CD plugins
        "GitHubActions": "--githubactions",
        "AppVeyor": "--appveyor",
        "CirrusCI": "--cirrusci",
        "DroneCI": "--droneci",
        "GitLabCI": "--gitlabci",
        "TravisCI": "--travisci",
        # Code coverage plugins
        "Codecov": "--codecov",
        "Coveralls": "--coveralls",
        # Documentation plugins
        "Documenter": "--documenter",
        # Automation plugins
        "TagBot": "--tagbot",
        "CompatHelper": "--compathelper",
        "Dependabot": "--dependabot",
        # Badge plugins
        "BlueStyleBadge": "--bluestylebadge",
        "ColPracBadge": "--colpracbadge",
        "PkgEvalBadge": "--pkgevalbadge",
        # Miscellaneous plugins
        "Develop": "--develop",
        "Citation": "--citation",
        "RegisterAction": "--registeraction",
        "CodeOwners": "--codeowners",
        "PkgBenchmark": "--pkgbenchmark",
        "Runic": "--runic",
        "License": "--license",
    }
    return plugin_option_names.get(plugin_name, f"--{plugin_name.lower()}")


def _get_plugins_from_julia() -> List[str]:
    """Get available plugins dynamically from Julia's PkgTemplates module"""
    return JuliaPackageGenerator.get_available_plugins()


def _add_jtc_plugin_examples(plugin_name: str):
    """Add jtc-specific usage examples for plugins"""
    plugin_option = _get_plugin_cli_option_name(plugin_name)

    click.echo("\njtc CLI usage examples:")
    click.echo("=" * 25)

    if plugin_name == "License":
        click.echo(f"  jtc create MyPkg {plugin_option} MIT")
        click.echo(f"  jtc create MyPkg {plugin_option} 'name=Apache'")
        click.echo(
            f"  jtc create MyPkg {plugin_option} 'name=MIT path=./custom-license.txt'"
        )
        click.echo(
            f"\nLicense aliases: {' '.join(JuliaPackageGenerator.LICENSE_MAPPING.keys())}"
        )
    else:
        click.echo(f"  jtc create MyPkg {plugin_option}")
        click.echo(
            f"  jtc create MyPkg {plugin_option} 'option1=value1 option2=value2'"
        )

    click.echo("\nFor more plugin configuration examples, see: jtc create --help")


@main.command()
@click.option(
    "--shell",
    type=click.Choice(["fish"]),
    default="fish",
    help="Shell type (currently only fish is supported)",
)
def completion(shell: str):
    """Generate shell completion script"""
    if shell == "fish":
        fish_completion = generate_fish_completion()
        click.echo(fish_completion)
    else:
        click.echo(f"Completion for {shell} is not yet supported", err=True)
        sys.exit(1)


def generate_fish_completion() -> str:
    """Generate fish completion script for jtc command using Jinja2 template"""
    # Get available plugins and licenses dynamically
    plugins = " ".join(JuliaPackageGenerator.get_available_plugins())

    licenses = " ".join(JuliaPackageGenerator.LICENSE_MAPPING.keys())

    # Generate plugin options dynamically based on current CLI structure
    plugin_options = []

    plugin_option_names = {
        # Core plugins
        "Git": "--git",
        "Tests": "--tests",
        "Formatter": "--formatter",
        "ProjectFile": "--projectfile",
        "SrcDir": "--srcdir",
        "Readme": "--readme",
        # CI/CD plugins
        "GitHubActions": "--githubactions",
        "AppVeyor": "--appveyor",
        "CirrusCI": "--cirrusci",
        "DroneCI": "--droneci",
        "GitLabCI": "--gitlabci",
        "TravisCI": "--travisci",
        # Code coverage plugins
        "Codecov": "--codecov",
        "Coveralls": "--coveralls",
        # Documentation plugins
        "Documenter": "--documenter",
        # Automation plugins
        "TagBot": "--tagbot",
        "CompatHelper": "--compathelper",
        "Dependabot": "--dependabot",
        # Badge plugins
        "BlueStyleBadge": "--bluestylebadge",
        "ColPracBadge": "--colpracbadge",
        "PkgEvalBadge": "--pkgevalbadge",
        # Miscellaneous plugins
        "Develop": "--develop",
        "Citation": "--citation",
        "RegisterAction": "--registeraction",
        "CodeOwners": "--codeowners",
        "PkgBenchmark": "--pkgbenchmark",
        "Runic": "--runic",
    }

    available_plugins = JuliaPackageGenerator.get_available_plugins()

    for plugin in available_plugins:
        if plugin == "License":
            continue  # License is handled separately

        option_name = plugin_option_names.get(plugin, f"--{plugin.lower()}")
        # Fish expects option names without the CLI prefix
        fish_option = option_name[2:]
        plugin_options.append(
            f'complete -c jtc -n "__fish_seen_subcommand_from create" -l {fish_option} -d "Enable {plugin} plugin (empty for defaults, or key=value pairs)"'
        )

    # Generate config command plugin options
    config_plugin_options = []
    for plugin in available_plugins:
        if plugin == "License":
            continue  # License is handled separately

        option_name = plugin_option_names.get(plugin, f"--{plugin.lower()}")
        # Fish expects option names without the CLI prefix
        fish_option = option_name[2:]
        config_plugin_options.append(
            f'complete -c jtc -n "__fish_seen_subcommand_from config" -l {fish_option} -d "Set default {plugin} plugin options (key=value pairs)"'
        )

    # Load and render template
    env = Environment(loader=PackageLoader("juliapkgtemplates", "templates"))
    template = env.get_template("fish_completion.j2")

    return template.render(
        plugins=plugins,
        licenses=licenses,
        plugin_options=plugin_options,
        config_plugin_options=config_plugin_options,
    )


@main.group(invoke_without_command=True)
@click.option("--author", help="Set default author")
@click.option("--user", help="Set default user")
@click.option("--mail", help="Set default mail")
@click.option("--license", help="Set default license")
@click.option("--template", help="Set default template")
@click.option(
    "--julia-version", help="Set default Julia version constraint (e.g., 1.10.9)"
)
@click.option("--mise-filename-base", help="Set default base name for mise config file")
@click.option(
    "--with-mise/--no-mise", default=None, help="Set default mise task file generation"
)
@create_dynamic_plugin_options
@click.pass_context
def config(
    ctx,
    author: Optional[str],
    user: Optional[str],
    mail: Optional[str],
    license: Optional[str],
    template: Optional[str],
    julia_version: Optional[str],
    mise_filename_base: Optional[str],
    with_mise: Optional[bool],
    **kwargs,
):
    """Configuration management"""
    if ctx.invoked_subcommand is None:
        # Check if any configuration options are provided
        has_config_options = any(
            [
                author is not None,
                user is not None,
                mail is not None,
                license is not None,
                template is not None,
                julia_version is not None,
                mise_filename_base is not None,
                with_mise is not None,
            ]
        )

        # Check if any plugin options are provided
        plugin_options = parse_plugin_options_from_cli(**kwargs)
        has_plugin_options = bool(plugin_options)

        if has_config_options or has_plugin_options:
            # Options provided, delegate to set functionality
            _set_config(
                author,
                user,
                mail,
                license,
                template,
                julia_version,
                mise_filename_base,
                with_mise,
                **kwargs,
            )
        else:
            # No options provided, show config as default
            _show_config()


def _show_config():
    """Display current configuration values"""
    config_data = load_config()
    click.echo("Current configuration:")
    click.echo("=" * 40)
    config_path = get_config_path()
    click.echo(f"Config file: {config_path}")
    click.echo()

    defaults = config_data.get("default", {})
    if not defaults:
        click.echo("No configuration set")
        return

    basic_config_keys = {
        "author",
        "user",
        "mail",
        "license_type",
        "template",
        "julia_version",
        "mise_filename_base",
        "with_mise",
    }
    basic_config = {}
    plugin_config = {}

    for key, value in defaults.items():
        if key in basic_config_keys:
            basic_config[key] = value
        elif isinstance(value, dict):
            plugin_config[key] = value

    for key, value in basic_config.items():
        if value is not None:
            click.echo(f"{key}: {repr(value)}")

    # Display plugin configuration
    if plugin_config:
        click.echo("\nPlugin configuration:")
        for plugin_name, options in plugin_config.items():
            click.echo(f"  {plugin_name}:")
            for option_key, option_value in options.items():
                click.echo(f"    {option_key}: {repr(option_value)}")


def _set_config(
    author: Optional[str],
    user: Optional[str],
    mail: Optional[str],
    license: Optional[str],
    template: Optional[str],
    julia_version: Optional[str],
    mise_filename_base: Optional[str],
    with_mise: Optional[bool],
    **kwargs,
):
    """Set configuration values (shared logic)"""
    config_data = load_config()
    if "default" not in config_data:
        config_data["default"] = {}

    # Check if any plugin options are provided
    plugin_options = parse_plugin_options_from_cli(**kwargs)

    # Set configuration values
    updated = False
    if author is not None:
        config_data["default"]["author"] = author
        click.echo(f"Set default author: {author}")
        updated = True
    if user is not None:
        config_data["default"]["user"] = user
        click.echo(f"Set default user: {user}")
        updated = True
    if mail is not None:
        config_data["default"]["mail"] = mail
        click.echo(f"Set default mail: {mail}")
        updated = True
    if license is not None:
        config_data["default"]["license_type"] = license
        click.echo(f"Set default license: {license}")
        updated = True
    if template is not None:
        config_data["default"]["template"] = template
        click.echo(f"Set default template: {template}")
        updated = True
    if julia_version is not None:
        config_data["default"]["julia_version"] = julia_version
        click.echo(f"Set default julia_version: {julia_version}")
        updated = True
    if mise_filename_base is not None:
        config_data["default"]["mise_filename_base"] = mise_filename_base
        click.echo(f"Set default mise_filename_base: {mise_filename_base}")
        updated = True
    if with_mise is not None:
        config_data["default"]["with_mise"] = with_mise
        click.echo(f"Set default with_mise: {with_mise}")
        updated = True

    # Process plugin options - save in nested structure
    for plugin_name, options in plugin_options.items():
        if plugin_name not in config_data["default"]:
            config_data["default"][plugin_name] = {}
        for option_key, option_value in options.items():
            config_data["default"][plugin_name][option_key] = option_value
            click.echo(f"Set default {plugin_name}.{option_key}: {option_value}")
            updated = True

    if updated:
        save_config(config_data)
        click.echo("Configuration saved")
    else:
        click.echo("No configuration options provided")


@config.command()
def show():
    """Display current configuration values"""
    _show_config()


@config.command("set")
@click.option("--author", help="Set default author")
@click.option("--user", help="Set default user")
@click.option("--mail", help="Set default mail")
@click.option("--license", help="Set default license")
@click.option("--template", help="Set default template")
@click.option(
    "--julia-version", help="Set default Julia version constraint (e.g., 1.10.9)"
)
@click.option("--mise-filename-base", help="Set default base name for mise config file")
@click.option(
    "--with-mise/--no-mise", default=None, help="Set default mise task file generation"
)
@create_dynamic_plugin_options
def set_config(
    author: Optional[str],
    user: Optional[str],
    mail: Optional[str],
    license: Optional[str],
    template: Optional[str],
    julia_version: Optional[str],
    mise_filename_base: Optional[str],
    with_mise: Optional[bool],
    **kwargs,
):
    """Set configuration values"""
    _set_config(
        author,
        user,
        mail,
        license,
        template,
        julia_version,
        mise_filename_base,
        with_mise,
        **kwargs,
    )


if __name__ == "__main__":
    main()

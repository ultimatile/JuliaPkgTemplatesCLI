"""
CLI interface for JuliaPkgTemplatesCLI - Julia package generator
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
        "License type", "license", "uses PkgTemplates.jl default if not set"
    ),
)
@click.option(
    "--with-docs/--no-docs",
    default=True,
    help="Include documentation setup (default: yes)",
)
@click.option(
    "--with-ci/--no-ci", default=True, help="Include CI/CD setup (default: yes)"
)
@click.option(
    "--with-codecov/--no-codecov",
    default=True,
    help="Include Codecov integration (default: yes)",
)
@click.option(
    "--formatter-style",
    type=click.Choice(["nostyle", "sciml", "blue", "yas"]),
    help=get_help_with_default("JuliaFormatter style", "formatter_style", "nostyle"),
)
@click.option(
    "--julia-version",
    help='Julia version constraint (e.g., v"1.10.9") for Template constructor',
)
@click.option(
    "--ssh/--no-ssh",
    default=None,
    help=get_help_with_default("Use SSH for Git operations", "ssh", "False"),
)
@click.option(
    "--ignore-patterns",
    help="Comma-separated list of patterns to ignore in Git (e.g., .vscode,.DS_Store)",
)
@click.option(
    "--tests-aqua/--no-tests-aqua",
    default=None,
    help=get_help_with_default("Enable Aqua.jl in Tests plugin", "tests_aqua", "False"),
)
@click.option(
    "--tests-jet/--no-tests-jet",
    default=None,
    help=get_help_with_default("Enable JET.jl in Tests plugin", "tests_jet", "False"),
)
@click.option(
    "--tests-project/--no-tests-project",
    default=None,
    help=get_help_with_default(
        "Enable separate project for tests", "tests_project", "True"
    ),
)
@click.option(
    "--project-version",
    help='Initial version for ProjectFile plugin (e.g., v"0.0.1")',
)
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
    with_docs: bool,
    with_ci: bool,
    with_codecov: bool,
    formatter_style: Optional[str],
    julia_version: Optional[str],
    ssh: Optional[bool],
    ignore_patterns: Optional[str],
    tests_aqua: Optional[bool],
    tests_jet: Optional[bool],
    tests_project: Optional[bool],
    project_version: Optional[str],
):
    """Create a new Julia package"""

    if not package_name.replace("_", "").replace("-", "").isalnum():
        click.echo(
            "Error: Package name must contain only letters, numbers, hyphens, and underscores",
            err=True,
        )
        sys.exit(1)

    if not package_name[0].isalpha():
        click.echo("Error: Package name must start with a letter", err=True)
        sys.exit(1)

    config = load_config()
    defaults = config.get("default", {})

    # Get author from config if not provided (let PkgTemplates.jl handle git config fallback)
    if not author:
        author = defaults.get("author") or None

    # Get user from config if not provided (let PkgTemplates.jl handle git config fallback)
    if not user:
        user = defaults.get("user") or None

    # Get mail from config if not provided (let PkgTemplates.jl handle git config fallback)
    if not mail:
        mail = defaults.get("mail") or None

    if license is None:
        license = defaults.get("license")

    if template is None:
        template = defaults.get("template") or "standard"

    if formatter_style is None:
        formatter_style = defaults.get("formatter_style") or "nostyle"

    if julia_version is None:
        julia_version = defaults.get("julia_version") or "1.10"

    if ssh is None:
        ssh = bool(defaults.get("ssh", False))

    if ignore_patterns is None:
        ignore_patterns = defaults.get("ignore_patterns") or ""

    if tests_aqua is None:
        tests_aqua = bool(defaults.get("tests_aqua", False))

    if tests_jet is None:
        tests_jet = bool(defaults.get("tests_jet", False))

    if tests_project is None:
        tests_project = bool(defaults.get("tests_project", True))

    if project_version is None:
        project_version = defaults.get("project_version") or "0.1.0"

    click.echo(f"Creating Julia package: {package_name}")
    click.echo(f"Author: {author if author is not None else 'None'}")
    click.echo(f"User: {user if user is not None else 'None (will use git config)'}")
    click.echo(f"Mail: {mail if mail is not None else 'None (will use git config)'}")
    click.echo(f"Template: {template}")
    click.echo(f"Output directory: {output_dir}")

    try:
        generator = JuliaPackageGenerator()
        config = PackageConfig(
            template=template,
            license_type=license,
            with_docs=with_docs,
            with_ci=with_ci,
            with_codecov=with_codecov,
            formatter_style=formatter_style,
            julia_version=julia_version,
            ssh=ssh,
            ignore_patterns=ignore_patterns,
            tests_aqua=tests_aqua,
            tests_jet=tests_jet,
            tests_project=tests_project,
            project_version=project_version,
        )
        package_dir = generator.create_package(
            package_name=package_name,
            author=author,
            user=user,
            mail=mail,
            output_dir=Path(output_dir),
            config=config,
        )

        click.echo(f"\nPackage created successfully at: {package_dir}")
        click.echo("\nNext steps:")
        click.echo(f"  cd {package_dir.name}")
        click.echo("  mise run instantiate  # Install dependencies")
        click.echo("  mise run test         # Run tests")
        click.echo("  mise run repl         # Start Julia REPL")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--author", "-a", help="Default author name")
@click.option("--user", "-u", help="Default GitHub username")
@click.option("--mail", "-m", help="Default email address")
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
    help="Default license type",
)
@click.option(
    "--template",
    type=click.Choice(["minimal", "standard", "full"]),
    help="Default template type",
)
@click.option(
    "--formatter-style",
    type=click.Choice(["nostyle", "sciml", "blue", "yas"]),
    help="Default JuliaFormatter style",
)
@click.option(
    "--julia-version",
    help="Default Julia version constraint",
)
@click.option(
    "--ssh/--no-ssh",
    default=None,
    help="Default SSH setting for Git operations",
)
@click.option(
    "--ignore-patterns",
    help="Default comma-separated list of Git ignore patterns",
)
@click.option(
    "--tests-aqua/--no-tests-aqua",
    default=None,
    help="Default Aqua.jl setting for Tests plugin",
)
@click.option(
    "--tests-jet/--no-tests-jet",
    default=None,
    help="Default JET.jl setting for Tests plugin",
)
@click.option(
    "--tests-project/--no-tests-project",
    default=None,
    help="Default separate project setting for tests",
)
@click.option(
    "--project-version",
    help="Default initial version for ProjectFile plugin",
)
def config(
    author: Optional[str],
    user: Optional[str],
    mail: Optional[str],
    license: Optional[str],
    template: Optional[str],
    formatter_style: Optional[str],
    julia_version: Optional[str],
    ssh: Optional[bool],
    ignore_patterns: Optional[str],
    tests_aqua: Optional[bool],
    tests_jet: Optional[bool],
    tests_project: Optional[bool],
    project_version: Optional[str],
):
    """Configure default settings"""
    config = load_config()

    if "default" not in config:
        config["default"] = {}

    if author:
        config["default"]["author"] = author
        click.echo(f"Set default author: {author}")

    if user:
        config["default"]["user"] = user
        click.echo(f"Set default user: {user}")

    if mail:
        config["default"]["mail"] = mail
        click.echo(f"Set default mail: {mail}")

    if license:
        config["default"]["license"] = license
        click.echo(f"Set default license: {license}")

    if template:
        config["default"]["template"] = template
        click.echo(f"Set default template: {template}")

    if formatter_style:
        config["default"]["formatter_style"] = formatter_style
        click.echo(f"Set default formatter style: {formatter_style}")

    if julia_version:
        config["default"]["julia_version"] = julia_version
        click.echo(f"Set default Julia version: {julia_version}")

    if ssh is not None:
        config["default"]["ssh"] = ssh
        click.echo(f"Set default SSH: {ssh}")

    if ignore_patterns:
        config["default"]["ignore_patterns"] = ignore_patterns
        click.echo(f"Set default ignore patterns: {ignore_patterns}")

    if tests_aqua is not None:
        config["default"]["tests_aqua"] = tests_aqua
        click.echo(f"Set default tests Aqua: {tests_aqua}")

    if tests_jet is not None:
        config["default"]["tests_jet"] = tests_jet
        click.echo(f"Set default tests JET: {tests_jet}")

    if tests_project is not None:
        config["default"]["tests_project"] = tests_project
        click.echo(f"Set default tests project: {tests_project}")

    if project_version:
        config["default"]["project_version"] = project_version
        click.echo(f"Set default project version: {project_version}")

    save_config(config)
    click.echo(f"Configuration saved to: {get_config_path()}")


if __name__ == "__main__":
    main()

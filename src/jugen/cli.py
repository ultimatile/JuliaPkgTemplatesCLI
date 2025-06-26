"""
CLI interface for jugen - Julia package generator
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click

from .generator import JuliaPackageGenerator


def get_config_path() -> Path:
    """Get the configuration file path using XDG_CONFIG_HOME"""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_dir = Path(xdg_config_home)
    else:
        config_dir = Path.home() / ".config"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "jugen.toml"


def load_config() -> dict:
    """Load configuration from jugen.toml"""
    config_path = get_config_path()
    config = {}

    if config_path.exists():
        try:
            # Try Python 3.11+ tomllib first, then fallback to tomli
            try:
                import tomllib

                with open(config_path, "rb") as f:
                    config = tomllib.load(f)
            except ImportError:
                import tomli

                with open(config_path, "rb") as f:
                    config = tomli.load(f)
        except Exception as e:
            click.echo(
                f"Warning: Error loading config file {config_path}: {e}", err=True
            )

    return config


def save_config(config: dict) -> None:
    """Save configuration to jugen.toml"""
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


@click.group()
@click.version_option()
def main():
    """jugen - Julia package generator with PkgTemplates.jl and mise tasks integration"""
    pass


@main.command()
@click.argument("package_name")
@click.option("--author", "-a", help="Author name for the package")
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
    help="Template type (default: standard or config value)",
)
@click.option(
    "--license",
    type=click.Choice(["MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0"]),
    help="License type (default: MIT or config value)",
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
    help="JuliaFormatter style (default: nostyle or config value)",
)
@click.pass_context
def create(
    ctx: click.Context,
    package_name: str,
    author: Optional[str],
    output_dir: str,
    template: Optional[str],
    license: Optional[str],
    with_docs: bool,
    with_ci: bool,
    with_codecov: bool,
    formatter_style: Optional[str],
):
    """Create a new Julia package"""

    # Validate package name
    if not package_name.replace("_", "").replace("-", "").isalnum():
        click.echo(
            "Error: Package name must contain only letters, numbers, hyphens, and underscores",
            err=True,
        )
        sys.exit(1)

    if not package_name[0].isalpha():
        click.echo("Error: Package name must start with a letter", err=True)
        sys.exit(1)

    # Load config for defaults
    config = load_config()
    defaults = config.get("default", {})

    # Get author from config or prompt
    if not author:
        author = defaults.get("author")
        if not author:
            author = click.prompt("Author name")

    # Apply config defaults for other options if not explicitly set
    if license is None:
        license = defaults.get("license", "MIT")

    if template is None:
        template = defaults.get("template", "standard")

    if formatter_style is None:
        formatter_style = defaults.get("formatter_style", "nostyle")

    click.echo(f"Creating Julia package: {package_name}")
    click.echo(f"Author: {author}")
    click.echo(f"Template: {template}")
    click.echo(f"Output directory: {output_dir}")

    try:
        generator = JuliaPackageGenerator()
        package_dir = generator.create_package(
            package_name=package_name,
            author=author,
            output_dir=Path(output_dir),
            template=template,
            license_type=license,
            with_docs=with_docs,
            with_ci=with_ci,
            with_codecov=with_codecov,
            formatter_style=formatter_style,
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
@click.option(
    "--license",
    type=click.Choice(["MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0"]),
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
def config(author: Optional[str], license: Optional[str], template: Optional[str], formatter_style: Optional[str]):
    """Configure default settings"""
    config = load_config()

    # Update config
    if "default" not in config:
        config["default"] = {}

    if author:
        config["default"]["author"] = author
        click.echo(f"Set default author: {author}")

    if license:
        config["default"]["license"] = license
        click.echo(f"Set default license: {license}")

    if template:
        config["default"]["template"] = template
        click.echo(f"Set default template: {template}")

    if formatter_style:
        config["default"]["formatter_style"] = formatter_style
        click.echo(f"Set default formatter style: {formatter_style}")

    # Save config
    save_config(config)
    click.echo(f"Configuration saved to: {get_config_path()}")


if __name__ == "__main__":
    main()

"""
CLI interface for jugen - Julia package generator
"""

import sys
from pathlib import Path
from typing import Optional

import click

from .generator import JuliaPackageGenerator


@click.group()
@click.version_option()
def main():
    """jugen - Julia package generator with PkgTemplates.jl and mise tasks integration"""
    pass


@main.command()
@click.argument('package_name')
@click.option('--author', '-a', help='Author name for the package')
@click.option('--output-dir', '-o', type=click.Path(), default='.', 
              help='Output directory (default: current directory)')
@click.option('--template', '-t', default='standard',
              type=click.Choice(['minimal', 'standard', 'full']),
              help='Template type (default: standard)')
@click.option('--license', type=click.Choice(['MIT', 'Apache-2.0', 'BSD-3-Clause', 'GPL-3.0']),
              default='MIT', help='License type (default: MIT)')
@click.option('--with-docs/--no-docs', default=True, 
              help='Include documentation setup (default: yes)')
@click.option('--with-ci/--no-ci', default=True,
              help='Include CI/CD setup (default: yes)')
@click.option('--with-codecov/--no-codecov', default=True,
              help='Include Codecov integration (default: yes)')
def create(
    package_name: str,
    author: Optional[str],
    output_dir: str,
    template: str,
    license: str,
    with_docs: bool,
    with_ci: bool,
    with_codecov: bool
):
    """Create a new Julia package"""
    
    # Validate package name
    if not package_name.replace('_', '').replace('-', '').isalnum():
        click.echo("Error: Package name must contain only letters, numbers, hyphens, and underscores", err=True)
        sys.exit(1)
    
    if not package_name[0].isalpha():
        click.echo("Error: Package name must start with a letter", err=True)
        sys.exit(1)
    
    # Get author from config or prompt
    if not author:
        config_path = Path.home() / '.jugen.toml'
        if config_path.exists():
            try:
                import tomli
                with open(config_path, 'rb') as f:
                    config = tomli.load(f)
                    author = config.get('default', {}).get('author')
            except Exception:
                pass
        
        if not author:
            author = click.prompt('Author name')
    
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
            with_codecov=with_codecov
        )
        
        click.echo(f"\n✅ Package created successfully at: {package_dir}")
        click.echo("\nNext steps:")
        click.echo(f"  cd {package_dir.name}")
        click.echo("  mise run instantiate  # Install dependencies")
        click.echo("  mise run test         # Run tests")
        click.echo("  mise run repl         # Start Julia REPL")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--author', '-a', help='Default author name')
@click.option('--license', type=click.Choice(['MIT', 'Apache-2.0', 'BSD-3-Clause', 'GPL-3.0']),
              help='Default license type')
@click.option('--template', type=click.Choice(['minimal', 'standard', 'full']),
              help='Default template type')
def config(author: Optional[str], license: Optional[str], template: Optional[str]):
    """Configure default settings"""
    import tomli_w
    
    config_path = Path.home() / '.jugen.toml'
    config = {}
    
    # Load existing config
    if config_path.exists():
        try:
            import tomli
            with open(config_path, 'rb') as f:
                config = tomli.load(f)
        except Exception:
            pass
    
    # Update config
    if 'default' not in config:
        config['default'] = {}
    
    if author:
        config['default']['author'] = author
        click.echo(f"Set default author: {author}")
    
    if license:
        config['default']['license'] = license
        click.echo(f"Set default license: {license}")
    
    if template:
        config['default']['template'] = template
        click.echo(f"Set default template: {template}")
    
    # Save config
    try:
        with open(config_path, 'wb') as f:
            tomli_w.dump(config, f)
        click.echo(f"Configuration saved to: {config_path}")
    except Exception as e:
        click.echo(f"Error saving configuration: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

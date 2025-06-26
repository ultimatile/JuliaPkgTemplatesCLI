"""
Julia package generator using PkgTemplates.jl and Jinja2
"""

import subprocess
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader


class JuliaPackageGenerator:
    """Julia package generator with PkgTemplates.jl and mise integration"""

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.scripts_dir = Path(__file__).parent / "scripts"

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def create_package(
        self,
        package_name: str,
        author: str,
        output_dir: Path,
        template: str = "standard",
        license_type: str = "MIT",
        with_docs: bool = True,
        with_ci: bool = True,
        with_codecov: bool = True,
        formatter_style: str = "nostyle",
    ) -> Path:
        """
        Create a new Julia package using PkgTemplates.jl

        Args:
            package_name: Name of the package
            author: Author name
            output_dir: Directory where package will be created
            template: Template type (minimal, standard, full)
            license_type: License type
            with_docs: Include documentation
            with_ci: Include CI/CD
            with_codecov: Include Codecov
            formatter_style: JuliaFormatter style (nostyle, sciml, blue, yas)

        Returns:
            Path to the created package directory
        """
        # Validate inputs
        output_dir = Path(output_dir).resolve()
        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        # Determine plugins based on template type
        plugins = self._get_plugins(
            template, license_type, with_docs, with_ci, with_codecov, formatter_style
        )

        # Call Julia script to create package
        package_dir = self._call_julia_generator(
            package_name, author, output_dir, plugins
        )

        # Add mise configuration
        self._add_mise_config(package_dir, package_name)

        return package_dir

    def _get_plugins(
        self,
        template: str,
        license_type: str,
        with_docs: bool,
        with_ci: bool,
        with_codecov: bool,
        formatter_style: str,
    ) -> Dict[str, Any]:
        """Get PkgTemplates.jl plugins configuration"""
        base_plugins = [
            f'License(; name="{license_type}")',
            "Git(; manifest=true)",
            f'Formatter(; style="{formatter_style}")',
        ]

        if template == "minimal":
            plugins = base_plugins
        elif template == "standard":
            plugins = base_plugins + [
                "GitHubActions()" if with_ci else None,
                "Codecov()" if with_codecov else None,
            ]
        elif template == "full":
            plugins = base_plugins + [
                "GitHubActions()" if with_ci else None,
                "Codecov()" if with_codecov else None,
                "Documenter{GitHubActions}()" if with_docs else None,
                "TagBot()",
                "CompatHelper()",
            ]
        else:
            raise ValueError(f"Unknown template type: {template}")

        # Filter out None values
        plugins = [p for p in plugins if p is not None]

        return {
            "plugins": plugins,
            "license_type": license_type,
            "with_docs": with_docs,
            "with_ci": with_ci,
            "with_codecov": with_codecov,
        }

    def _call_julia_generator(
        self, package_name: str, author: str, output_dir: Path, plugins: Dict[str, Any]
    ) -> Path:
        """Call Julia script to generate package"""
        julia_script = self.scripts_dir / "pkg_generator.jl"

        if not julia_script.exists():
            raise FileNotFoundError(f"Julia script not found: {julia_script}")

        # Convert plugins to Julia array format
        plugins_str = "[" + ", ".join(plugins["plugins"]) + "]"

        # Call Julia script
        cmd = [
            "julia",
            str(julia_script),
            package_name,
            author,
            str(output_dir),
            plugins_str,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse output to get package directory
            package_dir = output_dir / package_name
            if not package_dir.exists():
                raise RuntimeError(f"Package directory not created: {package_dir}")

            return package_dir

        except subprocess.CalledProcessError as e:
            # Check if the error is actually a failure by looking for error indicators
            if "Error creating package:" in e.stdout or "Error:" in e.stdout:
                error_msg = f"Julia script failed: {e.stdout}"
                if "PkgTemplates" in e.stderr:
                    error_msg += "\nHint: Make sure PkgTemplates.jl is installed: julia -e 'using Pkg; Pkg.add(\"PkgTemplates\")'"
                raise RuntimeError(error_msg) from e
            else:
                # Package might have been created successfully despite stderr output
                package_dir = output_dir / package_name
                if package_dir.exists():
                    return package_dir
                else:
                    error_msg = f"Julia script failed: {e.stderr}"
                    raise RuntimeError(error_msg) from e
        except FileNotFoundError:
            raise RuntimeError(
                "Julia not found. Please install Julia and ensure it's in your PATH."
            )

    def _add_mise_config(self, package_dir: Path, package_name: str) -> None:
        """Add mise configuration to the package"""
        template = self.jinja_env.get_template("mise.toml.j2")

        mise_content = template.render(package_name=package_name, project_dir=".")

        mise_file = package_dir / ".mise.toml"
        mise_file.write_text(mise_content)

    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """Check if required dependencies are available"""
        dependencies = {}

        # Check Julia
        try:
            result = subprocess.run(
                ["julia", "--version"], capture_output=True, check=True
            )
            dependencies["julia"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            dependencies["julia"] = False

        # Check PkgTemplates.jl
        try:
            result = subprocess.run(
                ["julia", "-e", "using PkgTemplates"], capture_output=True, check=True
            )
            dependencies["pkgtemplates"] = True
        except subprocess.CalledProcessError:
            dependencies["pkgtemplates"] = False

        # Check mise
        try:
            result = subprocess.run(
                ["mise", "--version"], capture_output=True, check=True
            )
            dependencies["mise"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            dependencies["mise"] = False

        return dependencies

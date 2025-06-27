"""
Julia package generator using PkgTemplates.jl and Jinja2
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from jinja2 import Environment, FileSystemLoader


class JuliaPackageGenerator:
    """Julia package generator with PkgTemplates.jl and mise integration"""

    # Map user-friendly license names to PkgTemplates.jl license identifiers
    LICENSE_MAPPING = {
        "MIT": "MIT",
        "Apache": "ASL",
        "BSD2": "BSD2",
        "BSD3": "BSD3",
        "GPL2": "GPL-2.0+",
        "GPL3": "GPL-3.0+",
        "MPL": "MPL",
        "ISC": "ISC",
        "LGPL2": "LGPL-2.1+",
        "LGPL3": "LGPL-3.0+",
        "AGPL3": "AGPL-3.0+",
        "EUPL": "EUPL-1.2+",
    }

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.scripts_dir = Path(__file__).parent / "scripts"

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _map_license(self, license_name: str) -> str:
        """Map user-friendly license name to PkgTemplates.jl identifier"""
        mapped_license = self.LICENSE_MAPPING.get(license_name, license_name)
        if (
            mapped_license == license_name
            and license_name not in self.LICENSE_MAPPING.values()
        ):
            # If no mapping found and it's not a valid PkgTemplates.jl license, warn
            logging.warning(f"Unknown license '{license_name}', using as-is")
        return mapped_license

    def create_package(
        self,
        package_name: str,
        author: Optional[str],
        user: Optional[str],
        output_dir: Path,
        template: str = "standard",
        license_type: str = "MIT",
        with_docs: bool = True,
        with_ci: bool = True,
        with_codecov: bool = True,
        formatter_style: str = "nostyle",
        julia_version: Optional[str] = None,
        ssh: bool = False,
        ignore_patterns: Optional[str] = None,
        tests_aqua: bool = False,
        tests_jet: bool = False,
        tests_project: bool = True,
        project_version: Optional[str] = None,
    ) -> Path:
        """
        Create a new Julia package using PkgTemplates.jl

        Args:
            package_name: Name of the package
            author: Author name
            user: Git hosting username
            output_dir: Directory where package will be created
            template: Template type (minimal, standard, full)
            license_type: License type
            with_docs: Include documentation
            with_ci: Include CI/CD
            with_codecov: Include Codecov
            formatter_style: JuliaFormatter style (nostyle, sciml, blue, yas)
            julia_version: Julia version constraint for Template constructor
            ssh: Use SSH for Git operations
            ignore_patterns: Comma-separated list of patterns to ignore in Git
            tests_aqua: Enable Aqua.jl in Tests plugin
            tests_jet: Enable JET.jl in Tests plugin
            tests_project: Enable separate project for tests
            project_version: Initial version for ProjectFile plugin

        Returns:
            Path to the created package directory
        """
        output_dir = Path(output_dir).resolve()
        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        plugins = self._get_plugins(
            template,
            license_type,
            with_docs,
            with_ci,
            with_codecov,
            formatter_style,
            ssh,
            ignore_patterns,
            tests_aqua,
            tests_jet,
            tests_project,
            project_version,
        )

        package_dir = self._call_julia_generator(
            package_name, author, user, output_dir, plugins, julia_version
        )

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
        ssh: bool,
        ignore_patterns: Optional[str],
        tests_aqua: bool,
        tests_jet: bool,
        tests_project: bool,
        project_version: Optional[str],
    ) -> Dict[str, Any]:
        """Get PkgTemplates.jl plugins configuration"""
        base_plugins = []

        version = project_version or "0.0.1"
        base_plugins.append(f'ProjectFile(; version=v"{version}")')

        mapped_license = self._map_license(license_type)
        base_plugins.append(f'License(; name="{mapped_license}")')

        git_options = ["manifest=true"]
        if ssh:
            git_options.append("ssh=true")
        if ignore_patterns:
            patterns = [
                f'"{p.strip()}"' for p in ignore_patterns.split(",") if p.strip()
            ]
            git_options.append(f"ignore=[{', '.join(patterns)}]")
        git_plugin = f"Git(; {', '.join(git_options)})"
        base_plugins.append(git_plugin)

        base_plugins.append(f'Formatter(; style="{formatter_style}")')

        test_options = []
        if tests_project:
            test_options.append("project=true")
        if tests_aqua:
            test_options.append("aqua=true")
        if tests_jet:
            test_options.append("jet=true")
        if test_options:
            tests_plugin = f"Tests(; {', '.join(test_options)})"
            base_plugins.append(tests_plugin)

        if template == "minimal":
            plugins = base_plugins
        elif template == "standard":
            additional_plugins = []
            if with_ci:
                additional_plugins.append("GitHubActions()")
            if with_codecov:
                additional_plugins.append("Codecov()")
            plugins = base_plugins + additional_plugins
        elif template == "full":
            additional_plugins = []
            if with_ci:
                additional_plugins.append("GitHubActions()")
            if with_codecov:
                additional_plugins.append("Codecov()")
            if with_docs:
                additional_plugins.append("Documenter{GitHubActions}()")
            additional_plugins.extend(["TagBot()", "CompatHelper()"])
            plugins = base_plugins + additional_plugins
        else:
            raise ValueError(f"Unknown template type: {template}")

        plugins = [p for p in plugins if p is not None]

        return {
            "plugins": plugins,
            "license_type": license_type,
            "with_docs": with_docs,
            "with_ci": with_ci,
            "with_codecov": with_codecov,
        }

    def _call_julia_generator(
        self,
        package_name: str,
        author: Optional[str],
        user: Optional[str],
        output_dir: Path,
        plugins: Dict[str, Any],
        julia_version: Optional[str] = None,
    ) -> Path:
        """Call Julia script to generate package"""
        julia_script = self.scripts_dir / "pkg_generator.jl"

        if not julia_script.exists():
            raise FileNotFoundError(f"Julia script not found: {julia_script}")

        plugins_str = "[" + ", ".join(plugins["plugins"]) + "]"

        cmd = [
            "julia",
            str(julia_script),
            package_name,
            author or "",
            user or "",
            str(output_dir),
            plugins_str,
        ]

        if julia_version:
            cmd.append(julia_version)

        try:
            _ = subprocess.run(cmd, capture_output=True, text=True, check=True)

            package_dir = output_dir / package_name
            if not package_dir.exists():
                raise RuntimeError(f"Package directory not created: {package_dir}")

            return package_dir

        except subprocess.CalledProcessError as e:
            if "Error creating package:" in e.stdout or "Error:" in e.stdout:
                error_pattern = re.compile(r"(Error:|Error creating package:)\s*(.+)")
                error_lines = error_pattern.findall(e.stdout)
                if error_lines:
                    error_msg = error_lines[-1][1]
                else:
                    error_msg = f"Julia script failed: {e.stdout}"
                if "PkgTemplates" in e.stderr:
                    error_msg += "\nHint: Make sure PkgTemplates.jl is installed: julia -e 'using Pkg; Pkg.add(\"PkgTemplates\")'"
                raise RuntimeError(error_msg) from e
            else:
                # PkgTemplates.jl may output warnings to stderr but still succeed
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

        try:
            _ = subprocess.run(["julia", "--version"], capture_output=True, check=True)
            dependencies["julia"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            dependencies["julia"] = False

        try:
            _ = subprocess.run(
                ["julia", "-e", "using PkgTemplates"], capture_output=True, check=True
            )
            dependencies["pkgtemplates"] = True
        except subprocess.CalledProcessError:
            dependencies["pkgtemplates"] = False

        try:
            _ = subprocess.run(["mise", "--version"], capture_output=True, check=True)
            dependencies["mise"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            dependencies["mise"] = False

        return dependencies

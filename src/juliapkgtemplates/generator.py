"""
Julia package generator using PkgTemplates.jl and Jinja2
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from jinja2 import Environment, FileSystemLoader


class JuliaDependencyError(Exception):
    """Raised when Julia dependencies are not available or properly configured"""

    pass


class JuliaNotFoundError(JuliaDependencyError):
    """Raised when Julia is not found in PATH"""

    def __init__(self):
        super().__init__(
            "Julia not found. Please install Julia and ensure it's in your PATH.\n"
            "Visit https://julialang.org/downloads/ for installation instructions."
        )


class PkgTemplatesError(JuliaDependencyError):
    """Raised when PkgTemplates.jl is not available or has issues"""

    def __init__(self, operation: str, stderr: str = ""):
        error_detail = f": {stderr.strip()}" if stderr.strip() else ""
        super().__init__(
            f"Failed to {operation}. This may indicate:\n"
            f"1. PkgTemplates.jl is not installed: julia -e 'using Pkg; Pkg.add(\"PkgTemplates\")'\n"
            f"2. PkgTemplates.jl version changed its internal structure\n"
            f"Error details{error_detail}"
        )


@dataclass(frozen=True)
class TemplateConfig:
    """Configuration for a package template"""

    plugins: List[str]

    def includes(self, plugin: str) -> bool:
        """Check if template includes a specific plugin"""
        return plugin in self.plugins


@dataclass
class PackageConfig:
    """Configuration for package creation"""

    enabled_plugins: Optional[List[str]] = None
    license_type: Optional[str] = None
    julia_version: Optional[str] = None
    plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    mise_filename_base: str = ".mise"
    with_mise: bool = True

    def __post_init__(self):
        if self.enabled_plugins is None:
            self.enabled_plugins = []

    @classmethod
    def from_dict(cls, config_dict: Optional[Dict[str, Any]] = None) -> "PackageConfig":
        """Create PackageConfig from dictionary, ignoring unknown keys"""
        if config_dict is None:
            return cls(plugin_options={})

        # Support both CLI and config file formats to maintain backward compatibility
        plugin_options = {}
        regular_config = {}

        for key, value in config_dict.items():
            if key == "plugin_options" and isinstance(value, dict):
                plugin_options.update(value)
            elif "." in key:
                # Config files use dot notation for nested plugin options
                plugin_name, option_name = key.split(".", 1)
                if plugin_name not in plugin_options:
                    plugin_options[plugin_name] = {}
                plugin_options[plugin_name][option_name] = value
            else:
                regular_config[key] = value

        # Prevent runtime errors from unknown configuration keys
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in regular_config.items() if k in valid_keys}

        # Config files may store lists as comma-separated strings
        if "enabled_plugins" in filtered_dict and isinstance(
            filtered_dict["enabled_plugins"], str
        ):
            filtered_dict["enabled_plugins"] = [
                p.strip()
                for p in filtered_dict["enabled_plugins"].split(",")
                if p.strip()
            ]

        # Ensure consistent plugin_options structure across all code paths
        filtered_dict["plugin_options"] = plugin_options if plugin_options else {}

        return cls(**filtered_dict)


class JuliaPackageGenerator:
    """Julia package generator with PkgTemplates.jl and mise integration"""

    # Provide convenient aliases for commonly used licenses while maintaining PkgTemplates.jl compatibility
    LICENSE_MAPPING = {
        "Apache": "ASL",
        "GPL2": "GPL-2.0+",
        "GPL3": "GPL-3.0+",
        "LGPL2": "LGPL-2.1+",
        "LGPL3": "LGPL-3.0+",
        "AGPL3": "AGPL-3.0+",
        "EUPL": "EUPL-1.2+",
    }

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"

        # Preserve template formatting by disabling automatic whitespace trimming
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=False,
            lstrip_blocks=False,
        )

    @staticmethod
    def get_available_plugins() -> List[str]:
        """Get available plugins dynamically from Julia's PkgTemplates module"""
        try:
            julia_cmd = [
                "julia",
                "-e",
                """
                using PkgTemplates
                M = PkgTemplates
                pairs = [(s, getfield(M, s)) for s in names(M; all=false, imported=true) if isdefined(M, s)]
                plugin_types = [t for (_, t) in pairs if t isa Type && t <: M.Plugin]
                plugin_names = [string(nameof(t)) for t in plugin_types]
                for name in sort(plugin_names)
                    println(name)
                end
                """,
            ]

            result = subprocess.run(
                julia_cmd, capture_output=True, text=True, check=True
            )
            plugins = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
            return plugins

        except FileNotFoundError:
            raise JuliaNotFoundError()
        except subprocess.CalledProcessError as e:
            raise PkgTemplatesError("load PkgTemplates.jl", e.stderr)

    @staticmethod
    def get_supported_licenses() -> List[str]:
        """Get supported licenses dynamically from PkgTemplates.jl"""
        try:
            julia_cmd = [
                "julia",
                "-e",
                """
                using PkgTemplates
                license_files = readdir(PkgTemplates.default_file("licenses"))
                for file in license_files
                    println(file)
                end
                """,
            ]

            result = subprocess.run(
                julia_cmd, capture_output=True, text=True, check=True
            )
            licenses = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
            return licenses

        except FileNotFoundError:
            raise JuliaNotFoundError()
        except subprocess.CalledProcessError as e:
            raise PkgTemplatesError(
                "access PkgTemplates.jl license information", e.stderr
            )

    def _map_license(self, license_name: str) -> str:
        """Convert CLI license names to PkgTemplates.jl format for interoperability"""
        mapped_license = self.LICENSE_MAPPING.get(license_name, license_name)

        supported_licenses = self.get_supported_licenses()
        if mapped_license not in supported_licenses:
            logging.warning(
                f"License '{mapped_license}' may not be supported by PkgTemplates.jl. Supported licenses: {', '.join(supported_licenses)}"
            )

        return mapped_license

    def _build_plugin(
        self,
        plugin_name: str,
        plugin_options: Optional[Dict[str, Any]] = None,
        license_type: Optional[str] = None,
    ) -> Optional[str]:
        """Generic plugin builder that handles any plugin with special License processing"""
        if plugin_name == "License":
            # License requires special mapping logic for user-friendly aliases
            license_plugin_options = {"License": plugin_options or {}}
            return self._build_license_plugin_special(
                license_type, license_plugin_options
            )

        if not plugin_options:
            return f"{plugin_name}()"

        option_strings = []
        for key, value in plugin_options.items():
            if isinstance(value, str):
                # Special handling for ProjectFile version parameter
                if plugin_name == "ProjectFile" and key == "version":
                    option_strings.append(f'{key}=v"{value}"')
                else:
                    option_strings.append(f'{key}="{value}"')
            elif isinstance(value, bool):
                option_strings.append(f"{key}={str(value).lower()}")
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    formatted_items = [f'"{item}"' for item in value]
                    option_strings.append(f"{key}=[{', '.join(formatted_items)}]")
                else:
                    option_strings.append(f"{key}={value}")
            else:
                option_strings.append(f"{key}={value}")

        if option_strings:
            return f"{plugin_name}(; {', '.join(option_strings)})"
        else:
            return f"{plugin_name}()"

    def _build_license_plugin_special(
        self,
        license_type: Optional[str],
        plugin_options: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Create License plugin with full support for all License plugin parameters"""
        license_options = {}
        license_config = (plugin_options or {}).get("License")
        license_explicitly_enabled = license_config is not None

        # Support legacy license_type parameter for backward compatibility
        if license_type:
            mapped_license = self._map_license(license_type)
            license_options["name"] = mapped_license

        # Plugin options take precedence to allow override of legacy parameter
        if license_explicitly_enabled and license_config is not None:
            for key, value in license_config.items():
                if key == "name":
                    license_options["name"] = self._map_license(value)
                else:
                    license_options[key] = value

        if not license_options:
            if license_explicitly_enabled:
                return "License()"
            return None

        option_strings = []
        for key, value in license_options.items():
            if isinstance(value, str):
                option_strings.append(f'{key}="{value}"')
            else:
                option_strings.append(f"{key}={value}")

        return f"License(; {', '.join(option_strings)})"

    def create_package(
        self,
        package_name: str,
        author: Optional[Union[str, List[str]]],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        config: Optional[PackageConfig] = None,
        verbose: bool = False,
    ) -> Path:
        """
        Create a new Julia package using PkgTemplates.jl

        Args:
            package_name: Name of the package
            author: Author name(s) - can be a string or list of strings
            user: Git hosting username
            mail: Email address
            output_dir: Directory where package will be created
            config: PackageConfig instance with package creation settings

        Returns:
            Path to the created package directory
        """
        output_dir = Path(output_dir)
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        output_dir = output_dir.resolve()

        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        cfg = config if config is not None else PackageConfig()

        plugins = self._get_plugins(
            cfg.enabled_plugins,
            cfg.license_type,
            cfg.plugin_options,
        )

        package_dir = self._call_julia_generator(
            package_name,
            author,
            user,
            mail,
            output_dir,
            plugins,
            cfg.julia_version,
            verbose,
        )

        if cfg.with_mise:
            self._add_mise_config(package_dir, package_name, cfg.mise_filename_base)

        return package_dir

    def generate_julia_code(
        self,
        package_name: str,
        author: Optional[Union[str, List[str]]],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        config: Optional[PackageConfig] = None,
    ) -> str:
        """
        Generate Julia Template function code without executing it (for dry-run mode)

        Args:
            package_name: Name of the package
            author: Author name(s) - can be a string or list of strings
            user: Git hosting username
            mail: Email address
            output_dir: Directory where package would be created
            config: PackageConfig instance with package creation settings

        Returns:
            String containing the Julia Template function code
        """
        output_dir = Path(output_dir)
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        output_dir = output_dir.resolve()

        cfg = config if config is not None else PackageConfig()

        plugins = self._get_plugins(
            cfg.enabled_plugins,
            cfg.license_type,
            cfg.plugin_options,
        )

        return self._generate_julia_template_code(
            package_name, author, user, mail, output_dir, plugins, cfg.julia_version
        )

    def _get_plugins(
        self,
        enabled_plugins: Optional[List[str]],
        license_type: Optional[str],
        plugin_options: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Assemble Julia plugin configuration based on explicitly enabled plugins using generic builder"""
        plugins = []

        # License plugin is implicitly enabled when license options are provided
        plugins_to_process = list(enabled_plugins or [])
        has_license_options = plugin_options and "License" in plugin_options
        if (
            license_type or has_license_options
        ) and "License" not in plugins_to_process:
            plugins_to_process.append("License")

        for plugin_name in plugins_to_process:
            options = plugin_options.get(plugin_name, {}) if plugin_options else {}
            plugin = self._build_plugin(plugin_name, options, license_type)
            if plugin:
                plugins.append(plugin)

        return {
            "plugins": plugins,
        }

    def _generate_julia_template_code(
        self,
        package_name: str,
        author: Optional[Union[str, List[str]]],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        plugins: Dict[str, Any],
        julia_version: Optional[str] = None,
    ) -> str:
        """Generate Julia Template function code for visualization using Jinja2 template"""
        # Generate Julia code using the same Jinja2 template
        template = self.jinja_env.get_template("julia_template.j2")

        # Normalize authors parameter to list format for template consistency
        # Supports both legacy single author and new multiple authors functionality
        if isinstance(author, list):
            authors_list = author
        elif author is not None:
            authors_list = [author]
        else:
            authors_list = None

        julia_code = template.render(
            package_name=package_name,
            authors=authors_list,
            author=authors_list[0]
            if authors_list
            else None,  # Legacy single author field for template compatibility
            user=user,
            mail=mail,
            output_dir=str(output_dir),
            plugins=plugins["plugins"],
            julia_version=julia_version,
        )

        return julia_code

    def _call_julia_generator(
        self,
        package_name: str,
        author: Optional[Union[str, List[str]]],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        plugins: Dict[str, Any],
        julia_version: Optional[str] = None,
        verbose: bool = False,
    ) -> Path:
        """Execute PkgTemplates.jl package generation via Jinja2 template"""
        # Generate Julia code using Jinja2 template
        template = self.jinja_env.get_template("julia_template.j2")

        # Normalize authors parameter to list format for template consistency
        # Supports both legacy single author and new multiple authors functionality
        if isinstance(author, list):
            authors_list = author
        elif author is not None:
            authors_list = [author]
        else:
            authors_list = None

        julia_code = template.render(
            package_name=package_name,
            authors=authors_list,
            author=authors_list[0]
            if authors_list
            else None,  # Legacy single author field for template compatibility
            user=user,
            mail=mail,
            output_dir=str(output_dir),
            plugins=plugins["plugins"],
            julia_version=julia_version,
        )

        cmd = ["julia", "-e", julia_code]

        try:
            if verbose:
                # In verbose mode, show Julia output in real-time
                _result = subprocess.run(cmd, text=True, check=True)
            else:
                # In normal mode, capture output for error handling
                _result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True
                )

            package_dir = output_dir / package_name
            if not package_dir.exists():
                raise RuntimeError(f"Package directory not created: {package_dir}")

            return package_dir

        except subprocess.CalledProcessError as e:
            if verbose:
                # In verbose mode, output was already shown, just handle the error
                package_dir = output_dir / package_name
                if package_dir.exists():
                    return package_dir
                else:
                    raise RuntimeError(
                        f"Julia execution failed with exit code {e.returncode}"
                    ) from e
            else:
                # In normal mode, parse error from captured output
                if "Error creating package:" in e.stdout or "Error:" in e.stdout:
                    error_pattern = re.compile(
                        r"(Error:|Error creating package:)\s*(.+)"
                    )
                    error_lines = error_pattern.findall(e.stdout)
                    if error_lines:
                        error_msg = error_lines[-1][1]
                    else:
                        error_msg = f"Julia execution failed: {e.stdout}"
                    # Only show PkgTemplates installation hint for actual module loading errors
                    if (
                        "ArgumentError: Package PkgTemplates not found" in e.stderr
                        or "LoadError" in e.stderr
                        and "PkgTemplates" in e.stderr
                    ):
                        error_msg += "\nHint: Make sure PkgTemplates.jl is installed: julia -e 'using Pkg; Pkg.add(\"PkgTemplates\")'"
                    raise RuntimeError(error_msg) from e
                else:
                    # Handle case where Julia generates warnings but completes successfully
                    package_dir = output_dir / package_name
                    if package_dir.exists():
                        return package_dir
                    else:
                        error_msg = f"Julia execution failed: {e.stderr}"
                        raise RuntimeError(error_msg) from e
        except FileNotFoundError:
            raise RuntimeError(
                "Julia not found. Please install Julia and ensure it's in your PATH."
            )

    def _add_mise_config(
        self, package_dir: Path, package_name: str, mise_filename_base: str = ".mise"
    ) -> None:
        """Add mise configuration to the package"""
        template = self.jinja_env.get_template("mise.toml.j2")

        mise_content = template.render(
            package_name=package_name,
            project_dir=".",
            mise_config_basename=mise_filename_base,
        )

        mise_file = package_dir / f"{mise_filename_base}.toml"
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

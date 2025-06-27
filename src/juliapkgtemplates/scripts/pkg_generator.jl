#!/usr/bin/env julia

"""
Julia script to generate packages using PkgTemplates.jl
Called from Python jugen CLI tool
"""

using Pkg

println("Loading PkgTemplates.jl...")
try
    using PkgTemplates
    println("PkgTemplates.jl loaded successfully")
catch e
    println("Error loading PkgTemplates.jl: ", e)
    rethrow(e)
end

# Try to import LibGit2 for GitError handling
try
    using LibGit2: GitError
catch
    # Define a fallback GitError check if LibGit2 is not available
    GitError = Exception
end


function parse_plugins(plugins_str::String)
  """Parse plugins string from Python and return Julia array"""
  # Plugin mapping table
  plugin_patterns = Dict(
    r"GitHubActions\(\)" => () -> GitHubActions(),
    r"Codecov\(\)" => () -> Codecov(),
    r"Documenter\{GitHubActions\}\(\)" => () -> Documenter{GitHubActions}(),
    r"Develop\(\)" => () -> Develop(),
    r"TagBot\(\)" => () -> TagBot(),
    r"CompatHelper\(\)" => () -> CompatHelper()
  )

  # Remove brackets and split by comma
  plugins_str = strip(plugins_str, ['[', ']'])
  plugin_strs = split(plugins_str, ',')

  plugins = []
  for plugin_str in plugin_strs
    plugin_str = strip(plugin_str)
    if isempty(plugin_str)
      continue
    end

    # Handle License plugin specially (requires parameter extraction)
    if occursin("License", plugin_str)
      license_match = match(r"License\(;\s*name=\"([^\"]+)\"\)", plugin_str)
      if license_match !== nothing
        license_name = license_match.captures[1]
        push!(plugins, License(; name=license_name))
      else
        push!(plugins, License(; name="MIT"))  # Default fallback
      end
      continue
    end

    # Handle Formatter plugin specially (requires parameter extraction)
    if occursin("Formatter", plugin_str)
      formatter_match = match(r"Formatter\(;\s*style=\"(\w+)\"\)", plugin_str)
      if formatter_match !== nothing
        style = formatter_match.captures[1]
        push!(plugins, Formatter(; style=style))
      else
        push!(plugins, Formatter())  # Default nostyle
      end
      continue
    end

    # Handle Git plugin with parameters (SSH, ignore patterns)
    if occursin("Git", plugin_str)
      # Parse Git plugin parameters dynamically
      git_params = Dict{Symbol, Any}()
      
      # Check for manifest
      if occursin("manifest=true", plugin_str)
        git_params[:manifest] = true
      end
      
      # Check for SSH
      if occursin("ssh=true", plugin_str)
        git_params[:ssh] = true
      end
      
      # Check for ignore patterns
      ignore_match = match(r"ignore=\[([^\]]+)\]", plugin_str)
      if ignore_match !== nothing
        ignore_str = ignore_match.captures[1]
        # Parse array of strings
        patterns = [strip(s, ['"', ' ']) for s in split(ignore_str, ',') if !isempty(strip(s))]
        git_params[:ignore] = patterns
      end
      
      push!(plugins, Git(; git_params...))
      continue
    end

    # Handle Tests plugin with parameters (aqua, jet, project)
    if occursin("Tests", plugin_str)
      test_params = Dict{Symbol, Any}()
      
      # Check for project
      if occursin("project=true", plugin_str)
        test_params[:project] = true
      end
      
      # Check for aqua
      if occursin("aqua=true", plugin_str)
        test_params[:aqua] = true
      end
      
      # Check for jet
      if occursin("jet=true", plugin_str)
        test_params[:jet] = true
      end
      
      push!(plugins, Tests(; test_params...))
      continue
    end

    # Handle ProjectFile plugin with version
    if occursin("ProjectFile", plugin_str)
      version_match = match(r"ProjectFile\(;\s*version=v\"([^\"]+)\"\)", plugin_str)
      if version_match !== nothing
        version_str = version_match.captures[1]
        push!(plugins, ProjectFile(; version=VersionNumber(version_str)))
      else
        push!(plugins, ProjectFile())
      end
      continue
    end

    # Check against plugin patterns table
    matched = false
    for (pattern, creator) in plugin_patterns
      if occursin(pattern, plugin_str)
        push!(plugins, creator())
        matched = true
        break
      end
    end

    if !matched
      @warn "Unknown plugin: $plugin_str"
    end
  end

  return plugins
end

function generate_package(package_name::String, author::String, output_dir::String, plugins_str::String, julia_version::Union{String, Nothing}=nothing)
  """Generate Julia package using PkgTemplates.jl"""

  # Parse plugins
  plugins = parse_plugins(plugins_str)

  println("Creating package: $package_name")
  println("Author: $author")
  println("Output directory: $output_dir")
  println("Plugins: $(length(plugins)) plugins configured")
  if julia_version !== nothing
    println("Julia version: $julia_version")
  end

  # Create template with optional Julia version
  template_args = Dict(:user => author, :dir => output_dir, :plugins => plugins)
  if julia_version !== nothing
    # Parse Julia version string like "v1.10.9" to VersionNumber
    version_str = replace(julia_version, "v" => "")
    template_args[:julia] = VersionNumber(version_str)
  end
  
  template = Template(; template_args...)

  # Generate package
  try
    package_dir = template(package_name)
    println("Package created successfully at: $package_dir")
    return package_dir
  catch e
    println("Error creating package: $e")
    # Print more detailed error information
    if isa(e, GitError)
      println("Git error details: $(e.msg)")
      println("Git error code: $(e.code)")
      println("Git error class: $(e.class)")
    end
    rethrow(e)
  end
end

function main()
  if length(ARGS) < 4
    println("Usage: julia pkg_generator.jl <package_name> <author> <output_dir> <plugins> [julia_version]")
    println("Example: julia pkg_generator.jl MyPackage \"John Doe\" \"/path/to/output\" \"[License(; name=\\\"MIT\\\"), Git(; manifest=true)]\" \"v1.10.9\"")
    exit(1)
  end

  package_name = ARGS[1]
  author = ARGS[2]
  output_dir = ARGS[3]
  plugins_str = ARGS[4]
  julia_version = length(ARGS) >= 5 ? ARGS[5] : nothing

  try
    generate_package(package_name, author, output_dir, plugins_str, julia_version)
  catch e
    println("Error: $e")
    exit(1)
  end
end

# Run if called directly
if abspath(PROGRAM_FILE) == @__FILE__
  main()
end

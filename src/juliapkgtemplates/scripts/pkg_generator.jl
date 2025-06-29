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

try
  using LibGit2: GitError
catch
  GitError = Exception
end


# Plugin parsers registry - each plugin type has its own parser
const PLUGIN_PARSERS = Dict{String,Function}()

function register_plugin_parser(plugin_type::String, parser::Function)
  PLUGIN_PARSERS[plugin_type] = parser
end

function parse_license_plugin(plugin_str::String)
  license_match = match(r"License\(;\s*name=\"([^\"]+)\"\)", plugin_str)
  if license_match !== nothing
    license_name = license_match.captures[1]
    return License(; name=license_name)
  else
    return License(; name="MIT")
  end
end

function parse_formatter_plugin(plugin_str::String)
  formatter_match = match(r"Formatter\(;\s*style=\"(\w+)\"\)", plugin_str)
  if formatter_match !== nothing
    style = formatter_match.captures[1]
    return Formatter(; style=style)
  else
    return Formatter()
  end
end

function parse_git_plugin(plugin_str::String)
  git_params = Dict{Symbol,Any}()

  if occursin("manifest=true", plugin_str)
    git_params[:manifest] = true
  end

  if occursin("ssh=true", plugin_str)
    git_params[:ssh] = true
  end

  ignore_match = match(r"ignore=\[([^\]]+)\]", plugin_str)
  if ignore_match !== nothing
    ignore_str = ignore_match.captures[1]
    patterns = [strip(s, ['"', ' ']) for s in split(ignore_str, ',') if !isempty(strip(s))]
    git_params[:ignore] = patterns
  end

  return Git(; git_params...)
end

function parse_tests_plugin(plugin_str::String)
  test_params = Dict{Symbol,Any}()

  if occursin("project=true", plugin_str)
    test_params[:project] = true
  end

  if occursin("aqua=true", plugin_str)
    test_params[:aqua] = true
  end

  if occursin("jet=true", plugin_str)
    test_params[:jet] = true
  end

  return Tests(; test_params...)
end

function parse_projectfile_plugin(plugin_str::String)
  version_match = match(r"ProjectFile\(;\s*version=v\"([^\"]+)\"\)", plugin_str)
  if version_match !== nothing
    version_str = version_match.captures[1]
    return ProjectFile(; version=VersionNumber(version_str))
  else
    return ProjectFile()
  end
end


function init_plugin_parsers()
  parametric_plugins = Dict(
    "License" => parse_license_plugin,
    "Formatter" => parse_formatter_plugin,
    "Git" => parse_git_plugin,
    "Tests" => parse_tests_plugin,
    "ProjectFile" => parse_projectfile_plugin
  )

  parameterless_plugins = Dict(
    "GitHubActions" => (plugin_str) -> GitHubActions(),
    "Codecov" => (plugin_str) -> Codecov(),
    "Documenter{GitHubActions}" => (plugin_str) -> Documenter{GitHubActions}(),
    "Develop" => (plugin_str) -> Develop(),
    "TagBot" => (plugin_str) -> TagBot(),
    "CompatHelper" => (plugin_str) -> CompatHelper()
  )

  # Register parametric plugins
  for (plugin_type, parser) in parametric_plugins
    register_plugin_parser(plugin_type, parser)
  end

  # Register parameterless plugins
  for (plugin_type, parser) in parameterless_plugins
    register_plugin_parser(plugin_type, parser)
  end
end

function find_plugin_type(plugin_str::String)
  for plugin_type in keys(PLUGIN_PARSERS)
    if occursin(plugin_type, plugin_str)
      return plugin_type
    end
  end
  return nothing
end

function parse_plugins(plugins_str::String)
  init_plugin_parsers()

  plugins_str = strip(plugins_str, ['[', ']'])
  plugin_strs = split(plugins_str, ',')

  plugins = []
  for plugin_str in plugin_strs
    plugin_str = strip(plugin_str)
    if isempty(plugin_str)
      continue
    end

    plugin_type = find_plugin_type(plugin_str)
    if !isnothing(plugin_type)
      parser = PLUGIN_PARSERS[plugin_type]
      try
        plugin = parser(plugin_str)
        push!(plugins, plugin)
      catch e
        @warn "Error parsing plugin $plugin_str: $e"
      end
    else
      @warn "Unknown plugin: $plugin_str"
    end
  end

  return plugins
end

function generate_package(package_name::String, author::String, user::String, mail::String, output_dir::String, plugins_str::String, julia_version::Union{String,Nothing}=nothing)
  """Generate Julia package using PkgTemplates.jl"""

  plugins = parse_plugins(plugins_str)

  println("Creating package: $package_name")
  println("Author: $author")
  println("User: $user")
  println("Output directory: $output_dir")
  println("Plugins: $(length(plugins)) plugins configured")
  if !isnothing(julia_version)
    println("Julia version: $julia_version")
  end

  template_args = Dict(:dir => output_dir, :plugins => plugins)

  # Handle author and mail combination
  if !isempty(author) && !isempty(mail)
    # When both author and mail are provided, combine them in "Name <email>" format
    template_args[:authors] = ["$author <$mail>"]
  elseif !isempty(author)
    # Only author provided
    template_args[:authors] = [author]
  end
  # If neither is provided, PkgTemplates.jl will use git config fallback

  # Add user parameter if provided (otherwise PkgTemplates.jl uses git config)
  if !isempty(user)
    template_args[:user] = user
  end

  if !isnothing(julia_version)
    version_str = replace(julia_version, "v" => "")
    template_args[:julia] = VersionNumber(version_str)
  end

  template = Template(; template_args...)

  try
    package_dir = template(package_name)
    println("Package created successfully at: $package_dir")
    return package_dir
  catch e
    println("Error creating package: $e")
    if isa(e, GitError)
      println("Git error details: $(e.msg)")
      println("Git error code: $(e.code)")
      println("Git error class: $(e.class)")
    end
    rethrow(e)
  end
end

function main()
  if length(ARGS) < 6
    println("Usage: julia pkg_generator.jl <package_name> <author> <user> <mail> <output_dir> <plugins> [julia_version]")
    println("Example: julia pkg_generator.jl MyPackage \"John Doe\" \"johndoe\" \"john@example.com\" \"/path/to/output\" \"[License(; name=\\\"MIT\\\"), Git(; manifest=true)]\" \"v1.10.9\"")
    exit(1)
  end

  package_name = ARGS[1]
  author = ARGS[2]
  user = ARGS[3]
  mail = ARGS[4]
  output_dir = ARGS[5]
  plugins_str = ARGS[6]
  julia_version = length(ARGS) >= 7 ? ARGS[7] : nothing

  try
    generate_package(package_name, author, user, mail, output_dir, plugins_str, julia_version)
  catch e
    println("Error: $e")
    exit(1)
  end
end

if abspath(PROGRAM_FILE) == @__FILE__
  main()
end

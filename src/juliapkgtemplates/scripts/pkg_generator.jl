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


const PLUGIN_PARSERS = Dict{String,Function}()

function register_plugin_parser(plugin_type::AbstractString, parser::Function)
  PLUGIN_PARSERS[plugin_type] = parser
end

function parse_license_plugin(plugin_str::AbstractString)
  license_match = match(r"License\(;\s*name=\"([^\"]+)\"\)", plugin_str)
  if !isnothing(license_match)
    license_name = license_match.captures[1]
    return License(; name=license_name)
  else
    return License(; name="MIT")
  end
end

function parse_formatter_plugin(plugin_str::AbstractString)
  formatter_match = match(r"Formatter\(;\s*style=\"(\w+)\"\)", plugin_str)
  if !isnothing(formatter_match)
    style = formatter_match.captures[1]
    return Formatter(; style=style)
  else
    return Formatter()
  end
end

function parse_git_plugin(plugin_str::AbstractString)
  git_params = Dict{Symbol,Any}()

  manifest_match = match(r"manifest=(true|false)", plugin_str)
  if !isnothing(manifest_match)
    git_params[:manifest] = manifest_match.captures[1] == "true"
  end

  ssh_match = match(r"ssh=(true|false)", plugin_str)
  if !isnothing(ssh_match)
    git_params[:ssh] = ssh_match.captures[1] == "true"
  end

  ignore_match = match(r"ignore=\[([^\]]+)\]", plugin_str)
  if !isnothing(ignore_match)
    ignore_str = ignore_match.captures[1]
    patterns = [strip(s, ['"', ' ']) for s in split(ignore_str, ',') if !isempty(strip(s))]
    git_params[:ignore] = patterns
  end

  return Git(; git_params...)
end

function parse_tests_plugin(plugin_str::AbstractString)
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

function parse_projectfile_plugin(plugin_str::AbstractString)
  version_match = match(r"ProjectFile\(;\s*version=v\"([^\"]+)\"\)", plugin_str)
  if !isnothing(version_match)
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

  for (plugin_type, parser) in parametric_plugins
    register_plugin_parser(plugin_type, parser)
  end

  for (plugin_type, parser) in parameterless_plugins
    register_plugin_parser(plugin_type, parser)
  end
end

function find_plugin_type(plugin_str::AbstractString)
  plugin_type = match(r"^([A-Za-z{}\[\]]+)", plugin_str)
  if isnothing(plugin_type)
    return nothing
  end
  
  extracted_type = plugin_type.captures[1]
  
  if haskey(PLUGIN_PARSERS, extracted_type)
    return extracted_type
  end
  
  return nothing
end

function parse_plugins(plugins_str::AbstractString)
  init_plugin_parsers()

  plugins_str = strip(plugins_str, ['[', ']'])
  
  plugin_strs = []
  current_plugin = ""
  paren_depth = 0
  bracket_depth = 0
  in_quotes = false
  quote_char = '\0'
  
  for char in plugins_str
    if !in_quotes && (char == '"' || char == '\'')
      in_quotes = true
      quote_char = char
    elseif in_quotes && char == quote_char
      in_quotes = false
      quote_char = '\0'
    elseif !in_quotes
      if char == '('
        paren_depth += 1
      elseif char == ')'
        paren_depth -= 1
      elseif char == '['
        bracket_depth += 1
      elseif char == ']'
        bracket_depth -= 1
      elseif char == ',' && paren_depth == 0 && bracket_depth == 0
        push!(plugin_strs, strip(current_plugin))
        current_plugin = ""
        continue
      end
    end
    current_plugin *= char
  end
  
  if !isempty(strip(current_plugin))
    push!(plugin_strs, strip(current_plugin))
  end

  plugins = []
  seen_plugin_types = Set{String}()
  
  for plugin_str in plugin_strs
    plugin_str = strip(plugin_str)
    if isempty(plugin_str)
      continue
    end

    plugin_type = find_plugin_type(plugin_str)
    if !isnothing(plugin_type)
      if plugin_type in seen_plugin_types
        @warn "Duplicate plugin type '$plugin_type' found. Skipping: $plugin_str"
        continue
      end
      
      parser = PLUGIN_PARSERS[plugin_type]
      try
        plugin = parser(plugin_str)
        push!(plugins, plugin)
        push!(seen_plugin_types, plugin_type)
      catch e
        @warn "Error parsing plugin $plugin_str: $e"
      end
    else
      @warn "Unknown plugin: $plugin_str"
    end
  end

  return plugins
end

function generate_package(package_name::AbstractString, author::AbstractString, user::AbstractString, mail::AbstractString, output_dir::AbstractString, plugins_str::AbstractString, julia_version::Union{AbstractString,Nothing}=nothing)
  """Create Julia package with PkgTemplates.jl using provided configuration"""

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

  if !isempty(author) && !isempty(mail)
    template_args[:authors] = ["$author <$mail>"]
  elseif !isempty(author)
    template_args[:authors] = [author]
  end

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

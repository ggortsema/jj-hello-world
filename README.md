# jj-hello-world

Permanent reference implementation for a `jj-core` CLI plugin.

This project is deliberately hosted and installed from Git. It is **not**
published to PyPI. It demonstrates the conventions every public or private JJ
plugin follows.

## Repository convention

The repository root contains:

```text
jj-plugin.toml
pyproject.toml
src/
```

`jj-plugin.toml` declares plugin identity and core compatibility. The Python
project declares a matching entry point:

```toml
[project.entry-points."jj.plugins"]
hello-world = "jj_hello_world.plugin:plugin"
```

The entry point resolves to a `jj_core.plugin_api.CliPlugin`, and the plugin owns
its Typer namespace and commands.

## Install by friendly name

`jj-core`'s packaged catalog maps `hello-world` to this GitHub repository:

```bash
jj plugin install hello-world
```

Then:

```bash
jj --help
jj hello-world --help
jj hello-world say-hello Grant
```

Output:

```text
Hello, Grant!
```

## Install by repository

The same plugin can be installed without a catalog entry:

```bash
jj plugin install https://github.com/ggortsema/jj-hello-world.git
```

JJ clones the repository long enough to inspect `jj-plugin.toml`, pins the exact
commit, and asks uv to include that Git package in the JJ tool environment.

## Local development

With `jj-core` and `jj-hello-world` as sibling directories:

```bash
cd ../jj-core
uv tool install -e .
jj plugin install ../jj-hello-world
```

The local plugin is installed editable. Its source stays in this directory.

The plugin also retains a tiny standalone development command:

```bash
uv sync
uv run jj-hello-world Grant
```

Output:

```text
Hello, Grant!
```

## Files to copy when creating another plugin

- `jj-plugin.toml` — identity and compatibility metadata.
- `pyproject.toml` — normal package metadata and the `jj.plugins` entry point.
- `src/jj_hello_world/plugin.py` — registration object.
- `src/jj_hello_world/commands.py` — plugin-owned Typer namespace.
- `tests/` — command and descriptor consistency examples.

No PyPI project, token, Trusted Publisher, or plugin release workflow is
required.

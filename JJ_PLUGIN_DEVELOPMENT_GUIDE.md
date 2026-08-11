# JJ Plugin Development Guide

**Applies to:** `jj-core` 0.1.x  
**Plugin descriptor schema:** 1  
**Python entry-point group:** `jj.plugins`  
**Reference implementation:** `jj-hello-world`

This guide documents the plugin contract that is implemented and working in
`jj-core` 0.1.0. It covers the required files and metadata, CLI registration,
local development, Git installation, friendly-name catalogs, testing,
versioning, secrets, and troubleshooting.

---

## 1. Mental model

`jj-core` is the lightweight platform runtime. A capability plugin is a
separate Python project, normally stored in its own Git repository.

```text
jj-core
  owns:
    - the global `jj` executable
    - plugin installation and removal
    - desired plugin state
    - entry-point discovery
    - CLI namespace composition
    - plugin contract validation

jj-<capability>
  owns:
    - provider- or capability-specific behavior
    - its Typer CLI namespace
    - commands, arguments, options, and help
    - API clients and services
    - authentication behavior
    - tests
```

A plugin does **not** need to be published to PyPI. JJ installs it from a local
directory or Git repository and composes it into the uv-managed `jj-core` tool
environment.

The intended user experience is:

```bash
uv tool install jj-core

jj plugin install hello-world
jj --help
jj hello-world say-hello Grant
```

---

## 2. What belongs in a plugin

Provider-native or capability-specific functionality belongs in a plugin:

```text
jj-github
jj-jira
jj-cloudflare
jj-datadog
jj-forge-misc
```

A new command should normally require **no change to `jj-core`**.

A core change is appropriate only when the platform itself needs a new
cross-cutting primitive, such as:

- a new extension point;
- plugin dependency support;
- shared agent-tool registration;
- common policy, approval, or audit contracts;
- common secret-provider registration;
- plugin lifecycle, compatibility, or diagnostics improvements.

A useful test is:

> If every optional plugin were removed, would this feature still make sense in
> `jj-core`?

Provider behavior generally fails that test and belongs in a plugin.

---

## 3. Prerequisites

For plugin development:

- `uv`;
- Git;
- a compatible Python version, currently Python 3.12 or newer;
- `jj-core`, either installed from PyPI or available as a sibling source tree.

A convenient local layout is:

```text
johnny-johnny/
├── jj-core/
└── jj-greeter/
```

Install the released core globally:

```bash
uv tool install --force jj-core
```

During core development, install the local core editable instead:

```bash
cd jj-core
uv tool install --force -e .
```

---

## 4. Required plugin contract

A JJ CLI plugin currently needs all of the following:

1. A normal installable Python project.
2. A root-level file named exactly `jj-plugin.toml`.
3. A `[project.entry-points."jj.plugins"]` entry in `pyproject.toml`.
4. An entry-point object that resolves to
   `jj_core.plugin_api.CliPlugin`.
5. A plugin-owned Typer application.
6. Matching identity, version, distribution, namespace, and entry-point
   metadata.

The current convention is **one JJ plugin per repository/distribution**.

---

## 5. Minimal repository layout

Required or effectively required:

```text
jj-greeter/
├── jj-plugin.toml
├── pyproject.toml
└── src/
    └── jj_greeter/
        ├── __init__.py
        ├── commands.py
        └── plugin.py
```

Recommended:

```text
jj-greeter/
├── .gitignore
├── .python-version
├── README.md
├── jj-plugin.toml
├── pyproject.toml
├── src/
│   └── jj_greeter/
│       ├── __init__.py
│       ├── commands.py
│       ├── plugin.py
│       ├── services.py
│       └── client.py
└── tests/
    ├── test_descriptor_metadata.py
    └── test_greeter.py
```

Optional:

```text
.github/workflows/ci.yml
src/jj_greeter/__main__.py
src/jj_greeter/standalone.py
```

A standalone executable is useful for package-level testing, but JJ itself loads
the plugin through the `jj.plugins` entry point, not through
`[project.scripts]`.

---

## 6. Naming conventions

For a capability called `greeter`:

```text
Git repository:       jj-greeter
Python distribution:  jj-greeter
Python import package: jj_greeter
JJ plugin name:       greeter
JJ CLI namespace:     greeter
```

Plugin names and namespaces must use lowercase words separated by hyphens:

```text
valid:
  github
  hello-world
  forge-misc

invalid:
  HelloWorld
  hello_world
  hello.world
  -hello
```

The enforced pattern is conceptually:

```regex
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

The namespace `plugin` is reserved by `jj-core`.

Two configured plugins cannot claim the same namespace.

---

## 7. `jj-plugin.toml` format

The descriptor must be located at the repository root and named exactly:

```text
jj-plugin.toml
```

Complete schema-1 example:

```toml
schema_version = 1

[plugin]
name = "greeter"
distribution = "jj-greeter"
version = "0.1.0"
namespace = "greeter"
description = "Tutorial plugin that prints greetings."

[compatibility]
jj_core = ">=0.1,<1"
```

### Field reference

#### `schema_version`

Required integer. The current value is:

```toml
schema_version = 1
```

#### `[plugin].name`

Required. This is JJ's stable plugin identity.

It must match:

- the entry-point key under `jj.plugins`;
- `CliPlugin.name`;
- a friendly catalog name when installed by friendly name.

#### `[plugin].distribution`

Required. This is the Python distribution name from `[project].name`.

```toml
distribution = "jj-greeter"
```

Comparison is normalized according to normal Python distribution-name rules.

#### `[plugin].version`

Required valid Python package version.

It must match:

- `[project].version`;
- the installed distribution version.

#### `[plugin].namespace`

Required lowercase hyphenated CLI namespace.

This becomes:

```bash
jj greeter ...
```

It must match `CliPlugin.namespace`.

#### `[plugin].description`

Required non-empty description.

It explains the plugin in configuration and should be kept identical to the
`CliPlugin.description` used in `jj --help`.

The current implementation requires both descriptions to be non-empty but does
not yet enforce that their text is identical. Keeping them identical avoids
confusing help and state output.

#### `[compatibility].jj_core`

Optional but strongly recommended Python version specifier:

```toml
jj_core = ">=0.1,<1"
```

JJ rejects installation when the active `jj-core` version does not satisfy the
specifier.

When the stable core contract moves to 1.x, a plugin should use an appropriate
supported range, for example:

```toml
jj_core = ">=1,<2"
```

---

## 8. `pyproject.toml` format

A minimal working project:

```toml
[project]
name = "jj-greeter"
version = "0.1.0"
description = "Tutorial CLI plugin for jj-core."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "jj-core>=0.1,<1",
    "typer>=0.16,<1",
]

[dependency-groups]
dev = [
    "pytest>=9,<10",
]

[project.entry-points."jj.plugins"]
greeter = "jj_greeter.plugin:plugin"

[build-system]
requires = ["uv_build>=0.10.0,<0.13.0"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "jj_greeter"
module-root = "src"

[tool.uv.sources]
jj-core = { path = "../jj-core", editable = true }

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v"
```

### Important details

The entry point:

```toml
[project.entry-points."jj.plugins"]
greeter = "jj_greeter.plugin:plugin"
```

means:

```text
entry-point group: jj.plugins
entry-point name:  greeter
Python module:     jj_greeter.plugin
Python object:     plugin
```

The object must be a `CliPlugin` instance. It is not currently a registration
function, class, or arbitrary module.

This local development source:

```toml
[tool.uv.sources]
jj-core = { path = "../jj-core", editable = true }
```

lets `uv sync` use a sibling `jj-core` checkout. JJ's runtime reconciliation
uses uv's `--no-sources` option, so a Git-installed plugin does not depend on
that local path.

A plugin still needs normal Python distribution metadata even though it is not
published to PyPI. uv builds and installs it from Git or from a local directory.

---

## 9. Python registration API

The public CLI plugin object currently has this shape:

```python
from dataclasses import dataclass
import typer


@dataclass(frozen=True, slots=True)
class CliPlugin:
    name: str
    namespace: str
    description: str
    app: typer.Typer
```

Import the real class from core:

```python
from jj_core.plugin_api import CliPlugin
```

Do not define a duplicate local class with the same fields. Core validates the
actual object type.

---

# 10. Tutorial: build `jj-greeter`

This tutorial creates a plugin that contributes:

```bash
jj greeter say-hello Grant
```

and prints:

```text
Hello, Grant!
```

## Step 1: create the package

Run this from the directory that should contain the new project:

```bash
uv init --package jj-greeter
cd jj-greeter
```

Do not first create `jj-greeter`, enter it, and then run
`uv init --package jj-greeter`; doing so creates an unnecessary nested
`jj-greeter/jj-greeter` directory.

Create the source and test directories if the scaffold does not already contain
them:

```bash
mkdir -p src/jj_greeter tests
```

## Step 2: replace `pyproject.toml`

```toml
[project]
name = "jj-greeter"
version = "0.1.0"
description = "Tutorial CLI plugin for jj-core."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "jj-core>=0.1,<1",
    "typer>=0.16,<1",
]

[dependency-groups]
dev = [
    "pytest>=9,<10",
]

[project.entry-points."jj.plugins"]
greeter = "jj_greeter.plugin:plugin"

[build-system]
requires = ["uv_build>=0.10.0,<0.13.0"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "jj_greeter"
module-root = "src"

[tool.uv.sources]
jj-core = { path = "../jj-core", editable = true }

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v"
```

If there is no sibling `../jj-core`, omit `[tool.uv.sources]` and let uv resolve
the released `jj-core` dependency.

## Step 3: create `jj-plugin.toml`

```toml
schema_version = 1

[plugin]
name = "greeter"
distribution = "jj-greeter"
version = "0.1.0"
namespace = "greeter"
description = "Tutorial plugin that prints greetings."

[compatibility]
jj_core = ">=0.1,<1"
```

## Step 4: create `src/jj_greeter/__init__.py`

```python
"""Tutorial JJ plugin."""
```

## Step 5: create `src/jj_greeter/commands.py`

```python
"""Plugin-owned CLI definitions."""

from __future__ import annotations

from typing import Annotated

import typer


app = typer.Typer(
    help="Tutorial plugin that prints greetings.",
    no_args_is_help=True,
)


@app.callback()
def greeter_namespace() -> None:
    """Tutorial plugin that prints greetings."""


@app.command("say-hello")
def say_hello(
    name: Annotated[str, typer.Argument(help="Name to greet.")],
) -> None:
    """Print a greeting to standard output."""
    typer.echo(f"Hello, {name}!")
```

The plugin owns this entire Typer app:

- namespace help;
- command names;
- arguments and options;
- output;
- errors;
- service calls.

`jj-core` only attaches the app beneath the declared namespace.

## Step 6: create `src/jj_greeter/plugin.py`

```python
"""JJ plugin registration object."""

from jj_core.plugin_api import CliPlugin
from jj_greeter.commands import app


plugin = CliPlugin(
    name="greeter",
    namespace="greeter",
    description="Tutorial plugin that prints greetings.",
    app=app,
)
```

These values should align with `jj-plugin.toml`.

## Step 7: add a command test

Create `tests/test_greeter.py`:

```python
from typer.testing import CliRunner

from jj_greeter.commands import app
from jj_greeter.plugin import plugin


runner = CliRunner()


def test_say_hello() -> None:
    result = runner.invoke(app, ["say-hello", "Grant"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "Hello, Grant!"


def test_plugin_metadata() -> None:
    assert plugin.name == "greeter"
    assert plugin.namespace == "greeter"
```

## Step 8: add a metadata consistency test

Create `tests/test_descriptor_metadata.py`:

```python
from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_descriptor_matches_distribution_metadata() -> None:
    project = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    descriptor = tomllib.loads(
        (PROJECT_ROOT / "jj-plugin.toml").read_text(encoding="utf-8")
    )

    assert descriptor["plugin"]["distribution"] == project["project"]["name"]
    assert descriptor["plugin"]["version"] == project["project"]["version"]
    assert descriptor["plugin"]["name"] in project["project"]["entry-points"][
        "jj.plugins"
    ]
```

## Step 9: sync and test

```bash
uv sync --all-groups
uv run pytest
```

Build the package exactly as a Git install will need it:

```bash
uv build --no-sources
```

`--no-sources` verifies that the package does not accidentally require a local
`[tool.uv.sources]` override to build.

## Step 10: install the plugin locally

Make sure `jj-core` owns the global `jj` executable:

```bash
uv tool install --force jj-core
```

From the plugin directory:

```bash
jj plugin install .
```

Expected output resembles:

```text
Installed and enabled plugin 'greeter'.
Namespace: jj greeter
Configuration: /Users/<user>/.config/jj/plugins.toml
Run 'jj greeter --help' to inspect its commands.
```

Verify composition:

```bash
jj --help
```

The commands should include:

```text
plugin
greeter
```

Inspect the namespace:

```bash
jj greeter --help
```

Run it:

```bash
jj greeter say-hello Grant
```

Expected:

```text
Hello, Grant!
```

## Step 11: prove editable development

Because a local directory is installed editable, change:

```python
typer.echo(f"Hello, {name}!")
```

to:

```python
typer.echo(f"Welcome, {name}!")
```

Run without reinstalling:

```bash
jj greeter say-hello Grant
```

Expected:

```text
Welcome, Grant!
```

Revert the tutorial change when finished.

## Step 12: inspect and remove

```bash
jj plugin list
```

A local install should show an editable source pointing at the project
directory.

Remove it:

```bash
jj plugin remove greeter
```

Then:

```bash
jj --help
```

should no longer show the `greeter` namespace.

---

## 11. Installation references supported by `jj plugin install`

### Friendly catalog name

```bash
jj plugin install greeter
```

This works only when the active plugin catalog contains an entry named
`greeter`.

### Local project directory

```bash
jj plugin install ./jj-greeter
```

The local directory is installed editable.

### Local descriptor file

Because JJ recognizes an existing file and treats its parent as the project
root, this is also accepted:

```bash
jj plugin install ./jj-greeter/jj-plugin.toml
```

### HTTPS Git repository

```bash
jj plugin install https://github.com/example/jj-greeter.git
```

### SSH Git repository

```bash
jj plugin install git+ssh://git@github.com/company/jj-greeter.git
```

SCP-style SSH Git syntax is also recognized:

```bash
jj plugin install git@github.com:company/jj-greeter.git
```

Git authentication must already work for the user.

Test GitHub SSH independently with:

```bash
ssh -T git@github.com
```

### Important Git behavior

For a remote Git install, JJ:

1. shallow-clones the repository;
2. requires `jj-plugin.toml` at its root;
3. validates the descriptor and `pyproject.toml`;
4. resolves the checked-out commit;
5. installs a source pinned to that exact commit;
6. verifies the installed entry point in a fresh Python process;
7. writes configuration only after verification succeeds.

A later branch update does not silently change the installed plugin. Reinstall
it to move to a newer commit.

Repository URLs must not embed credentials. This is rejected:

```text
https://username:password@example.com/repository.git
```

Use Git credential management or SSH instead.

---

## 12. Friendly-name catalog

A catalog maps a short name to a Git repository.

Schema 1:

```toml
schema_version = 1

[plugins."greeter"]
repository = "https://github.com/example/jj-greeter.git"

[plugins."github"]
repository = "https://github.com/example/jj-github.git"
```

The friendly name must match `[plugin].name` in the resolved repository.

List the active catalog:

```bash
jj plugin catalog
```

### Current 0.1.x behavior

`jj-core` 0.1.x ships a built-in catalog. It also supports overriding the
catalog location with:

```bash
export JJ_PLUGIN_CATALOG=/absolute/path/to/catalog.toml
```

or an HTTP(S) location:

```bash
export JJ_PLUGIN_CATALOG=https://plugins.example.com/catalog.toml
```

Then:

```bash
jj plugin catalog
jj plugin install greeter
```

Relative repository locations are resolved relative to the catalog file or URL.

The planned stable architecture can move the official catalog outside the core
release while preserving this schema-driven boundary. The catalog should only
identify plugins and sources; it should not contain arbitrary install commands
or redefine core behavior.

---

## 13. Runtime configuration

JJ stores desired local plugin state at:

```text
~/.config/jj/plugins.toml
```

A configured local plugin resembles:

```toml
schema_version = 1

[plugins."greeter"]
distribution = "jj-greeter"
version = "0.1.0"
namespace = "greeter"
description = "Tutorial plugin that prints greetings."
source = "/Users/grant/dev/jj-greeter"
editable = true
enabled = true
```

A Git source is recorded as a commit-pinned PEP 508 Git source.

Normally, do not hand-edit this file. Use:

```bash
jj plugin install ...
jj plugin list
jj plugin remove ...
```

The state model already includes `enabled`, but 0.1.x does not yet expose
separate `enable` and `disable` commands.

Configuration-location overrides:

```text
JJ_CONFIG_HOME
XDG_CONFIG_HOME
```

---

## 14. How plugin loading works

Every `jj` invocation follows this conceptual sequence:

```text
start jj
  -> create root Typer app
  -> register core `plugin` namespace
  -> read configured plugin state
  -> discover installed entry points in group `jj.plugins`
  -> load enabled configured plugins
  -> validate each CliPlugin
  -> reject missing, duplicate, invalid, or conflicting namespaces
  -> attach healthy plugin Typer apps
  -> parse command line or render help
```

This is why:

```bash
jj --help
```

shows the namespaces available in that specific JJ installation.

A missing or broken optional plugin produces a warning. Healthy core commands
and other plugins continue loading.

---

## 15. Validation performed by core

Before a plugin install is committed, current core validates the following.

### Descriptor validation

- `jj-plugin.toml` exists at the project/repository root.
- `schema_version` equals `1`.
- `[plugin]` exists.
- name, distribution, version, namespace, and description are non-empty.
- name and namespace are lowercase hyphenated identifiers.
- version is valid.
- `compatibility.jj_core`, when present, is valid and includes the installed
  core version.

### Project metadata validation

- `pyproject.toml` exists.
- `[project]` exists.
- descriptor distribution matches `[project].name`.
- descriptor version matches `[project].version`.
- an entry point with the plugin name exists in
  `[project.entry-points."jj.plugins"]`.

### Runtime validation

- exactly one installed entry point exists for the configured plugin name;
- the entry point belongs to the expected Python distribution;
- the installed distribution version matches the descriptor;
- loading the entry point produces a real `CliPlugin`;
- `CliPlugin.name` matches the entry-point/configured name;
- `CliPlugin.namespace` matches the descriptor/configuration;
- the namespace is not reserved or already claimed.

If fresh-process verification fails, JJ attempts to restore the previous uv
tool environment and does not write the new desired state.

---

## 16. Recommended internal architecture

A simple plugin can keep everything in `commands.py`.

A substantial provider plugin should separate CLI presentation from reusable
capability behavior:

```text
jj_github/
├── plugin.py
├── commands/
│   ├── __init__.py
│   ├── issues.py
│   ├── pull_requests.py
│   └── repositories.py
├── services/
│   ├── issues.py
│   ├── pull_requests.py
│   └── repositories.py
├── client.py
├── models.py
└── auth.py
```

Recommended call flow:

```text
Typer command
  -> plugin service/capability
  -> provider client/SDK/API
```

Avoid putting all provider calls, parsing, policy, and output formatting in one
command function.

This creates a reusable capability layer for a future agent adapter:

```text
human CLI
  -> jj-github service
  -> GitHub

future jj-github-agent tool
  -> the same jj-github service
  -> GitHub
```

An agent adapter should not reimplement the provider client or invoke Typer
commands as its API.

Provider plugins should preserve provider-native concepts rather than force
GitHub, Jira, Cloudflare, and similar systems into a lowest-common-denominator
model. Higher-level plugins can correlate or orchestrate across native
capabilities later.

---

## 17. Secrets and authentication

### Core rule

Do not store plaintext secrets in:

- `jj-plugin.toml`;
- `pyproject.toml`;
- the source repository;
- the JJ plugin catalog;
- JJ's `plugins.toml`;
- command history, logs, test fixtures, or audit output.

Today, provider-specific credential acquisition belongs in the provider plugin.

Use either:

1. the shell/process environment; or
2. an external credential or secret provider.

Examples include:

```text
GitHub CLI authentication
AWS SSO
macOS Keychain
HashiCorp Vault
AWS Secrets Manager
1Password
environment variables
```

Example environment lookup:

```python
import os


def cloudflare_token() -> str:
    try:
        return os.environ["CLOUDFLARE_API_TOKEN"]
    except KeyError as exc:
        raise RuntimeError(
            "CLOUDFLARE_API_TOKEN is required in the process environment."
        ) from exc
```

A private shell script may populate environment variables:

```bash
source ~/private/load-jj-secrets.sh
jj cloudflare ...
```

Keep the script outside the repository. A stronger version of the script can
retrieve values from a secret manager rather than containing plaintext itself.

Editable local installation does not automatically load `.env.local`. The
plugin may deliberately implement that behavior, but runtime environment or an
external provider is the portable design for local and Git installations.

Never pass raw secrets into agent prompts or agent-tool metadata. Future agent
tools should invoke governed services that acquire credentials below the model
boundary.

---

## 18. Testing recommendations

At minimum, test:

1. command behavior;
2. plugin registration metadata;
3. descriptor/project metadata consistency.

Recommended command test:

```python
from typer.testing import CliRunner

from jj_greeter.commands import app


runner = CliRunner()


def test_say_hello() -> None:
    result = runner.invoke(app, ["say-hello", "Grant"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "Hello, Grant!"
```

Recommended metadata test:

```python
def test_plugin_registration_metadata() -> None:
    from jj_greeter.plugin import plugin

    assert plugin.name == "greeter"
    assert plugin.namespace == "greeter"
    assert plugin.description
```

Recommended build checks:

```bash
uv sync --all-groups
uv run pytest
uv build --no-sources
```

Recommended end-to-end local lifecycle:

```bash
jj plugin remove greeter 2>/dev/null || true
jj plugin install .
jj --help
jj greeter --help
jj greeter say-hello Grant
jj plugin list
jj plugin remove greeter
```

Before testing a remote install, push the repository, then:

```bash
jj plugin install https://github.com/example/jj-greeter.git
jj greeter say-hello Grant
jj plugin remove greeter
```

---

## 19. Versioning and release discipline

Plugins are Git-managed rather than PyPI-managed, but they still have Python
distribution versions.

Before releasing a new plugin version, update both:

```toml
# pyproject.toml
[project]
version = "0.2.0"
```

and:

```toml
# jj-plugin.toml
[plugin]
version = "0.2.0"
```

Keep the compatibility range accurate:

```toml
[compatibility]
jj_core = ">=0.1,<1"
```

Run:

```bash
uv run pytest
uv build --no-sources
```

Commit and push the plugin. A direct Git install resolves and pins the current
repository HEAD.

Plugins do not require:

- a PyPI project;
- a PyPI token;
- a PyPI Trusted Publisher;
- a PyPI release workflow.

Git tags are still recommended for meaningful plugin releases, documentation,
and human traceability, even though current JJ remote installation pins a commit
rather than selecting a tag by friendly name.

---

## 20. Optional standalone command

A plugin may retain a package-specific executable for development or smoke
testing:

```toml
[project.scripts]
jj-greeter = "jj_greeter.standalone:main"
```

Example `standalone.py`:

```python
import typer

from jj_greeter.commands import say_hello


def main() -> None:
    typer.run(say_hello)
```

Then:

```bash
uv run jj-greeter Grant
```

This is optional. It does not replace the JJ entry point, and normal users should
use:

```bash
jj greeter say-hello Grant
```

---

## 21. Troubleshooting

### `Unknown plugin '<name>'`

The name is not present in the active catalog.

Use a local path or repository URL:

```bash
jj plugin install ./jj-greeter
```

or:

```bash
jj plugin install https://github.com/example/jj-greeter.git
```

### `does not contain jj-plugin.toml at its root`

The file must be at the Git repository/project root:

```text
repository/
├── jj-plugin.toml
└── pyproject.toml
```

It cannot live only under `src/` or a nested package directory.

### Descriptor distribution does not match pyproject name

These must identify the same distribution:

```toml
# jj-plugin.toml
distribution = "jj-greeter"
```

```toml
# pyproject.toml
[project]
name = "jj-greeter"
```

### Descriptor version does not match pyproject version

Update both files to the same version.

### Missing `jj.plugins` entry point

Add:

```toml
[project.entry-points."jj.plugins"]
greeter = "jj_greeter.plugin:plugin"
```

### Entry point loads the wrong type

The target must resolve to an instantiated `CliPlugin`:

```python
plugin = CliPlugin(...)
```

It must not resolve to the module, Typer app by itself, a class, or a
`register()` function under the current 0.1.x contract.

### Entry-point name mismatch

All of these should be `greeter`:

```text
jj-plugin.toml plugin.name
pyproject entry-point key
CliPlugin.name
catalog friendly name, when applicable
```

### Namespace conflict

Choose a unique namespace. `plugin` is reserved by core.

### Local source changes are not visible

Confirm the plugin was installed from an existing local path:

```bash
jj plugin list
```

The row should show:

```text
Editable: yes
Source: /absolute/path/to/jj-greeter
```

If it was installed from Git, remove it and install the local directory:

```bash
jj plugin remove greeter
jj plugin install ./jj-greeter
```

### SSH authentication failure

Test Git directly:

```bash
ssh -T git@github.com
git clone git@github.com:company/jj-greeter.git
```

Fix Git/SSH authentication independently, then retry JJ.

### `uv is required ... but was not found on PATH`

JJ delegates runtime composition to uv. Install uv and ensure a fresh shell can
find it:

```bash
uv --version
```

### Plugin is configured but not installed

JJ warns and continues loading healthy commands. Inspect:

```bash
jj plugin list
```

A reinstall of the plugin or removal of stale desired state should restore
consistency.

### Global `jj` still runs the historical agent

Replace the executable link with core:

```bash
uv tool install --force jj-core
jj --help
```

A clean core help screen contains the `plugin` namespace and enabled plugin
namespaces, not the old `serve` or `backlog` commands.

---

## 22. Current 0.1.x limitations

The following are not yet general plugin contracts:

- plugin-to-plugin dependency declarations at the JJ descriptor level;
- separate enable/disable CLI commands;
- agent-tool registration;
- policy/approval/audit extension points;
- secret-provider registration;
- server or remote exposure;
- automatic plugin update commands;
- namespace aliases;
- multiple presentation surfaces from one descriptor;
- a stable external official catalog release contract.

Do not build a provider plugin by privately inventing a core-like version of
one of these contracts. Build provider functionality natively, and add a new
core extension point only when multiple capabilities need a stable shared
primitive.

Installing a CLI plugin does not expose it remotely and does not grant an LLM
access to it. Agent access should later be an explicit, separately governed
extension.

---

## 23. Plugin author checklist

### Required metadata

- [ ] Repository has root `jj-plugin.toml`.
- [ ] `schema_version = 1`.
- [ ] Plugin name is lowercase and hyphenated.
- [ ] Namespace is lowercase, hyphenated, unique, and not `plugin`.
- [ ] Distribution matches `[project].name`.
- [ ] Descriptor version matches `[project].version`.
- [ ] Core compatibility is declared.
- [ ] Entry-point group is exactly `jj.plugins`.
- [ ] Entry-point key matches plugin name.
- [ ] Entry point resolves to a `CliPlugin` object.
- [ ] `CliPlugin.name` and namespace match the descriptor.

### Code quality

- [ ] Plugin owns its Typer app and help.
- [ ] Commands delegate substantial behavior to services.
- [ ] Provider concepts remain provider-native.
- [ ] No provider-specific code was added to `jj-core`.
- [ ] Tests cover commands and metadata.
- [ ] `uv build --no-sources` succeeds.

### Security

- [ ] No plaintext secrets are in the repository or descriptors.
- [ ] Credentials come from environment or an external provider.
- [ ] Repository URLs do not embed credentials.
- [ ] Logs and errors do not print tokens or secret values.
- [ ] Future agent access will use explicit governed tools, not direct SDK
      access.

### Lifecycle

- [ ] `jj plugin install .` succeeds.
- [ ] `jj --help` shows the namespace.
- [ ] `jj <namespace> --help` works.
- [ ] Commands work from directories outside the plugin checkout.
- [ ] Editable source changes appear without reinstalling.
- [ ] `jj plugin remove <name>` removes the namespace cleanly.
- [ ] HTTPS or SSH Git installation is tested before wider use.

---

## 24. Quick reference

```bash
# Test the package
uv sync --all-groups
uv run pytest
uv build --no-sources

# Install local editable plugin
jj plugin install .

# Inspect installation
jj plugin list
jj --help
jj greeter --help

# Run a plugin command
jj greeter say-hello Grant

# Remove plugin
jj plugin remove greeter

# Install from HTTPS Git
jj plugin install https://github.com/example/jj-greeter.git

# Install from SSH Git
jj plugin install git+ssh://git@github.com/company/jj-greeter.git

# List friendly names
jj plugin catalog

# Use a custom catalog
export JJ_PLUGIN_CATALOG=/path/to/catalog.toml
jj plugin catalog
jj plugin install greeter
```

---

## 25. Canonical reference

When uncertain, compare the plugin against the working `jj-hello-world`
reference repository. The most important reference files are:

```text
jj-plugin.toml
pyproject.toml
src/jj_hello_world/commands.py
src/jj_hello_world/plugin.py
tests/test_descriptor_metadata.py
tests/test_hello_world.py
```

The durable core rule is:

> Core owns discovery and composition. The plugin owns the capability and its
> native implementation.

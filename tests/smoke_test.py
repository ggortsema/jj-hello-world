"""Smoke test executed against built wheel and source distributions."""

from importlib.metadata import entry_points, version
import subprocess
import sys

assert version("jj-hello-world")
plugins = [
    entry_point
    for entry_point in entry_points(group="jj.plugins")
    if entry_point.name == "hello-world"
]
assert len(plugins) == 1
plugin = plugins[0].load()
assert plugin.name == "hello-world"
assert plugin.namespace == "hello-world"

completed = subprocess.run(
    [sys.executable, "-m", "jj_hello_world", "Grant"],
    text=True,
    capture_output=True,
    check=True,
)
assert completed.stdout.strip() == "Hello, Grant!"

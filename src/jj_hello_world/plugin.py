"""JJ plugin registration object."""

from jj_core.plugin_api import CliPlugin
from jj_hello_world.commands import app

plugin = CliPlugin(
    name="hello-world",
    namespace="hello-world",
    description="Reference plugin demonstrating JJ CLI extension.",
    app=app,
)

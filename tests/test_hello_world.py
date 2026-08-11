from typer.testing import CliRunner

from jj_hello_world.commands import app
from jj_hello_world.plugin import plugin

runner = CliRunner()


def test_say_hello() -> None:
    result = runner.invoke(app, ["say-hello", "Grant"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "Hello, Grant!"


def test_plugin_registration_metadata() -> None:
    assert plugin.name == "hello-world"
    assert plugin.namespace == "hello-world"

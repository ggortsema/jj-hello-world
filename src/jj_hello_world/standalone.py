"""Optional standalone executable retained for package-level smoke testing."""

import typer

from jj_hello_world.commands import say_hello


def main() -> None:
    typer.run(say_hello)

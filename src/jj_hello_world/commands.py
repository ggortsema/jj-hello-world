"""Plugin-owned CLI definitions."""

from __future__ import annotations

from typing import Annotated

import typer

app = typer.Typer(
    help="Reference plugin demonstrating JJ CLI extension.",
    no_args_is_help=True,
)


@app.callback()
def hello_world_namespace() -> None:
    """Reference plugin demonstrating JJ CLI extension."""


@app.command("say-hello")
def say_hello(
    name: Annotated[str, typer.Argument(help="Name to greet.")],
) -> None:
    """Print a greeting to standard output."""
    typer.echo(f"Hello, {name}!")

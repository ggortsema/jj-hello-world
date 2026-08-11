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

    distribution = project["project"]["name"]
    version = project["project"]["version"]

    assert descriptor["plugin"]["distribution"] == distribution
    assert descriptor["plugin"]["version"] == version
    assert descriptor["plugin"]["name"] in project["project"]["entry-points"][
        "jj.plugins"
    ]

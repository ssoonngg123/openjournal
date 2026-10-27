import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib

import openjournal


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_python_package_version_matches_runtime_version():
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["version"] == openjournal.__version__


def test_claude_marketplace_points_to_plugin_wrapper():
    marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert marketplace["name"] == "openjournal"
    assert marketplace["version"] == openjournal.__version__
    assert len(marketplace["plugins"]) == 1
    plugin = marketplace["plugins"][0]
    assert plugin["name"] == "openjournal"
    assert plugin["version"] == openjournal.__version__
    assert plugin["source"] == "../plugins/openjournal"
    assert plugin["category"] == "productivity"
    assert plugin["author"]["name"] == "anonymous-org"
    assert plugin.get("description"), "plugin description must be present but can evolve freely"


def test_plugin_wrapper_uses_root_skills_via_symlink():
    plugin_root = REPO_ROOT / "plugins" / "openjournal"
    plugin_manifest = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
    skills_link = plugin_root / "skills"

    assert plugin_manifest["name"] == "openjournal"
    assert plugin_manifest["version"] == openjournal.__version__
    assert skills_link.is_symlink()
    assert skills_link.resolve() == (REPO_ROOT / "skills").resolve()

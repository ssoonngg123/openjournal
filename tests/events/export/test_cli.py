"""End-to-end CLI smoke test: `openjournal events export` then `events import`."""

from __future__ import annotations

import json
from pathlib import Path

from openjournal.cli import main as cli_main

from ._helpers import (
    insert_event,
    insert_event_session,
)


def _bootstrap_workbench(db_path: Path) -> None:
    """Open the index DB through workbench machinery so the full schema
    (sessions / shares / policies / findings) lands and `events export`
    can read share-time settings via `get_effective_share_settings`.

    Also bootstrap events / view / cost / incidents / export schemas so
    direct inserts work without going through `events ingest`.
    """
    from openjournal.events.cost.schema import ensure_cost_schema
    from openjournal.events.export.schema import ensure_export_schema
    from openjournal.events.incidents.schema import ensure_incidents_schema
    from openjournal.events.schema import ensure_schema as ensure_events_schema
    from openjournal.events.view import ensure_view_schema
    from openjournal.workbench.index import open_index

    conn = open_index()
    ensure_events_schema(conn)
    ensure_view_schema(conn)
    ensure_cost_schema(conn)
    ensure_incidents_schema(conn)
    ensure_export_schema(conn)
    conn.commit()
    conn.close()


def _run_cli(monkeypatch, args, env=None):
    monkeypatch.setattr("sys.argv", ["openjournal", *args])
    cli_main()


def test_cli_export_then_import(tmp_path, monkeypatch, capsys):
    config_dir = tmp_path / ".openjournal"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps({
            "source": "claude",
            "projects_confirmed": True,
            "redact_strings": [],
            "redact_usernames": [],
            "allowlist_entries": [],
            "excluded_projects": [],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr("openjournal.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("openjournal.config.CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr(
        "openjournal.workbench.index.CONFIG_DIR", config_dir,
    )
    monkeypatch.setattr(
        "openjournal.workbench.index.INDEX_DB", config_dir / "index.db",
    )
    monkeypatch.setattr(
        "openjournal.workbench.index.BLOBS_DIR", config_dir / "blobs",
    )

    _bootstrap_workbench(config_dir / "index.db")

    from openjournal.workbench.index import open_index

    conn = open_index()
    sid = insert_event_session(conn, session_key="claude:cli:s1")
    insert_event(
        conn,
        session_id=sid,
        event_type="user_message",
        source_path="/tmp/cli.jsonl",
        source_offset=0,
        seq=0,
        raw_json={"text": "hello CLI"},
    )
    conn.close()

    # Don't pass --out so the default landing site (under monkeypatched
    # CONFIG_DIR) is used; the explicit-path validator only allows
    # paths under $HOME or /tmp, and macOS pytest tmpdirs are neither.
    _run_cli(monkeypatch, [
        "events", "export",
        "claude:cli:s1",
        "--allow-no-workbench-row",
        "--json",
    ])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    bundle_path = Path(payload["bundle_path"])
    assert bundle_path.exists()
    assert payload["blocked"] is False
    assert payload["event_count"] == 1

    # Import into a second config dir to simulate a different host.
    config_dir2 = tmp_path / ".openjournal2"
    config_dir2.mkdir()
    monkeypatch.setattr("openjournal.config.CONFIG_DIR", config_dir2)
    monkeypatch.setattr("openjournal.config.CONFIG_FILE", config_dir2 / "config.json")
    monkeypatch.setattr(
        "openjournal.workbench.index.CONFIG_DIR", config_dir2,
    )
    monkeypatch.setattr(
        "openjournal.workbench.index.INDEX_DB", config_dir2 / "index.db",
    )
    monkeypatch.setattr(
        "openjournal.workbench.index.BLOBS_DIR", config_dir2 / "blobs",
    )

    _bootstrap_workbench(config_dir2 / "index.db")

    _run_cli(monkeypatch, [
        "events", "import",
        str(bundle_path),
        "--json",
    ])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["events_inserted"] == 1
    assert "claude:cli:s1" in payload["session_keys"]

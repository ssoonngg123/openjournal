# Examples

Runnable command sequences for common workflows. Substitute
`{HOME}` for your home directory and `{INDEX_DB}` for
`{HOME}/.openjournal/index.db` when copy-pasting.

## Diagnose, then ingest

```
openjournal events doctor
openjournal events ingest --json
openjournal events doctor --json
```

If the first invocation reports `install_state: "fresh"`, run
`openjournal scan` first to populate the workbench schema.

## Inspect a single event

```
openjournal events ingest
openjournal events inspect 1234 --json
```

Or by session + event_key:

```
openjournal events inspect --session "claude:my-app:abc-123" \
  --event-key "tool_call:tu-1" --json
```

## Compute costs and detect anomalies

```
openjournal events cost ingest --json
openjournal events doctor --json | jq '.cost'
```

## Detect repeat-loop incidents

```
openjournal events incidents detect --json
openjournal events doctor --json | jq '.incidents.counts_by_kind'
```

## Export a session as a bundle, then import elsewhere

```
openjournal events export "claude:my-app:abc-123" --out bundle.json
openjournal events import bundle.json
openjournal events import bundle.json --rebuild-derived
```

## Read agent-consumable docs

```
openjournal events features --json
openjournal events docs commands
openjournal events docs schemas --json
openjournal events docs errors --json
```

## Capability overlay (when adding additive drift)

```
openjournal events capabilities | jq '.claude'
# … upstream client adds a new known-supported event type …
$EDITOR {HOME}/.openjournal/capability_overlay.yaml
openjournal events doctor
```

The overlay merges over the shipped matrix on next read.

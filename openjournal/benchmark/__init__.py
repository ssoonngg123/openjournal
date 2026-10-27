"""Personalized weekly benchmark generation, storage, and selection.

The benchmark pipeline turns a week of the user's own scored failure traces
into an adversarial, judgment-focused benchmark (themes + grounded tasks). This
package holds the backend-only substrate:

- :mod:`openjournal.benchmark.schema` — typed shapes, (de)serialization,
  validation, and the agent-packet / grader-packet split.
- :mod:`openjournal.benchmark.store` — persistence over the ``benchmarks`` /
  ``benchmark_tasks`` / ``benchmark_exports`` tables.
- :mod:`openjournal.benchmark.select` — selecting the week's failure-signal
  sessions to feed the generator.
- :mod:`openjournal.benchmark.generate` — the deep, backend-orchestrated
  multi-pass generation pipeline.
- :mod:`openjournal.benchmark.render` — rendering a benchmark to the export
  kinds (authoring markdown + agent/grader packets).

The daemon API / CLI / UI tab are layered on top of these in later phases.
"""

from . import generate, render, schema, select, store  # noqa: F401

__all__ = ["generate", "render", "schema", "select", "store"]

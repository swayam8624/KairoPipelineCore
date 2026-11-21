# KairoPipelineCore — read the host-independent Python pipeline

This standard-library-only package owns **portable production contracts** shared by [KairoBlender](https://github.com/swayam8624/KairoBlender), [KairoMaya](https://github.com/swayam8624/KairoMaya), [KairoHoudini](https://github.com/swayam8624/KairoHoudini), and [KairoNuke](https://github.com/swayam8624/KairoNuke). It does not import Blender, Maya, Houdini, or Nuke APIs.

## Source reading order

1. [README](../README.md), [pyproject.toml](../pyproject.toml) — package entry points, test command.
2. [src/kairo_pipeline/paths.py](../src/kairo_pipeline/paths.py) — normalize portable project-relative paths, forbid traversal/devices and resolve containment.
3. [src/kairo_pipeline/fingerprint.py](../src/kairo_pipeline/fingerprint.py) — SHA-256 content identity; independent of timestamps.
4. [src/kairo_pipeline/diagnostics.py](../src/kairo_pipeline/diagnostics.py) — stable diagnostic codes/severity and host-owned location tokens.
5. [src/kairo_pipeline/manifest.py](../src/kairo_pipeline/manifest.py) — versioned publish manifest and strict validation of roles, paths, dependencies and fingerprints.
6. [src/kairo_pipeline/sequences.py](../src/kairo_pipeline/sequences.py) — frame pattern expansion and missing/out-of-range frame inspection.
7. [src/kairo_pipeline/publish.py](../src/kairo_pipeline/publish.py) — `plan_publish` read-only preflight vs `publish_bundle` staged copy and atomic rename. Understand replacement/rollback before using it.
8. [src/kairo_pipeline/cli.py](../src/kairo_pipeline/cli.py) — translates command-line flags into the modules above.
9. [src/kairo_pipeline/__init__.py](../src/kairo_pipeline/__init__.py) — public package exports.
10. [docs/MANIFEST.md](MANIFEST.md) and [tests](../tests/) — schema examples, malformed input cases, publishing failure and rollback tests.

## Concrete flow

DCC host adapter extracts scene/cache/render files → publishes a versioned manifest → `normalize_project_path` validates portable names → `fingerprint_file` checks contents → `plan_publish` verifies intended target without writing → `publish_bundle` stages and re-verifies files → final atomic rename exposes the new bundle → downstream DCC adapter consumes manifest and records diagnostics. Host-specific UI and DCC objects must stay in their adapters.

## Teaching exercises

1. Follow a rejected `../` manifest path from parsing to exception, then test a Windows device name.
2. Change a payload without changing the filename; show how the hash check detects it.
3. Explain why `plan_publish` must not mutate the destination.
4. Test a partial failure during staging/replacement and determine what remains visible.
5. Compare a diagnostic's host-owned object path with a filesystem path—only the latter is resolved here.

Original source and documentation retain the repository's existing [license](../LICENSE). External DCC software and assets have separate terms.

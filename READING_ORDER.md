# KairoPipelineCore — source reading path and API interactions

Learn cross-DCC publishing from path validation → content hash → strict manifest → diagnostics → publish transaction. Blender, Houdini, Maya, Nuke and KairoAssets consume this Python publishing contract. A successful export is not trustworthy until the downstream importer re-verifies the checksums.

## Key interfaces and cross-repository calls

Manifest records provenance and immutable artifact hashes; the publisher stages then atomically publishes. Validate traversal/symlink boundaries, stale inputs, duplicate names, failure rollback and exact byte checks before packaging.

## Read the source and tests in this order (15 files)

1. [`src/kairo_pipeline/paths.py`](src/kairo_pipeline/paths.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
2. [`src/kairo_pipeline/fingerprint.py`](src/kairo_pipeline/fingerprint.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
3. [`src/kairo_pipeline/manifest.py`](src/kairo_pipeline/manifest.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
4. [`src/kairo_pipeline/diagnostics.py`](src/kairo_pipeline/diagnostics.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
5. [`src/kairo_pipeline/sequences.py`](src/kairo_pipeline/sequences.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
6. [`src/kairo_pipeline/publish.py`](src/kairo_pipeline/publish.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
7. [`src/kairo_pipeline/cli.py`](src/kairo_pipeline/cli.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
8. [`src/kairo_pipeline/__init__.py`](src/kairo_pipeline/__init__.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
9. [`tests/test_certification.py`](tests/test_certification.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
10. [`tests/test_diagnostics.py`](tests/test_diagnostics.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
11. [`tests/test_manifest.py`](tests/test_manifest.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
12. [`tests/test_package.py`](tests/test_package.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
13. [`tests/test_paths_and_fingerprints.py`](tests/test_paths_and_fingerprints.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
14. [`tests/test_publish.py`](tests/test_publish.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.
15. [`tests/test_sequences.py`](tests/test_sequences.py) — inspect its callers and imports, owned resources, validated inputs, failure states, and matching tests.

## Licensing and verification

This repository already has its own [LICENSE](LICENSE). The existing MIT terms permit learning, modification, redistribution and further development of the original code. Native DCC app APIs and third-party assets retain their own conditions. Read [README](README.md) for host-specific setup; pure tests cannot establish all native integration gates. Further in-file function annotations will complement this guide.

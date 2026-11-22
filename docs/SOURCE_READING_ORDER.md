# Teaching source map — KairoPipelineCore
**Worked source walkthrough:** [Strict manifest, safe paths, hashes, staging and consumer verification](CROSS_DCC_PUBLICATION_WALKTHROUGH.md).

Portable Python publication/manifest contract shared by DCC tool adapters.

Follow source links sequentially. For each API/function, identify its input contract, owning data structure, called modules, failure modes, outputs, test and downstream consumers.

## Read in this order

1. [`README.md`](../README.md)
2. [`pyproject.toml`](../pyproject.toml)
3. [`src`](../src)
4. [`tests`](../tests)
5. [`docs`](../docs)

## How this repository interacts with others

Blender, Houdini, Maya and Nuke adapters validate and publish content through this shared contract; KairoAssets checks the resulting bundle/hash at runtime.

## Verification and study rules

- Read the public C++23 module/entrypoint first, then its implementation and tests.
- Explain invariants, ownership, error states, concurrency or numerical assumptions in comments, not trivial syntax.
- A passing CI job covers only tests actually run on that commit/host; source presence is not runtime certification.
- Check [STATUS.md](../STATUS.md) and [STATUS.yaml](../STATUS.yaml) for current explicit verification limitations.
- Original work may be modified and extended under the repository license; third-party content retains upstream terms.


## Complete source-file inventory

After the curated teaching path, follow this deterministic inventory of first-party source, scripts, shaders, and tests. Grouping is a suggested learning order, not an indication that every function is already annotated. Vendored dependencies, ROMs, binaries, data, media, and generated evidence are excluded.

### Implementation and other source (8)

1. [`src/kairo_pipeline/__init__.py`](../src/kairo_pipeline/__init__.py)
2. [`src/kairo_pipeline/cli.py`](../src/kairo_pipeline/cli.py)
3. [`src/kairo_pipeline/diagnostics.py`](../src/kairo_pipeline/diagnostics.py)
4. [`src/kairo_pipeline/fingerprint.py`](../src/kairo_pipeline/fingerprint.py)
5. [`src/kairo_pipeline/manifest.py`](../src/kairo_pipeline/manifest.py)
6. [`src/kairo_pipeline/paths.py`](../src/kairo_pipeline/paths.py)
7. [`src/kairo_pipeline/publish.py`](../src/kairo_pipeline/publish.py)
8. [`src/kairo_pipeline/sequences.py`](../src/kairo_pipeline/sequences.py)

### Verification and tests (7)

1. [`tests/test_certification.py`](../tests/test_certification.py)
2. [`tests/test_diagnostics.py`](../tests/test_diagnostics.py)
3. [`tests/test_manifest.py`](../tests/test_manifest.py)
4. [`tests/test_package.py`](../tests/test_package.py)
5. [`tests/test_paths_and_fingerprints.py`](../tests/test_paths_and_fingerprints.py)
6. [`tests/test_publish.py`](../tests/test_publish.py)
7. [`tests/test_sequences.py`](../tests/test_sequences.py)

Snapshot totals: 15 first-party source/build/test files, 27 tracked files overall. Re-audit when files are renamed or added.

# KairoPipelineCore

**Study the implementation:** [linked file-reading order](docs/SOURCE_READING_ORDER.md) · [Cross-DCC source-to-publish-to-consumer validation](docs/CROSS_DCC_PUBLICATION_WALKTHROUGH.md).

`KairoPipelineCore` provides the host-neutral contracts shared by Kairo's
Blender, Maya, Houdini, and Nuke production tools. It deliberately depends only
on the Python standard library so it can be packaged into DCC applications
that ship different Python environments.

The package owns:

- strict versioned asset, cache, and render-publish manifests;
- navigable structured diagnostics with deterministic ordering;
- portable project-relative path validation;
- streaming SHA-256 content fingerprints;
- Houdini/Nuke-style frame-sequence inspection;
- dry-run planning and rollback-safe atomic filesystem publication; and
- machine-readable command-line operations for automation and CI.

Host repositories remain responsible for translating their native scene or
graph data into these contracts. The core never imports a DCC API.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m pip install -e .
kairo-pipeline --help
```

Validate a manifest or inspect a frame sequence:

```bash
kairo-pipeline validate-manifest publish.kairo.json --json
kairo-pipeline scan-sequence ./shot 'renders/beauty.####.exr' 1001 1100 --json
```

Plan and publish a bundle:

```bash
kairo-pipeline publish ./staging ./library publish.kairo.json --dry-run --json
kairo-pipeline publish ./staging ./library publish.kairo.json --json
```

Publication verifies every declared file before staging and again after copy.
The finished bundle becomes visible through one filesystem rename. Explicit
replacement keeps the old version available for rollback until the new bundle
has been exposed successfully.

See [the manifest contract](docs/MANIFEST.md) for the interchange format.

## Status

Version `0.1.0` is the initial portfolio contract. Each host repository records
the DCC and bundled Python versions used for native verification.



## Source learning pathway

Follow [the linked reading order](docs/SOURCE_READING_ORDER.md) to study the public interfaces, implementations, tests and cross-repository dependencies in a deliberate sequence. It explains what each subsystem owns, where its outputs go, and which behaviors require verification. Distinguish C++23 module interfaces, actual backend implementations and planned APIs.

## Open-source learning and extension

Original project code is available to learn from, modify and develop further under the applicable [LICENSE](LICENSE). Keep copyright/license notices when redistributing substantial portions. Dependencies, code adapted from other sources, media, datasets, models and other third-party materials remain subject to their original licenses. Consult [STATUS.md](STATUS.md) for evidence limitations rather than treating documentation or an unverified completion target as a guarantee of functionality.

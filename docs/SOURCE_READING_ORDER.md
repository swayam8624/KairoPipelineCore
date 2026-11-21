# Teaching source map — KairoPipelineCore

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

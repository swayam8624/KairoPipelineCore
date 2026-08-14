# Publish Manifest Contract

`kairo.publish.v1` is a deterministic JSON interchange contract used by the
Blender, Maya, Houdini, Nuke, and Kairo command-line tools. It describes one
immutable version of an asset, simulation/cache, or render result.

```json
{
  "dependencies": [],
  "kind": "asset",
  "metadata": {"artist": "Example Artist"},
  "name": "WorkshopChair",
  "outputs": [
    {
      "fingerprint": {
        "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "size": 1024
      },
      "media_type": "model/gltf+json",
      "path": "geometry/chair.gltf",
      "role": "scene"
    }
  ],
  "project": "Portfolio",
  "schema": "kairo.publish.v1",
  "source_fingerprint": {
    "sha256": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    "size": 4096
  },
  "source_host": "blender",
  "source_path": "scenes/workshop.blend",
  "version": 1
}
```

## Invariants

- Unknown fields and unsupported schema versions fail explicitly.
- Paths are project-relative POSIX paths and cannot escape their root.
- Paths must remain unique after Unicode-aware case folding.
- Every output and dependency carries its exact byte count and SHA-256 digest.
- Metadata maps bounded identifier keys to bounded string values.
- JSON serialization sorts keys and uses a canonical compact representation.
- A manifest contains at least one output.

The manifest describes provenance and files; it does not contain host-native
object handles. Navigable scene/node locations belong in diagnostic reports.


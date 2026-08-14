# KairoPipelineCore

`KairoPipelineCore` provides the host-neutral contracts shared by Kairo's
Blender, Maya, Houdini, and Nuke production tools. It deliberately depends only
on the Python standard library so it can be packaged into DCC applications
that ship different Python environments.

The package will own versioned publish manifests, structured diagnostics,
portable paths, content fingerprints, frame-sequence inspection, and atomic
filesystem publication. Host repositories remain responsible for translating
their native scene or graph data into these contracts.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m pip install -e .
kairo-pipeline --help
```

## Status

The repository is under active portfolio development. Each public release will
identify the DCC versions verified against its contracts.


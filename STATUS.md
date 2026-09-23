# KairoPipelineCore Status

Wave: A — production-contract certification  
Frozen v1 target: 95/100  
Source gate: complete  
Execution gate: `python3 -m unittest discover -s tests -v`

## Frozen v1 scope

PipelineCore v1 owns portable paths, fingerprints, strict versioned publish manifests, deterministic diagnostics, sequence inspection, dry-run planning and rollback-safe atomic publication. DCC-specific scene interpretation belongs to Blender/Maya/Houdini/Nuke.

## 95 exit evidence

- Manifest input is bounded, strict and deterministic.
- Publish inputs and staged outputs are fingerprint verified.
- Existing versions are immutable unless replacement is explicit.
- New certification tests prove planning is non-mutating, tampered replacement leaves the previous target intact, and a new validated replacement becomes visible atomically.
- Standard-library-only runtime keeps the contract portable across DCC-bundled Python installations.

## Verification policy

A 95 release requires the complete Python unit suite at the exact SHA. Host-native DCC behavior is deliberately verified in the host repositories rather than inferred here.

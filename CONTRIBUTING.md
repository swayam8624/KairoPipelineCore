# Contributing

Keep changes scoped to one production-pipeline contract or behavior. Public
formats require strict parsing, deterministic serialization, explicit limits,
and regression tests for malformed input.

Before requesting review, run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
git diff --check
```

Do not add a runtime dependency without documenting why the Python standard
library cannot meet the requirement. DCC-specific code belongs in the relevant
host repository.


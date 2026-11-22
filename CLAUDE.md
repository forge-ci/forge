# Agent guidance

Pushes from clud sessions are gated by `pr_checks` (talos-hq/clud#2720): run `clud pr-check` before pushing; it runs `uv run --no-project --python 3.12 --with basedpyright==1.38.1 --with pyyaml basedpyright scripts/`, matching the CI type checker without running the test suite.

# CA Lab — Documentation

> **Primary documentation** lives in [../documents/README.md](../documents/README.md).  
> **Repository memory** (file map, history): [../documents/reference/memory.md](../documents/reference/memory.md)

Draft research material and migration notes:

| Document | Description | Status |
|----------|-------------|--------|
| [../documents/README.md](../documents/README.md) | **Main documentation hub** | Current |
| [../documents/reference/memory.md](../documents/reference/memory.md) | Repository map and project memory | Current |
| [WHITEPAPER_DRAFT.md](WHITEPAPER_DRAFT.md) | Architecture, formalism, deployment, notebooks, and migration plan | **Draft** |
| [../REFERENCE_CODE_ANALYSIS.md](../documents/reference/REFERENCE_CODE_ANALYSIS.md) | Analysis of the original Java reference implementation | Complete |

## Audience

- **Researchers** — reproducible experiments, metrics, rule evolution, citation-ready artifacts
- **Instructors** — Jupyter-based labs, cross-platform (Windows / Linux)
- **Students** — interactive notebooks and optional web UI

## Next steps (implementation)

1. Scaffold `ca_engine` Python package with Conway parity tests against Java
2. Add CLI and `experiment.yaml` runner
3. Publish student notebooks under `notebooks/`
4. Optional Phase 2: web UI on top of the same engine

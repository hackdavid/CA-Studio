# 📋 Report Writing Guide — Start Here

> **Rule #1:** Read this file first. It tells you *when* to read *what* — both report rules and project source material.

---

## 🗺️ Navigation Philosophy

Every folder under `report/` is numbered in the **exact order** you will encounter those sections in your final submission. The **Source Material** section below links to project docs you'll need to reference while writing.

---

## Step-by-Step: What to Read Before You Write

### ✅ Phase 0 — Before You Touch a Single Word

**When:** Before writing *anything*.

**Read in this exact order:**

1. **`00-before-you-start/README.md`**
   - The "golden rules" and quick-reference overview.
   - This is your 2-minute sanity check. Read it every time you sit down to write.

2. **`00-before-you-start/structure-guide.md`**
   - Report structure, word counts, and section ordering.
   - **Why first:** You need to know the map before you start the journey.

3. **`00-before-you-start/writing-style.md`**
   - Third-person rules and the **banned-word list**.
   - **Why first:** If you write in first person, you will have to rewrite everything. Internalise this *before* you draft.

4. **`00-before-you-start/layout-and-formatting.md`**
   - Font, spacing, margins, figure/table rules.
   - **Why first:** Set up your document template correctly from day one.

5. **`99-compliance/copyright-ipr.md`**
   - Copyright and Intellectual Property Rights guidance.
   - **Why first:** If you have external collaborators, you need to know your protection strategies *now*, not after submission.

> 🔴 **Checkpoint:** If you cannot recite the banned-word list from memory, re-read `writing-style.md`.

---

### ✅ Phase 1 — Writing the Front Matter

**When:** You are ready to write Declaration, Acknowledgements, and Abstract.

> **Recommendation:** Write the Abstract **last**, after all chapters are complete.

**Read:**

- **`01-front-matter/front-matter.md`**
  - Guidance for Declaration, Acknowledgements, and Abstract (500-word limit).

---

### ✅ Phase 2 — Writing Each Chapter

**When:** You are ready to write a specific chapter.

**For every chapter, read TWO things before you draft:**
1. The chapter guidance file (rules for that chapter)
2. The linked source material (facts, diagrams, and evidence from the project)

| Chapter | Guidance File | Source Material to Reference |
|---|---|---|
| **Chapter 1 — Introduction** | `02-chapters/01-introduction.md` | [`../docs/WHITEPAPER_DRAFT.md`](../docs/WHITEPAPER_DRAFT.md) §1–3 (motivation, goals, contributions) <br> [`../documents/developer/architecture.md`](../documents/developer/architecture.md) (system overview) <br> [`../documents/reference/memory.md`](../documents/reference/memory.md) (project context) <br> [`../README.md`](../README.md) (capabilities summary) |
| **Chapter 2 — Literature & Technology Review** | `02-chapters/02-literature-technology-review.md` | [`../docs/WHITEPAPER_DRAFT.md`](../docs/WHITEPAPER_DRAFT.md) §2 (legacy system summary), §4 (architecture), §6 (metrics catalogue), §7 (rules & evolution) <br> [`../documents/reference/REFERENCE_CODE_ANALYSIS.md`](../documents/reference/REFERENCE_CODE_ANALYSIS.md) (Java reference analysis) <br> [`../documents/developer/ca-engine.md`](../documents/developer/ca-engine.md) (technology choices) |
| **Chapter 3 — Implementation** | `02-chapters/03-implementation.md` | [`../documents/developer/architecture.md`](../documents/developer/architecture.md) (layered architecture, design decisions) <br> [`../documents/developer/ca-engine.md`](../documents/developer/ca-engine.md) (engine internals, YAML schema, experiment spec) <br> [`../documents/developer/dev_log.md`](../documents/developer/dev_log.md) (milestones & phases) <br> [`../documents/reference/memory.md`](../documents/reference/memory.md) (directory map, API endpoints, schema) <br> [`../design-system/ca-lab/MASTER.md`](../design-system/ca-lab/MASTER.md) (UI design system, components) <br> [`../documents/user-guide/navigation.md`](../documents/user-guide/navigation.md) (page flows, screenshots) |
| **Chapter 4 — Evaluation & Results** | `02-chapters/04-evaluation-results.md` | [`../documents/user-guide/features.md`](../documents/user-guide/features.md) (capability checklist) <br> [`../documents/user-guide/experiments.md`](../documents/user-guide/experiments.md) (experiment workflow, reproducibility checklist) <br> [`../documents/developer/dev_log.md`](../documents/developer/dev_log.md) §Known Fixes & Open Items <br> [`../tests/`](../tests/) (test suite as evidence of validation) <br> [`../documents/reference/FINAL_STATUS.md`](../documents/reference/FINAL_STATUS.md) (resolved issues) |
| **Chapter 5 — Conclusion** | `02-chapters/05-conclusion.md` | [`../documents/developer/dev_log.md`](../documents/developer/dev_log.md) §Open Items (future work) <br> [`../documents/user-guide/features.md`](../documents/user-guide/features.md) §Roadmap (planned features) <br> [`../docs/WHITEPAPER_DRAFT.md`](../docs/WHITEPAPER_DRAFT.md) §13 (implementation roadmap) |

**Special rule for Chapter 1:**

- Before writing the **Legal, Social, Ethical and Professional Considerations** subsection, read:
  - `99-compliance/legal-social-ethical.md`

---

### ✅ Phase 3 — Writing the Back Matter

**When:** All chapters are complete and you are finalising references and appendices.

**Read:**

- **`03-back-matter/references.md`**
  - IEEE format, RefWorks guidance, and legitimacy rules.
  - **Read this before you cite your first source** — not after.

- **`03-back-matter/appendices.md`**
  - Required appendices (A: Proposal, B: Project Management, C: Artefact/Dataset, D: Screencast).
  - **Read this early** so you collect evidence (screenshots, links, Gantt charts) as you go, rather than scrambling at the end.

---

## 📚 Source Material — Full Project Document Map

Use this table to find any project document quickly. These are the **facts** you'll reference in your report.

### 🏗️ Architecture & Design

| Document | What It Contains | Useful For |
|---|---|---|
| [`../documents/developer/architecture.md`](../documents/developer/architecture.md) | High-level diagram, entry points, web layer, engine layer, data model, WebSocket protocol, design decisions | Ch 1 (Methodology), Ch 3 (Implementation) |
| [`../documents/developer/ca-engine.md`](../documents/developer/ca-engine.md) | Engine package layout, simulation step example, YAML schema, seed config, adding metrics, experiment YAML, tests, performance | Ch 2 (Technology Review), Ch 3 (Implementation) |
| [`../design-system/ca-lab/MASTER.md`](../design-system/ca-lab/MASTER.md) | Colour palette, typography, component specs, spacing, shadows, anti-patterns, pre-delivery checklist | Ch 3 (Implementation — UI/UX) |

### 👤 User-Facing Documentation

| Document | What It Contains | Useful For |
|---|---|---|
| [`../documents/user-guide/navigation.md`](../documents/user-guide/navigation.md) | Site map, landing page, dashboard layout, New Session modal fields, simulation page layout, keyboard/accessibility | Ch 3 (Implementation — UI), Ch 4 (Evaluation — usability) |
| [`../documents/user-guide/features.md`](../documents/user-guide/features.md) | Core capabilities: multi-state CA, rule system, neighbourhoods, session management, seeds, real-time sim, metrics, canvas, CLI, renderers, design principles, roadmap | Ch 1 (Objectives), Ch 3 (Implementation), Ch 4 (Evaluation) |
| [`../documents/user-guide/experiments.md`](../documents/user-guide/experiments.md) | Workflow overview, rule selection, board sizes, metrics selection, seed strategies, drawing, starting, saving/exporting, CLI experiments, reproducibility checklist | Ch 3 (Implementation), Ch 4 (Evaluation — reproducibility) |
| [`../documents/getting-started/quick-start.md`](../documents/getting-started/quick-start.md) | 5-minute setup guide: start server, create session, paint and run, export, CLI alternative | Ch 3 (Implementation — user flow) |
| [`../documents/getting-started/installation.md`](../documents/getting-started/installation.md) | Requirements, git clone, venv, pip install, start commands, URLs, troubleshooting | Ch 3 (Implementation — deployment) |

### 🔌 API & Technical Reference

| Document | What It Contains | Useful For |
|---|---|---|
| [`../documents/developer/api-reference.md`](../documents/developer/api-reference.md) | REST endpoint summary (rules, sessions, metrics), WebSocket sim, request/response examples, page routes, error format | Ch 3 (Implementation — API layer) |
| [`../documents/reference/memory.md`](../documents/reference/memory.md) | Full repo map, web pages & routes, API endpoints summary, frontend behaviours, database schema, built-in rules/metrics, timeline, CLI commands, tests, legacy notes | Ch 1–5 (fact-checking anything) |

### 📖 Research & Legacy

| Document | What It Contains | Useful For |
|---|---|---|
| [`../docs/WHITEPAPER_DRAFT.md`](../docs/WHITEPAPER_DRAFT.md) | Full academic whitepaper: abstract, motivation, legacy summary, design goals, architecture, mathematical formalism, metrics catalogue, rules & GA, deployment options, educational programme, validation, experiment spec, roadmap, references | Ch 1 (Introduction), Ch 2 (Literature & Technology), Ch 5 (Future Work) |
| [`../documents/reference/REFERENCE_CODE_ANALYSIS.md`](../documents/reference/REFERENCE_CODE_ANALYSIS.md) | Deep analysis of original Java reference implementation: file inventory, core algorithm, formulas, rule system, statistics registry, redundant files | Ch 2 (Literature — legacy context), Ch 3 (Implementation — migration) |
| [`../documents/reference/FINAL_STATUS.md`](../documents/reference/FINAL_STATUS.md) | Resolved issues: database schema, type annotations, Unicode/emoji fixes | Ch 4 (Evaluation — issues resolved) |
| [`../documents/developer/dev_log.md`](../documents/developer/dev_log.md) | Chronological milestones: Phase 1 (engine), Phase 2 (web consolidation), Phase 3 (UX/canvas), Phase 4 (experiment config), known fixes, open items, version | Ch 3 (Implementation — sprint narrative), Ch 5 (Reflection) |

### 🗂️ Other Reference

| Document | What It Contains | Useful For |
|---|---|---|
| [`../README.md`](../README.md) | Project homepage: overview, capabilities, architecture diagram, repository layout, installation, usage, API example, CLI, technology stack, troubleshooting, contributing | Ch 1 (Background), Appendix C (Artefact link) |
| [`../documents/README.md`](../documents/README.md) | Documentation hub: map of all user/dev guides, related material, legacy notes | Navigating to other docs |
| [`../docs/README.md`](../docs/README.md) | Docs index: points to main docs, memory, whitepaper draft, reference code analysis | Navigating to research drafts |
| [`../documents/assets/README.md`](../documents/assets/README.md) | Screenshot guidelines, naming conventions | Appendix D (Screencast/assets) |

---

## 🚦 Daily Writing Workflow

Use this as your pre-writing ritual:

1. Open `index.md` (this file).
2. Identify which chapter/section you are writing today.
3. Read the **Guidance File** for that chapter *before* you write.
4. Open the **Source Material** files listed for that chapter in side tabs.
5. Keep `00-before-you-start/writing-style.md` open in a side panel while you write.
6. After finishing a section, re-read `00-before-you-start/structure-guide.md` to verify word-count compliance.

---

## 📁 Folder Map

```
report/
├── index.md                          ← 📍 YOU ARE HERE (master writing hub)
│
├── 00-before-you-start/              ← READ FIRST — ALWAYS
│   ├── README.md                     ← Golden rules (2-min read)
│   ├── structure-guide.md            ← Word counts & section order
│   ├── writing-style.md              ← Banned words & third-person rules
│   └── layout-and-formatting.md      ← Font, spacing, margins
│
├── 01-front-matter/                  ← READ WHEN WRITING DECLARATION/ACKS/ABSTRACT
│   └── front-matter.md
│
├── 02-chapters/                      ← READ BEFORE WRITING EACH CHAPTER
│   ├── 01-introduction.md
│   ├── 02-literature-technology-review.md
│   ├── 03-implementation.md
│   ├── 04-evaluation-results.md
│   └── 05-conclusion.md
│
├── 03-back-matter/                   ← READ WHEN FINALISING
│   ├── references.md
│   └── appendices.md
│
└── 99-compliance/                    ← READ EARLY (IPR) & DURING CHAPTER 1 (LSE&P)
    ├── legal-social-ethical.md
    └── copyright-ipr.md
```

---

## ⚠️ Critical Reminders

| # | Rule |
|---|---|
| 1 | **Never write without reading the chapter guide first.** Every chapter has required subheadings and specific expectations. |
| 2 | **The Abstract is written last.** It summarises the entire report. |
| 3 | **Start each section on a new page.** |
| 4 | **Delete all template guidance text** (dark blue notes, red lines) before submission. |
| 5 | **All text must be black.** No exceptions unless approved. |
| 6 | **Every reference must be read by you.** No AI-generated references. |
| 7 | **Appendices need evidence collected early.** Do not leave them until the final week. |
| 8 | **Use the Source Material table above** to find project facts quickly. Do not waste tokens re-reading the whole repo. |

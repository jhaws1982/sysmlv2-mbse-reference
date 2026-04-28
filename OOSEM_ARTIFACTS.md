# OOSEM Artifact Inventory
## SysML v2 MBSE Reference

This document catalogues every OOSEM artifact produced by the toolchain for
this model. It is the reference for modelers and reviewers: what exists, which
model elements are required, how to generate it, and what the output format is.

Methodology reference: *Model-Based Systems Engineering with SysML*
(Friedenthal, Moore, Steiner) — INCOSE OOSEM working group.

---

## Toolchain Directory Structure

```
__Tools/
├── generate_artifacts.py       # Orchestrator — runs suites from artifacts.yaml
├── artifacts.yaml              # Suite definitions and script configuration
├── _tool_utils.py              # Shared utilities for all scripts
├── report_builder.py           # PDF/HTML report rendering infrastructure
├── requirements.txt            # Python dependencies
│
├── OOSEM/                      # Official OOSEM artifact scripts (named by artifact ID)
│   ├── SN01_stakeholder_register.py
│   ├── SN03_use_case_catalog.py
│   ├── SN04_opscon_report.py
│   ├── SN05_stakeholder_req_spec.py
│   ├── SN06_stakeholder_traceability.py
│   ├── SR01_sys_req_spec.py
│   ├── SR02_req_hierarchy.py
│   ├── SR03_req_traceability.py
│   ├── SR04_req_traceability_matrix.py
│   ├── SR05_req_completeness.py
│   ├── SR06_req_quality.py
│   ├── LA01_logical_arch_report.py
│   ├── LA02_logical_decomposition.py
│   ├── LA03_interface_catalog.py
│   ├── LA04_behavioral_summary.py
│   ├── LA05_req_allocation.py
│   ├── LA06_logical_completeness.py
│   └── RM01_risk_report.py
│
└── generic/                    # Utility scripts without a direct OOSEM artifact mapping
    ├── generic_concern_report.py
    ├── generic_concerns_matrix.py
    ├── generic_coverage_matrix.py
    ├── generic_dependency_map.py
    ├── generic_req_debug.py
    ├── generic_req_report.py
    ├── generic_req_validate.py
    ├── generic_result_matrix.py
    ├── generic_satisfaction_matrix.py
```

---

## Phase 1 — Stakeholder Needs & Requirements

| ID | Artifact | Script | Output | Required Model Elements |
|----|----------|--------|--------|-------------------------|
| SN-01 | Stakeholder Register | `OOSEM/SN01_stakeholder_register.py` | Markdown | `StakeholderDefs`, `StakeholderConcerns` packages |
| SN-03 | Use Case Catalog | `OOSEM/SN03_use_case_catalog.py` | Markdown | `UseCaseDefs`, `UseCaseModel` packages |
| SN-04 | Operational Concept Description | `OOSEM/SN04_opscon_report.py` | Markdown + PDF | `SystemContext`, `OperationalConcept` packages |
| SN-05 | Stakeholder Requirements Specification | `OOSEM/SN05_stakeholder_req_spec.py` | Markdown + PDF | Stakeholder requirement usages with `doc` + `doc Rationale` |
| SN-06 | Stakeholder Req → Use Case Traceability | `OOSEM/SN06_stakeholder_traceability.py` | Markdown | `frame concern` links in use case usages |

---

## Phase 2 — System Requirements

| ID | Artifact | Script | Output | Required Model Elements |
|----|----------|--------|--------|-------------------------|
| SR-01 | System Requirements Specification | `OOSEM/SR01_sys_req_spec.py` | Markdown + PDF | All requirement usages with `doc` + `doc Rationale` |
| SR-02 | Requirements Hierarchy / Decomposition | `OOSEM/SR02_req_hierarchy.py` | Markdown + Graphviz PNG | Nested `requirement` usages (subrequirements) |
| SR-03 | Stakeholder→System Req Traceability Matrix | `OOSEM/SR03_req_traceability.py` | Markdown | `#derivation connection` or nested subrequirements |
| SR-04 | Requirements Derivation Traceability Matrix | `OOSEM/SR04_req_traceability_matrix.py` | Markdown + Excel | Nested requirement usages and/or `DeriveRequirementUsage` |
| SR-05 | Requirements Completeness Gap Report | `OOSEM/SR05_req_completeness.py` | Markdown | Any `requirement` usages |
| SR-06 | Requirements Quality Report | `OOSEM/SR06_req_quality.py` | Markdown | `requirement` usages with `doc` text |

### SR-04 — Requirements Derivation Traceability Matrix

Produces a cross-reference matrix showing which requirements are derived from
which parent requirements. Both rows and columns are ordered by pre-order tree
traversal so derived requirements appear immediately after their parent in both
axes. A requirement may appear in both rows and columns simultaneously (e.g.
with `--depth 2`, L1 requirements are row sources for L2 derivations and
column targets derived from L0).

**Options** (CLI or `artifacts.yaml` `script_config`):

| Option | Default | Description |
|--------|---------|-------------|
| `--start-level` | `0` | Floor level — requirements above this are excluded |
| `--depth` | `1` | Levels to traverse. Rows = L{start}..L{start+depth-1}, cols = L{start+1}..L{start+depth} |
| `--program` | _(none)_ | Restrict to one program's requirements package (e.g. `Program_A` → `ProgramA_Requirements`). Without this flag all `*_Requirements` program packages are excluded |
| `--format` | `md` | `md`, `xlsx`, or `both` |

**Cell colouring (Excel):**
- ✓ light blue — derivation relationship exists
- Yellow row — source requirement has no derived reqs in the column window (coverage gap)
- Red column — derived requirement has no source in the row window (orphaned)

**Examples:**
```bash
# Core requirements, roots as rows, direct children as columns
python __Tools/OOSEM/SR04_req_traceability_matrix.py . --format xlsx

# Two levels deep — L0+L1 as rows, L1+L2 as columns
python __Tools/OOSEM/SR04_req_traceability_matrix.py . --depth 2 --format both

# Program A requirements only
python __Tools/OOSEM/SR04_req_traceability_matrix.py . --program Program_A --format xlsx
```

---

## Phase 3 — Logical Architecture

| ID | Artifact | Script | Output | Required Model Elements |
|----|----------|--------|--------|-------------------------|
| LA-01 | Logical Architecture Description | `OOSEM/LA01_logical_arch_report.py` | Markdown + PDF | `LogicalArchDefs`, `LogicalArchModel` with `doc` blocks |
| LA-02 | Logical Block Decomposition | `OOSEM/LA02_logical_decomposition.py` | Markdown + Graphviz PNG | `part def` hierarchy in logical layer |
| LA-03 | Interface Catalog | `OOSEM/LA03_interface_catalog.py` | Markdown | `port def`, `item def` in `LogicalInterfaces` |
| LA-04 | Behavioral Summary | `OOSEM/LA04_behavioral_summary.py` | Markdown | `action def`, `state def`, `perform` links |
| LA-05 | Requirements Allocation Matrix | `OOSEM/LA05_req_allocation.py` | Markdown | `satisfy`/`allocate` links in `RequirementAllocations` |
| LA-06 | Logical Architecture Completeness | `OOSEM/LA06_logical_completeness.py` | Markdown | All `02_Core/Logical/` and `02_Core/Allocations/` packages |

---

## Risk Management

| ID | Artifact | Script | Output | Required Model Elements |
|----|----------|--------|--------|-------------------------|
| RM-01 | Risk Register | `OOSEM/RM01_risk_report.py` | Markdown | `@RiskItem` metadata annotations across all packages |

---

## Generic Utility Scripts

These scripts do not map directly to a named OOSEM artifact but support
model analysis, validation, and debugging across all phases.

| Script | Purpose | Notes |
|--------|---------|-------|
| `generic/generic_req_report.py` | Requirements table with `satisfy` and `#derive` relationship columns | Complements SR-02; shows cross-package traceability links alongside requirement text |
| `generic/generic_req_validate.py` | Full SRS requirement validation (ID, text, rationale checks) | Invoked by SR-05 (`SR05_req_completeness.py`) |
| `generic/generic_result_matrix.py` | V&V result status joined from CTest JUnit XML | Phase 4–5 use |
| `generic/generic_concerns_matrix.py` | Concern → requirement coverage matrix | Feeds SN-06 |
| `generic/generic_satisfaction_matrix.py` | Requirement → architecture satisfaction matrix | Feeds LA-05 |
| `generic/generic_coverage_matrix.py` | Requirement → verification coverage matrix | Phase 4–5 use |
| `generic/generic_dependency_map.py` | Executable `dependency` relationship mapping | Dev/build toolchain analysis |
| `generic/generic_concern_report.py` | Stakeholder concern narrative report | Detailed concern-level output |
| `generic/generic_req_debug.py` | Requirement element inspection / API debugging | Developer use |

---

## Artifact Generation Suites

Run `python __Tools/generate_artifacts.py --suite <name>`:

| Suite | Contents |
|-------|----------|
| `stakeholder` | SN-01, SN-03, SN-04, SN-05, SN-06 |
| `requirements` | SR-01, SR-02, SR-03, SR-04, SR-05, SR-06 |
| `logical` | LA-01 through LA-06 |
| `risk` | RM-01 |
| `diagnostics` | SR-05, SR-06, LA-06 (gap reports only) |
| `formal_docs` | SN-04, SN-05, SR-01, LA-01 (PDF deliverables) |
| `all` | Full Phases 1–3 + RM-01 |

---

## Requirement Convention Reference

All requirement usages in this model follow the doc-based convention
established in `00_Shared/SRS_Definitions.sysml`:

```sysml
requirement <'REQ-CAP-001'> myRequirement : CapabilityRequirement {
    doc
    /* The CSCI shall <verb> <object> under <conditions>. */
    doc Rationale
    /* Why this requirement exists and what risk it mitigates. */
    subject sys : MySystem;
    attribute :>> capabilityName = "...";
    part :>> criteria : VerificationCriteria {
        doc
        /* Test setup and PASS/FAIL condition in narrative form. */
        attribute :>> verificationMethod = VerificationMethodKind::test;
        attribute :>> threshold          = "compact measurable bound";
    }
}
```

**Mandatory on every requirement usage:**
1. `<'REQ-ID'>` — short-name identifier (validated by `generic_req_validate.py` HasId check)
2. Unnamed `doc` block — normative "shall" text (HasText check)
3. `doc Rationale` block — justification (HasRationale check)

**Removed in this revision** (no longer exist in `SRS_Definitions.sysml`):
- `id`, `text`, `rationale` string attributes on requirements
- `passFailLogic`, `conditions`, `criteriaObjective` on `VerificationCriteria`

---

## Source File → Artifact Map

| Source File | Artifacts |
|-------------|-----------|
| `02_Core/Context/system_context.sysml` | SN-04, SR-01 context section |
| `02_Core/Context/operational_concept.sysml` | SN-04 |
| `01_Stakeholders/Stakeholders.sysml` | SN-01 |
| `01_Stakeholders/Concerns.sysml` | SN-01, SN-05, SN-06 |
| `02_Core/UseCases/use_case_defs.sysml` | SN-03 |
| `02_Core/UseCases/use_case_model.sysml` | SN-03, SN-06 |
| `02_Core/Requirements/Requirements_Decl.sysml` | SR-01, SR-02, SR-03, SR-04, SR-05, SR-06 |
| `04_Programs/*/Requirements/Requirements.sysml` | SR-04 (with `--program`), SR-01, SR-05, SR-06 |
| `02_Core/Logical/logical_arch_defs.sysml` | LA-01, LA-02, LA-04 |
| `02_Core/Logical/logical_arch_model.sysml` | LA-01, LA-02 |
| `02_Core/Logical/interfaces.sysml` | LA-03 |
| `02_Core/Logical/Behavior/state_machines.sysml` | LA-04 |
| `02_Core/Logical/Behavior/action_sequences.sysml` | LA-04 |
| `02_Core/Allocations/req_allocations.sysml` | LA-05, LA-06 |
| All packages (metadata annotations) | RM-01 |

# OOSEM Artifact Inventory
## SysML v2 MBSE Reference

This document catalogues every OOSEM artifact produced by the toolchain for
this model. It is the reference for modelers and reviewers: what exists, which
model elements are required, how to generate it, and what the output format is.

Methodology reference: *Model-Based Systems Engineering with SysML*
(Friedenthal, Moore, Steiner) — INCOSE OOSEM working group.

---

## Phase 1 — Stakeholder Needs & Requirements

| ID | Artifact | Script | Output | Required Model Elements |
|----|----------|--------|--------|-------------------------|
| SN-01 | Stakeholder Register | `stakeholder_register.py` | Markdown | `StakeholderDefs`, `StakeholderConcerns` packages |
| SN-03 | Use Case Catalog | `use_case_catalog.py` | Markdown | `UseCaseDefs`, `UseCaseModel` packages |
| SN-04 | Operational Concept Description | `opscon_report.py` | Markdown + PDF | `SystemContext`, `OperationalConcept` packages |
| SN-05 | Stakeholder Requirements Specification | `stakeholder_req_spec.py` | Markdown + PDF | Stakeholder requirement usages with `doc` + `doc Rationale` |
| SN-06 | Stakeholder Req → Use Case Traceability | `stakeholder_traceability.py` | Markdown | `frame concern` links in use case usages |

---

## Phase 2 — System Requirements

| ID | Artifact | Script | Output | Required Model Elements |
|----|----------|--------|--------|-------------------------|
| SR-01 | System Requirements Specification | `sys_req_spec.py` | Markdown + PDF | All requirement usages with `doc` + `doc Rationale` |
| SR-02 | Requirements Hierarchy / Decomposition | `req_hierarchy.py` | Markdown + Graphviz PNG | Nested `requirement` usages (subrequirements) |
| SR-03 | Stakeholder→System Req Traceability Matrix | `req_traceability.py` | Markdown | `#derivation connection` or nested subrequirements |
| SR-05 | Requirements Completeness Gap Report | `req_completeness.py` | Markdown | Any `requirement` usages |
| SR-06 | Requirements Quality Report | `req_quality.py` | Markdown | `requirement` usages with `doc` text |

---

## Phase 3 — Logical Architecture

| ID | Artifact | Script | Output | Required Model Elements |
|----|----------|--------|--------|-------------------------|
| LA-01 | Logical Architecture Description | `logical_arch_report.py` | Markdown + PDF | `LogicalArchDefs`, `LogicalArchModel` with `doc` blocks |
| LA-02 | Logical Block Decomposition | `logical_decomposition.py` | Markdown + Graphviz PNG | `part def` hierarchy in logical layer |
| LA-03 | Interface Catalog | `interface_catalog.py` | Markdown | `port def`, `item def` in `LogicalInterfaces` |
| LA-04 | Behavioral Summary | `behavioral_summary.py` | Markdown | `action def`, `state def`, `perform` links |
| LA-05 | Requirements Allocation Matrix | `req_allocation.py` | Markdown | `satisfy`/`allocate` links in `RequirementAllocations` |
| LA-06 | Logical Architecture Completeness | `logical_completeness.py` | Markdown | All `02_Core/Logical/` and `02_Core/Allocations/` packages |

---

## Existing Tools (retained from original toolchain)

| Script | Purpose | Notes |
|--------|---------|-------|
| `req_validate.py` | Full SRS requirement validation | Updated for doc-convention |
| `req_report.py` | Requirements list + hierarchy | Predecessor to `req_hierarchy.py` |
| `result_matrix.py` | V&V result status (CTest XML) | Phase 4–5 use |
| `concerns_matrix.py` | Concern → requirement coverage | |
| `satisfaction_matrix.py` | Requirement → architecture satisfaction | |
| `coverage_matrix.py` | Requirement → verification coverage | |
| `dependency_map.py` | Executable dependency mapping | |

---

## Artifact Generation Suites

Run `python __Tools/generate_artifacts.py --suite <name>`:

| Suite | Contents |
|-------|----------|
| `stakeholder` | SN-01, SN-03, SN-04, SN-05, SN-06 |
| `requirements` | SR-01, SR-02, SR-03, SR-05, SR-06 |
| `logical` | LA-01 through LA-06 |
| `diagnostics` | SR-05, SR-06, LA-06 (gap reports only) |
| `formal_docs` | SN-04, SN-05, SR-01, LA-01 (PDF deliverables) |
| `all` | Full Phases 1–3 |

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
        attribute :>> verificationMethod = VerificationMethodKind::Test;
        attribute :>> threshold          = "compact measurable bound";
    }
}
```

**Mandatory on every requirement usage:**
1. `<'REQ-ID'>` — short-name identifier (validated by `req_validate.py` HasId check)
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
| `02_Core/Requirements/Requirements_Decl.sysml` | SR-01, SR-02, SR-05, SR-06 |
| `04_Programs/*/Requirements/Requirements.sysml` | SR-01, SR-02, SR-05, SR-06 |
| `02_Core/Logical/logical_arch_defs.sysml` | LA-01, LA-02, LA-04 |
| `02_Core/Logical/logical_arch_model.sysml` | LA-01, LA-02 |
| `02_Core/Logical/interfaces.sysml` | LA-03 |
| `02_Core/Logical/Behavior/state_machines.sysml` | LA-04 |
| `02_Core/Logical/Behavior/action_sequences.sysml` | LA-04 |
| `02_Core/Allocations/req_allocations.sysml` | LA-05, LA-06 |

# SysML v2 MBSE Reference

A reference SysML v2 model demonstrating multi-file architecture with the
Leaf + Hub namespace pattern, DI-IPSC-81433A compliant requirements using
`SRS_Definitions`, and a Python Automator toolchain aligned to the OOSEM
artifact suite.

---

## Python Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Python dependencies
pip install -r __Tools/requirements.txt

# 3. Install system packages required for diagrams and PDF output
sudo apt install pandoc graphviz
```

`syside` requires a license file. Place it at the path syside expects (see
`syside_license` package docs or your Sensmetry license delivery email).

PDF generation uses `pandoc --pdf-engine=weasyprint`. The `weasyprint` binary
is resolved from the active Python environment, so the venv must be activated
(or scripts run via `python` from the venv) for PDF output to work.
Diagram generation uses the `dot` CLI from graphviz; without it, diagrams are
skipped and a notice is printed.

---

## File Layout

```
sysmlv2-mbse-reference/
│
├── Model.sysml                              ← root index package
│
├── 00_Shared/
│   ├── Data_Types.sysml                     leaf: SharedData
│   ├── SRS_Definitions.sysml                leaf: SRS_Definitions  ← DI-IPSC-81433A metamodel
│   └── _namespace.sysml                     hub:  Shared::Data, Shared::SRS
│
├── 01_Stakeholders/
│   ├── Stakeholders.sysml                   leaf: StakeholderDefs
│   ├── Concerns.sysml                       leaf: StakeholderConcerns
│   └── _namespace.sysml                     hub:  Stakeholders::Roles, Stakeholders::Concerns
│
├── 02_Core/
│   ├── _namespace.sysml                     hub:  Core::*
│   ├── Context/
│   │   ├── system_context.sysml             leaf: SystemContext
│   │   └── operational_concept.sysml        leaf: OperationalConcept
│   ├── UseCases/
│   │   ├── use_case_defs.sysml              leaf: UseCaseDefs
│   │   └── use_case_model.sysml             leaf: UseCaseModel
│   ├── Logical/
│   │   ├── FeatureA.sysml                   leaf: FeatureA
│   │   ├── FeatureB.sysml                   leaf: FeatureB
│   │   ├── FeatureC.sysml                   leaf: FeatureC
│   │   ├── Core_System.sysml                leaf: CoreSystem
│   │   ├── logical_arch_defs.sysml          leaf: LogicalArchDefs
│   │   ├── logical_arch_model.sysml         leaf: LogicalArchModel
│   │   ├── interfaces.sysml                 leaf: LogicalInterfaces
│   │   └── Behavior/
│   │       ├── state_machines.sysml         leaf: StateMachines
│   │       └── action_sequences.sysml       leaf: ActionSequences
│   ├── Requirements/
│   │   ├── Requirements_Def.sysml           leaf: RequirementsDef
│   │   └── Requirements_Decl.sysml          leaf: RequirementsDecl
│   └── Allocations/
│       └── req_allocations.sysml            leaf: RequirementAllocations
│
├── 03_ProductLine/
│   └── Configurations.sysml                 leaf: ProductLineConfigurations
│
├── 04_Programs/
│   ├── _namespace.sysml                     hub:  Programs::ProgramA, Programs::ProgramB
│   ├── Program_A/
│   │   ├── Config.sysml                     leaf: ProgramA
│   │   ├── Stakeholders/
│   │   ├── Architecture/
│   │   ├── Requirements/Requirements.sysml  leaf: ProgramA_Requirements
│   │   └── Verification/
│   └── Program_B/  (same structure)
│
├── 05_Verification/
│   ├── TestCases.sysml                      leaf: TestCases
│   ├── Traceability.sysml                   leaf: Traceability
│   └── _namespace.sysml
│
└── __Tools/
    ├── generate_artifacts.py                ← Orchestrator — runs suites from artifacts.yaml
    ├── artifacts.yaml                       ← Suite definitions + per-script config
    ├── _tool_utils.py                       ← Shared utilities for all scripts
    ├── report_builder.py                    ← PDF/HTML rendering infrastructure
    ├── requirements.txt                     ← Python dependencies
    │
    ├── OOSEM/                               ← Official OOSEM artifact scripts
    │   ├── SN01_stakeholder_register.py     SN-01 Stakeholder Register
    │   ├── SN03_use_case_catalog.py         SN-03 Use Case Catalog
    │   ├── SN04_opscon_report.py            SN-04 Operational Concept Description
    │   ├── SN05_stakeholder_req_spec.py     SN-05 Stakeholder Requirements Spec
    │   ├── SN06_stakeholder_traceability.py SN-06 Stakeholder → Use Case Traceability
    │   ├── SR01_sys_req_spec.py             SR-01 System Requirements Specification
    │   ├── SR02_req_hierarchy.py            SR-02 Requirements Hierarchy / Decomposition
    │   ├── SR03_req_traceability.py         SR-03 Stakeholder → System Req Traceability
    │   ├── SR04_req_traceability_matrix.py  SR-04 Requirements Derivation Matrix
    │   ├── SR05_req_completeness.py         SR-05 Requirements Completeness Gap Report
    │   ├── SR06_req_quality.py              SR-06 Requirements Quality Report
    │   ├── LA01_logical_arch_report.py      LA-01 Logical Architecture Description
    │   ├── LA02_logical_decomposition.py    LA-02 Logical Block Decomposition
    │   ├── LA03_interface_catalog.py        LA-03 Interface Catalog
    │   ├── LA04_behavioral_summary.py       LA-04 Behavioral Summary
    │   ├── LA05_req_allocation.py           LA-05 Requirements Allocation Matrix
    │   ├── LA06_logical_completeness.py     LA-06 Logical Architecture Completeness
    │   └── RM01_risk_report.py              RM-01 Risk Register
    │
    └── generic/                             ← Utility scripts (no direct OOSEM artifact ID)
        ├── generic_concern_report.py        Stakeholder concern narrative report
        ├── generic_concerns_matrix.py       Concern → requirement coverage matrix
        ├── generic_coverage_matrix.py       Requirement → verification coverage matrix
        ├── generic_dependency_map.py        Executable dependency relationship mapping
        ├── generic_req_debug.py             Requirement element inspection / API debugging
        ├── generic_req_report.py            Requirements table with satisfy/derive columns
        ├── generic_req_validate.py          Full SRS requirement validation
        ├── generic_result_matrix.py         V&V result status joined from CTest JUnit XML
        ├── generic_satisfaction_matrix.py   Requirement → architecture satisfaction matrix
```

---

## Namespace Architecture

Every layer uses the **Leaf + Hub** pattern:

- **LEAF FILE** — flat, globally-unique package name, owns the content
- **HUB FILE** (`_namespace.sysml`) — the ONE declaration of a nested namespace
  node, assembles leaf packages via `public import`

Consumers always import via the nested path: `private import Core::Architecture::*`

`public import` appears **only** in hub files. All other imports are `private import`.

---

## SRS Requirements Pattern

All requirements in this model specialize types from `SRS_Definitions`
(DI-IPSC-81433A compliant). Import the package via:

```sysml
private import SRS_Definitions::*;
// or via the namespace hub:
private import Shared::SRS::*;
```

Each requirement follows the Def/Decl split and the doc-block convention:

```sysml
// DEF — stable type, framing a concern
requirement def <'REQ-CAP-001-DEF'> MyCapability_Def :> CapabilityRequirement {
    doc /* Capability requirement description. */
    frame concern MyConcern;
}

// DECL — usage with all SRS fields populated
requirement <'REQ-CAP-001'> myCapability : MyCapability_Def {
    doc
    /* The CSCI shall <verb> <object> under <conditions>. */
    doc Rationale
    /* Why this requirement exists and what risk it mitigates. */
    subject sys : MySystem;
    attribute :>> source      = "SYS-PERF-003";
    attribute :>> priority    = CMNDEF::LevelKind::High;
    attribute :>> criticality = CMNDEF::LevelKind::High;
    part :>> criteria : VerificationCriteria {
        doc
        /* Test setup and PASS/FAIL condition in narrative prose. */
        attribute :>> verificationMethod = VerificationMethodKind::test;
        attribute :>> threshold          = "compact measurable bound";
    }
}
```

**Mandatory on every requirement usage:**
1. `<'REQ-ID'>` short-name identifier
2. Unnamed `doc` block — normative "shall" statement
3. `doc Rationale` block — justification

**Not in `SRS_Definitions.sysml`** (removed):
- `id`, `text`, `rationale` string attributes on requirements
- `passFailLogic`, `conditions`, `criteriaObjective` on `VerificationCriteria`

---

## Tooling

All tools run from the model root directory. OOSEM artifact scripts live in
`__Tools/OOSEM/`; utility scripts live in `__Tools/generic/`.

```bash
# Run the full artifact suite
python __Tools/generate_artifacts.py --suite all

# Run a specific suite
python __Tools/generate_artifacts.py --suite requirements
python __Tools/generate_artifacts.py --suite stakeholder
python __Tools/generate_artifacts.py --suite risk

# Run a single script
python __Tools/generate_artifacts.py --script OOSEM/SR04_req_traceability_matrix

# List all available suites and scripts
python __Tools/generate_artifacts.py --list

# Dry run (check script existence without executing)
python __Tools/generate_artifacts.py --suite all --dry-run

# ── Individual OOSEM scripts ──────────────────────────────────────────────────

# SR-01 System Requirements Specification
python __Tools/OOSEM/SR01_sys_req_spec.py .

# SR-02 Requirements Hierarchy (ID-only diagrams by default)
python __Tools/OOSEM/SR02_req_hierarchy.py .
python __Tools/OOSEM/SR02_req_hierarchy.py . --show-doc   # include req text in diagrams

# SR-04 Requirements Derivation Traceability Matrix
python __Tools/OOSEM/SR04_req_traceability_matrix.py . --format xlsx
python __Tools/OOSEM/SR04_req_traceability_matrix.py . --start-level 0 --depth 2
python __Tools/OOSEM/SR04_req_traceability_matrix.py . --program Program_A --depth 1

# RM-01 Risk Register
python __Tools/OOSEM/RM01_risk_report.py .

# ── Generic utility scripts ───────────────────────────────────────────────────

# Validate SRS requirements
python __Tools/generic/generic_req_validate.py .
python __Tools/generic/generic_req_validate.py . --fail-on-invalid
python __Tools/generic/generic_req_validate.py . --package ProgramA_Requirements

# Requirements table with satisfy/derive relationship columns
python __Tools/generic/generic_req_report.py . --format md

# V&V result matrix (joined from CTest JUnit XML)
python __Tools/generic/generic_result_matrix.py .

# Other matrices
python __Tools/generic/generic_concerns_matrix.py .
python __Tools/generic/generic_satisfaction_matrix.py .
python __Tools/generic/generic_coverage_matrix.py .
python __Tools/generic/generic_dependency_map.py .

```

See `OOSEM_ARTIFACTS.md` for the complete artifact inventory, required model
elements, and output format for each script.

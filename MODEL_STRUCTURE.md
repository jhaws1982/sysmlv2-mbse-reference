# Model Structure Guide
## SysML v2 MBSE Reference

Canonical directory layout, import rules, and authoring conventions.
Consult this file when deciding where a new element belongs.

---

## Design Philosophy

OOSEM artifacts are **interwoven into the existing numbered layer structure**,
not isolated in a separate layer. Core OOSEM concerns (context, use cases,
logical architecture, allocations) live inside `02_Core/` alongside existing
architecture and requirements. Program-specific OOSEM elements extend
each `04_Programs/Program_X/` directory.

This keeps related concerns co-located: a systems engineer working on the
logical architecture finds it next to the requirements and physical architecture
it relates to, not in a separate tree.

---

## Directory Layout

```
sysmlv2-mbse-reference/
│
├── 00_Shared/
│   ├── SRS_Definitions.sysml     ← Requirement def library (DI-IPSC-81433A)
│   │                               Doc-convention: unnamed doc + doc Rationale
│   │                               (no id/text/rationale string attributes)
│   ├── Data_Types.sysml          ← Shared data type and enum definitions
│   └── _namespace.sysml          ← Hub: package Shared { Data, SRS }
│
├── 01_Stakeholders/
│   ├── Stakeholders.sysml        ← Leaf: StakeholderDefs (part defs for roles)
│   ├── Concerns.sysml            ← Leaf: StakeholderConcerns (concern defs)
│   │                               Rule: subject must be FIRST in every concern def body
│   └── _namespace.sysml          ← Hub: package Stakeholders { Roles, Concerns }
│
├── 02_Core/                      ← All core model content
│   ├── Context/                  ← OOSEM Phase 1 — system boundary & OpsCon
│   │   ├── system_context.sysml  ← leaf: SystemContext
│   │   │                           Black-box system part def + external actors
│   │   │                           + context assembly. Source for SN-04, SR-01.
│   │   └── operational_concept.sysml ← leaf: OperationalConcept
│   │                               Missions and operational scenarios. Source for SN-04.
│   │
│   ├── UseCases/                 ← OOSEM Phase 1 — core use case model
│   │   ├── use_case_defs.sysml   ← leaf: UseCaseDefs (stable use case types)
│   │   └── use_case_model.sysml  ← leaf: UseCaseModel (assembled usages + includes)
│   │                               Source for SN-03, SN-06.
│   │
│   ├── Logical/                  ← All architecture and logical modeling
│   │   ├── FeatureA.sysml        ← leaf: FeatureA        (feature component + port def)
│   │   ├── FeatureB.sysml        ← leaf: FeatureB        (feature component + port def)
│   │   ├── FeatureC.sysml        ← leaf: FeatureC        (integration component)
│   │   ├── Core_System.sysml     ← leaf: CoreSystem      (top-level assembly)
│   │   ├── logical_arch_defs.sysml ← leaf: LogicalArchDefs
│   │   │                             Logical subsystem part defs + action defs.
│   │   │                             Stable types — treat as a configuration item.
│   │   ├── logical_arch_model.sysml ← leaf: LogicalArchModel
│   │   │                             Assembled part usages + perform links.
│   │   │                             Changes with architecture decisions.
│   │   ├── interfaces.sysml      ← leaf: LogicalInterfaces
│   │   │                           Shared port defs, flow item defs.
│   │   │                           Rule: NO composite usages inside port defs.
│   │   └── Behavior/
│   │       ├── state_machines.sysml  ← leaf: StateMachines
│   │       └── action_sequences.sysml ← leaf: ActionSequences
│   │
│   ├── Requirements/             ← Core CSCI requirements
│   │   ├── Requirements_Def.sysml ← leaf: RequirementsDef (stable req types)
│   │   └── Requirements_Decl.sysml ← leaf: RequirementsDecl (req usages, doc-convention)
│   │
│   ├── Allocations/              ← OOSEM Phase 3 — req → logical allocation
│   │   └── req_allocations.sysml ← leaf: RequirementAllocations
│   │                               satisfy + allocate links. Kept separate from
│   │                               requirements and architecture because allocations
│   │                               change frequently without touching stable CIs.
│   │
│   └── _namespace.sysml          ← Hub: package Core {
│                                       Architecture, Context, UseCases,
│                                       Logical, Behavior, Requirements, Allocations }
│
├── 03_ProductLine/
│   └── Configurations.sysml      ← Product line variation points
│
├── 04_Programs/
│   ├── Program_A/
│   │   ├── Config.sysml          ← leaf: ProgramA (product line variant selection)
│   │   ├── Stakeholders/         ← Program A specific stakeholder defs + concerns
│   │   ├── Architecture/         ← Program A system and deployment definitions
│   │   │   ├── system.sysml      ← leaf: ProgramA_System
│   │   │   │                       Top-level logical system assembly.
│   │   │   │                       Composes core system + program config.
│   │   │   └── deployment.sysml  ← leaf: ProgramA_Deployment
│   │   │                           Operational deployment context.
│   │   ├── Requirements/         ← leaf: ProgramA_Requirements (doc-convention)
│   │   │   └── Requirements.sysml  Package: ProgramA_Requirements
│   │   │                           Convention: <ProgramName>_Requirements
│   │   │                           SR-04 --program flag filters by this package name.
│   │   └── Verification/         ← leaf: ProgramA_Verification
│   │
│   ├── Program_B/  (same structure as Program_A)
│   └── _namespace.sysml          ← Hub: package Programs { ProgramA, ProgramB }
│                                   Update this when adding new program sub-packages.
│
├── 05_Verification/
│   ├── TestCases.sysml           ← leaf: TestCases (verification def stubs)
│   ├── Traceability.sysml        ← leaf: Traceability (verification usages + satisfy links)
│   └── _namespace.sysml          ← Hub: package Verification { TestCases, Traceability }
│
│   Note: Results.sysml removed. Live test results are not stored in the model.
│   generic_result_matrix.py reads from CTest JUnit XML and joins against
│   verification names declared in Traceability.sysml.
│
├── Model.sysml                   ← Top-level index (imports only, no definitions)
├── README.md                     ← Project overview and quick-start
├── OOSEM_ARTIFACTS.md            ← OOSEM artifact inventory and convention reference
├── MODEL_STRUCTURE.md            ← This file
│
└── __Tools/
    ├── generate_artifacts.py     ← Orchestrator — runs suites from artifacts.yaml
    ├── artifacts.yaml            ← Suite definitions + per-script config
    ├── _tool_utils.py            ← Shared utilities (imported by all scripts)
    ├── report_builder.py         ← PDF/HTML rendering infrastructure
    ├── requirements.txt          ← Python dependencies
    │
    ├── OOSEM/                    ← Official OOSEM artifact scripts, named by artifact ID
    │   │                           Scripts in this directory use sys.path to reach
    │   │                           __Tools/ for _tool_utils and report_builder imports.
    │   │
    │   ├── SN01_stakeholder_register.py     SN-01 Stakeholder Register
    │   ├── SN03_use_case_catalog.py         SN-03 Use Case Catalog
    │   ├── SN04_opscon_report.py            SN-04 Operational Concept Description
    │   ├── SN05_stakeholder_req_spec.py     SN-05 Stakeholder Requirements Spec
    │   ├── SN06_stakeholder_traceability.py SN-06 Stakeholder → Use Case Traceability
    │   ├── SR01_sys_req_spec.py             SR-01 System Requirements Specification
    │   ├── SR02_req_hierarchy.py            SR-02 Requirements Hierarchy / Decomposition
    │   ├── SR03_req_traceability.py         SR-03 Stakeholder → System Req Traceability
    │   ├── SR04_req_traceability_matrix.py  SR-04 Requirements Derivation Matrix       ← NEW
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
    └── generic/                  ← Utility scripts without a direct OOSEM artifact ID
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

## Adding Program-Specific Architecture Content

When a program introduces subsystems, interfaces, or behaviors not in the
core, add them to `Architecture/system.sysml` for that program:

```sysml
// In 04_Programs/Program_A/Architecture/system.sysml
package ProgramA_System {
    private import Core::Logical::*;
    private import ProgramA::*;

    part def ProgramA_SensorSubsystem {
        doc /* Sensor processing subsystem unique to Program A. */
        port sensorIn : SensorDataPort;
    }

    part def ProgramA_SystemDef {
        part core      : CoreSystem_Assembly;
        part config    : ProgramA_Config;
        part sensorSys : ProgramA_SensorSubsystem;
    }
}
```

For program-specific use cases, context, or allocations that grow large
enough to warrant separate files, add them as additional leaves inside
`Architecture/` and register them in `04_Programs/_namespace.sysml`.

---

## Adding a New Program

1. Create `04_Programs/Program_X/` with the standard subdirectory structure
2. Add `Program_X/Requirements/Requirements.sysml` with package `ProgramX_Requirements`
   — the naming convention `<DirName without underscores>_Requirements` is required
   for `SR04_req_traceability_matrix.py --program Program_X` to resolve correctly
3. Register the new program in `04_Programs/_namespace.sysml`
4. Add `ProgramX` to the `Programs` hub package

---

## Import Rules

### Hub pattern
`_namespace.sysml` is the single declaration of its package. External consumers
import through the hub path:

```sysml
private import Core::Logical::*;          // through hub — correct
private import LogicalArchDefs::*;        // also valid (leaf is globally unique)
```

### Leaf-to-leaf imports (within the same hub)
A leaf assembled into a hub must NOT import through that hub — this creates
a circular dependency. Import sibling leaves directly by their package name:

```sysml
// In logical_arch_model.sysml (assembled into Core::Logical):
private import LogicalArchDefs::*;        // correct: leaf-to-leaf
private import LogicalInterfaces::*;      // correct: leaf-to-leaf
// NOT: private import Core::Logical::*  ← would be circular
```

Same rule applies within Stakeholders: `Concerns.sysml` imports
`StakeholderDefs::*` directly, not `Stakeholders::Roles::*`.

### Cross-layer imports
- Requirements import from `Shared::SRS::*` and `Stakeholders::Concerns::*`
- Logical imports from `SystemContext::*` (leaf) and `SRS_Definitions::*` (leaf)
- Allocations import from `Core::Requirements::*` and `Core::Logical::*`

---

## Requirement Authoring Convention

**Mandatory on every requirement usage:**

```sysml
requirement <'REQ-CAP-001'> myRequirement : CapabilityRequirement {
    doc
    /* The CSCI shall <verb> <object> under <conditions>. */
    doc Rationale
    /* Why this requirement exists and what risk it mitigates. */
    subject sys : MySystem;

    attribute :>> capabilityName = "MyCapability";   // type-specific attrs

    part :>> criteria : VerificationCriteria {
        doc
        /* Test setup and PASS/FAIL condition in narrative prose. */
        attribute :>> verificationMethod = VerificationMethodKind::test;
        attribute :>> threshold          = "compact measurable bound";
    }
}
```

**Removed — no longer in `SRS_Definitions.sysml`:**
- `id`, `text`, `rationale` string attributes on requirements
- `passFailLogic`, `conditions`, `criteriaObjective` on `VerificationCriteria`

---

## Key SysIDE Rules

**Concern defs** — `subject` must be FIRST in every concern def body. Use `actor` not `stakeholder`:

```sysml
concern def MyConcern {
    subject sys;                        // FIRST
    actor stakeholderA : StakeholderA;  // actor keyword, not stakeholder
    doc /* ... */
}
```

**Port defs** — no composite usages inside port defs (`port-definition-owned-usages-not-composite`):

```sysml
port def MyPort {
    in  item request  : DataRequest;   // OK — flow items only
    out item response : DataResponse;
    // part x : SomePart;             // INVALID
}
```

**Action defs** — must be at package level, never nested inside `part def`:

```sysml
// CORRECT — action def at package scope
action def ProcessData { in item d; out item result; }
part def MyComponent { perform action process : ProcessData; }

// WRONG — nested action def
part def MyComponent { action def ProcessData { ... } }
```

**Reserved keywords** — do not use as feature names:
`variant`, `variation`, `individual`, `snapshot`, `timeslice`,
`case`, `verify`, `constraint`

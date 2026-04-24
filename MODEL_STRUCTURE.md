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
│   │                               Updated: doc-convention (no id/text/rationale attrs)
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
│   │   │                           Feature components and logical subsystems
│   │   │                           live here as separate leaf files — one
│   │   │                           concern per file, all under one sub-package.
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
│   ├── Requirements/             ← Core CSCI requirements (existing, updated)
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
│   │   │   │                       This is what requirements and verification
│   │   │   │                       cases use as their subject.
│   │   │   │                       Add program-specific subsystems here.
│   │   │   │                       Change driver: architecture changes.
│   │   │   └── deployment.sysml  ← leaf: ProgramA_Deployment
│   │   │                           Operational deployment context: hardware
│   │   │                           platform, OS, site topology.
│   │   │                           Instantiates ProgramA_SystemDef in its
│   │   │                           operational environment.
│   │   │                           Change driver: environment changes.
│   │   ├── Requirements/         ← leaf: ProgramA_Requirements (doc-convention)
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
│   result_matrix.py reads from CTest JUnit XML / ATP documents and joins
│   against verification names declared in Traceability.sysml.
│
├── Model.sysml                   ← Top-level index (imports only, no definitions)
├── README.md                     ← Project overview and quick-start
├── OOSEM_ARTIFACTS.md            ← OOSEM artifact inventory and convention reference
├── MODEL_STRUCTURE.md            ← This file
│
└── __Tools/
    ├── generate_artifacts.py     ← Orchestrator
    ├── artifacts.yaml            ← Suite definitions + per-script config
    ├── _tool_utils.py            ← Shared library for OOSEM tools
    │
    ├── OOSEM artifact scripts:
    │   ├── stakeholder_register.py    SR-01 / SN-01
    │   ├── use_case_catalog.py        SN-03
    │   ├── opscon_report.py           SN-04
    │   ├── stakeholder_req_spec.py    SN-05
    │   ├── stakeholder_traceability.py SN-06
    │   ├── sys_req_spec.py            SR-01
    │   ├── req_hierarchy.py           SR-02
    │   ├── req_traceability.py        SR-03
    │   ├── req_completeness.py        SR-05
    │   ├── req_quality.py             SR-06
    │   ├── logical_arch_report.py     LA-01
    │   ├── logical_decomposition.py   LA-02
    │   ├── interface_catalog.py       LA-03
    │   ├── behavioral_summary.py      LA-04
    │   ├── req_allocation.py          LA-05
    │   └── logical_completeness.py    LA-06
    │
    └── Original toolchain (retained):
        ├── req_validate.py        Full SRS validation (updated for doc-convention)
        ├── req_report.py          Requirements list + hierarchy (predecessor to req_hierarchy.py)
        ├── result_matrix.py       V&V result status (CTest XML)
        ├── concerns_matrix.py     Concern → requirement coverage
        ├── satisfaction_matrix.py Requirement → architecture satisfaction
        ├── coverage_matrix.py     Requirement → verification coverage
        └── dependency_map.py      Executable dependency mapping
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

    // Program-specific subsystem definition
    part def ProgramA_SensorSubsystem {
        doc /* Sensor processing subsystem unique to Program A. */
        port sensorIn : SensorDataPort;
    }

    part def ProgramA_SystemDef {
        part core        : CoreSystem_Assembly;
        part config      : ProgramA_Config;
        part sensorSys   : ProgramA_SensorSubsystem; // program-specific addition
    }
}
```

For program-specific use cases, context, or allocations that grow large
enough to warrant separate files, add them as additional leaves inside
`Architecture/` and register them in `04_Programs/_namespace.sysml`.

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
        attribute :>> verificationMethod = VerificationMethodKind::Test;
        attribute :>> threshold          = "compact measurable bound";
    }
}
```

**Removed — no longer in `SRS_Definitions.sysml`:**
- `id`, `text`, `rationale` string attributes on requirements
- `passFailLogic`, `conditions`, `criteriaObjective` on VerificationCriteria

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

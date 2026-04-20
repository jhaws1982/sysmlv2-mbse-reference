# Generic Model v3 — Nested Namespace Pattern

## What Changed from v2

v3 introduces the **leaf + hub** pattern throughout.  Every layer now has:

- **Leaf files** — define content under short, globally-unique package names
  (`FeatureA`, `FeatureB`, `RequirementsDef`, etc.)
- **Hub files** (`_namespace.sysml`) — the **one and only** declaration of each
  nested namespace node, assembling leaf packages via `public import`

This eliminates the `'Core' shadows previously declared element` warning by
ensuring each namespace node (`Core`, `Programs`, `Verification`, etc.) is
declared in exactly one place.

---

## The Leaf + Hub Pattern

```
┌─────────────────────────────────────────────────────────┐
│  FeatureA.sysml                                         │
│  ─────────────                                          │
│  package FeatureA {          ← short, unique, no ::    │
│      part def FeatureA_Component { ... }                │
│  }                                                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  02_Core/_namespace.sysml    (the hub — ONE file)       │
│  ─────────────────────────                              │
│  package Core {              ← declared ONCE, here only │
│      package Architecture {                             │
│          public import FeatureA::*;   ← re-exports      │
│          public import FeatureB::*;                     │
│          public import FeatureC::*;                     │
│          public import CoreSystem::*;                   │
│      }                                                  │
│      package Requirements {                             │
│          public import RequirementsDef::*;              │
│          public import RequirementsDecl::*;             │
│      }                                                  │
│  }                                                      │
└─────────────────────────────────────────────────────────┘

// Any consumer file:
private import Core::Architecture::*;   // ← clean nested path
// FeatureA_Component, FeatureB_Component, Core_System all visible
```

---

## Which `_namespace.sysml` Files Are Active

| Hub file | Declares | Assembles |
|---|---|---|
| `00_Shared/_namespace.sysml` | `package Shared` | `SharedData` leaf |
| `02_Core/_namespace.sysml` | `package Core` | `FeatureA`, `FeatureB`, `FeatureC`, `CoreSystem`, `RequirementsDef`, `RequirementsDecl` |
| `04_Programs/_namespace.sysml` | `package Programs` | all four ProgramA_* and ProgramB_* leaves |
| `05_Verification/_namespace.sysml` | `package Verification` | `TestCases`, `Results`, `Traceability` leaves |

The files `02_Core/Architecture/_namespace.sysml` and
`02_Core/Requirements/_namespace.sysml` are **superseded** by
`02_Core/_namespace.sysml` and should be deleted (or ignored — they are
provided as documentation of the split-hub alternative).

---

## Import Path Reference

| What you want | Import to write |
|---|---|
| Shared enums / items | `private import Shared::Data::*;` |
| Stakeholders / concerns | `private import Stakeholders::*;` |
| Feature components + Core_System | `private import Core::Architecture::*;` |
| Requirement defs (types) | `private import Core::Requirements::*;` |
| Requirement decls (usages) | `private import Core::Requirements::*;` (same import — hub re-exports both) |
| Product-line base config | `private import Configurations::*;` |
| Program A everything | `private import Programs::ProgramA::*;` |
| Program B everything | `private import Programs::ProgramB::*;` |
| Verification test case defs | `private import Verification::TestCases::*;` |
| Verification traceability | `private import Verification::Traceability::*;` |

---

## Rules for Extending the Model

### Adding a Feature D

1. Create `02_Core/Architecture/FeatureD.sysml` with `package FeatureD { ... }`
2. Add `public import FeatureD::*;` inside the `Architecture` block of
   `02_Core/_namespace.sysml`
3. Add `part featureD : FeatureD_Component;` inside `Core_System` in
   `02_Core/Architecture/Core_System.sysml`

No other files need to change.

### Adding a Program C

1. Create `04_Programs/Program_C/` with the same four leaf files as Program A/B
2. Add a `package ProgramC { public import ProgramC::*; ... }` block inside
   `04_Programs/_namespace.sysml`

### Why `public import` Only in Hub Files

`public import` makes imported names *re-exportable* — anyone who imports the hub
package also sees the leaf package members.  This is what makes the nested path work.
Using `public import` anywhere else would create unintended namespace leakage, which
is why every non-hub import in the model is `private import`.

---

## File Layout

```
Generic_Model_v3/
│
├── Model.sysml                              ← root index, all imports via nested paths
│
├── 00_Shared/
│   ├── Data_Types.sysml                     leaf: SharedData
│   └── _namespace.sysml                     hub:  Shared::Data
│
├── 01_Stakeholders/
│   └── Stakeholders_and_Concerns.sysml      leaf+public name: Stakeholders
│
├── 02_Core/
│   ├── _namespace.sysml                     hub:  Core::Architecture + Core::Requirements
│   ├── Architecture/
│   │   ├── FeatureA.sysml                   leaf: FeatureA
│   │   ├── FeatureB.sysml                   leaf: FeatureB
│   │   ├── FeatureC.sysml                   leaf: FeatureC
│   │   ├── Core_System.sysml                leaf: CoreSystem
│   │   └── _namespace.sysml                 (superseded — kept for reference)
│   └── Requirements/
│       ├── Requirements_Def.sysml           leaf: RequirementsDef
│       ├── Requirements_Decl.sysml          leaf: RequirementsDecl
│       └── _namespace.sysml                 (superseded — kept for reference)
│
├── 03_ProductLine/
│   └── Configurations.sysml                 leaf+public name: Configurations
│
├── 04_Programs/
│   ├── _namespace.sysml                     hub:  Programs::ProgramA + Programs::ProgramB
│   ├── Program_A/
│   │   ├── Config.sysml                     leaf: ProgramA
│   │   ├── Deployment/Deployment.sysml      leaf: ProgramA_Deployment
│   │   ├── Requirements/Requirements.sysml  leaf: ProgramA_Requirements
│   │   └── Verification/Verification.sysml  leaf: ProgramA_Verification
│   └── Program_B/
│       ├── Config.sysml                     leaf: ProgramB
│       ├── Deployment/Deployment.sysml      leaf: ProgramB_Deployment
│       ├── Requirements/Requirements.sysml  leaf: ProgramB_Requirements
│       └── Verification/Verification.sysml  leaf: ProgramB_Verification
│
└── 05_Verification/
    ├── _namespace.sysml                     hub:  Verification::TestCases/Results/Traceability
    ├── TestCases.sysml                      leaf: TestCases
    ├── Results.sysml                        leaf: Results
    └── Traceability.sysml                   leaf: Traceability
```

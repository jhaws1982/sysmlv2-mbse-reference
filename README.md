# SysML v2 MBSE Reference

A reference SysML v2 model demonstrating multi-file architecture with the
Leaf + Hub namespace pattern, DI-IPSC-81433A compliant requirements using
`SRS_Definitions`, and Python Automator tooling.

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
│   ├── _namespace.sysml                     hub:  Core::Architecture, Core::Requirements
│   ├── Architecture/
│   │   ├── FeatureA.sysml                   leaf: FeatureA
│   │   ├── FeatureB.sysml                   leaf: FeatureB
│   │   ├── FeatureC.sysml                   leaf: FeatureC
│   │   └── Core_System.sysml               leaf: CoreSystem
│   └── Requirements/
│       ├── Requirements_Def.sysml           leaf: RequirementsDef  (SRS types)
│       └── Requirements_Decl.sysml          leaf: RequirementsDecl (bound to architecture)
│
├── 03_ProductLine/
│   └── Configurations.sysml                 leaf: ProductLineConfigurations
│
├── 04_Programs/
│   ├── _namespace.sysml                     hub:  Programs::ProgramA, Programs::ProgramB
│   ├── Program_A/
│   │   ├── Config.sysml                     leaf: ProgramA
│   │   ├── Stakeholders/
│   │   │   ├── Stakeholders.sysml           leaf: ProgramA_StakeholderDefs
│   │   │   └── Concerns.sysml               leaf: ProgramA_StakeholderConcerns
│   │   ├── Deployment/Deployment.sysml      leaf: ProgramA_Deployment
│   │   ├── Requirements/Requirements.sysml  leaf: ProgramA_Requirements (SRS types)
│   │   └── Verification/Verification.sysml  leaf: ProgramA_Verification
│   └── Program_B/
│       ├── Config.sysml                     leaf: ProgramB
│       ├── Stakeholders/
│       │   ├── Stakeholders.sysml           leaf: ProgramB_StakeholderDefs
│       │   └── Concerns.sysml               leaf: ProgramB_StakeholderConcerns
│       ├── Deployment/Deployment.sysml      leaf: ProgramB_Deployment
│       ├── Requirements/Requirements.sysml  leaf: ProgramB_Requirements (SRS types)
│       └── Verification/Verification.sysml  leaf: ProgramB_Verification
│
├── 05_Verification/
│   ├── _namespace.sysml                     hub:  Verification::TestCases, Verification::Traceability
│   ├── TestCases.sysml                      leaf: TestCases
│   └── Traceability.sysml                   leaf: Traceability
│
└── __Tools/
    ├── concerns_matrix.py                   Concern → Requirement traceability matrix
    ├── coverage_matrix.py                   Requirement → Verification coverage matrix
    ├── dependency_map.py                    Software artifact dependency map
    ├── req_debug.py                         SysIDE API diagnostic tool
    ├── req_report.py                        Requirements list + hierarchy diagrams
    ├── req_validate.py                      SRS_Definitions constraint validator  ← NEW
    ├── result_matrix.py                     CTest result matrix
    ├── satisfaction_matrix.py               Requirement satisfaction matrix
    ├── test_req_validate.py                 Unit tests for req_validate.py        ← NEW
    └── sample_data/
        ├── ctest_core.xml
        ├── ctest_Program_A.xml
        └── ctest_Program_B.xml
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

Each requirement follows the Def/Decl split:

```sysml
// DEF — stable type, framing a concern
requirement def <'REQ-CAP-001-DEF'> MyCapability_Def :> CapabilityRequirement {
    doc /* ... */
    frame concern MyConcern;
}

// DECL — usage with all SRS fields populated
requirement <'REQ-CAP-001'> myCapability : MyCapability_Def {
    subject sys : MySystem;
    attribute :>> id             = "REQ-CAP-001";
    attribute :>> text           = "The system shall ...";
    attribute :>> rationale      = "...";
    attribute :>> source         = "...";
    attribute :>> priority       = "High";
    attribute :>> criticality    = "Critical";
    attribute :>> capabilityName = "...";
    attribute :>> latency        = "...";
    part :>> criteria : VerificationCriteria {
        attribute :>> verificationMethod = VerificationMethodKind::Test;
        attribute :>> passFailLogic      = "PASS if ...";
        attribute :>> threshold          = "...";
        attribute :>> conditions         = "...";
    }
}
```

---

## Tooling

All tools run from the model root directory:

```bash
# Validate SRS requirements (default: show all levels)
python __Tools/req_validate.py .

# Validate with CI gate (fail if any INVALID)
python __Tools/req_validate.py . --fail-on-invalid

# Validate specific package only
python __Tools/req_validate.py . --package ProgramA_Requirements

# Use a different SRS definitions package name
python __Tools/req_validate.py . --srs-package MyProject_SRS

# Run unit tests
pytest __Tools/test_req_validate.py -v

# Requirements report
python __Tools/req_report.py . --format md

# Other matrices
python __Tools/concerns_matrix.py .
python __Tools/satisfaction_matrix.py .
python __Tools/coverage_matrix.py .
python __Tools/dependency_map.py .
```

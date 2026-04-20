/**
 * Generic_Model — top-level index package.
 *
 * Imports via the nested namespace paths exposed by each layer's hub file.
 * No element definitions live here — this is purely a table of contents and
 * entry point for tools that require a single root package.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * NAMESPACE ARCHITECTURE SUMMARY
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Every layer follows the same two-file pattern:
 *
 *   LEAF FILE   — defines content in a flat, globally-unique package name
 *                 (e.g.  package FeatureA { ... })
 *
 *   HUB FILE    — the ONE declaration of the nested namespace node that
 *   (_namespace.sysml)  re-exports leaf packages via `public import`
 *                 (e.g.  package Core { package Architecture {
 *                             public import FeatureA::*; } })
 *
 * Consumers always import via the NESTED path the hub exposes.
 * This eliminates "shadows" warnings because each namespace node is declared
 * exactly once.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * FILE MAP
 * ───────────────────────────────────────────────────────────────────────────
 *
 * 00_Shared/
 *   Data_Types.sysml          leaf:  package SharedData
 *   SRS_Definitions.sysml     leaf:  package SRS_Definitions  (DI-IPSC-81433A metamodel)
 *   _namespace.sysml          hub:   package Shared {
 *                                        package Data { ... }
 *                                        package SRS  { ... }
 *                                    }
 *
 * 01_Stakeholders/
 *   Stakeholders.sysml                       leaf: StakeholderDefs
 *   Concerns.sysml                           leaf: StakeholderConcerns
 *   _namespace.sysml                         hub:  Stakeholders::Roles, Stakeholders::Concerns
 *
 * 02_Core/
 *   _namespace.sysml          hub:   package Core {
 *                                        package Architecture { ... }
 *                                        package Requirements { ... }
 *                                    }
 *   Architecture/
 *     FeatureA.sysml          leaf:  package FeatureA
 *     FeatureB.sysml          leaf:  package FeatureB
 *     FeatureC.sysml          leaf:  package FeatureC
 *     Core_System.sysml       leaf:  package CoreSystem
 *     _namespace.sysml        (superseded by 02_Core/_namespace.sysml)
 *   Requirements/
 *     Requirements_Def.sysml  leaf:  package RequirementsDef
 *     Requirements_Decl.sysml leaf:  package RequirementsDecl
 *     _namespace.sysml        (superseded by 02_Core/_namespace.sysml)
 *
 * 03_ProductLine/
 *   Configurations.sysml      leaf+hub:  package Configurations
 *
 * 04_Programs/
 *   _namespace.sysml          hub:   package Programs {
 *                                        package ProgramA { ... }
 *                                        package ProgramB { ... }
 *                                    }
 *   Program_A/
 *     Config.sysml            leaf:  package ProgramA
 *     Deployment/             leaf:  package ProgramA_Deployment
 *     Requirements/           leaf:  package ProgramA_Requirements
 *     Verification/           leaf:  package ProgramA_Verification
 *   Program_B/
 *     Config.sysml            leaf:  package ProgramB
 *     Deployment/             leaf:  package ProgramB_Deployment
 *     Requirements/           leaf:  package ProgramB_Requirements
 *     Verification/           leaf:  package ProgramB_Verification
 *
 * 05_Verification/
 *   _namespace.sysml          hub:   package Verification {
 *                                        package TestCases { ... }
 *                                        package Results { ... }
 *                                        package Traceability { ... }
 *                                    }
 *   TestCases.sysml           leaf:  package TestCases
 *   Results.sysml             leaf:  package Results
 *   Traceability.sysml        leaf:  package Traceability
 */
package Generic_Model {
    private import Shared::Data::*;
    private import Shared::SRS::*;
    private import Stakeholders::Roles::*;
    private import Stakeholders::Concerns::*;
    private import Core::Architecture::*;
    private import Core::Requirements::*;
    private import Configurations::*;
    private import Programs::ProgramA::*;
    private import Programs::ProgramB::*;
    private import Verification::TestCases::*;
    private import Verification::Results::*;
    private import Verification::Traceability::*;
}

// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramB_Requirements — Program B requirement definitions and declarations.
 *
 * LEAF FILE. Re-exported as Programs::ProgramB by 04_Programs/_namespace.sysml.
 *
 * All requirements specialize types from SRS_Definitions. Program B focuses
 * on safety integrity, interface stability, and resource constraints.
 */
package ProgramB_Requirements {
    private import SRS_Definitions::*;
    private import Core::Requirements::*;
    private import ProgramB_Deployment::*;
    private import ProgramB_StakeholderConcerns::*;
    private import ScalarValues::*;

    // ── Definitions ────────────────────────────────────────────────────

    requirement def <'PB-SAF-001-DEF'> ProgramB_SafetyIntegrity_Def
        :> SafetyRequirement {
        doc /* Program B safety integrity level requirement. */
        frame concern ProgramB_SafetyConcern;
    }

    requirement def <'PB-IFC-001-DEF'> ProgramB_InterfaceStability_Def
        :> InterfaceRequirement {
        doc /* Program B external interface stability and versioning requirement. */
        frame concern ProgramB_InterfaceConcern;
    }

    requirement def <'PB-RES-001-DEF'> ProgramB_ResourceConstraint_Def
        :> ResourceRequirement {
        doc /* Program B compute and memory resource utilization constraint. */
        frame concern ProgramB_SafetyConcern;
    }

    requirement def <'PB-QUA-001-DEF'> ProgramB_Maintainability_Def
        :> QualityRequirement {
        doc /* Program B maintainability requirement. */
        frame concern ProgramB_InterfaceConcern;
    }

    // ── Declarations ───────────────────────────────────────────────────

    requirement <'PB-SAF-001'> programB_SafetyIntegrity
        : ProgramB_SafetyIntegrity_Def {
        doc /* Program B safety integrity requirement for inadvertent command prevention. */
        subject sys : ProgramB_System;
        attribute :>> id          = "PB-SAF-001";
        attribute :>> text        = "The Program B CSCI shall implement safeguards to prevent inadvertent issuance of safety-critical commands, requiring a minimum of two independent confirmations before any safety-critical action is executed.";
        attribute :>> rationale   = "Program B operates in a safety-critical environment where inadvertent commands could result in harm to personnel or equipment. Two-confirmation requirement derived from PB-SHA §5.3.";
        attribute :>> source      = "PB-SHA §5.3";
        attribute :>> priority    = "Critical";
        attribute :>> criticality = "Safety-Critical";
        attribute :>> hazard      = "Inadvertent execution of a safety-critical command resulting from software fault, operator error, or electromagnetic interference.";
        attribute :>> mitigation  = "Dual-confirmation interlock: command accepted only when two independent confirmations received within a 5-second window. All safety-critical command attempts logged to tamper-evident audit trail.";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Test;
            attribute :>> passFailLogic      = "PASS if (1) no safety-critical command executes with fewer than two confirmations in 1000 test attempts, and (2) all attempts are recorded in audit log.";
            attribute :>> threshold          = "0 inadvertent executions in 1000 tests; 100% audit log coverage";
            attribute :>> conditions         = "Fault injection test including single-confirmation attempts, timeout scenarios, and concurrent command injection.";
            attribute :>> criteriaObjective  = "Verify dual-confirmation interlock prevents inadvertent safety-critical command execution.";
        }
    }

    requirement <'PB-IFC-001'> programB_InterfaceStability
        : ProgramB_InterfaceStability_Def {
        doc /* Program B external interface stability requirement. */
        subject sys : ProgramB_System;
        attribute :>> id              = "PB-IFC-001";
        attribute :>> text            = "All Program B external interfaces shall be versioned using semantic versioning (MAJOR.MINOR.PATCH) and shall maintain backward compatibility within a MAJOR version series.";
        attribute :>> rationale       = "Program B integrates with multiple external systems maintained by independent teams. Interface versioning prevents integration failures during independent release cycles.";
        attribute :>> source          = "PB-ICD-001 §2.1";
        attribute :>> priority        = "High";
        attribute :>> criticality     = "High";
        attribute :>> interfaceName   = "ProgramB_ExternalInterfaces";
        attribute :>> primaryEntity   = "ProgramB_System";
        attribute :>> secondaryEntity = "ExternalIntegrationSystem";
        attribute :>> protocol        = "REST/JSON over HTTPS with semantic versioned API";
        attribute :>> messageFormat   = "JSON per PB-ICD-001 schema definitions";
        attribute :>> dataName        = "ProgramB_APIMessage";
        attribute :>> dataType        = "JSON";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Inspection;
            attribute :>> passFailLogic      = "PASS if all interfaces in PB-ICD-001 carry a semantic version header and interface compatibility test suite passes against the previous MAJOR version.";
            attribute :>> threshold          = "100% of interfaces versioned; 100% backward-compat test pass rate";
            attribute :>> conditions         = "Interface review against PB-ICD-001 and automated compatibility test suite execution.";
        }
    }

    requirement <'PB-RES-001'> programB_ResourceConstraint
        : ProgramB_ResourceConstraint_Def {
        doc /* Program B compute and memory resource utilization constraint. */
        subject sys : ProgramB_System;
        attribute :>> id          = "PB-RES-001";
        attribute :>> text        = "The Program B CSCI shall not exceed 70% CPU utilization and 80% memory utilization under peak operational load, leaving adequate headroom for safety monitoring processes.";
        attribute :>> rationale   = "Safety monitoring processes require guaranteed CPU and memory headroom at all times. 30% CPU / 20% memory margins ensure safety processes are never starved.";
        attribute :>> source      = "PB-SHA §3.1; PB-HWS-001";
        attribute :>> priority    = "High";
        attribute :>> criticality = "Safety-Critical";
        attribute :>> resource    = "CPU: <= 70% utilization; Memory: <= 80% utilization. Both measured as sustained averages over any 60-second window under peak operational load per PB-ITP §4.2.";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Analysis;
            attribute :>> passFailLogic      = "PASS if resource utilization analysis and stress test both confirm CPU <= 70% and memory <= 80% over all 60-second windows during peak load run.";
            attribute :>> threshold          = "CPU <= 70%; Memory <= 80%; no 60-second window exceeds limits";
            attribute :>> conditions         = "Peak load per PB-ITP §4.2; all Program B functions active; safety monitoring processes running.";
            attribute :>> criteriaObjective  = "Verify resource headroom for safety monitoring under peak load.";
        }
    }

    requirement <'PB-QUA-001'> programB_Maintainability
        : ProgramB_Maintainability_Def {
        doc /* Program B maintainability requirement. */
        subject sys : ProgramB_System;
        attribute :>> id               = "PB-QUA-001";
        attribute :>> text             = "The Program B CSCI shall be maintainable such that a qualified software engineer can diagnose and resolve any Category 1 defect within 4 hours of receipt of the defect report, using only the delivered documentation and source code.";
        attribute :>> rationale        = "Program B has a 4-hour MTTR SLA for Category 1 defects per the Program B support contract PB-SLA-001.";
        attribute :>> source           = "PB-SLA-001 §4";
        attribute :>> priority         = "High";
        attribute :>> criticality      = "High";
        attribute :>> qualityAttribute = "Maintainability";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Analysis;
            attribute :>> passFailLogic      = "PASS if maintainability analysis confirms that all interfaces, data flows, and state transitions are documented and that a structured diagnostic procedure can be derived from delivered documentation alone.";
            attribute :>> threshold          = "100% coverage of interfaces, data flows, and state transitions in delivered documentation";
            attribute :>> conditions         = "Documentation completeness review against PB-SDD checklist.";
        }
    }
}

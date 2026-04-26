// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramB_Requirements — Program B requirement definitions and declarations.
 *
 * LEAF FILE. Re-exported as Programs::ProgramB by 04_Programs/_namespace.sysml.
 *
 * Doc convention (per SRS_Definitions.sysml):
 *   - Short-name ID in the <'PB-ID'> position
 *   - Unnamed doc block  — normative "shall" statement
 *   - doc Rationale      — why this requirement exists
 *   - Criteria doc block — narrative pass/fail objective
 *   - passFailLogic, conditions, criteriaObjective removed
 */
package ProgramB_Requirements {
    private import SRS_Definitions::*;
    private import Core::Requirements::*;
    private import ProgramB_System::*;
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
        doc
        /* The Program B CSCI shall implement safeguards to prevent
         * inadvertent issuance of safety-critical commands, requiring
         * a minimum of two independent confirmations before any
         * safety-critical action is executed.
         */
        doc Rationale
        /* Program B operates in a safety-critical environment where
         * inadvertent commands could result in harm to personnel or
         * equipment. Two-confirmation requirement derived from PB-SHA §5.3.
         */
        subject sys : ProgramB_SystemDef;
        attribute :>> source      = "PB-SHA §5.3";
        attribute :>> priority    = CMNDEF::LevelKind::High;
        attribute :>> criticality = CMNDEF::LevelKind::High;
        attribute :>> hazard      = "Inadvertent execution of a safety-critical command  resulting from software fault, operator error, or electromagnetic interference.";
        attribute :>> mitigation  = "Dual-confirmation interlock: command accepted only when  two independent confirmations received within a 5-second window. All safety-critical  command attempts logged to tamper-evident audit trail.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Fault injection test: 1000 attempts including single-confirmation
             * attempts, timeout scenarios, and concurrent command injection.
             * PASS if (1) no safety-critical command executes with fewer than
             * two confirmations, and (2) all attempts appear in the audit log.
             */
            attribute :>> verificationMethod = VerificationMethodKind::test;
            attribute :>> threshold          = "0 inadvertent executions in 1000 tests; 100% audit log coverage";
        }
    }

    requirement <'PB-IFC-001'> programB_InterfaceStability
            : ProgramB_InterfaceStability_Def {
        doc
        /* All Program B external interfaces shall be versioned using
         * semantic versioning (MAJOR.MINOR.PATCH) and shall maintain
         * backward compatibility within a MAJOR version series.
         */
        doc Rationale
        /* Program B integrates with multiple external systems maintained
         * by independent teams. Interface versioning prevents integration
         * failures during independent release cycles.
         */
        subject sys : ProgramB_SystemDef;
        attribute :>> source          = "PB-ICD-001 §2.1";
        attribute :>> priority        = CMNDEF::LevelKind::High;
        attribute :>> criticality     = CMNDEF::LevelKind::High;
        attribute :>> interfaceName   = "ProgramB_ExternalInterfaces";
        attribute :>> primaryEntity   = "ProgramB_System";
        attribute :>> secondaryEntity = "ExternalIntegrationSystem";
        attribute :>> protocol        = "REST/JSON over HTTPS with semantic versioned API";
        attribute :>> messageFormat   = "JSON per PB-ICD-001 schema definitions";
        attribute :>> dataName        = "ProgramB_APIMessage";
        attribute :>> dataType        = "JSON";
        part :>> criteria : VerificationCriteria {
            doc
            /* Interface review against PB-ICD-001 and automated compatibility
             * test suite execution against previous MAJOR version.
             * PASS if all interfaces carry a semantic version header and
             * 100% of backward-compatibility tests pass.
             */
            attribute :>> verificationMethod = VerificationMethodKind::inspect;
            attribute :>> threshold          = "100% interfaces versioned; 100% backward-compat pass rate";
        }
    }

    requirement <'PB-RES-001'> programB_ResourceConstraint
            : ProgramB_ResourceConstraint_Def {
        doc
        /* The Program B CSCI shall not exceed 70% CPU utilization and
         * 80% memory utilization under peak operational load, leaving
         * adequate headroom for safety monitoring processes.
         */
        doc Rationale
        /* Safety monitoring processes require guaranteed CPU and memory
         * headroom at all times. 30% CPU / 20% memory margins ensure
         * safety processes are never resource-starved per PB-SHA §3.1.
         */
        subject sys : ProgramB_SystemDef;
        attribute :>> source      = "PB-SHA §3.1; PB-HWS-001";
        attribute :>> priority    = CMNDEF::LevelKind::High;
        attribute :>> criticality = CMNDEF::LevelKind::High;
        attribute :>> resource    = "CPU: <= 70% utilization; Memory: <= 80% utilization.  Both measured as sustained averages over any 60-second window under peak  operational load per PB-ITP §4.2.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Peak load test per PB-ITP §4.2 with all Program B functions
             * active and safety monitoring processes running.
             * PASS if resource utilization analysis and stress test both
             * confirm CPU <= 70% and memory <= 80% over all 60-second windows.
             */
            attribute :>> verificationMethod = VerificationMethodKind::analyze;
            attribute :>> threshold          = "CPU <= 70%; Memory <= 80%; no 60-s window exceeds limits";
        }
    }

    requirement <'PB-QUA-001'> programB_Maintainability
            : ProgramB_Maintainability_Def {
        doc
        /* The Program B CSCI shall be maintainable such that a qualified
         * software engineer can diagnose and resolve any Category 1 defect
         * within 4 hours of receipt of the defect report, using only the
         * delivered documentation and source code.
         */
        doc Rationale
        /* Program B has a 4-hour MTTR SLA for Category 1 defects per
         * the Program B support contract PB-SLA-001 §4.
         */
        subject sys : ProgramB_SystemDef;
        attribute :>> source           = "PB-SLA-001 §4";
        attribute :>> priority         = CMNDEF::LevelKind::High;
        attribute :>> criticality      = CMNDEF::LevelKind::High;
        attribute :>> qualityAttribute = "Maintainability";
        part :>> criteria : VerificationCriteria {
            doc
            /* Documentation completeness review against PB-SDD checklist.
             * PASS if analysis confirms that all interfaces, data flows, and
             * state transitions are documented and a structured diagnostic
             * procedure can be derived from delivered documentation alone.
             */
            attribute :>> verificationMethod = VerificationMethodKind::analyze;
            attribute :>> threshold          = "100% coverage of interfaces, data flows, state transitions";
        }
    }
}

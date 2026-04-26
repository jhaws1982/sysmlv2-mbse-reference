/**
 * RequirementsDecl — core CSCI requirement declarations (Decl side of Def/Decl split).
 *
 * LEAF FILE. Globally unique name "RequirementsDecl".
 * Assembled into Core::Requirements by 02_Core/_namespace.sysml.
 *
 * Doc convention (per SRS_Definitions.sysml):
 *   Mandatory on every requirement usage:
 *     <'REQ-ID'>      short-name identifier
 *     doc             normative "shall" statement
 *     doc Rationale   justification
 *
 * ── INTENTIONAL VALIDATION EXAMPLES ────────────────────────────────────────
 *
 * This file contains a mix of VALID, INCOMPLETE, and INVALID requirements
 * so that req_validate.py and req_completeness.py produce non-trivial output:
 *
 *   processingCapability  — COMPLETE  (all fields, correct method)
 *   integrationCapability — COMPLETE  (all fields, correct method)
 *   externalDataInterface — COMPLETE  (all fields, correct method)
 *   systemAvailability    — COMPLETE  (all fields, correct method)
 *   programmingLanguageConstraint — COMPLETE
 *   incompleteReq         — INCOMPLETE (missing source, priority, criteria)
 *   invalidReq_noId       — INVALID   (no short-name ID)
 *   invalidReq_noDoc      — INVALID   (no doc block)
 *   invalidReq_noRationale — INVALID  (no doc Rationale)
 */
package RequirementsDecl {
    private import RequirementsDef::*;
    private import SRS_Definitions::*;
    private import CommonDefinitions::*;
    private import CoreSystem::*;
    private import FeatureA::*;
    private import FeatureB::*;

    // ════════════════════════════════════════════════════════════════════════
    // COMPLETE requirements — pass all validation checks
    // ════════════════════════════════════════════════════════════════════════

    requirement <'REQ-CAP-001'> processingCapability
            : ProcessingCapability_Def {
        doc
        /* The CSCI shall process all inbound data streams within
         * 50 milliseconds of receipt under nominal operating load
         * of 1000 messages per second.
         */
        doc Rationale
        /* Derived from system-level response time budget SYS-PERF-003.
         * 50 ms is the CSCI allocation after network transit time.
         * Exceeding this bound causes downstream pipeline stalls.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> source         = "SYS-PERF-003";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
        attribute :>> capabilityName = "InboundDataProcessing";
        attribute :>> latency        = "50 ms maximum at 99th percentile.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Inject 1000 messages/second for 10 minutes under nominal load.
             * PASS if 99th-percentile latency <= 50 ms and zero messages dropped.
             */
            attribute :>> verificationMethod = VerificationMethodKind::test;
            attribute :>> threshold          = "50 ms at 99th percentile";
        }
    }

    requirement <'REQ-CAP-002'> integrationCapability
            : IntegrationCapability_Def {
        doc
        /* The CSCI shall integrate Feature A and Feature B subsystems
         * into a unified processing pipeline with no data loss under
         * nominal operating conditions.
         */
        doc Rationale
        /* A single pipeline eliminates inter-process latency and reduces
         * integration complexity. Derived from system architecture SYS-ARCH-001.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> source         = "SYS-ARCH-001";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
        attribute :>> capabilityName = "SubsystemIntegration";
        attribute :>> performance    = "Zero data loss under nominal load.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Run both subsystems under nominal load for 30 minutes.
             * PASS if zero messages lost and queue depth stays <= 1000.
             */
            attribute :>> verificationMethod = VerificationMethodKind::test;
            attribute :>> threshold          = "0 messages lost; queue <= 1000";
        }
    }

    requirement <'REQ-IFC-001'> externalDataInterface
            : ExternalDataInterface_Def {
        doc
        /* The CSCI shall implement a binary message interface to the
         * external data source conforming to ICD-EXT-001 revision C.
         */
        doc Rationale
        /* ExternalDataSource uses a fixed binary protocol in ICD-EXT-001
         * that cannot be modified. Conformance is a contractual criterion.
         */
        subject featureA : FeatureA_Component;
        attribute :>> source          = "ICD-EXT-001 Rev C";
        attribute :>> priority        = CMNDEF::LevelKind::High;
        attribute :>> criticality     = CMNDEF::LevelKind::High;
        attribute :>> interfaceName   = "ExternalDataSource_Interface";
        attribute :>> primaryEntity   = "CoreCSCI";
        attribute :>> secondaryEntity = "ExternalDataSource";
        attribute :>> protocol        = "Binary framed message protocol per ICD-EXT-001";
        attribute :>> messageFormat   = "256-byte header + variable payload + 4-byte CRC";
        attribute :>> dataName        = "ExternalDataMessage";
        attribute :>> dataType        = "Binary framed message";
        part :>> criteria : VerificationCriteria {
            doc
            /* Exercise all ICD-EXT-001 §3 message types with nominal and
             * boundary values (10 000 total messages).
             * PASS if zero encoding or decoding errors observed.
             */
            attribute :>> verificationMethod = VerificationMethodKind::test;
            attribute :>> threshold          = "0 errors in 10 000 messages";
        }
    }

    requirement <'REQ-QUA-001'> systemAvailability
            : SystemAvailability_Def {
        doc
        /* The CSCI shall achieve a minimum operational availability of
         * 99.5% over any 30-day measurement period.
         */
        doc Rationale
        /* Mission profile requires near-continuous operation. Planned
         * maintenance windows must not exceed 0.5% of the measurement period.
         * Derived from SYS-RELY-001.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> source           = "SYS-RELY-001";
        attribute :>> priority         = CMNDEF::LevelKind::High;
        attribute :>> criticality      = CMNDEF::LevelKind::High;
        attribute :>> qualityAttribute = "Availability";
        part :>> criteria : VerificationCriteria {
            doc
            /* Reliability analysis using component MTBF data, 30-day window,
             * normal operating environment, planned maintenance excluded.
             * PASS if predicted availability >= 99.5%.
             */
            attribute :>> verificationMethod = VerificationMethodKind::analyze;
            attribute :>> threshold          = "99.5% over 30-day period";
        }
    }

    requirement <'REQ-DSN-001'> programmingLanguageConstraint
            : ProgrammingLanguageConstraint_Def {
        doc
        /* The CSCI shall be implemented in C++ (ISO/IEC 14882:2017) or
         * Python 3.10+ as specified in the Software Development Plan.
         */
        doc Rationale
        /* Organizational toolchain and code review processes support only
         * these languages. No waiver exists for other languages.
         * Derived from SDP-001 §4.2.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> source         = "SDP-001 §4.2";
        attribute :>> priority       = CMNDEF::LevelKind::Medium;
        attribute :>> criticality    = CMNDEF::LevelKind::Medium;
        attribute :>> constraintText = "C++ (ISO/IEC 14882:2017) or Python 3.10+ only.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Code review at CDR confirms all source files use approved languages.
             * PASS if 100% of source files are in approved languages with no waivers.
             */
            attribute :>> verificationMethod = VerificationMethodKind::inspect;
            attribute :>> threshold          = "100% approved languages";
        }
    }

    // ════════════════════════════════════════════════════════════════════════
    // INCOMPLETE requirement — passes VALID checks but has completeness gaps.
    // @RiskItem demonstrates risk annotation on a requirement.
    // ════════════════════════════════════════════════════════════════════════

    @RiskItem {
        riskId      = "RISK-CORE-REQ-001";
        title       = "BIT requirement lacks acceptance criteria";
        category    = RiskCategory::Technical;
        probability = LevelKind::Medium;
        impact      = LevelKind::Medium;
        exposure    = 4;
        status      = RiskStatus::Open;
        description = "REQ-CAP-003 (incompleteReq) has no defined verification
                       criteria or threshold. Without these, acceptance testing
                       for the BIT capability cannot be objectively assessed.";
        mitigation  = "Complete the verification criteria for REQ-CAP-003 before CDR.
                       Assign to systems engineer to draft test procedure.";
        owner       = "Systems Engineer";
    }

    // INCOMPLETE requirement — passes VALID checks but has completeness gaps.
    // Missing: source, priority, criticality, criteria.
    // req_validate.py will report this as INCOMPLETE.
    // ════════════════════════════════════════════════════════════════════════

    requirement <'REQ-CAP-003'> incompleteReq
            : ProcessingCapability_Def {
        doc
        /* The CSCI shall provide a built-in self-test capability that
         * verifies all subsystem interfaces during initialization.
         */
        doc Rationale
        /* Early fault detection during initialization prevents the system
         * from entering operational mode with undetected hardware faults.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> capabilityName = "BuiltInSelfTest";
        attribute :>> timing         = "Completes within 30 seconds of power-on.";
        // source, priority, criticality intentionally omitted — INCOMPLETE demo
        // criteria intentionally omitted — INCOMPLETE demo
    }

    // ════════════════════════════════════════════════════════════════════════
    // INVALID requirements — fail VALID checks.
    // These demonstrate what req_validate.py catches.
    // ════════════════════════════════════════════════════════════════════════

    // INVALID: no short-name ID (HasId violation)
    requirement invalidReq_noId : ProcessingCapability_Def {
        doc
        /* The CSCI shall log all interface transactions with sufficient
         * detail to support post-event audit and replay.
         */
        doc Rationale
        /* Audit logs are required by the program compliance framework and
         * are essential for incident investigation.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> capabilityName = "AuditLogging";
        attribute :>> source         = "COMPLIANCE-001";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
    }

    // INVALID: no doc block (HasText violation)
    requirement <'REQ-CAP-005'> invalidReq_noDoc
            : ProcessingCapability_Def {
        doc Rationale
        /* Throughput is a contractual performance threshold derived from
         * the program operational concept document.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> capabilityName = "PeakThroughput";
        attribute :>> source         = "PA-OCD §4.2";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
        attribute :>> throughput     = "5000 messages/second minimum.";
    }

    // INVALID: no doc Rationale block (HasRationale violation)
    requirement <'REQ-QUA-002'> invalidReq_noRationale
            : SystemAvailability_Def {
        doc
        /* The CSCI shall support online diagnostics accessible to the
         * system administrator without interrupting operational processing.
         */
        // doc Rationale intentionally absent — INVALID demo
        subject sys : CoreSystem_Assembly;
        attribute :>> qualityAttribute = "Maintainability";
        attribute :>> source           = "SDP-001 §5.1";
        attribute :>> priority         = CMNDEF::LevelKind::Medium;
        attribute :>> criticality      = CMNDEF::LevelKind::Medium;
    }
}

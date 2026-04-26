// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramA_Requirements — Program A requirement definitions and declarations.
 *
 * LEAF FILE. Re-exported as Programs::ProgramA by 04_Programs/_namespace.sysml.
 *
 * Doc convention (per SRS_Definitions.sysml):
 *   - Short-name ID in the <'PA-ID'> position
 *   - Unnamed doc block  — normative "shall" statement
 *   - doc Rationale      — why this requirement exists
 *   - Criteria doc block — narrative pass/fail objective
 *   - passFailLogic, conditions, criteriaObjective removed
 */
package ProgramA_Requirements {
    private import SRS_Definitions::*;
    private import Core::Requirements::*;
    private import ProgramA_System::*;
    private import ProgramA_StakeholderConcerns::*;
    private import ScalarValues::*;

    // ── Definitions ────────────────────────────────────────────────────

    requirement def <'PA-CAP-001-DEF'> ProgramA_ThroughputReq_Def
            :> CapabilityRequirement {
        doc /* Program A peak throughput capability requirement. */
        frame concern ProgramA_PerformanceConcern;
    }

    requirement def <'PA-ENV-001-DEF'> ProgramA_OperatingEnvironment_Def
            :> EnvironmentalRequirement {
        doc /* Program A hardware and OS execution environment requirement. */
        frame concern ProgramA_PerformanceConcern;
    }

    requirement def <'PA-DSN-001-DEF'> ProgramA_ComplianceConstraint_Def
            :> DesignConstraintRequirement {
        doc /* Program A regulatory compliance design constraint. */
        frame concern ProgramA_ComplianceConcern;
    }

    requirement def <'PA-ADP-001-DEF'> ProgramA_SiteAdaptation_Def
            :> AdaptationRequirement {
        doc /* Program A site-specific configuration parameters. */
        frame concern ProgramA_ComplianceConcern;
    }

    // ── Declarations ───────────────────────────────────────────────────

    requirement <'PA-CAP-001'> programA_ThroughputReq
            : ProgramA_ThroughputReq_Def {
        doc
        /* The Program A system shall sustain a minimum throughput of
         * 5000 messages per second under peak operational load without
         * exceeding the defined latency budget.
         */
        doc Rationale
        /* Program A operational profile requires higher throughput than
         * the core baseline due to additional sensor inputs.
         * Derived from PA-OCD §4.2.1.
         */
        subject sys : ProgramA_SystemDef;
        attribute :>> source         = "PA-OCD §4.2.1";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
        attribute :>> capabilityName = "ProgramA_PeakThroughput";
        attribute :>> throughput     = "5000 messages/second minimum under peak load,  measured over a 5-minute sustained run.";
        attribute :>> latency        = "End-to-end latency shall not exceed 75 ms at  99th percentile during peak throughput operation.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Run Program A under peak load profile (PA-ITP §3.1) with all
             * sensor inputs active for 5 minutes.
             * PASS if throughput >= 5000 msg/s, 99th-percentile latency
             * <= 75 ms, and zero messages are lost.
             */
            attribute :>> verificationMethod = VerificationMethodKind::Test;
            attribute :>> threshold          = "5000 msg/s; latency <= 75 ms at P99; 0 message loss";
        }
    }

    requirement <'PA-ENV-001'> programA_OperatingEnvironment
            : ProgramA_OperatingEnvironment_Def {
        doc
        /* The Program A CSCI shall execute on a Linux-based platform
         * running RHEL 9.x or equivalent, on hardware meeting the Program A
         * minimum hardware specification PA-HWS-001.
         */
        doc Rationale
        /* Program A deployment sites are standardised on RHEL 9.x.
         * Hardware specification PA-HWS-001 defines minimum CPU, memory,
         * and storage for the operational load profile.
         */
        subject sys : ProgramA_SystemDef;
        attribute :>> source      = "PA-HWS-001; PA-SDP-001 §3.4";
        attribute :>> priority    = CMNDEF::LevelKind::High;
        attribute :>> criticality = CMNDEF::LevelKind::High;
        attribute :>> environment = "RHEL 9.x (or equivalent); hardware per PA-HWS-001:  minimum 16-core CPU, 32 GB RAM, 1 TB NVMe storage.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Pre-deployment configuration review confirms hardware meets
             * PA-HWS-001 and OS is RHEL 9.x compatible.
             * PASS if 100% compliance with PA-HWS-001 hardware spec is confirmed.
             */
            attribute :>> verificationMethod = VerificationMethodKind::Inspection;
            attribute :>> threshold          = "100% compliance with PA-HWS-001 hardware spec";
        }
    }

    requirement <'PA-DSN-001'> programA_ComplianceConstraint
            : ProgramA_ComplianceConstraint_Def {
        doc
        /* The Program A CSCI shall comply with all applicable requirements
         * of the Program A regulatory framework PA-REG-001 throughout its
         * operational lifetime.
         */
        doc Rationale
        /* Program A operates under a specific regulatory framework with
         * mandatory data handling constraints that differ from the core
         * baseline. Non-compliance creates deployment approval risk.
         */
        subject sys : ProgramA_SystemDef;
        attribute :>> source         = "PA-REG-001";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
        attribute :>> constraintText = "All data handling, storage, and transmission shall  conform to PA-REG-001 data governance requirements. Cryptographic  algorithms shall be FIPS 140-3 validated where required.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Compliance audit prior to Program A deployment approval.
             * Review compliance matrix PA-CM-001 for 100% coverage of
             * PA-REG-001 requirements.
             * PASS if compliance matrix shows 100% coverage with no open waivers.
             */
            attribute :>> verificationMethod = VerificationMethodKind::Inspection;
            attribute :>> threshold          = "100% PA-REG-001 compliance; zero open waivers";
        }
    }

    requirement <'PA-ADP-001'> programA_SiteAdaptation
            : ProgramA_SiteAdaptation_Def {
        doc
        /* The Program A CSCI shall accept site-specific configuration
         * parameters at installation time to adapt to the operational site
         * network topology and data source endpoints.
         */
        doc Rationale
        /* Program A is deployed across multiple sites with different network
         * configurations. Site parameters must be configurable without
         * software modification per PA-OCD §6.
         */
        subject sys : ProgramA_SystemDef;
        attribute :>> source         = "PA-OCD §6";
        attribute :>> priority       = CMNDEF::LevelKind::Medium;
        attribute :>> criticality    = CMNDEF::LevelKind::Medium;
        attribute :>> siteParameters = "Network interface address, data source endpoint URI,  site identifier code, local time zone offset, and operational mode flag (primary/backup).";
        part :>> criteria : VerificationCriteria {
            doc
            /* Installation test at representative site configuration.
             * Apply all five site parameters from configuration file at startup.
             * PASS if all parameters are correctly applied with zero source
             * code changes required.
             */
            attribute :>> verificationMethod = VerificationMethodKind::Test;
            attribute :>> threshold          = "All 5 site parameters applied correctly; zero source changes";
        }
    }
}

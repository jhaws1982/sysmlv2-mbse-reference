// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramA_Requirements — Program A requirement definitions and declarations.
 *
 * LEAF FILE. Re-exported as Programs::ProgramA by 04_Programs/_namespace.sysml.
 *
 * All requirements specialize types from SRS_Definitions (imported via
 * Shared::SRS). Program-specific defs frame stakeholder concerns; declarations
 * bind requirements to the deployed Program A architecture.
 */
package ProgramA_Requirements {
    private import SRS_Definitions::*;
    private import Core::Requirements::*;
    private import ProgramA_Deployment::*;
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
        doc /* Program A shall sustain peak throughput under maximum operational load. */
        subject sys : ProgramA_System;
        attribute :>> id             = "PA-CAP-001";
        attribute :>> text           = "The Program A system shall sustain a minimum throughput of 5000 messages per second under peak operational load without exceeding the defined latency budget.";
        attribute :>> rationale      = "Program A operational profile requires higher throughput than the core baseline due to additional sensor inputs. Derived from PA-OCD §4.2.1.";
        attribute :>> source         = "PA-OCD §4.2.1";
        attribute :>> priority       = "High";
        attribute :>> criticality    = "Critical";
        attribute :>> capabilityName = "ProgramA_PeakThroughput";
        attribute :>> throughput     = "5000 messages/second minimum under peak load, measured over a 5-minute sustained run.";
        attribute :>> latency        = "End-to-end latency shall not exceed 75 ms at 99th percentile during peak throughput operation.";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Test;
            attribute :>> passFailLogic      = "PASS if system sustains >= 5000 msg/s for 5 minutes with 99th-percentile latency <= 75 ms and zero message loss.";
            attribute :>> threshold          = "5000 msg/s; latency <= 75 ms at P99; 0 message loss";
            attribute :>> conditions         = "Peak load profile per PA-ITP §3.1; all Program A sensor inputs active.";
            attribute :>> criteriaObjective  = "Verify Program A peak throughput and latency under maximum operational load.";
        }
    }

    requirement <'PA-ENV-001'> programA_OperatingEnvironment
        : ProgramA_OperatingEnvironment_Def {
        doc /* Program A execution environment constraints. */
        subject sys : ProgramA_System;
        attribute :>> id          = "PA-ENV-001";
        attribute :>> text        = "The Program A CSCI shall execute on a Linux-based platform running RHEL 9.x or equivalent, on hardware meeting the Program A minimum hardware specification PA-HWS-001.";
        attribute :>> rationale   = "Program A deployment sites are standardised on RHEL 9.x. Hardware specification PA-HWS-001 defines minimum CPU, memory, and storage for the operational load profile.";
        attribute :>> source      = "PA-HWS-001; PA-SDP-001 §3.4";
        attribute :>> priority    = "High";
        attribute :>> criticality = "High";
        attribute :>> environment = "RHEL 9.x (or equivalent); hardware per PA-HWS-001: minimum 16-core CPU, 32 GB RAM, 1 TB NVMe storage.";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Inspection;
            attribute :>> passFailLogic      = "PASS if deployment configuration confirms hardware meets PA-HWS-001 and OS is RHEL 9.x compatible.";
            attribute :>> threshold          = "100% compliance with PA-HWS-001 hardware spec";
            attribute :>> conditions         = "Pre-deployment configuration review.";
        }
    }

    requirement <'PA-DSN-001'> programA_ComplianceConstraint
        : ProgramA_ComplianceConstraint_Def {
        doc /* Program A regulatory compliance design constraint. */
        subject sys : ProgramA_System;
        attribute :>> id             = "PA-DSN-001";
        attribute :>> text           = "The Program A CSCI shall comply with all applicable requirements of the Program A regulatory framework PA-REG-001 throughout its operational lifetime.";
        attribute :>> rationale      = "Program A operates under a specific regulatory framework with mandatory design and data handling constraints that differ from the core baseline.";
        attribute :>> source         = "PA-REG-001";
        attribute :>> priority       = "High";
        attribute :>> criticality    = "Critical";
        attribute :>> constraintText = "All data handling, storage, and transmission shall conform to PA-REG-001 data governance requirements. Cryptographic algorithms shall be FIPS 140-3 validated where required.";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Inspection;
            attribute :>> passFailLogic      = "PASS if compliance matrix PA-CM-001 shows 100% coverage of PA-REG-001 requirements with no open waivers.";
            attribute :>> threshold          = "100% PA-REG-001 compliance; zero open waivers";
            attribute :>> conditions         = "Compliance audit prior to Program A deployment approval.";
        }
    }

    requirement <'PA-ADP-001'> programA_SiteAdaptation
        : ProgramA_SiteAdaptation_Def {
        doc /* Program A site-specific configuration parameters. */
        subject sys : ProgramA_System;
        attribute :>> id             = "PA-ADP-001";
        attribute :>> text           = "The Program A CSCI shall accept site-specific configuration parameters at installation time to adapt to the operational site network topology and data source endpoints.";
        attribute :>> rationale      = "Program A is deployed across multiple sites with different network configurations. Site parameters must be configurable without software modification per PA-OCD §6.";
        attribute :>> source         = "PA-OCD §6";
        attribute :>> priority       = "Medium";
        attribute :>> criticality    = "Medium";
        attribute :>> siteParameters = "Network interface address, data source endpoint URI, site identifier code, local time zone offset, and operational mode flag (primary/backup).";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Test;
            attribute :>> passFailLogic      = "PASS if system correctly applies all site parameters from configuration file at startup with no source modification.";
            attribute :>> threshold          = "All 5 site parameters applied correctly; zero source code changes required";
            attribute :>> conditions         = "Installation test at representative site configuration.";
        }
    }
}

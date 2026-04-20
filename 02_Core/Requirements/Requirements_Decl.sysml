/**
 * RequirementsDecl — core CSCI requirement declarations (Decl side of Def/Decl split).
 *
 * LEAF file. Re-exported as Core::Requirements by 02_Core/_namespace.sysml.
 *
 * Each requirement here is a usage typed by a def from RequirementsDef,
 * with all SRS_Definitions attributes populated. The subject binds each
 * requirement to the architectural element it constrains.
 */
package RequirementsDecl {
    private import RequirementsDef::*;
    private import SRS_Definitions::*;
    private import CoreSystem::*;
    private import FeatureA::*;
    private import FeatureB::*;
    private import FeatureC::*;

    //------------------------------------------------------------------
    // Capability Requirement Declarations
    //------------------------------------------------------------------

    requirement <'REQ-CAP-001'> processingCapability
        : ProcessingCapability_Def {
        doc /* The CSCI shall process all inbound data streams within
               50 milliseconds of receipt under nominal operating load. */
        subject sys : CoreSystem_Assembly;
        attribute :>> id             = "REQ-CAP-001";
        attribute :>> text           = "The CSCI shall process all inbound data streams "
                                       "within 50 milliseconds of receipt under nominal load.";
        attribute :>> rationale      = "Derived from system-level response time budget SYS-PERF-003. "
                                       "50 ms allocated to CSCI processing after network transit.";
        attribute :>> source         = "SYS-PERF-003";
        attribute :>> priority       = "High";
        attribute :>> criticality    = "Critical";
        attribute :>> capabilityName = "InboundDataProcessing";
        attribute :>> latency        = "50 ms maximum at 99th percentile, measured from "
                                       "data receipt at input port to output availability.";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Test;
            attribute :>> passFailLogic      = "PASS if measured 99th-percentile latency <= 50 ms "
                                               "over a 10-minute run at 1000 messages/second nominal load.";
            attribute :>> threshold          = "50 ms at 99th percentile";
            attribute :>> conditions         = "Nominal load: 1000 messages/second, "
                                               "standard integration test environment.";
        }
    }

    requirement <'REQ-CAP-002'> integrationCapability
        : IntegrationCapability_Def {
        doc /* The CSCI shall integrate Feature A and Feature B into a unified pipeline. */
        subject sys : CoreSystem_Assembly;
        attribute :>> id             = "REQ-CAP-002";
        attribute :>> text           = "The CSCI shall integrate the Feature A and Feature B "
                                       "subsystems into a single unified processing pipeline "
                                       "with no data loss under nominal conditions.";
        attribute :>> rationale      = "System architecture requires a single pipeline to reduce "
                                       "integration complexity and eliminate inter-process latency.";
        attribute :>> source         = "SYS-ARCH-001";
        attribute :>> priority       = "High";
        attribute :>> criticality    = "Critical";
        attribute :>> capabilityName = "SubsystemIntegration";
        attribute :>> performance    = "Zero data loss under nominal load; graceful degradation "
                                       "under overload with defined queue depth limits.";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Test;
            attribute :>> passFailLogic      = "PASS if zero messages lost during 30-minute "
                                               "nominal load test and queue depth remains within limits.";
            attribute :>> threshold          = "0 messages lost; queue depth <= 1000 messages";
            attribute :>> conditions         = "Nominal load profile, both subsystems active.";
        }
    }

    //------------------------------------------------------------------
    // Interface Requirement Declarations
    //------------------------------------------------------------------

    requirement <'REQ-IFC-001'> externalDataInterface
        : ExternalDataInterface_Def {
        doc /* External data interface between Core and the external data source. */
        subject featureA : FeatureA_Component;
        attribute :>> id              = "REQ-IFC-001";
        attribute :>> text            = "The CSCI shall implement a binary message interface "
                                        "to the external data source conforming to ICD-EXT-001.";
        attribute :>> rationale       = "External data source uses a fixed binary protocol "
                                        "defined in ICD-EXT-001 which cannot be modified.";
        attribute :>> source          = "ICD-EXT-001";
        attribute :>> priority        = "High";
        attribute :>> criticality     = "Critical";
        attribute :>> interfaceName   = "ExternalDataSource_Interface";
        attribute :>> primaryEntity   = "CoreSystem_CSCI";
        attribute :>> secondaryEntity = "ExternalDataSource";
        attribute :>> protocol        = "Binary framed message protocol per ICD-EXT-001";
        attribute :>> messageFormat   = "Fixed-length binary frames, 256-byte header + variable payload";
        attribute :>> dataName        = "ExternalDataMessage";
        attribute :>> dataType        = "Binary framed message";
        attribute :>> format          = "256-byte header, variable-length payload, 4-byte CRC";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Test;
            attribute :>> passFailLogic      = "PASS if all message types in ICD-EXT-001 §3 "
                                               "are correctly encoded and decoded with zero errors "
                                               "over 10000 test messages.";
            attribute :>> threshold          = "0 encoding/decoding errors in 10000 messages";
            attribute :>> conditions         = "All message types exercised; nominal and boundary values.";
        }
    }

    //------------------------------------------------------------------
    // Quality Requirement Declarations
    //------------------------------------------------------------------

    requirement <'REQ-QUA-001'> systemAvailability
        : SystemAvailability_Def {
        doc /* System availability requirement for the core CSCI. */
        subject sys : CoreSystem_Assembly;
        attribute :>> id                 = "REQ-QUA-001";
        attribute :>> text               = "The CSCI shall achieve a minimum operational "
                                           "availability of 99.5% over any 30-day measurement period.";
        attribute :>> rationale          = "Mission profile requires continuous operation with "
                                           "planned maintenance windows not exceeding 0.5%.";
        attribute :>> source             = "SYS-RELY-001";
        attribute :>> priority           = "High";
        attribute :>> criticality        = "High";
        attribute :>> qualityAttribute   = "Availability";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Analysis;
            attribute :>> passFailLogic      = "PASS if reliability analysis demonstrates "
                                               "predicted availability >= 99.5% over 30-day window.";
            attribute :>> threshold          = "99.5% availability over 30-day period";
            attribute :>> conditions         = "Normal operating environment; planned maintenance excluded.";
        }
    }

    //------------------------------------------------------------------
    // Design Constraint Declarations
    //------------------------------------------------------------------

    requirement <'REQ-DSN-001'> programmingLanguageConstraint
        : ProgrammingLanguageConstraint_Def {
        doc /* Programming language constraint for CSCI implementation. */
        subject sys : CoreSystem_Assembly;
        attribute :>> id                = "REQ-DSN-001";
        attribute :>> text              = "The CSCI shall be implemented in C++ (ISO/IEC 14882:2017) "
                                          "or Python 3.10+ as specified in the Software Development Plan.";
        attribute :>> rationale         = "Organizational standard languages; toolchain and code review "
                                          "processes are established for these languages only.";
        attribute :>> source            = "SDP-001 §4.2";
        attribute :>> priority          = "Medium";
        attribute :>> criticality       = "Medium";
        attribute :>> constraintText    = "C++ (ISO/IEC 14882:2017) or Python 3.10+ only. "
                                          "No other languages permitted without waiver.";
        part :>> criteria : VerificationCriteria {
            attribute :>> verificationMethod = VerificationMethodKind::Inspection;
            attribute :>> passFailLogic      = "PASS if code review confirms all source files "
                                               "use only approved languages with no waivers outstanding.";
            attribute :>> threshold          = "100% of source files in approved languages";
            attribute :>> conditions         = "Final code review prior to CDR.";
        }
    }
}

// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * Traceability — core verification cases.
 *
 * LEAF FILE. Globally unique name "Traceability".
 * Assembled into Verification::Traceability by the namespace hub.
 *
 * Verification names MUST match CTest test names exactly.
 * result_matrix.py joins on these names against CTest XML output.
 *
 * Intentional gaps for tool demonstration:
 *   - REQ-CAP-003 (incompleteReq): no verification — coverage gap
 *   - REQ-CAP-004 (invalidReq_noId): no verification — coverage gap
 *   - REQ-CAP-005 (invalidReq_noDoc): no verification — coverage gap
 *   - REQ-QUA-002 (invalidReq_noRationale): no verification — coverage gap
 */
package Traceability {
    private import Core::Logical::*;
    private import Core::Requirements::*;

    // ── Complete verifications (have satisfy links) ───────────────────────

    verification processingCapability_Test {
        doc /* Verifies REQ-CAP-001 processingCapability.
               Injects 1000 msg/s for 10 minutes and measures p99 latency. */
        subject sys : CoreSystem_Assembly;
        satisfy requirement processingCapability;
    }

    verification integrationCapability_Test {
        doc /* Verifies REQ-CAP-002 integrationCapability.
               Runs both subsystems under nominal load for 30 minutes. */
        subject sys : CoreSystem_Assembly;
        satisfy requirement integrationCapability;
    }

    verification externalDataInterface_Test {
        doc /* Verifies REQ-IFC-001 externalDataInterface.
               Exercises all ICD-EXT-001 §3 message types — 10 000 messages. */
        subject featureA_Subject : FeatureA_Component;
        satisfy requirement externalDataInterface;
    }

    verification systemAvailability_Analysis {
        doc /* Verifies REQ-QUA-001 systemAvailability.
               Reliability analysis using component MTBF data. */
        subject sys : CoreSystem_Assembly;
        satisfy requirement systemAvailability;
    }

    verification programmingLanguageConstraint_Inspection {
        doc /* Verifies REQ-DSN-001 programmingLanguageConstraint.
               Code review at CDR confirms all source files use approved languages. */
        subject sys : CoreSystem_Assembly;
        satisfy requirement programmingLanguageConstraint;
    }

    // ── incompleteReq (REQ-CAP-003): intentionally unverified ────────────
    // coverage_matrix.py will flag this as a gap.
}

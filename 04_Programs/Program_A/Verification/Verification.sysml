// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramA_Verification — Program A verification cases.
 *
 * LEAF FILE. Globally unique name "ProgramA_Verification".
 * Assembled into Programs::ProgramA by 04_Programs/_namespace.sysml.
 *
 * Verification names MUST match CTest test names exactly.
 * result_matrix.py joins on these names against CTest XML output.
 *
 * Intentional gap: programA_ComplianceConstraint has no verification —
 * demonstrates coverage gap reporting in coverage_matrix.py.
 */
package ProgramA_Verification {
    private import ProgramA_Requirements::*;
    private import ProgramA_System::*;

    verification programA_ThroughputTest {
        doc /* Verifies PA-CAP-001 programA_ThroughputReq.
               Peak load test per PA-ITP §3.1 with all sensor inputs active
               for 5 minutes. */
        subject sys : ProgramA_SystemDef;
        satisfy requirement programA_ThroughputReq;
    }

    verification programA_EnvironmentInspection {
        doc /* Verifies PA-ENV-001 programA_OperatingEnvironment.
               Pre-deployment configuration review against PA-HWS-001. */
        subject sys : ProgramA_SystemDef;
        satisfy requirement programA_OperatingEnvironment;
    }

    verification programA_SiteAdaptationTest {
        doc /* Verifies PA-ADP-001 programA_SiteAdaptation.
               Installation test applying all five site parameters at startup. */
        subject sys : ProgramA_SystemDef;
        satisfy requirement programA_SiteAdaptation;
    }

    // programA_ComplianceConstraint intentionally unverified — gap demo
}

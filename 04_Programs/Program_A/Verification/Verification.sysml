// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramA_Verification — Program A verification cases.
 *
 * Verification names MUST match CTest test names exactly.
 * programA_ComplianceReq intentionally unverified — gap demo.
 */
package ProgramA_Verification {
    private import ProgramA_Requirements::*;
    private import ProgramA_Deployment::*;

    verification programA_Test {
        doc /* Verifies programA_Requirement against ProgramA_System. */
        subject sys : ProgramA_System;
        satisfy requirement programA_Requirement;
    }

    verification programA_PerformanceTest {
        doc /* Verifies programA_PerformanceReq against ProgramA_System. */
        subject sys : ProgramA_System;
        satisfy requirement programA_PerformanceReq;
    }

    // programA_ComplianceReq intentionally unverified — gap demo
}

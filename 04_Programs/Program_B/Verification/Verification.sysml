// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramB_Verification — Program B verification cases.
 *
 * Verification names MUST match CTest test names exactly.
 * programB_SafetyReq intentionally unverified — gap demo.
 */
package ProgramB_Verification {
    private import ProgramB_Requirements::*;
    private import ProgramB_Deployment::*;

    verification programB_Test {
        doc /* Verifies programB_Requirement against ProgramB_System. */
        subject sys : ProgramB_System;
        satisfy requirement programB_Requirement;
    }

    verification programB_InterfaceTest {
        doc /* Verifies programB_InterfaceReq against ProgramB_System. */
        subject sys : ProgramB_System;
        satisfy requirement programB_InterfaceReq;
    }

    // programB_SafetyReq intentionally unverified — gap demo
}

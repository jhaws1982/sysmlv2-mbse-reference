// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramB_Requirements — Program B requirement definitions and declarations.
 */
package ProgramB_Requirements {
    private import Core::Requirements::*;
    private import ProgramB_Deployment::*;
    private import ProgramB_StakeholderConcerns::*;

    // ── Program B specific requirement definitions ─────────────────────
    requirement def ProgramB_InterfaceReq_Def {
        doc /* Program B interface stability requirement type. */
        frame concern ProgramB_InterfaceConcern;
    }

    requirement def ProgramB_SafetyReq_Def {
        doc /* Program B safety integrity requirement type. */
        frame concern ProgramB_SafetyConcern;
    }

    // ── Program B requirement declarations ────────────────────────────
    requirement programB_Requirement : RequirementB_Def {
        doc /* Program B assertion of core RequirementB against ProgramB_System. */
        subject sys : ProgramB_System;
    }

    requirement programB_InterfaceReq : ProgramB_InterfaceReq_Def {
        doc /* Program B external interfaces must be stable and versioned. */
        subject sys : ProgramB_System;
    }

    requirement programB_SafetyReq : ProgramB_SafetyReq_Def {
        doc /* Program B system must meet applicable safety integrity level. */
        subject sys : ProgramB_System;
    }
}

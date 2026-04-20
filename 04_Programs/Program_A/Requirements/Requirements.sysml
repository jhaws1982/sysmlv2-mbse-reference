// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramA_Requirements — Program A requirement definitions and declarations.
 *
 * Contains both requirement defs (framing Program A concerns) and
 * requirement usages (bound to Program A architecture).
 */
package ProgramA_Requirements {
    private import Core::Requirements::*;
    private import ProgramA_Deployment::*;
    private import ProgramA_StakeholderConcerns::*;

    // ── Program A specific requirement definitions ─────────────────────
    requirement def ProgramA_PerformanceReq_Def {
        doc /* Program A throughput requirement type. */
        frame concern ProgramA_PerformanceConcern;
    }

    requirement def ProgramA_ComplianceReq_Def {
        doc /* Program A regulatory compliance requirement type. */
        frame concern ProgramA_ComplianceConcern;
    }

    // ── Program A requirement declarations (bound to architecture) ─────
    requirement programA_Requirement : RequirementA_Def {
        doc /* Program A assertion of core RequirementA against ProgramA_System. */
        subject sys : ProgramA_System;
    }

    requirement programA_PerformanceReq : ProgramA_PerformanceReq_Def {
        doc /* Program A system must meet throughput targets. */
        subject sys : ProgramA_System;
    }

    requirement programA_ComplianceReq : ProgramA_ComplianceReq_Def {
        doc /* Program A system must comply with applicable standard. */
        subject sys : ProgramA_System;
    }
}

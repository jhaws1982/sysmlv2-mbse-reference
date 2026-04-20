// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramA_StakeholderConcerns — Program A specific concerns.
 *
 * These concerns are distinct from core concerns and are specific to
 * the operational and compliance context of Program A.
 */
package ProgramA_StakeholderConcerns {
    private import ProgramA_StakeholderDefs::*;

    concern def ProgramA_PerformanceConcern {
        doc /* Program A operator requires that the system meets
               Program A specific throughput targets under peak load. */
        subject sys;
        actor operator : ProgramA_Operator;
    }

    concern def ProgramA_ComplianceConcern {
        doc /* Program A auditor requires that all data handling
               complies with the applicable regulatory standard. */
        subject sys;
        actor auditor : ProgramA_Auditor;
    }
}

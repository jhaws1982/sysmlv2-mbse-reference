// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramB_StakeholderConcerns — Program B specific concerns.
 */
package ProgramB_StakeholderConcerns {
    private import ProgramB_StakeholderDefs::*;

    concern def ProgramB_InterfaceConcern {
        doc /* Program B integrator requires that all external interfaces
               are stable and versioned across releases. */
        subject sys;
        actor integrator : ProgramB_Integrator;
    }

    concern def ProgramB_SafetyConcern {
        doc /* Program B safety officer requires that the system meets
               the applicable safety integrity level. */
        subject sys;
        actor safetyOfficer : ProgramB_SafetyOfficer;
    }
}

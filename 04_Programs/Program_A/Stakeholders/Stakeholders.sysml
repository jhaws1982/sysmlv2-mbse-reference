// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * ProgramA_StakeholderDefs — Program A specific stakeholder roles.
 *
 * These are roles that exist only in the context of Program A and are
 * not shared with core or other programs.
 */
package ProgramA_StakeholderDefs {

    part def ProgramA_Operator {
        doc /* Operator role specific to Program A deployment context.
               Responsible for day-to-day operation of the Program A system. */
    }

    part def ProgramA_Auditor {
        doc /* Compliance auditor for Program A regulatory requirements. */
    }
}

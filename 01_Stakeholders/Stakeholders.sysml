/**
 * StakeholderDefs — stakeholder role definitions.
 *
 * LEAF FILE.  Globally unique name "StakeholderDefs".
 * Assembled into  Stakeholders::Roles  by  01_Stakeholders/_namespace.sysml.
 *
 * SysIDE note: `stakeholder def` is only valid as a nested membership INSIDE
 * a concern def or viewpoint def body — NOT at package scope.  Define
 * stakeholder roles as `part def` at package level.  They are referenced
 * inside concern defs using the `actor` keyword (see Concerns.sysml).
 *
 * This file is STABLE — stakeholder roles reflect your system's audience and
 * change only when the organizational or operational context changes.
 */
package StakeholderDefs {

    part def StakeholderA {
        doc /* Role description: primary operator / owner of the system.
               Responsible for day-to-day operation and functional outcomes. */
    }

    part def StakeholderB {
        doc /* Role description: secondary stakeholder (e.g. regulator, auditor,
               or external integrator).  Primarily concerned with compliance
               and interface contracts. */
    }
}

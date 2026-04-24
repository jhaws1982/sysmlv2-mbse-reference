/**
 * ProgramB_System — Program B logical system definition.
 *
 * LEAF FILE. Globally unique name "ProgramB_System".
 * Assembled into Programs::ProgramB by 04_Programs/_namespace.sysml.
 *
 * Purpose: Defines the top-level logical system assembly for Program B.
 * This is the architectural identity of Program B — the element that
 * requirements are written against and verification cases subject.
 *
 * Extend this file when Program B requires:
 *   - Program-specific subsystems not present in the core
 *   - Specializations or overrides of core logical architecture
 *   - Program-unique interfaces or components
 *
 * Change driver: changes when the Program B architecture changes.
 * (Operational environment / hardware context lives in deployment.sysml)
 */
package ProgramB_System {
    private import Core::Logical::*;
    private import ProgramB::*;

    part def ProgramB_SystemDef {
        doc /* Top-level logical system assembly for Program B.
               Composes the core system with Program B configuration
               and any program-specific architectural extensions.
             */
        part core   : CoreSystem_Assembly;
        part config : ProgramB_Config;

        // Add program-specific subsystems here as the architecture matures.
        // Example:
        //   part programB_SafetyModule : ProgramB_SafetySubsystem;
    }
}

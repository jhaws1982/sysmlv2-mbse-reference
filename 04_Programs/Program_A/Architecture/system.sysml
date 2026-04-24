/**
 * ProgramA_System — Program A logical system definition.
 *
 * LEAF FILE. Globally unique name "ProgramA_System".
 * Assembled into Programs::ProgramA by 04_Programs/_namespace.sysml.
 *
 * Purpose: Defines the top-level logical system assembly for Program A.
 * This is the architectural identity of Program A — the element that
 * requirements are written against and verification cases subject.
 *
 * Extend this file when Program A requires:
 *   - Program-specific subsystems not present in the core
 *   - Specializations or overrides of core logical architecture
 *   - Program-unique interfaces or components
 *
 * Change driver: changes when the Program A architecture changes.
 * (Operational environment / hardware context lives in deployment.sysml)
 */
package ProgramA_System {
    private import Core::Logical::*;
    private import ProgramA::*;

    part def ProgramA_SystemDef {
        doc /* Top-level logical system assembly for Program A.
               Composes the core system with Program A configuration
               and any program-specific architectural extensions.
             */
        part core   : CoreSystem_Assembly;
        part config : ProgramA_Config;

        // Add program-specific subsystems here as the architecture matures.
        // Example:
        //   part programA_Sensor : ProgramA_SensorSubsystem;
    }
}

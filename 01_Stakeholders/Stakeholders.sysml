/**
 * StakeholderDefs — stakeholder role definitions.
 *
 * LEAF FILE. Globally unique name "StakeholderDefs".
 * Assembled into Stakeholders::Roles by 01_Stakeholders/_namespace.sysml.
 *
 * SysIDE: stakeholder roles are part defs at package scope.
 * Referenced inside concern defs using the `actor` keyword.
 */
package StakeholderDefs {
    private import CommonDefinitions::*;

    part def PrimaryOperator :> CommonStakeholder {
        doc /* Primary operational user of the system. Initiates data processing
               commands, monitors system health, and responds to alerts during
               operational windows. Primary driver of performance and usability
               requirements. */
    }

    part def SystemAdministratorRole :> CommonStakeholder {
        doc /* Responsible for system installation, configuration updates, and
               routine maintenance. Primary driver of maintainability,
               configurability, and administrative interface requirements. */
    }

    part def SystemsEngineerRole :> CommonStakeholder {
        doc /* Responsible for system integration, verification, and validation.
               Primary driver of testability, interface control, and
               traceability requirements. */
    }

    part def ProgramManagerRole :> CommonProgramManager {
        doc /* Accountable for program cost, schedule, and contractual compliance.
               Primary driver of documentation standards and deliverable
               requirements. */
    }
}

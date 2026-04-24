/**
 * ProgramA_Deployment — Program A operational deployment context.
 *
 * LEAF FILE. Globally unique name "ProgramA_Deployment".
 * Assembled into Programs::ProgramA by 04_Programs/_namespace.sysml.
 *
 * Describes the operational environment: hardware platform, OS, site topology.
 * Change driver: environment changes (new hardware, site, OS upgrade).
 * Architecture changes belong in system.sysml.
 */
package ProgramA_Deployment {
    private import ProgramA_System::*;
    private import ScalarValues::*;
    private import CommonDefinitions::*;

    // Risk on the deployment — demonstrates @RiskItem on a part def
    @RiskItem {
        riskId      = "RISK-PA-DEP-001";
        title       = "RHEL 9.x end-of-support within program lifecycle";
        category    = RiskCategory::Technical;
        probability = LevelKind::Medium;
        impact      = LevelKind::Medium;
        exposure    = 4;
        status      = RiskStatus::Open;
        description = "RHEL 9.x standard support ends before the planned Program A
                       end-of-life date, requiring either an OS upgrade or an
                       extended support contract mid-program.";
        mitigation  = "Evaluate RHEL 9.x extended support contract cost by Q3.
                       Add OS lifecycle review to annual program health check.";
        owner       = "Systems Engineering Lead";
    }
    part def ProgramA_DeployedSystem {
        doc /* Program A system instantiated in its operational deployment context.
               References ProgramA_SystemDef as the logical system and describes
               the platform on which it executes.
             */
        part system : ProgramA_SystemDef;

        attribute platform     : ScalarValues::String = "RHEL 9.x (or equivalent)";
        attribute hardwareSpec : ScalarValues::String =
            "PA-HWS-001: minimum 16-core CPU, 32 GB RAM, 1 TB NVMe storage";
        attribute siteId       : ScalarValues::String; // set at installation time
    }
}

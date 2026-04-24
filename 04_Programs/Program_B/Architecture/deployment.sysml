/**
 * ProgramB_Deployment — Program B operational deployment context.
 *
 * LEAF FILE. Globally unique name "ProgramB_Deployment".
 * Assembled into Programs::ProgramB by 04_Programs/_namespace.sysml.
 *
 * Describes the operational environment for Program B.
 * Program B requires safety-rated hardware with CPU/memory headroom
 * for safety monitoring processes (see PB-RES-001).
 */
package ProgramB_Deployment {
    private import ProgramB_System::*;
    private import ScalarValues::*;
    private import CommonDefinitions::*;

    // High-exposure risk on the Program B deployment — demonstrates @RiskItem
    @RiskItem {
        riskId      = "RISK-PB-DEP-001";
        title       = "Safety-rated hardware lead time risk";
        category    = RiskCategory::Schedule;
        probability = LevelKind::High;
        impact      = LevelKind::High;
        exposure    = 9;
        status      = RiskStatus::Open;
        description = "Safety-certified hardware components for PB-HWS-001 have
                       a 26-week lead time. Late procurement order could delay
                       integration test entry by 2-3 months.";
        mitigation  = "Place hardware order by program month 3. Track weekly
                       with procurement team. Maintain approved alternate vendor list.";
        contingency = "Procure evaluation units from alternate vendor (pre-approved)
                       for integration test entry; replace with certified units
                       before qualification testing.";
        owner       = "Program Manager";
    }
    part def ProgramB_DeployedSystem {
        doc /* Program B system instantiated in its safety-critical operational
               context. Safety monitoring requires guaranteed CPU/memory headroom
               as specified in PB-RES-001.
             */
        part system : ProgramB_SystemDef;

        attribute platform     : ScalarValues::String = "Safety-certified Linux platform";
        attribute hardwareSpec : ScalarValues::String =
            "PB-HWS-001: redundant hardware per safety requirements";
        attribute safetyRating : ScalarValues::String; // populated per site certification
        attribute siteId       : ScalarValues::String; // set at installation time
    }
}

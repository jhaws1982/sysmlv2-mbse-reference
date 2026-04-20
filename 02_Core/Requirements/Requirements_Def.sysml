/**
 * RequirementsDef — core CSCI requirement definitions (Def side of Def/Decl split).
 *
 * LEAF file. Re-exported as Core::Requirements by 02_Core/_namespace.sysml.
 *
 * All requirement defs specialize types from SRS_Definitions (Shared::SRS).
 * This file is stable — it defines the types. The Decl file binds them to
 * architecture elements and changes with the design.
 */
package RequirementsDef {
    private import SRS_Definitions::*;
    private import ScalarValues::*;

    //------------------------------------------------------------------
    // Capability Requirements (§3.2.x) — what the CSCI must do
    //------------------------------------------------------------------

    requirement def <'REQ-CAP-001-DEF'> ProcessingCapability_Def
        :> CapabilityRequirement {
        doc /* The CSCI shall provide real-time data processing capability
               for all inbound data streams within the defined latency budget. */
    }

    requirement def <'REQ-CAP-002-DEF'> IntegrationCapability_Def
        :> CapabilityRequirement {
        doc /* The CSCI shall integrate Feature A and Feature B subsystems
               into a unified processing pipeline. */
    }

    //------------------------------------------------------------------
    // Interface Requirements (§3.3.x) — external interfaces
    //------------------------------------------------------------------

    requirement def <'REQ-IFC-001-DEF'> ExternalDataInterface_Def
        :> InterfaceRequirement {
        doc /* The CSCI shall implement the external data interface between
               the Core processing subsystem and the external data source. */
    }

    //------------------------------------------------------------------
    // Quality Requirements (§3.11) — software quality factors
    //------------------------------------------------------------------

    requirement def <'REQ-QUA-001-DEF'> SystemAvailability_Def
        :> QualityRequirement {
        doc /* The CSCI shall meet the availability requirement specified
               in the system-level performance budget. */
    }

    //------------------------------------------------------------------
    // Design Constraint Requirements (§3.12)
    //------------------------------------------------------------------

    requirement def <'REQ-DSN-001-DEF'> ProgrammingLanguageConstraint_Def
        :> DesignConstraintRequirement {
        doc /* The CSCI shall be implemented using the approved programming
               language(s) specified in the Software Development Plan. */
    }
}

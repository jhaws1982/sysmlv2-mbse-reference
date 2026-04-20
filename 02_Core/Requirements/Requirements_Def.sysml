/**
 * RequirementsDef — requirement type definitions (stable, stakeholder-driven).
 *
 * LEAF FILE.  Globally unique name "RequirementsDef".
 * Assembled into  Core::Requirements  by the namespace hub.
 *
 * `frame concern` is the SysML v2 mechanism for tracing a requirement back
 * to the stakeholder concern that motivated it.
 * `derive ... from` is not valid SysML v2 syntax.
 */
package RequirementsDef {
    private import Stakeholders::Concerns::*;

    requirement def RequirementA_Def {
        doc /* Requirement type derived from ConcernA. */
        frame concern ConcernA;
    }

    requirement def RequirementB_Def {
        doc /* Requirement type derived from ConcernC. */
        frame concern ConcernC;
    }

    requirement def RequirementC_Def {
        doc /* Requirement type for Feature C — add require constraint blocks as needed. */
    }
}

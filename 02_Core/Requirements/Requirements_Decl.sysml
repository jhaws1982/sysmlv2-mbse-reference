// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * RequirementsDecl — requirement usage declarations (architecture-bound).
 *
 * LEAF FILE.  Globally unique name "RequirementsDecl".
 * Assembled into  Core::Requirements  by the namespace hub.
 *
 * Derived requirements are expressed by nesting `requirement` usages inside
 * a parent requirement body.  There is no `derived` keyword in SysML v2 —
 * containment is the canonical mechanism for expressing derivation.
 *
 * The short name (<'A'>, <'A.1'>, etc.) is the requirement ID read by
 * the req_report.py tool via RequirementUsage.req_id / short_name.
 */
package RequirementsDecl {
    private import RequirementsDef::*;
    private import Core::Architecture::*;

    requirement <'A'> requirementA : RequirementA_Def {
        doc /* FeatureA must satisfy RequirementA. */
        subject featureA : FeatureA_Component;

        requirement <'A.1'> derivedA1 {
            doc /* FeatureA shall maintain a minimum throughput of
                   1000 operations per second under nominal load. */
        }
        requirement <'A.2'> derivedA2 {
            doc /* FeatureA shall expose a versioned external API
                   with documented backward-compatibility guarantees. */
        }
        requirement <'A.3'> derivedA3 {
            doc /* FeatureA shall recover from a fault condition
                   within 500 ms without operator intervention. */
        }
    }

    requirement <'B'> requirementB : RequirementB_Def {
        doc /* FeatureB must satisfy RequirementB. */
        subject featureB : FeatureB_Component;

        requirement <'B.1'> derivedB1 {
            doc /* FeatureB shall conform to the agreed protocol
                   standard on all external interfaces. */
        }
        requirement <'B.2'> derivedB2 {
            doc /* FeatureB shall log all interface transactions
                   with sufficient detail for audit replay. */
        }
    }

    requirement <'C'> requirementC : RequirementC_Def {
        doc /* FeatureC must satisfy RequirementC. */
        subject featureC : FeatureC_Component;
        // No derived requirements yet — gap intentional for matrix demos
    }
}

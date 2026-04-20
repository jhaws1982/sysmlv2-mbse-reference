// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * Traceability — verification usages.
 *
 * LEAF FILE.  Globally unique name "Traceability".
 *
 * Verification names here MUST match test names in CTest XML output.
 * The result_matrix.py tool joins on this name to produce the RTM.
 *
 * requirementC has no verification — intentional gap demo.
 */
package Traceability {
    private import Core::Architecture::*;
    private import Core::Requirements::*;

    verification testA {
        doc /* Verifies requirementA against FeatureA_Component. */
        subject featureA_Subject : FeatureA_Component;
        satisfy requirement requirementA;
    }

    verification testB {
        doc /* Verifies requirementB against FeatureB_Component. */
        subject featureB_Subject : FeatureB_Component;
        satisfy requirement requirementB;
    }

    // testC intentionally absent — requirementC has no verification
}

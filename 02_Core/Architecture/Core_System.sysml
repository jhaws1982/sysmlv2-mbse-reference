// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * CoreSystem — top-level structural assembly of the core system.
 *
 * LEAF FILE.  Globally unique name "CoreSystem".
 * Assembled into  Core::Architecture  by the namespace hub.
 */
package CoreSystem {
    private import FeatureA::*;
    private import FeatureB::*;
    private import FeatureC::*;

    part def Core_System {
        doc /* Top-level assembly composing the three feature components. */
        part featureA : FeatureA_Component;
        part featureB : FeatureB_Component;
        part featureC : FeatureC_Component;
    }
}

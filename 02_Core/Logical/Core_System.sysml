/**
 * CoreSystem — top-level core system assembly.
 * LEAF file. Re-exported as Core::Logical by 02_Core/_namespace.sysml.
 */
package CoreSystem {
    private import SharedData::*;
    private import FeatureA::*;
    private import FeatureB::*;
    private import FeatureC::*;

    part def CoreSystem_Assembly {
        doc /* Top-level assembly of the core CSCI. */
        part featureC : FeatureC_Component;
    }
}

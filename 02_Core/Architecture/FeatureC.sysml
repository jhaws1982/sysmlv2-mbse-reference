/**
 * FeatureC — core architecture component C.
 * LEAF file. Re-exported as Core::Architecture by 02_Core/_namespace.sysml.
 */
package FeatureC {
    private import SharedData::*;
    private import FeatureA::*;
    private import FeatureB::*;

    part def FeatureC_Component {
        doc /* Integration component — coordinates Feature A and Feature B. */
        attribute componentId : ScalarValues::String;
        part featureA : FeatureA_Component;
        part featureB : FeatureB_Component;
        interface connect featureA.dataOut to featureB.dataIn;
    }
}

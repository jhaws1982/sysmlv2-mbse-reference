/**
 * FeatureA — core architecture component A.
 * LEAF file. Re-exported as Core::Architecture by 02_Core/_namespace.sysml.
 */
package FeatureA {
    private import SharedData::*;

    part def FeatureA_Component {
        doc /* Primary processing component for Feature A. */
        attribute componentId  : ScalarValues::String;
        attribute nodeRole     : NodeRole;
        port dataIn  : ~FeatureA_Port;
        port dataOut :  FeatureA_Port;
    }

    port def FeatureA_Port {
        out item data : DataA;
    }
}

/**
 * FeatureB — core architecture component B.
 * LEAF file. Re-exported as Core::Logical by 02_Core/_namespace.sysml.
 */
package FeatureB {
    private import SharedData::*;

    part def FeatureB_Component {
        doc /* Secondary processing component for Feature B. */
        attribute componentId : ScalarValues::String;
        attribute protocol    : GenericProtocol;
        port dataIn  : ~FeatureB_Port;
        port dataOut :  FeatureB_Port;
    }

    port def FeatureB_Port {
        out item data : DataB;
    }
}

/**
 * FeatureB — part definition for Feature B.
 *
 * LEAF FILE.  Globally unique name "FeatureB".
 * Assembled into  Core::Architecture  by the namespace hub.
 */
package FeatureB {
    private import Shared::Data::*;

    port def FeatureB_InPort  { in item data : DataA; }
    port def FeatureB_OutPort { out item data : DataA; }

    part def FeatureB_Component {
        doc /* Feature B structural component. */
        port dataIn  : FeatureB_InPort;
        port dataOut : FeatureB_OutPort;
        attribute protocol : GenericProtocol;
    }
}

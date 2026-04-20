/**
 * FeatureA — part definition for Feature A.
 *
 * LEAF FILE.  Globally unique name "FeatureA".
 *
 * This package is assembled into the nested namespace  Core::Architecture
 * by  02_Core/Architecture/_namespace.sysml  via  public import FeatureA::*.
 * Consumers reach these definitions through:
 *     private import Core::Architecture::*;
 *
 * Port syntax note:
 *   Direction keywords (`in`, `out`) belong INSIDE the port definition body
 *   on item features — not on the port usage itself.
 *   `port in dataIn : DataA` is invalid SysML v2.
 */
package FeatureA {
    private import Shared::Data::*;

    port def FeatureA_InPort  { in item data : DataA; }
    port def FeatureA_OutPort { out item data : DataB; }

    part def FeatureA_Component {
        doc /* Feature A structural component. */
        port dataIn  : FeatureA_InPort;
        port dataOut : FeatureA_OutPort;
        attribute featureVariant : FeatureKind;
    }
}

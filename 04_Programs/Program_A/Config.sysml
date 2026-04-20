/**
 * Programs::ProgramA — Program A configuration.
 *
 * LEAF FILE.  Globally unique name "ProgramA".
 * Assembled into  Programs::ProgramA  by the namespace hub.
 */
package ProgramA {
    private import Configurations::*;
    private import Shared::Data::*;

    part def ProgramA_Config :> Base_Config {
        doc /* Program A is configured with Variant1 / Proto1. */
        attribute :>> featureAVariant  = FeatureKind::Variant1;
        attribute :>> featureBProtocol = GenericProtocol::Proto1;
    }
}

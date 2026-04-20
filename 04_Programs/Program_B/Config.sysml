/**
 * ProgramB — Program B configuration.
 *
 * LEAF FILE.  Globally unique name "ProgramB".
 * Assembled into  Programs::ProgramB  by the namespace hub.
 */
package ProgramB {
    private import Configurations::*;
    private import Shared::Data::*;

    part def ProgramB_Config :> Base_Config {
        doc /* Program B is configured with Variant2 / Proto2. */
        attribute :>> featureAVariant  = FeatureKind::Variant2;
        attribute :>> featureBProtocol = GenericProtocol::Proto2;
    }
}

/**
 * ProductLineConfigurations — variation points for the product line.
 * LEAF file. Standalone public package.
 */
package Configurations {
    private import SharedData::*;
    private import ScalarValues::*;

    abstract part def Base_Config {
        doc /* Abstract base configuration for all program variants. */
        attribute featureAVariant  : FeatureKind;
        attribute featureBProtocol : GenericProtocol;
    }
}

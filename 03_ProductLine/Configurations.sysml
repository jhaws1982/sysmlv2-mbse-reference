/**
 * Configurations — product-line variation point definitions.
 *
 * LEAF FILE.  Globally unique name "Configurations".
 *
 * `configuration def` is NOT a SysML v2 keyword.  Use `abstract part def`
 * with attribute specialization instead.
 *
 * For this single-package layer the leaf name doubles as the public name;
 * no separate hub file is needed.  Consumers write:
 *     private import Configurations::*;
 *
 * If you later want  ProductLine::Configurations::*  as the path, add a hub:
 *   package ProductLine {
 *       package Configurations { public import Configurations::*; }
 *   }
 * in a  03_ProductLine/_namespace.sysml  file.
 */
package Configurations {
    private import Shared::Data::*;

    abstract part def Base_Config {
        doc /* Abstract base configuration for all program variants. */
        attribute featureAVariant  : FeatureKind;
        attribute featureBProtocol : GenericProtocol;
    }
}

/**
 * Shared — namespace hub for the 00_Shared layer.
 *
 * ONE declaration of package Shared assembling all shared leaf packages.
 * Consumers write:
 *     private import Shared::Common::*;   // CommonDefinitions (LevelKind, RiskItem, etc.)
 *     private import Shared::Data::*;     // SharedData
 *     private import Shared::SRS::*;      // SRS_Definitions
 */
package Shared {

    package Common {
        public import CommonDefinitions::*;
    }

    package Data {
        public import SharedData::*;
    }

    package SRS {
        public import SRS_Definitions::*;
    }
}

/**
 * Shared — namespace hub for the 00_Shared layer.
 *
 * ONE declaration of package Shared assembling all shared leaf packages.
 * Consumers write:
 *     private import Shared::Data::*;
 *     private import Shared::SRS::*;
 */
package Shared {

    package Data {
        public import SharedData::*;
    }

    package SRS {
        public import SRS_Definitions::*;
    }
}

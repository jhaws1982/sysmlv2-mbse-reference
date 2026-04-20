/**
 * Verification — single namespace hub for ALL of  05_Verification.
 *
 * ONE declaration of  package Verification  assembling all three leaf packages.
 *
 * Consumers write:
 *     private import Verification::TestCases::*;
 *     private import Verification::Traceability::*;
 *     private import Verification::Results::*;
 */
package Verification {

    package TestCases {
        public import TestCases::*;
    }

    package Results {
        public import Results::*;
    }

    package Traceability {
        public import Traceability::*;
    }
}

/**
 * Verification — namespace hub for the 05_Verification layer.
 *
 * ONE declaration of package Verification assembling both leaf packages.
 *
 * Results.sysml has been removed. Live test results are not stored in the
 * model — they come from external sources (CTest JUnit XML, ATP documents,
 * etc.) and are joined against verification names by result_matrix.py.
 *
 * Consumers write:
 *     private import Verification::TestCases::*;
 *     private import Verification::Traceability::*;
 */
package Verification {

    package TestCases {
        public import TestCases::*;
    }

    package Traceability {
        public import Traceability::*;
    }
}

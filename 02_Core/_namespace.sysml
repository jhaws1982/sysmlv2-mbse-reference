/**
 * Core — namespace hub for the 02_Core layer.
 * ONE declaration of package Core assembling Architecture and Requirements.
 *
 * Consumers write:
 *     private import Core::Architecture::*;
 *     private import Core::Requirements::*;
 */
package Core {

    package Architecture {
        public import FeatureA::*;
        public import FeatureB::*;
        public import FeatureC::*;
        public import CoreSystem::*;
    }

    package Requirements {
        public import RequirementsDef::*;
        public import RequirementsDecl::*;
    }
}

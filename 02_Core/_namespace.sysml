/**
 * Core — namespace hub for the 02_Core layer.
 *
 * THE ONE AND ONLY declaration of package Core in the model.
 * Assembles all Core leaf packages. Architecture and Logical are unified
 * under Core::Logical — features (FeatureA/B/C, CoreSystem) and logical
 * subsystem definitions live side by side as separate leaf files under
 * 02_Core/Logical/.
 *
 * CONSUMER IMPORT PATHS
 * ─────────────────────
 *   private import Core::Logical::*;        // FeatureA/B/C, CoreSystem,
 *                                           // LogicalArchDefs, LogicalArchModel,
 *                                           // LogicalInterfaces
 *   private import Core::Behavior::*;       // StateMachines, ActionSequences
 *   private import Core::Context::*;        // SystemContext, OperationalConcept
 *   private import Core::UseCases::*;       // UseCaseDefs, UseCaseModel
 *   private import Core::Requirements::*;   // RequirementsDef, RequirementsDecl
 *   private import Core::Allocations::*;    // RequirementAllocations
 */
package Core {

    package Logical {
        // Feature components (physical/component architecture)
        public import FeatureA::*;
        public import FeatureB::*;
        public import FeatureC::*;
        public import CoreSystem::*;
        // Logical architecture (subsystem decomposition and interfaces)
        public import LogicalArchDefs::*;
        public import LogicalArchModel::*;
        public import LogicalInterfaces::*;
    }

    package Behavior {
        public import StateMachines::*;
        public import ActionSequences::*;
    }

    package Context {
        public import SystemContext::*;
        public import OperationalConcept::*;
    }

    package UseCases {
        public import UseCaseDefs::*;
        public import UseCaseModel::*;
    }

    package Requirements {
        public import RequirementsDef::*;
        public import RequirementsDecl::*;
    }

    package Allocations {
        public import RequirementAllocations::*;
    }
}

// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * Core — single consolidated namespace hub for ALL of 02_Core.
 *
 * ONE package Core declaration covers both Architecture and Requirements.
 * SysIDE warns about global-namespace-distinguishability when the same
 * package name appears in multiple files — this single-file pattern avoids
 * that entirely.
 *
 * Leaf files remain unchanged (FeatureA.sysml, Requirements_Def.sysml, etc.).
 * Consumers import via:
 *   private import Core::Architecture::*;   ← FeatureA_Component, etc.
 *   private import Core::Requirements::*;   ← RequirementA_Def, etc.
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

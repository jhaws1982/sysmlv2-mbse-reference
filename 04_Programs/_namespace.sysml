/**
 * Programs — single namespace hub for ALL of 04_Programs.
 *
 * THE ONE AND ONLY declaration of package Programs in the model.
 *
 * Each program sub-package assembles:
 *   Config           — product line variant selection (which features/protocols)
 *   Stakeholders     — program-specific stakeholder defs and concerns
 *   Architecture     — logical system definition (system.sysml) and
 *                      operational deployment context (deployment.sysml)
 *   Requirements     — program-specific requirement defs and declarations
 *   Verification     — program-specific verification cases
 *
 * CONSUMER IMPORT PATHS
 * ─────────────────────
 *   private import Programs::ProgramA::*;   // all Program A elements
 *   private import ProgramA_System::*;      // Program A system def (direct leaf import)
 *   private import ProgramA_Deployment::*;  // Program A deployment (direct leaf import)
 */
package Programs {

    package ProgramA {
        public import ProgramA::*;
        public import ProgramA_StakeholderDefs::*;
        public import ProgramA_StakeholderConcerns::*;
        public import ProgramA_System::*;
        public import ProgramA_Deployment::*;
        public import ProgramA_Requirements::*;
        public import ProgramA_Verification::*;
    }

    package ProgramB {
        public import ProgramB::*;
        public import ProgramB_StakeholderDefs::*;
        public import ProgramB_StakeholderConcerns::*;
        public import ProgramB_System::*;
        public import ProgramB_Deployment::*;
        public import ProgramB_Requirements::*;
        public import ProgramB_Verification::*;
    }
}

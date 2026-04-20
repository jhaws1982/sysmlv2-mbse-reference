/**
 * Programs — single namespace hub for ALL of  04_Programs.
 */
package Programs {

    package ProgramA {
        public import ProgramA::*;
        public import ProgramA_StakeholderDefs::*;
        public import ProgramA_StakeholderConcerns::*;
        public import ProgramA_Deployment::*;
        public import ProgramA_Requirements::*;
        public import ProgramA_Verification::*;
    }

    package ProgramB {
        public import ProgramB::*;
        public import ProgramB_StakeholderDefs::*;
        public import ProgramB_StakeholderConcerns::*;
        public import ProgramB_Deployment::*;
        public import ProgramB_Requirements::*;
        public import ProgramB_Verification::*;
    }
}

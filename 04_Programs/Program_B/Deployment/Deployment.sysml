/**
 * ProgramB_Deployment — Program B deployed system assembly.
 *
 * LEAF FILE.  Globally unique name "ProgramB_Deployment".
 * Assembled into  Programs::ProgramB  by the namespace hub.
 */
package ProgramB_Deployment {
    private import Core::Architecture::*;
    private import ProgramB::*;

    part def ProgramB_System {
        doc /* Top-level deployed system for Program B. */
        part core   : Core_System;
        part config : ProgramB_Config;
    }
}

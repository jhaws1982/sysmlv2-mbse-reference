/**
 * ProgramA_Deployment — Program A deployed system assembly.
 *
 * LEAF FILE.  Globally unique name "ProgramA_Deployment".
 * Assembled into  Programs::ProgramA  by the namespace hub.
 */
package ProgramA_Deployment {
    private import Core::Architecture::*;
    private import ProgramA::*;

    part def ProgramA_System {
        doc /* Top-level deployed system for Program A. */
        part core   : Core_System;
        part config : ProgramA_Config;
    }
}

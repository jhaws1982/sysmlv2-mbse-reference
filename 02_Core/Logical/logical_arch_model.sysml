/**
 * LogicalArchModel — assembled logical architecture.
 *
 * LEAF FILE. Globally unique name "LogicalArchModel".
 * Assembled into Core::Logical by 02_Core/_namespace.sysml.
 *
 * Composes LogicalArchDefs subsystems with perform links that assign
 * behaviors to structural elements. Changes with architecture decisions.
 *
 * The logical subsystems map to physical components:
 *   DataIngestionSubsystem  ← FeatureA_Component
 *   DataProcessingSubsystem ← FeatureB_Component + FeatureC_Component
 *   SystemManagementSubsystem ← CoreSystem_Assembly (management plane)
 */
package LogicalArchModel {
    private import LogicalArchDefs::*;
    private import CoreSystem::*;
    private import FeatureA::*;
    private import FeatureB::*;
    private import FeatureC::*;

    part def CoreLogicalArchitecture {
        doc /* Top-level logical decomposition of the core CSCI into its three
               primary subsystems. Each subsystem is independently allocatable
               to a physical component in a program-specific deployment. */

        part ingestion  : DataIngestionSubsystem {
            perform action ingest   : IngestMessage;
        }

        part processing : DataProcessingSubsystem {
            perform action process  : ProcessMessage;
        }

        part management : SystemManagementSubsystem {
            perform action selfTest : ExecuteSelfTest;
            perform action applyConfig : ApplyConfiguration;
        }
    }

    // Top-level logical architecture instance
    part coreLogicalArch : CoreLogicalArchitecture;
}

/**
 * LogicalArchDefs — logical subsystem type definitions.
 *
 * LEAF FILE. Globally unique name "LogicalArchDefs".
 * Assembled into Core::Logical by 02_Core/_namespace.sysml.
 *
 * Defines the logical decomposition of the core CSCI into subsystems.
 * These are stable types — changes only when the logical architecture
 * changes. Assembled model with part usages and perform links lives in
 * logical_arch_model.sysml.
 *
 * SysIDE rule: action defs must be at package level, never nested inside
 * part defs.
 */
package LogicalArchDefs {
    private import SharedData::*;
    private import ScalarValues::*;

    // ── Logical Subsystem Definitions ─────────────────────────────────────

    part def DataIngestionSubsystem {
        doc /* Receives and validates inbound data messages from external
               sources. Implements the ICD-EXT-001 protocol decode and
               forwards validated messages to the processing pipeline.
               Corresponds to the FeatureA component in the physical architecture. */
    }

    part def DataProcessingSubsystem {
        doc /* Applies protocol processing, transformation, and integration
               to validated inbound messages. Coordinates Feature A output
               with Feature B processing to produce integrated results.
               Corresponds to the FeatureB and FeatureC components. */
    }

    part def SystemManagementSubsystem {
        doc /* Provides runtime configuration management, built-in self-test
               execution, health monitoring, and administrative interface.
               Supports all maintenance and diagnostic use cases. */
    }

    // ── Action Definitions (package level — never nested in part defs) ─────

    action def IngestMessage {
        doc /* Receives one inbound message from ExternalDataSource,
               validates the frame structure, and queues for processing. */
        in  item rawMessage  : DataA;
        out item validMessage : DataA;
    }

    action def ProcessMessage {
        doc /* Applies protocol processing and transformation to a validated
               inbound message and produces an integrated output record. */
        in  item validMessage  : DataA;
        out item processedData : DataB;
    }

    action def ExecuteSelfTest {
        doc /* Executes the built-in self-test suite against all subsystem
               interfaces and returns an overall health status. */
        out attribute testPassed : ScalarValues::Boolean;
    }

    action def ApplyConfiguration {
        doc /* Validates and applies a new configuration parameter set
               without interrupting active data processing. */
        in  attribute configPayload : ScalarValues::String;
        out attribute applied       : ScalarValues::Boolean;
    }
}

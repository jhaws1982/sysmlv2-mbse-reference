/**
 * ActionSequences — action sequence flow definitions.
 *
 * LEAF FILE. Globally unique name "ActionSequences".
 * Assembled into Core::Behavior by 02_Core/_namespace.sysml.
 *
 * Defines the primary operational workflows using first/then ordering.
 * Pattern B: the action tree owns the sequence; parts perform sub-actions
 * via perform links in logical_arch_model.sysml.
 */
package ActionSequences {
    private import LogicalArchDefs::*;

    // ── Message Processing Flow ────────────────────────────────────────────

    action def MessageProcessingFlow {
        doc /* End-to-end flow for a single inbound message: ingestion,
               validation, processing, and output. This is the primary
               operational loop executed continuously during the operational
               state of CoreCSCI_Lifecycle.
             */
        action ingest   : IngestMessage;
        action process  : ProcessMessage;

        first start;
        then ingest;
        then process;
        then done;
    }

    // ── Initialization Flow ────────────────────────────────────────────────

    action def InitializationFlow {
        doc /* Startup sequence: execute self-test then apply stored configuration.
               Transitions the system from initializing to operational state
               if both steps succeed.
             */
        action selfTest   : ExecuteSelfTest;
        action applyConfig : ApplyConfiguration;

        first start;
        then selfTest;
        then applyConfig;
        then done;
    }

    // ── Configuration Update Flow ─────────────────────────────────────────

    action def ConfigurationUpdateFlow {
        doc /* Online configuration update sequence.
               Validates, applies, and confirms a configuration change
               without interrupting active message processing.
             */
        action applyConfig : ApplyConfiguration;

        first start;
        then applyConfig;
        then done;
    }
}

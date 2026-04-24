/**
 * UseCaseDefs — core system use case type definitions.
 *
 * LEAF FILE. Globally unique name "UseCaseDefs".
 * Assembled into Core::UseCases by 02_Core/_namespace.sysml.
 *
 * Stable types — changes only when new system capabilities are identified.
 * Assembled use case model with usages and include relationships:
 *   → 02_Core/UseCases/use_case_model.sysml
 */
package UseCaseDefs {
    private import SystemContext::*;

    use case def SystemUseCaseDef {
        doc /* Base use case type for all CoreCSCI use cases. */
        subject sys : CoreCSCI;
    }

    use case def UC_InboundDataProcessing :> SystemUseCaseDef {
        doc /* Core operational use case: ingest, parse, and process inbound
               data messages from ExternalDataSource within the latency budget.
               Initiated continuously while the system is in operational mode. */
    }

    use case def UC_SystemInitialization :> SystemUseCaseDef {
        doc /* Sequence from system start through readiness for operational use.
               Includes configuration load and built-in self-test execution.
               Operator is notified when system declares ready. */
    }

    use case def UC_ConfigurationUpdate :> SystemUseCaseDef {
        doc /* Administrator applies runtime configuration changes without
               system restart. System validates, applies, and confirms
               the new configuration before returning to operational mode. */
    }

    use case def UC_FaultResponseAndRecovery :> SystemUseCaseDef {
        doc /* System detects a fault condition, transitions to a safe or
               degraded operating state, notifies the operator, and either
               recovers automatically or awaits administrator intervention. */
    }
}

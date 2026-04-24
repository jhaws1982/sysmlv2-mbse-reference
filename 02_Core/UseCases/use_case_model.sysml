/**
 * UseCaseModel — assembled core system use case model.
 *
 * LEAF FILE. Globally unique name "UseCaseModel".
 * Assembled into Core::UseCases by 02_Core/_namespace.sysml.
 *
 * Contains use case usages, include relationships, and actor assignments.
 * Primary source for Use Case Catalog (SN-03) and traceability (SN-06).
 */
package UseCaseModel {
    private import UseCaseDefs::*;
    private import StakeholderDefs::*;
    private import StakeholderConcerns::*;
    private import SystemContext::*;

    use case inboundDataProcessing : UC_InboundDataProcessing {
        doc /* Continuously processes inbound data from ExternalDataSource.
               Initiated automatically while system is operational. */
        subject sys : CoreCSCI;
        // frames Concern_ProcessingLatency and Concern_SystemAvailability
    }

    use case systemInitialization : UC_SystemInitialization {
        doc /* System start sequence: load config, execute BIT, declare ready.
               Operator is notified at completion. */
        subject sys : CoreCSCI;
        include use case builtInSelfTest;
    }

    use case builtInSelfTest : SystemUseCaseDef {
        doc /* Built-in self-test executed during initialization and on demand.
               Verifies all subsystem interfaces before declaring readiness.
               Included by systemInitialization; may also be triggered manually. */
        subject sys : CoreCSCI;
    }

    use case configurationUpdate : UC_ConfigurationUpdate {
        doc /* Administrator applies runtime configuration parameter update.
               System validates new values, applies without restart, and
               confirms success to the administrator. */
        subject sys : CoreCSCI;
    }

    use case faultResponseAndRecovery : UC_FaultResponseAndRecovery {
        doc /* System detects internal fault, transitions to degraded or safe
               state, notifies operator, and attempts recovery. If recovery
               fails, administrator is escalated. */
        subject sys : CoreCSCI;
    }
}

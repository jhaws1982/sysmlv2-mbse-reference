/**
 * StateMachines — state machine definitions for logical subsystems.
 *
 * LEAF FILE. Globally unique name "StateMachines".
 * Assembled into Core::Behavior by 02_Core/_namespace.sysml.
 *
 * Primary source for Behavioral Summary (LA-04).
 */
package StateMachines {
    private import LogicalArchDefs::*;

    // ── Core CSCI Lifecycle State Machine ─────────────────────────────────

    state def CoreCSCI_Lifecycle {
        doc /* Governs the operational lifecycle of the core CSCI from
               startup through steady-state operation to shutdown.
             */
        entry; then initializing;

        state initializing {
            doc /* Executing startup sequence: load configuration and run
                   built-in self-test before declaring operational readiness. */
            entry action runBIT : ExecuteSelfTest;
        }

        state operational {
            doc /* Steady-state: continuously processing inbound messages
                   within the latency and throughput requirements. */
            do action processMsg : ProcessMessage;
        }

        state degraded {
            doc /* One or more non-critical subsystems have faulted.
                   Processing continues at reduced capacity. Operator notified. */
        }

        state administrativeMode {
            doc /* System has suspended operational processing to accept
                   configuration updates from the system administrator. */
            do action applyConfig : ApplyConfiguration;
        }

        transition initializing_to_operational
            first initializing then operational;

        transition operational_to_degraded
            first operational then degraded;

        transition degraded_to_operational
            first degraded then operational;

        transition operational_to_admin
            first operational then administrativeMode;

        transition admin_to_operational
            first administrativeMode then operational;
    }

    // ── System Management Subsystem State Machine ─────────────────────────

    state def SystemManagement_Lifecycle {
        doc /* Controls the SystemManagementSubsystem: monitors system health
               continuously and responds to detected fault conditions.
             */
        entry; then monitoring;

        state monitoring {
            doc /* Continuously polling all subsystem health reporters. */
            do action runBIT : ExecuteSelfTest;
        }

        state faultDetected {
            doc /* A fault condition has been identified. Correlating fault
                   data to isolate root cause before escalating. */
        }

        state alertingOperator {
            doc /* Root cause identified. Notifying operator and awaiting
                   acknowledgement before switching to degraded mode. */
        }

        transition monitoring_to_faultDetected
            first monitoring then faultDetected;

        transition faultDetected_to_monitoring
            first faultDetected then monitoring;

        transition faultDetected_to_alerting
            first faultDetected then alertingOperator;

        transition alerting_to_monitoring
            first alertingOperator then monitoring;
    }
}

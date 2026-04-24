/**
 * StakeholderConcerns — stakeholder concern definitions.
 *
 * LEAF FILE. Globally unique name "StakeholderConcerns".
 * Assembled into Stakeholders::Concerns by 01_Stakeholders/_namespace.sysml.
 *
 * SysIDE rules:
 *   - `subject` must be FIRST in every concern def body.
 *   - Use `actor` (not `stakeholder`) for the role membership.
 *
 * These concerns drive requirements via `frame concern` in requirement defs.
 * A concern with no framing requirement is a traceability gap.
 */
package StakeholderConcerns {
    private import StakeholderDefs::*;
    private import SystemContext::*;

    // ── PrimaryOperator concerns ──────────────────────────────────────────

    concern def Concern_ProcessingLatency {
        subject sys : CoreCSCI;                        // subject FIRST
        actor op : PrimaryOperator;
        doc /* The operator requires that all inbound data streams are processed
               within a time bound that does not impede operational tempo.
               Delayed processing causes downstream stalls and missed deadlines. */
    }

    concern def Concern_SystemAvailability {
        subject sys : CoreCSCI;
        actor op : PrimaryOperator;
        doc /* The operator requires the system to be available throughout all
               scheduled operational windows without unplanned interruption.
               Downtime directly reduces mission throughput. */
    }

    // ── SystemAdministratorRole concerns ──────────────────────────────────

    concern def Concern_Configurability {
        subject sys : CoreCSCI;
        actor admin : SystemAdministratorRole;
        doc /* The administrator requires the ability to apply configuration
               changes at runtime without restarting the system or modifying
               source code. */
    }

    // ── SystemsEngineerRole concerns ──────────────────────────────────────

    concern def Concern_InterfaceConformance {
        subject sys : CoreCSCI;
        actor eng : SystemsEngineerRole;
        doc /* The systems engineer requires all external interfaces to conform
               precisely to published ICDs so that integration with external
               systems can proceed without coordination during implementation. */
    }

    concern def Concern_Testability {
        subject sys : CoreCSCI;
        actor eng : SystemsEngineerRole;
        doc /* The systems engineer requires all requirements to be verifiable
               by an approved method so that acceptance testing can produce
               objective evidence of compliance. */
    }
}

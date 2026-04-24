/**
 * OperationalConcept — missions and operational scenarios.
 *
 * LEAF FILE. Globally unique name "OperationalConcept".
 * Assembled into Core::Context by 02_Core/_namespace.sysml.
 *
 * Problem-space description only — no architecture decisions here.
 * doc blocks drive the OpsCon report (SN-04).
 */
package OperationalConcept {
    private import SystemContext::*;

    part def OperationalConceptSummary {
        doc /* The core CSCI operates in a data-intensive distributed environment
               processing real-time inbound data streams from external sources.
               It serves a community of operational users who require low-latency
               responses and high availability across planned maintenance windows.
               The CSCI is deployed in two program variants (Program A, Program B)
               each with distinct performance profiles and regulatory contexts.
               Key operational constraints: sub-50ms processing latency, 99.5%
               availability, and strict conformance to ICD-EXT-001.
             */
    }

    // ── Missions ──────────────────────────────────────────────────────────

    part def Mission_ContinuousDataProcessing {
        doc /* Primary mission: continuously ingest and process data streams
               from ExternalDataSource within the defined latency budget.
               Success criteria: zero message loss, latency <= 50ms at p99,
               availability >= 99.5% over any 30-day window.
             */
    }

    part def Mission_SystemAdministration {
        doc /* Sustainment mission: allow qualified system administrators to
               configure, update, and diagnose the CSCI without source code
               modification or vendor support for routine operations.
             */
    }

    // ── Operational Scenarios ─────────────────────────────────────────────

    part def Scenario_NominalOperation {
        doc /* Precondition: system initialized, all subsystems healthy.
               Trigger: ExternalDataSource begins streaming inbound messages.
               System response: FeatureA ingests and parses each message,
               FeatureB applies protocol processing, FeatureC integrates
               the output and makes it available downstream.
               Postcondition: all messages processed within latency budget,
               operator dashboard shows healthy status.
             */
        part system : CoreCSCI;
        part operatorRef  : Operator;
    }

    part def Scenario_DegradedOperation {
        doc /* Precondition: one non-safety-critical subsystem has failed.
               Trigger: internal health monitor detects degraded state.
               System response: switches to degraded operating mode,
               notifies operator, continues processing at reduced capacity.
               Postcondition: operator acknowledges, maintenance scheduled.
             */
        part system : CoreCSCI;
    }

    part def Scenario_ConfigurationUpdate {
        doc /* Precondition: system in administrative mode, operator logged out.
               Trigger: system administrator initiates configuration update.
               System response: validates new parameters, applies without restart,
               confirms successful application to administrator.
               Postcondition: system returns to operational mode with new config.
             */
        part system : CoreCSCI;
        part admin  : SystemAdministrator;
    }
}

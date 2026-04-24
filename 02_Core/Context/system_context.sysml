/**
 * SystemContext — system boundary and external actors.
 *
 * LEAF FILE. Globally unique name "SystemContext".
 * Assembled into Core::Context by 02_Core/_namespace.sysml.
 *
 * Defines the black-box view of the core CSCI: the system itself,
 * the actors that interact with it, and external systems at the boundary.
 * This is the primary source for OpsCon (SN-04) and the system context
 * section of the SRS (SR-01).
 *
 * Rule: do NOT decompose MySystem here — decomposition lives in
 * 02_Core/Logical/logical_arch_model.sysml.
 */
package SystemContext {

    // ── System Under Development (black box) ─────────────────────────────

    part def CoreCSCI {
        doc /* The core CSCI — a software-intensive system providing real-time
               data processing, integration of Feature A and Feature B, and
               an external data interface conforming to ICD-EXT-001.
               Deployed across multiple program variants (Program A, Program B).
             */
    }

    // ── External Actors ───────────────────────────────────────────────────

    part def Operator {
        doc /* Primary operational user. Initiates processing commands, monitors
               system outputs, and responds to system status notifications
               during normal operations. */
    }

    part def SystemAdministrator {
        doc /* Responsible for system installation, configuration, and routine
               maintenance. Operates the administrative interface to adjust
               runtime parameters without modifying source code. */
    }

    // ── External Systems ──────────────────────────────────────────────────

    part def ExternalDataSource {
        doc /* External data producer. Sends binary framed messages conforming
               to ICD-EXT-001 to the core CSCI input port. Owned by an
               independent team; protocol cannot be modified by this program. */
    }

    // ── Context Assembly ──────────────────────────────────────────────────

    part def CoreSystemContextAssembly {
        doc /* Operational context placing the core CSCI alongside its external
               actors and systems. Defines the system boundary for requirements
               and use case analysis. */
        part system      : CoreCSCI;
        part operator    : Operator;
        part admin       : SystemAdministrator;
        part dataSource  : ExternalDataSource;
    }
}

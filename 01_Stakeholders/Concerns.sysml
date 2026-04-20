/**
 * StakeholderConcerns — stakeholder concern definitions.
 *
 * LEAF FILE.  Globally unique name "StakeholderConcerns".
 * Assembled into  Stakeholders::Concerns  by  01_Stakeholders/_namespace.sysml.
 *
 * This file EVOLVES — concerns grow as you discover what each stakeholder
 * actually needs from the system.  It is the direct input to requirement
 * definitions via  `frame concern`.  Keep it in sync with your requirements
 * Def file; a concern with no framing requirement is a gap worth tracking.
 *
 * SysIDE notes:
 *   - `subject` must be the first parameter in a concern def body.
 *   - `stakeholder` membership inside a concern def causes usage-feature-typing
 *     warnings because `stakeholder def` does not produce a Classifier.
 *     Use `actor` instead — it is accepted at this position and is semantically
 *     equivalent for linking a concern to a role.
 *   - Stakeholder roles are defined as `part def` in Stakeholders.sysml.
 */
package StakeholderConcerns {
    private import StakeholderDefs::*;

    // ── Concerns owned by StakeholderA ────────────────────────────────────

    concern def ConcernA {
        doc /* <Describe the need here — e.g. "StakeholderA requires that
               the system processes requests reliably under nominal load."> */
        subject sys;
        actor stakeholderA : StakeholderA;
    }

    concern def ConcernB {
        doc /* <Describe the need here — e.g. "StakeholderA requires that
               the system exposes a consistent and documented external API."> */
        subject sys;
        actor stakeholderA : StakeholderA;
    }

    // ── Concerns owned by StakeholderB ────────────────────────────────────

    concern def ConcernC {
        doc /* <Describe the need here — e.g. "StakeholderB requires that
               all external interfaces conform to the agreed protocol standard."> */
        subject sys;
        actor stakeholderB : StakeholderB;
    }
}

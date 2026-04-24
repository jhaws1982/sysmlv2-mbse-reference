// Package: CommonDefinitions <CMNDEF>
// Description:
// Reusable library package providing common definitions for stakeholders,
// program management, networking, and risk tracking across all programs
// in the model. Import via:
//
//   private import CommonDefinitions::*;
//
// Or selectively:
//   private import CommonDefinitions::LevelKind;
//   private import CommonDefinitions::RiskItem;
//
// ── Risk tracking design pattern ────────────────────────────────────────────
//
// RiskItem is a metadata def. Apply it with @ to any model element that
// carries a risk — a requirement, a part def, a use case, a verification
// case, or any other element. The annotated element IS the context; the
// @RiskItem annotation IS the risk entry. The model as a whole becomes the
// risk register — there is no separate container to maintain.
//
// Usage (annotate any model element):
//
//   @RiskItem {
//       riskId      = "RISK-PA-001";
//       title       = "Key developer attrition";
//       category    = RiskCategory::Schedule;
//       probability = LevelKind::Medium;
//       impact      = LevelKind::High;
//       status      = RiskStatus::Open;
//       description = "Loss of the lead integration engineer before CDR
//                      would delay integration by 4-6 weeks.";
//       mitigation  = "Cross-train two engineers on integration procedures
//                      by end of Q2.";
//       contingency = "Activate reserve contractor from approved vendor list.";
//       owner       = "Engineering Lead";
//   }
//   requirement <'PA-CAP-001'> programA_ThroughputReq : ProgramA_ThroughputReq_Def {
//       ...
//   }
//
// SysIDE Automator query pattern:
//
//   for element in all_elements:
//       for meta in element.metadata.collect():
//           if meta.metadata_definition.declared_name == "RiskItem":
//               risk_id  = get_attr(meta, "riskId")
//               status   = get_attr(meta, "status")
//               exposure = get_attr(meta, "exposure")
//               # element is what the risk is attached to (req, part, etc.)
//
// Validation (enforced by risk_report.py, not by assert constraints):
//   - riskId must be non-empty
//   - title must be non-empty
//   - description must be non-empty
//   - Open or Mitigated risks must have a non-empty mitigation statement
//   - exposure = probability * impact (1=Low×Low … 9=High×High)
//     Scores 6–9 red, 3–5 yellow, 1–2 green
//
// ────────────────────────────────────────────────────────────────────────────

library package <CMNDEF> CommonDefinitions {
  private import ScalarValues::*;

  // ══════════════════════════════════════════════════════════════════════
  // SHARED ENUMERATIONS
  // Defined first so they are available to all defs in this package.
  // ══════════════════════════════════════════════════════════════════════

  // ----------------------------------------------------------------------
  // LevelKind — ordered severity/priority scale
  //
  // Specializes ScalarValues::Integer so that enum literals carry a
  // numeric value. This enables derived calculations such as:
  //   priority = probability * impact
  // Low=1, Medium=2, High=3 are the three operational levels.
  // Undefined=0 is the sentinel for "not yet assessed".
  // ----------------------------------------------------------------------
  enum def LevelKind :> ScalarValues::Integer {
    doc
    /* Ordered level scale used for risk, effort, priority, and similar
     * ordinal attributes. Integer values enable numeric computations
     * (e.g. risk exposure = probability * impact).
     */
    Undefined = 0; // not yet assessed — treat as a completeness gap
    Low       = 1;
    Medium    = 2;
    High      = 3;
  }

  // ----------------------------------------------------------------------
  // StakeholderCategoryKind — role classification for stakeholders
  // ----------------------------------------------------------------------
  enum def StakeholderCategoryKind {
    doc
    /* Classifies the role or relationship of a stakeholder to the system.
     * A stakeholder may hold more than one category (multiplicity [1..*]
     * on the attribute in CommonStakeholder).
     */
    Expert;          // subject matter expert providing technical input
    RequirementOwner; // accountable for one or more requirement sets
    User;            // end user of the delivered system
    Customer;        // acquirer or sponsor funding the effort
    Internal;        // within the same organization as the developer
    External;        // outside the developing organization
    Governing;       // regulatory or oversight authority
  }

  // ----------------------------------------------------------------------
  // RiskCategory — the domain in which the risk originates
  // ----------------------------------------------------------------------
  enum def RiskCategory {
    doc
    /* Classifies the primary domain of a risk item. A risk may be
     * recategorized as understanding improves; the category informs
     * which team owns the mitigation action.
     */
    Technical;    // architecture, design, integration, or technology maturity
    Schedule;     // delivery timeline and milestone achievement
    Cost;         // budget, resource availability, or procurement
    Safety;       // hazards to personnel, property, or the environment
    Security;     // cyber, physical, or information security threats
    External;     // dependencies outside the program's control (supply chain, regulation)
    Programmatic; // staffing, organizational, contractual, or management risks
  }

  // ----------------------------------------------------------------------
  // RiskStatus — lifecycle state of a risk item
  // ----------------------------------------------------------------------
  enum def RiskStatus {
    doc
    /* Tracks the current lifecycle state of a risk item.
     * Open      — identified, not yet mitigated or closed.
     * Mitigated — mitigation action in place; residual exposure monitored.
     * Accepted  — risk accepted by the program; no further action planned.
     * Closed    — risk no longer applicable (threat passed, condition resolved).
     * Realized  — risk has materialized and become an issue; track in issue log.
     */
    Open;
    Mitigated;
    Accepted;
    Closed;
    Realized;
  }

  // ══════════════════════════════════════════════════════════════════════
  // STAKEHOLDER DEFINITIONS
  // ══════════════════════════════════════════════════════════════════════

  // ----------------------------------------------------------------------
  // CommonStakeholder — base definition for all stakeholder roles
  //
  // Captures stakeholder identity, category, and a simple engagement
  // priority score derived from the risk × effort product.
  //
  // Usage in a program model:
  //   part systemOwner : CommonStakeholder {
  //       attribute :>> name   = "System Owner";
  //       attribute :>> type   = StakeholderCategoryKind::Customer;
  //       attribute :>> risk   = LevelKind::High;
  //       attribute :>> effort = LevelKind::Medium;
  //   }
  // ----------------------------------------------------------------------
  part def CommonStakeholder {
    doc
    /* Base stakeholder definition. Specialize this for program-specific
     * stakeholder roles, or use directly for simple cases.
     */

    attribute name   : ScalarValues::String;
    attribute type   : StakeholderCategoryKind [1..*];

    // Engagement assessment — how important and how hard to engage
    attribute risk   : LevelKind; // consequence if this stakeholder is not engaged
    attribute effort : LevelKind; // effort required to engage this stakeholder

    // Derived engagement priority: higher score = higher engagement priority.
    // LevelKind :> Integer so the multiplication is valid.
    attribute priority : ScalarValues::Integer = risk * effort;
  }

  // ----------------------------------------------------------------------
  // CommonProgramManager — program manager as a specialized stakeholder
  //
  // Adds the list of programs this person manages. A PM may manage
  // multiple programs simultaneously ([1..*] multiplicity).
  // ----------------------------------------------------------------------
  part def CommonProgramManager :> CommonStakeholder {
    doc
    /* Program manager: a stakeholder who is accountable for one or more
     * programs. Inherits all CommonStakeholder attributes.
     */

    attribute program : ScalarValues::String [1..*];
  }

  // ══════════════════════════════════════════════════════════════════════
  // RISK TRACKING — METADATA DEFINITION
  //
  // RiskItem is a metadata def. It is applied with @ to any model element
  // that carries a risk. The model as a whole is the risk register.
  // RiskRegister (part def container) is intentionally omitted — it is
  // not needed because tools traverse @RiskItem annotations directly.
  //
  // Validation rules (enforced by risk_report.py, not assert constraints,
  // because metadata def bodies do not support assert constraint):
  //   INVALID  riskId is empty
  //   INVALID  title is empty
  //   INVALID  description is empty
  //   INVALID  Open or Mitigated status with empty mitigation statement
  //   WARNING  probability or impact is LevelKind::Undefined
  //   WARNING  owner is not set
  //   WARNING  contingency is not set for High-exposure risks (score >= 6)
  // ══════════════════════════════════════════════════════════════════════

  // ----------------------------------------------------------------------
  // RiskItem — metadata def for annotating model elements with a risk
  // ----------------------------------------------------------------------
  metadata def RiskItem {
    doc
    /* Applied with @ to any model element (requirement, part def, use case,
     * verification case, etc.) that is associated with a program risk.
     * The annotated element provides the context; the annotation provides
     * the risk details.
     *
     * The exposure attribute (probability * impact, range 1–9) is set by
     * the author and verified by risk_report.py:
     *   1–2  green  (low exposure)
     *   3–5  yellow (moderate exposure)
     *   6–9  red    (high exposure — contingency strongly recommended)
     */

    // Identity
    attribute riskId    : ScalarValues::String;       // program-unique ID, e.g. RISK-PA-001
    attribute title     : ScalarValues::String;       // one-line descriptive title
    attribute category  : RiskCategory;
    attribute status    : RiskStatus = RiskStatus::Open;

    // Assessment
    attribute probability : LevelKind = LevelKind::Undefined; // likelihood of occurrence
    attribute impact      : LevelKind = LevelKind::Undefined; // severity if risk occurs
    attribute exposure    : ScalarValues::Integer;   // set to probability * impact (1–9)

    // Narrative
    attribute description : ScalarValues::String;           // full risk description
    attribute mitigation  : ScalarValues::String;           // planned or active mitigation
    attribute contingency : ScalarValues::String [0..1];    // fallback if mitigation fails
    attribute owner       : ScalarValues::String [0..1];    // person/team accountable
  }
}

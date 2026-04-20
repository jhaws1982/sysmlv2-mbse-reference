/**
 * Stakeholders — namespace hub for the 01_Stakeholders layer.
 *
 * THE ONE AND ONLY declaration of  package Stakeholders  in the model.
 * Replaces both the old placeholder _namespace.sysml and the old combined
 * Stakeholders_and_Concerns.sysml — delete that file if it still exists.
 *
 * LEAF FILES ASSEMBLED HERE
 * ─────────────────────────
 *   Stakeholders.sysml  →  package StakeholderDefs     { stakeholder def ... }
 *   Concerns.sysml      →  package StakeholderConcerns { concern def ...     }
 *
 * CONSUMER IMPORT PATHS
 * ─────────────────────
 *   private import Stakeholders::Roles::*;      // StakeholderA, StakeholderB
 *   private import Stakeholders::Concerns::*;   // ConcernA, ConcernB, ConcernC
 *
 * WHY TWO SUB-PACKAGES INSTEAD OF ONE FLAT IMPORT?
 * ─────────────────────────────────────────────────
 * Splitting into Roles and Concerns lets consumers be precise about what they
 * actually depend on:
 *
 *   - RequirementsDef imports Stakeholders::Concerns::* only.
 *     It does not need to know about stakeholder role definitions.
 *
 *   - A viewpoint or stakeholder analysis imports Stakeholders::Roles::* only.
 *     It does not care about the concerns.
 *
 *   - Anything that needs both writes two explicit imports, making the
 *     dependency visible in the model.
 *
 * The `public import` here is intentional — it re-exports the leaf package
 * members so that consumers see them through the nested path.
 * All other imports in the model are `private import`.
 */
package Stakeholders {

    package Roles {
        public import StakeholderDefs::*;
    }

    package Concerns {
        public import StakeholderConcerns::*;
    }
}

/**
 * Generic_Model — top-level index package.
 *
 * Entry point for tools that require a single root package.
 * No element definitions live here — imports only.
 *
 * For the full file map, layer descriptions, import rules, and authoring
 * conventions see MODEL_STRUCTURE.md in the repository root.
 */
package Generic_Model {
    private import Shared::Common::*;
    private import Shared::Data::*;
    private import Shared::SRS::*;
    private import Stakeholders::Roles::*;
    private import Stakeholders::Concerns::*;
    private import Core::Context::*;
    private import Core::UseCases::*;
    private import Core::Logical::*;
    private import Core::Behavior::*;
    private import Core::Requirements::*;
    private import Core::Allocations::*;
    private import Configurations::*;
    private import Programs::ProgramA::*;
    private import Programs::ProgramB::*;
    private import Verification::TestCases::*;
    private import Verification::Traceability::*;
}

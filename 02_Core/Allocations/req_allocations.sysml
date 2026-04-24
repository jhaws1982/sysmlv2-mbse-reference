/**
 * RequirementAllocations — core requirement to architecture allocations.
 *
 * LEAF FILE. Globally unique name "RequirementAllocations".
 * Assembled into Core::Allocations by 02_Core/_namespace.sysml.
 *
 * Maps core system requirements to the architectural elements responsible
 * for satisfying them. Kept separate from requirements and architecture
 * because allocations change frequently without touching stable CIs.
 *
 * satisfy <req> by <part_usage>  — design-intent claim.
 * Evidence is provided by verification cases in 05_Verification/.
 *
 * Note: subject parts from CoreSystem_Assembly are used as the satisfying
 * elements here. Logical subsystem mappings are placeholders until the
 * logical architecture is fully elaborated.
 */
package RequirementAllocations {
    private import Core::Requirements::*;
    private import CoreSystem::*;
    private import FeatureA::*;
    private import FeatureB::*;

    // Top-level system assembly satisfies capability and quality requirements
    part coreInstance : CoreSystem_Assembly;

    satisfy processingCapability          by coreInstance;
    satisfy integrationCapability         by coreInstance;
    satisfy systemAvailability            by coreInstance;
    satisfy programmingLanguageConstraint by coreInstance;

    // FeatureA component satisfies the external data interface requirement
    part featureAInstance : FeatureA_Component;
    satisfy externalDataInterface         by featureAInstance;

    // incompleteReq intentionally not allocated — gap for tool demonstration
}

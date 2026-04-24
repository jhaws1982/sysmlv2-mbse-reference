// Package: SRS_Definitions <SRSREQ>
// Description:
// This package defines a reusable SysML v2 requirement metamodel aligned to
// DI-IPSC-81433A (Software Requirements Specification DID).
// It provides standardized requirement definitions, reusable aspects,
// and validation rules to enforce completeness and consistency of requirements.
// This library is intended to be reused across programs to ensure SRS-compliant
// requirement structure, especially for capability, interface, data, and
// verification definitions.
//
// ── Doc Convention ──────────────────────────────────────────────────────────
//
// Every requirement usage instantiated from this library MUST carry the
// following doc annotations on the usage site (i.e., in your *Decl.sysml
// files), in order:
//
// 1. Unnamed doc — the normative requirement statement (the "shall" text):
//
// doc
// /* The CSCI shall <verb> <object> under <conditions>. */
//
// 2. Named doc Rationale — explanation of why this requirement exists:
//
// doc Rationale
// /* <Why this is required, what risk it mitigates, or what
// * stakeholder concern it addresses.> */
//
// The short-name position carries the project-unique identifier:
//
// requirement <'REQ-CAP-001'> myRequirement : CapabilityRequirement { ... }
//
// These are enforced at tool validation time (req_validate.py), not by the
// SysML type system — the language provides no mechanism to mandate doc
// annotation presence on a subtype. The assert constraints below cover only
// what the type system CAN enforce: structured attributes with typed values.
//
// ── What NOT to put in doc annotations ──────────────────────────────────────
//
// Keep the following as typed attributes (they are already defined below):
// - verificationMethod (enum-typed — tool constraints depend on this value)
// - priority / criticality (enum-typed)
// - units (enum-typed)
// - all identifier-like name fields (interfaceName, capabilityName, etc.)
//
// ────────────────────────────────────────────────────────────────────────────

library package <SRSREQ> SRS_Definitions {
  // Private imports: names are visible inside this package only, not re-exported.
  // Use 'public import' only in namespace hub files intended to re-export names.
  private import ScalarValues::*;
  private import CommonDefinitions::*;

  // Allowed verification methods per DI-IPSC-81433A §4.
  enum def VerificationMethodKind {
    Test;
    Analysis;
    Inspection;
    Demonstration;
  }

  // ----------------------------------------
  // ISQ Quantity Kind Enumeration
  //
  // Restricts the 'units' attribute in DataAspect to a valid ISQ quantity kind.
  // Using an enum def rather than a library type reference avoids tool-specific
  // resolution issues with MeasurementReferences / Quantities library internals,
  // while still providing meaningful semantic restriction. Extend as needed for
  // your program domain.
  // ----------------------------------------
  enum def UnitKind {
    doc
    /* ISQ-aligned quantity kinds applicable to SRS data requirements (ISO 80000). */
    Length; // metre (m)
    Mass; // kilogram (kg)
    Duration; // second (s)
    Temperature; // kelvin (K)
    ElectricCurrent; // ampere (A)
    AmountOfSubstance; // mole (mol)
    LuminousIntensity; // candela (cd)
    Frequency; // hertz (Hz)
    Velocity; // metre/second (m/s)
    Acceleration; // metre/second² (m/s²)
    Force; // newton (N)
    Pressure; // pascal (Pa)
    Energy; // joule (J)
    Power; // watt (W)
    Voltage; // volt (V)
    DataRate; // bit/second (b/s)
    StorageSize; // byte (B) / bit (b)
    Dimensionless; // ratio, percentage, count
  }

  // ----------------------------------------
  // Structured Verification Criteria
  //
  // Design rationale: verificationMethod lives here, not on SRS_Requirement.
  // Coupling rule: if you define criteria, you must define a method.
  // If you don't define criteria, no method is required.
  // Enforced structurally — verificationMethod is [1] (default) inside this
  // part def, so its presence is required whenever criteria is instantiated.
  //
  // Doc convention for VerificationCriteria usage sites:
  // doc — describe the overall test objective in prose (replaces the former
  // criteriaObjective, conditions, and passFailLogic string attributes).
  //
  // Example:
  // part myCriteria : VerificationCriteria {
  // doc
  // /* Under nominal load (≤ 1000 concurrent users), inject 100 requests
  // * at 10 req/s. The test passes if ≥ 99% of responses arrive within
  // * 200ms and no error responses are returned.
  // */
  // attribute verificationMethod = VerificationMethodKind::Test;
  // attribute threshold = "200ms at p99";
  // }
  //
  // threshold is kept as a typed attribute because it is a compact, queryable
  // value (e.g. "200ms", "99.9%") used by automated reporting tools.
  // ----------------------------------------
  part def VerificationCriteria {
    attribute threshold : ScalarValues::String [0..1];
    // [1] by default — required whenever a VerificationCriteria part is instantiated.
    attribute verificationMethod : VerificationMethodKind;
  }

  // ----------------------------------------
  // Base Requirement Definition             [DI-IPSC-81433A §3, §3.18]
  //
  // Root type for all SRS requirement definitions in this library. Provides
  // the structure common to every CSCI requirement per §3.
  //
  // REQUIRED at every usage site — enforced by req_validate.py:
  // <'REQ-ID'>      project-unique identifier in the short-name position
  // doc             normative requirement text ("shall" statement)
  // doc Rationale   rationale for this requirement
  //
  // OPTIONAL attributes:
  // source          traceability to a parent requirement or stakeholder need
  // priority        precedence ordering per §3.18
  // criticality     safety/security/privacy designation per §3.18
  // criteria        structured verification criteria (adds verificationMethod)
  //
  // All specializations inherit these fields and conventions.
  // ----------------------------------------
  requirement def SRS_Requirement {
    attribute source : ScalarValues::String [0..1];
    attribute priority : CMNDEF::LevelKind [0..1];
    attribute criticality : CMNDEF::LevelKind [0..1];

    // Optional: if absent, no verificationMethod is required (see VerificationCriteria above).
    part criteria : VerificationCriteria [0..1];
  }

  // ----------------------------------------
  // Performance Aspect                      [DI-IPSC-81433A §3.2.x]
  //
  // Captures quantitative performance characteristics associated with a CSCI
  // capability. Per §3.2.x, capability requirements shall include applicable
  // parameters such as response times, throughput times, timing constraints,
  // sequencing, accuracy, and allowable deviations under operating conditions.
  // At least one performance attribute must be populated to ensure the
  // requirement is measurable and testable.
  //
  // Doc convention: the unnamed doc at the usage site should state the
  // performance constraint in measurable terms. Example:
  // doc
  // /* The CSCI shall process inbound telemetry at ≥ 10,000 messages per
  // * second with end-to-end latency ≤ 50ms at p99 under nominal load. */
  // ----------------------------------------
  requirement def PerformanceAspect :> SRS_Requirement {
    attribute performance : ScalarValues::String [0..1];
    attribute timing : ScalarValues::String [0..1];
    attribute throughput : ScalarValues::String [0..1];
    attribute latency : ScalarValues::String [0..1];
    attribute accuracy : ScalarValues::String [0..1];
    attribute capacity : ScalarValues::String [0..1];

    assert constraint PerformanceDefined {
      performance != "" or timing != "" or throughput != "" or latency != "" or accuracy != "" or capacity != ""
    }
  }

  // ----------------------------------------
  // Data Aspect                             [DI-IPSC-81433A §3.3.x.c, §3.5]
  //
  // Captures the required characteristics of individual data elements that the
  // CSCI must provide, store, send, access, or receive. Per §3.3.x.c, these
  // characteristics include the data element name/identifier, data type
  // (alphanumeric, integer, etc.), size and format, units of measurement, and
  // range or enumeration of possible values. Also applicable to internal data
  // requirements per §3.5, covering databases and data files internal to the
  // CSCI whose structure is imposed as a requirement rather than left to design.
  // ----------------------------------------
  requirement def DataAspect :> SRS_Requirement {
    attribute dataName : ScalarValues::String;
    attribute dataType : ScalarValues::String;
    attribute format : ScalarValues::String [0..1];

    // Typed by UnitKind enum — restricts to valid ISQ quantity kinds.
    // At declaration time, usage sites set this to e.g. UnitKind::Duration.
    attribute units : UnitKind [0..1];

    assert constraint DataHasName { dataName != "" }
    assert constraint DataHasType { dataType != "" }
  }

  // ----------------------------------------
  // Interface Aspect                        [DI-IPSC-81433A §3.3, §3.3.1, §3.3.x]
  //
  // Captures the identification and communication characteristics of a CSCI
  // external interface. Per §3.3.1, each interface shall be identified with a
  // project-unique identifier and shall designate the interfacing entities
  // (systems, CIs, users, etc.) by name. Per §3.3.x, requirements shall cover
  // the type of interface (e.g., real-time transfer, storage-and-retrieval),
  // communication protocol, and message format. A minimum of two interfacing
  // entities is required to constitute a valid interface definition.
  // ----------------------------------------
  requirement def InterfaceAspect :> SRS_Requirement {
    attribute interfaceName : ScalarValues::String;

    // '>= 2 entities' enforced structurally (no size() in SysML v2):
    // primaryEntity   [1] — first  entity required
    // secondaryEntity [1] — second entity required
    // additionalEntities [*] — further entities optional
    attribute primaryEntity : ScalarValues::String;
    attribute secondaryEntity : ScalarValues::String;
    attribute additionalEntities : ScalarValues::String [*];

    attribute protocol : ScalarValues::String [0..1];
    attribute messageFormat : ScalarValues::String [0..1];

    assert constraint InterfaceHasName { interfaceName != "" }
    assert constraint PrimaryDefined { primaryEntity != "" }
    assert constraint SecondaryDefined { secondaryEntity != "" }
    assert constraint InterfaceDefined { protocol != "" or messageFormat != "" }
  }

  // ----------------------------------------
  // Capability Requirement                  [DI-IPSC-81433A §3.2, §3.2.x]
  //
  // Specifies a required CSCI capability — a named group of related behavioral
  // requirements that the CSCI must satisfy for acceptance. Per §3.2.x, each
  // capability requirement shall identify required behavior of the CSCI and
  // include applicable performance parameters. "Capability" may be replaced by
  // "function," "subject," or "object" per program convention. Specializes
  // PerformanceAspect so that all timing, throughput, accuracy, and latency
  // constraints are inherited. Verification is restricted to Test or Analysis,
  // consistent with the objective and measurable nature of capability acceptance.
  // ----------------------------------------
  requirement def CapabilityRequirement :> PerformanceAspect {
    attribute capabilityName : ScalarValues::String;

    assert constraint CapabilityNamed { capabilityName != "" }

    assert constraint CapabilityVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Test or
      criteria.verificationMethod == VerificationMethodKind::Analysis
    }
  }

  // ----------------------------------------
  // Interface Requirement                   [DI-IPSC-81433A §3.3, §3.3.x, §3.3.x.c]
  //
  // Combines interface identification (InterfaceAspect) with the required
  // characteristics of individual data elements exchanged across that interface
  // (DataAspect). Per §3.3.x.c, interface requirements shall address each data
  // element the CSCI must provide, store, send, access, or receive, including
  // its name, data type, format, units, and range. The diamond inheritance
  // through SRS_Requirement is intentional — both parent aspects ultimately
  // trace to the same base requirement. Verification methods exclude Analysis-
  // only, reflecting that interface conformance is typically demonstrated,
  // tested, or inspected against a defined protocol or data standard.
  // ----------------------------------------
  // Multiple specialization creates a diamond through SRS_Requirement — valid in SysML v2.
  // ----------------------------------------
  requirement def InterfaceRequirement :> InterfaceAspect, DataAspect {
    assert constraint InterfaceHasData {
      dataName != "" and dataType != ""
    }

    assert constraint InterfaceVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Test or
      criteria.verificationMethod == VerificationMethodKind::Inspection or
      criteria.verificationMethod == VerificationMethodKind::Demonstration
    }
  }

  // ----------------------------------------
  // Data Requirement                        [DI-IPSC-81433A §3.5]
  //
  // Specifies requirements imposed on data internal to the CSCI, including
  // databases and data files that must be included in or managed by the CSCI.
  // Per §3.5, if all decisions about internal data are left to the designer this
  // requirement type need not be used; it applies only when specific data
  // structure, naming, format, or type constraints are contractually imposed.
  // Verification is restricted to Analysis or Inspection, since internal data
  // structures are typically verified by reviewing code, schemas, or data
  // dictionaries rather than by operational test.
  // ----------------------------------------
  requirement def DataRequirement :> DataAspect {
    assert constraint DataVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Analysis or
      criteria.verificationMethod == VerificationMethodKind::Inspection
    }
  }

  // ----------------------------------------
  // Safety Requirement                      [DI-IPSC-81433A §3.7]
  //
  // Specifies CSCI requirements concerned with preventing or minimizing
  // unintended hazards to personnel, property, and the physical environment.
  // Per §3.7, examples include safeguards against inadvertent actions (e.g.,
  // accidentally issuing a critical command) and non-actions (e.g., failure to
  // issue an intended command). Also covers nuclear safety rules where
  // applicable.
  //
  // Doc convention for SafetyRequirement usage sites:
  // The unnamed doc should state the hazard and the mitigation in the
  // normative "shall" text. The Rationale doc should explain the hazard
  // severity and reference the applicable hazard analysis (e.g., PHA, FMEA).
  //
  // Example:
  // doc
  // /* The CSCI shall inhibit all actuator commands for ≥ 500ms following
  // * operator mode transition to prevent inadvertent actuation during
  // * mode-change transients. */
  // doc Rationale
  // /* Mode-change transients cause spurious command signals in legacy
  // * hardware. See PHA-SW-007. Severity: Catastrophic / Likelihood: Remote. */
  //
  // hazard and mitigation are retained as typed attributes because automated
  // safety analysis tools query them by name.
  // ----------------------------------------
  requirement def SafetyRequirement :> SRS_Requirement {
    attribute hazard : ScalarValues::String;
    attribute mitigation : ScalarValues::String;

    assert constraint SafetyComplete { hazard != "" and mitigation != "" }

    assert constraint SafetyVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Analysis or
      criteria.verificationMethod == VerificationMethodKind::Test or
      criteria.verificationMethod == VerificationMethodKind::Inspection
    }
  }

  // ----------------------------------------
  // Security Requirement                    [DI-IPSC-81433A §3.8]
  //
  // Specifies CSCI requirements concerned with maintaining security and privacy.
  // Per §3.8, these requirements shall address the security/privacy environment
  // in which the CSCI must operate, the type and degree of security or privacy
  // to be provided, the risks the CSCI must withstand, required safeguards,
  // the security/privacy policy that must be met, accountability requirements,
  // and the criteria for security/privacy certification or accreditation.
  // The classification attribute captures the security level or policy
  // designation applicable to this requirement. Verification is restricted to
  // Analysis or Test, consistent with accreditation and penetration testing
  // practices.
  // ----------------------------------------
  requirement def SecurityRequirement :> SRS_Requirement {
    attribute classification : ScalarValues::String;

    assert constraint SecurityDefined { classification != "" }

    assert constraint SecurityVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Analysis or
      criteria.verificationMethod == VerificationMethodKind::Test
    }
  }

  // ----------------------------------------
  // Environmental Requirement               [DI-IPSC-81433A §3.9]
  //
  // Specifies requirements regarding the environment in which the CSCI must
  // operate. Per §3.9, this covers the computer hardware platform and operating
  // system on which the CSCI must run. Examples include required OS version,
  // hardware architecture, virtualization constraints, or co-hosting restrictions.
  // Note: requirements on the amount of hardware resources consumed (CPU, memory,
  // storage) are captured separately in ResourceRequirement (§3.10.1/3.10.2);
  // this type addresses the nature and configuration of the execution environment
  // itself.
  // ----------------------------------------
  requirement def EnvironmentalRequirement :> SRS_Requirement {
    attribute environment : ScalarValues::String;

    assert constraint EnvironmentDefined { environment != "" }

    assert constraint EnvironmentalVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Test or
      criteria.verificationMethod == VerificationMethodKind::Analysis
    }
  }

  // ----------------------------------------
  // Resource Requirement                    [DI-IPSC-81433A §3.10.1, §3.10.2]
  //
  // Specifies requirements on computer hardware and hardware resource utilization.
  // Per §3.10.1, this includes required number, type, size, capacity, and other
  // characteristics of processors, memory, I/O devices, auxiliary storage, and
  // network equipment. Per §3.10.2, resource utilization requirements state the
  // maximum allowable use of processor capacity, memory, I/O device capacity,
  // auxiliary storage, and network capacity — typically expressed as percentages
  // of total capacity and including the conditions under which utilization is to
  // be measured. Use this type when hardware resource consumption is a
  // contractually imposed acceptance criterion, not merely a design goal.
  // ----------------------------------------
  requirement def ResourceRequirement :> SRS_Requirement {
    attribute resource : ScalarValues::String;

    assert constraint ResourceDefined { resource != "" }

    assert constraint ResourceVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Analysis or
      criteria.verificationMethod == VerificationMethodKind::Inspection
    }
  }

  // ----------------------------------------
  // Quality Requirement                     [DI-IPSC-81433A §3.11]
  //
  // Specifies CSCI requirements concerned with software quality factors
  // identified in the contract or derived from a higher-level specification.
  // Per §3.11, applicable quality attributes include: functionality (ability to
  // perform all required functions), reliability (correct, consistent results),
  // maintainability (ease of correction), availability (accessible when needed),
  // flexibility (adaptable to changing requirements), portability (modifiable for
  // new environment), reusability (usable in multiple applications), testability
  // (thoroughly testable), and usability (easily learned and used). The
  // qualityAttribute field names the specific factor being quantified or
  // constrained.
  // ----------------------------------------
  requirement def QualityRequirement :> SRS_Requirement {
    attribute qualityAttribute : ScalarValues::String;

    assert constraint QualityDefined { qualityAttribute != "" }

    assert constraint QualityVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Test or
      criteria.verificationMethod == VerificationMethodKind::Analysis
    }
  }

  // ----------------------------------------
  // Design Constraint Requirement           [DI-IPSC-81433A §3.12]
  //
  // Specifies requirements that constrain the design and implementation of the
  // CSCI, as opposed to requirements on its behavior or outputs. Per §3.12,
  // examples include: required use of a particular CSCI architecture or specific
  // databases/software units; use of Government/acquirer-furnished property;
  // mandated design or implementation standards; required programming language;
  // use of particular data standards; and flexibility or expandability provisions
  // to accommodate anticipated growth in technology, threat, or mission. These
  // requirements may reference applicable commercial or military standards.
  // 'constraint' is a reserved SysML v2 keyword — the attribute is named
  // 'constraintText'.
  // ----------------------------------------
  requirement def DesignConstraintRequirement :> SRS_Requirement {
    attribute constraintText : ScalarValues::String;

    assert constraint ConstraintDefined { constraintText != "" }

    assert constraint ConstraintVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Inspection or
      criteria.verificationMethod == VerificationMethodKind::Analysis
    }
  }

  // ----------------------------------------
  // Adaptation Requirement                  [DI-IPSC-81433A §3.6]
  //
  // Specifies requirements concerning installation-dependent data to be provided
  // by the CSCI and operational parameters that may vary according to deployment
  // needs. Per §3.6, examples include site-dependent geographic parameters
  // (latitude, longitude), site-specific tax or configuration codes, and
  // operation-dependent targeting constants or data recording parameters.
  // These requirements define the bounds and format of data that must be
  // configurable at installation time, ensuring the CSCI can be adapted to
  // different operational sites without software modification.
  // ----------------------------------------
  requirement def AdaptationRequirement :> SRS_Requirement {
    attribute siteParameters : ScalarValues::String;

    assert constraint AdaptationDefined { siteParameters != "" }

    assert constraint AdaptationVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Test or
      criteria.verificationMethod == VerificationMethodKind::Analysis
    }
  }

  // ----------------------------------------
  // COTS Requirement                        [DI-IPSC-81433A §3.10.3]
  //
  // Specifies requirements regarding computer software that must be used by, or
  // incorporated into, the CSCI. Per §3.10.3, this covers operating systems,
  // database management systems, communications/network software, utility
  // software, input/output device simulators, test software, and manufacturing
  // software — including COTS and Government-furnished software (GFS). The
  // correct nomenclature, version number, and documentation references of each
  // such software item shall be provided. Verification is restricted to
  // Inspection or Analysis, since COTS product compliance is confirmed by
  // reviewing product documentation, licenses, and configuration records rather
  // than by operational test.
  // ----------------------------------------
  requirement def COTSRequirement :> SRS_Requirement {
    attribute product : ScalarValues::String;

    assert constraint COTSDefined { product != "" }

    assert constraint COTSVerificationValid {
      not (criteria hastype VerificationCriteria) or
      criteria.verificationMethod == VerificationMethodKind::Inspection or
      criteria.verificationMethod == VerificationMethodKind::Analysis
    }
  }
}

/**
 * Shared::Data — shared enumerations and item definitions.
 *
 * This is a LEAF file.  The package name "SharedData" is a globally unique
 * flat identifier owned by this file alone.
 *
 * The namespace hub file (00_Shared/_namespace.sysml) re-exports this package
 * under the nested name  Shared::Data  so that consumers can write:
 *     private import Shared::Data::*;
 */
package SharedData {

    // ── Enumerations ──────────────────────────────────────────────────────
    enum def GenericTypeA    { Type1; Type2; Type3; }
    enum def GenericProtocol { Proto1; Proto2; Proto3; }
    enum def FeatureKind     { Variant1; Variant2; }
    enum def NodeRole        { Role1; Role2; Role3; }

    enum def VerificationMethod { Test; Analysis; Inspection; Demonstration; }

    // ── Item definitions (passive data / signals) ─────────────────────────
    item def DataA;
    item def DataB;
}

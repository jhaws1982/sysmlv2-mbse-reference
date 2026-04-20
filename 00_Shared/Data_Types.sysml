/**
 * SharedData — shared enumerations and item definitions.
 * LEAF file. Re-exported as Shared::Data by 00_Shared/_namespace.sysml.
 */
package SharedData {
    private import ScalarValues::*;

    enum def GenericTypeA    { Type1; Type2; Type3; }
    enum def GenericProtocol { Proto1; Proto2; Proto3; }
    enum def FeatureKind     { Variant1; Variant2; }
    enum def NodeRole        { Role1; Role2; Role3; }

    item def DataA;
    item def DataB;
}

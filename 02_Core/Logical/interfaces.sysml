/**
 * LogicalInterfaces — port and flow item definitions for the logical layer.
 *
 * LEAF FILE. Globally unique name "LogicalInterfaces".
 * Assembled into Core::Logical by 02_Core/_namespace.sysml.
 *
 * Primary source for the Interface Catalog (LA-03).
 *
 * SysIDE rule: port defs must NOT contain composite usages.
 * Only `in item`, `out item`, `in attribute`, `out attribute` inside port defs.
 * Constraints on port contents go on the owning part, not the port def.
 */
package LogicalInterfaces {
    private import SharedData::*;
    private import ScalarValues::*;

    // ── Flow Item Definitions ─────────────────────────────────────────────

    item def InboundMessage {
        doc /* Raw inbound message from ExternalDataSource conforming to
               ICD-EXT-001. Contains a 256-byte header, variable-length
               payload, and 4-byte CRC. */
        attribute messageType : ScalarValues::String;
        attribute payloadSize : ScalarValues::Integer;
    }

    item def ProcessedRecord {
        doc /* Integrated output record produced by DataProcessingSubsystem
               after applying protocol processing and Feature A/B coordination. */
        attribute recordId    : ScalarValues::String;
        attribute timestamp   : ScalarValues::Integer;
    }

    item def HealthReport {
        doc /* Subsystem health status report. Produced by SystemManagement
               and consumed by operators and administrative interfaces. */
        attribute subsystemId : ScalarValues::String;
        attribute healthy     : ScalarValues::Boolean;
        attribute faultCode   : ScalarValues::String;
    }

    item def ConfigUpdate {
        doc /* Runtime configuration parameter update payload. */
        attribute parameterKey   : ScalarValues::String;
        attribute parameterValue : ScalarValues::String;
    }

    // ── Port Definitions ──────────────────────────────────────────────────

    port def ExternalDataInputPort {
        doc /* Port through which the core CSCI receives inbound messages
               from ExternalDataSource. Implements ICD-EXT-001 framing. */
        in message : InboundMessage;
    }

    port def ProcessedOutputPort {
        doc /* Port through which processed records are made available
               to downstream consumers. */
        out record : ProcessedRecord;
    }

    port def HealthStatusPort {
        doc /* Port through which subsystems report health status for
               operator monitoring and built-in test evaluation. */
        out report : HealthReport;
    }

    port def AdminInterfacePort {
        doc /* Port through which the administrator submits configuration
               updates and receives confirmation. */
        in config      : ConfigUpdate;
        out result : ScalarValues::Boolean;
    }
}

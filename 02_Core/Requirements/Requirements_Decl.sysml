/**
 * RequirementsDecl — core CSCI requirement declarations (Decl side of Def/Decl split).
 *
 * LEAF FILE. Globally unique name "RequirementsDecl".
 * Assembled into Core::Requirements by 02_Core/_namespace.sysml.
 *
 * Doc convention (per SRS_Definitions.sysml):
 *   Mandatory on every requirement usage:
 *     <'REQ-ID'>      short-name identifier
 *     doc             normative "shall" statement
 *     doc Rationale   justification
 *
 * Traceability convention:
 *   - ROOT (L1) requirements carry a 'source' attribute naming the external
 *     document or stakeholder need that originated the requirement
 *     (e.g. source = "SYS-PERF-003").
 *   - CHILD (L2/L3) requirements use #derivation connection elements co-located
 *     inside their parent requirement; the structural nesting expresses
 *     decomposition, and the derivation connections make the parent-child link
 *     explicitly queryable by SysML v2 tools.
 *
 * ── INTENTIONAL VALIDATION EXAMPLES ────────────────────────────────────────
 *
 * This file contains a mix of VALID, INCOMPLETE, and INVALID requirements
 * so that req_validate.py and req_completeness.py produce non-trivial output:
 *
 *   processingCapability  — COMPLETE  (all fields, correct method)
 *   integrationCapability — COMPLETE  (all fields, correct method)
 *   externalDataInterface — COMPLETE  (all fields, correct method)
 *   systemAvailability    — COMPLETE  (all fields, correct method)
 *   programmingLanguageConstraint — COMPLETE
 *   incompleteReq         — INCOMPLETE (missing source, priority, criteria)
 *   invalidReq_noId       — INVALID   (no short-name ID)
 *   invalidReq_noDoc      — INVALID   (no doc block)
 *   invalidReq_noRationale — INVALID  (no doc Rationale)
 *
 *   Three child requirements intentionally omit their derivation connection
 *   to demonstrate INVALID traceability gaps in req_completeness.py:
 *     featureAFaultIsolation  (REQ-CAP-002-A-2) — no derivation connection (INVALID)
 *     headerFieldLayout       (REQ-IFC-001-A-1) — no derivation connection (INVALID)
 *     pythonStaticAnalysis    (REQ-DSN-001-B-2) — no derivation connection (INVALID)
 */
package RequirementsDecl {
    private import RequirementsDef::*;
    private import SRS_Definitions::*;
    private import CommonDefinitions::*;
    private import CoreSystem::*;
    private import FeatureA::*;
    private import FeatureB::*;
    private import RequirementDerivation::*;

    // ════════════════════════════════════════════════════════════════════════
    // COMPLETE requirements — pass all validation checks
    // ════════════════════════════════════════════════════════════════════════

    requirement <'REQ-CAP-001'> processingCapability
            : ProcessingCapability_Def {
        doc
        /* The CSCI shall process all inbound data streams within
         * 50 milliseconds of receipt under nominal operating load
         * of 1000 messages per second.
         */
        doc Rationale
        /* Derived from system-level response time budget SYS-PERF-003.
         * 50 ms is the CSCI allocation after network transit time.
         * Exceeding this bound causes downstream pipeline stalls.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> source         = "SYS-PERF-003";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
        attribute :>> capabilityName = "InboundDataProcessing";
        attribute :>> latency        = "50 ms maximum at 99th percentile.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Inject 1000 messages/second for 10 minutes under nominal load.
             * PASS if 99th-percentile latency <= 50 ms and zero messages dropped.
             */
            attribute :>> verificationMethod = VerificationMethodKind::test;
            attribute :>> threshold          = "50 ms at 99th percentile";
        }

        requirement <'REQ-CAP-001-A'> throughputCapacity : CapabilityRequirement {
            doc
            /* The CSCI shall sustain a continuous inbound message throughput
             * of at least 1000 messages per second without message loss or
             * queue overflow under nominal operating conditions.
             */
            doc Rationale
            /* Throughput capacity is the primary determinant of downstream
             * pipeline sizing. 1000 msg/s is the nominal mission rate from
             * SYS-PERF-003; a queue overflow causes silent message loss.
             */
            subject sys : CoreSystem_Assembly;
            attribute :>> priority       = CMNDEF::LevelKind::High;
            attribute :>> criticality    = CMNDEF::LevelKind::High;
            attribute :>> capabilityName = "InboundThroughput";
            attribute :>> throughput     = "1000 messages per second minimum.";
            part :>> criteria : VerificationCriteria {
                doc
                /* Inject exactly 1000 msg/s for 10 minutes. PASS if zero messages
                 * are dropped and input queue depth never exceeds 500 entries.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::test;
                attribute :>> threshold          = "0 drops; queue <= 500 at 1000 msg/s";
            }

            requirement <'REQ-CAP-001-A-1'> inboundQueueCapacity : CapabilityRequirement {
                doc
                /* The CSCI shall maintain an inbound message queue capable of
                 * holding at least 5000 messages to absorb burst arrivals
                 * without dropping messages.
                 */
                doc Rationale
                /* A 5000-entry queue provides a 5-second burst absorption buffer
                 * at nominal 1000 msg/s, preventing message loss during transient
                 * load spikes before backpressure takes effect.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::High;
                attribute :>> criticality    = CMNDEF::LevelKind::High;
                attribute :>> capabilityName = "InboundQueueCapacity";
                attribute :>> capacity       = "5000 message entries minimum.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Inject a burst of 5000 messages with no consumer running.
                     * PASS if all 5000 messages are queued with zero drops.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "5000 messages queued; 0 drops";
                }
            }

            requirement <'REQ-CAP-001-A-2'> backpressureControl : CapabilityRequirement {
                doc
                /* The CSCI shall assert a backpressure signal to the upstream
                 * source within 10 milliseconds when inbound queue depth
                 * exceeds 80% of maximum capacity.
                 */
                doc Rationale
                /* Early backpressure prevents queue overflow; the 80% trigger
                 * provides margin for in-flight messages already transmitted
                 * before the signal reaches the source.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::High;
                attribute :>> criticality    = CMNDEF::LevelKind::High;
                attribute :>> capabilityName = "BackpressureControl";
                attribute :>> timing         = "Backpressure asserted within 10 ms of 80% queue threshold.";
                // criteria intentionally omitted — INCOMPLETE: verification procedure not yet defined
            }

            #derivation connection <'REQ-CAP-001-A-1-DRV'> drv_inboundQueueCapacity {
                end #original orig references processingCapability::throughputCapacity;
                end #derive derv references processingCapability::throughputCapacity::inboundQueueCapacity;
            }
            #derivation connection <'REQ-CAP-001-A-2-DRV'> drv_backpressureControl {
                end #original orig references processingCapability::throughputCapacity;
                end #derive derv references processingCapability::throughputCapacity::backpressureControl;
            }
        }

        requirement <'REQ-CAP-001-B'> processingLatency : CapabilityRequirement {
            doc
            /* The CSCI shall process each inbound message within 50 milliseconds
             * of receipt at the 99th percentile under the nominal 1000 msg/s load.
             */
            doc Rationale
            /* 50 ms is the CSCI share of the system latency budget after network
             * transit is deducted. Exceeding this allocation causes downstream
             * pipeline stalls per SYS-PERF-003.
             */
            subject sys : CoreSystem_Assembly;
            attribute :>> priority       = CMNDEF::LevelKind::High;
            attribute :>> criticality    = CMNDEF::LevelKind::High;
            attribute :>> capabilityName = "MessageProcessingLatency";
            attribute :>> latency        = "50 milliseconds maximum at 99th percentile.";
            part :>> criteria : VerificationCriteria {
                doc
                /* Inject 1000 msg/s for 10 minutes and record per-message latency.
                 * PASS if 99th-percentile latency is at or below 50 ms.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::test;
                attribute :>> threshold          = "50 ms at 99th percentile";
            }

            requirement <'REQ-CAP-001-B-1'> nominalLoadLatency : CapabilityRequirement {
                doc
                /* The CSCI shall process each inbound message within 30 milliseconds
                 * at the 50th percentile under nominal 1000 msg/s load.
                 */
                doc Rationale
                /* A 30 ms median latency provides scheduling headroom below the
                 * 50 ms 99th-percentile allocation, allowing occasional spikes
                 * without breaching the overall latency budget.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::High;
                attribute :>> criticality    = CMNDEF::LevelKind::High;
                attribute :>> capabilityName = "NominalLoadLatency";
                attribute :>> latency        = "30 milliseconds at 50th percentile under nominal load.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Inject 1000 msg/s for 10 minutes. PASS if 50th-percentile
                     * latency is at or below 30 ms.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "30 ms at 50th percentile";
                }
            }

            requirement <'REQ-CAP-001-B-2'> peakLoadLatency : CapabilityRequirement {
                doc
                /* The CSCI shall process each inbound message within 120 milliseconds
                 * at the 99th percentile when operating at 150% of nominal load
                 * (1500 messages per second).
                 */
                doc Rationale
                /* Graceful degradation under surge load is required by the mission
                 * profile. 120 ms at 150% load is the system-level surge allocation
                 * from SYS-PERF-003 after upstream derating.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::High;
                attribute :>> criticality    = CMNDEF::LevelKind::High;
                attribute :>> capabilityName = "PeakLoadLatency";
                attribute :>> latency        = "120 milliseconds at 99th percentile at 1500 msg/s.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Inject 1500 msg/s for 5 minutes. PASS if 99th-percentile
                     * latency is at or below 120 ms.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "120 ms at 99th percentile at 1500 msg/s";
                }
            }

            #derivation connection <'REQ-CAP-001-B-1-DRV'> drv_nominalLoadLatency {
                end #original orig references processingCapability::processingLatency;
                end #derive derv references processingCapability::processingLatency::nominalLoadLatency;
            }
            #derivation connection <'REQ-CAP-001-B-2-DRV'> drv_peakLoadLatency {
                end #original orig references processingCapability::processingLatency;
                end #derive derv references processingCapability::processingLatency::peakLoadLatency;
            }
        }

        #derivation connection <'REQ-CAP-001-A-DRV'> drv_throughputCapacity {
            end #original orig references processingCapability;
            end #derive derv references processingCapability::throughputCapacity;
        }
        #derivation connection <'REQ-CAP-001-B-DRV'> drv_processingLatency {
            end #original orig references processingCapability;
            end #derive derv references processingCapability::processingLatency;
        }
    }

    requirement <'REQ-CAP-002'> integrationCapability
            : IntegrationCapability_Def {
        doc
        /* The CSCI shall integrate Feature A and Feature B subsystems
         * into a unified processing pipeline with no data loss under
         * nominal operating conditions.
         */
        doc Rationale
        /* A single pipeline eliminates inter-process latency and reduces
         * integration complexity. Derived from system architecture SYS-ARCH-001.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> source         = "SYS-ARCH-001";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
        attribute :>> capabilityName = "SubsystemIntegration";
        attribute :>> performance    = "Zero data loss under nominal load.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Run both subsystems under nominal load for 30 minutes.
             * PASS if zero messages lost and queue depth stays <= 1000.
             */
            attribute :>> verificationMethod = VerificationMethodKind::test;
            attribute :>> threshold          = "0 messages lost; queue <= 1000";
        }

        requirement <'REQ-CAP-002-A'> featureAIntegration : CapabilityRequirement {
            doc
            /* The CSCI shall integrate Feature A into the unified processing
             * pipeline with lossless data handoff at the Feature A output
             * boundary under nominal operating conditions.
             */
            doc Rationale
            /* Derived from SYS-ARCH-001. Feature A data must reach the integration
             * layer without loss to prevent downstream state inconsistencies.
             */
            subject sys : CoreSystem_Assembly;
            attribute :>> priority       = CMNDEF::LevelKind::High;
            attribute :>> criticality    = CMNDEF::LevelKind::High;
            attribute :>> capabilityName = "FeatureA_PipelineIntegration";
            attribute :>> performance    = "Zero data loss at Feature A output boundary.";
            part :>> criteria : VerificationCriteria {
                doc
                /* Run Feature A under nominal load for 30 minutes with the
                 * integration layer active. PASS if zero messages lost at handoff.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::test;
                attribute :>> threshold          = "0 messages lost at Feature A handoff";
            }

            requirement <'REQ-CAP-002-A-1'> featureAHandoffFormat : CapabilityRequirement {
                doc
                /* The CSCI shall pass data from Feature A to the integration layer
                 * in the internal canonical message format defined in IDD-INT-001.
                 */
                doc Rationale
                /* A canonical format at the handoff boundary decouples Feature A's
                 * internal representation from the integration layer, reducing
                 * interface brittleness across independent release cycles.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::High;
                attribute :>> criticality    = CMNDEF::LevelKind::High;
                attribute :>> capabilityName = "FeatureA_HandoffFormat";
                attribute :>> performance    = "All Feature A output conforms to IDD-INT-001 canonical format.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Capture Feature A output under nominal load and validate
                     * each message against the IDD-INT-001 schema.
                     * PASS if 100% of messages are schema-conformant.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "100% IDD-INT-001 schema conformance";
                }
            }

            requirement <'REQ-CAP-002-A-2'> featureAFaultIsolation : CapabilityRequirement {
                doc
                /* The CSCI shall isolate Feature A processing faults such that
                 * a Feature A failure does not interrupt or corrupt Feature B
                 * operation.
                 */
                doc Rationale
                /* Independent fault domains prevent a single subsystem failure
                 * from cascading into a total system outage, maintaining partial
                 * mission capability when Feature A is unavailable.
                 */
                subject sys : CoreSystem_Assembly;
                // derivation connection intentionally omitted — INCOMPLETE: parent traceability not yet confirmed
                attribute :>> priority       = CMNDEF::LevelKind::High;
                attribute :>> criticality    = CMNDEF::LevelKind::High;
                attribute :>> capabilityName = "FeatureA_FaultIsolation";
                attribute :>> performance    = "Feature A fault boundary enforced; zero Feature B impact on Feature A failure.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Inject a fatal fault into Feature A while Feature B is
                     * processing nominal load. PASS if Feature B continues
                     * without data loss or error.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "Feature B unaffected; 0 errors during Feature A fault";
                }
            }

            #derivation connection <'REQ-CAP-002-A-1-DRV'> drv_featureAHandoffFormat {
                end #original orig references integrationCapability::featureAIntegration;
                end #derive derv references integrationCapability::featureAIntegration::featureAHandoffFormat;
            }
            // featureAFaultIsolation (REQ-CAP-002-A-2): derivation intentionally omitted — INCOMPLETE
        }

        requirement <'REQ-CAP-002-B'> featureBIntegration : CapabilityRequirement {
            doc
            /* The CSCI shall integrate Feature B into the unified processing
             * pipeline with lossless data handoff at the Feature B output
             * boundary under nominal operating conditions.
             */
            doc Rationale
            /* Derived from SYS-ARCH-001. Feature B data must reach the integration
             * layer without loss to prevent downstream state inconsistencies.
             */
            subject sys : CoreSystem_Assembly;
            attribute :>> priority       = CMNDEF::LevelKind::High;
            attribute :>> criticality    = CMNDEF::LevelKind::High;
            attribute :>> capabilityName = "FeatureB_PipelineIntegration";
            attribute :>> performance    = "Zero data loss at Feature B output boundary.";
            part :>> criteria : VerificationCriteria {
                doc
                /* Run Feature B under nominal load for 30 minutes with the
                 * integration layer active. PASS if zero messages lost at handoff.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::test;
                attribute :>> threshold          = "0 messages lost at Feature B handoff";
            }

            requirement <'REQ-CAP-002-B-1'> featureBHandoffFormat : CapabilityRequirement {
                doc
                /* The CSCI shall pass data from Feature B to the integration layer
                 * in the internal canonical message format defined in IDD-INT-001.
                 */
                doc Rationale
                /* A canonical format at the handoff boundary decouples Feature B's
                 * internal representation from the integration layer, reducing
                 * interface brittleness across independent release cycles.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::High;
                attribute :>> criticality    = CMNDEF::LevelKind::High;
                attribute :>> capabilityName = "FeatureB_HandoffFormat";
                attribute :>> performance    = "All Feature B output conforms to IDD-INT-001 canonical format.";
                // criteria intentionally omitted — INCOMPLETE: IDD-INT-001 schema not yet baselined
            }

            requirement <'REQ-CAP-002-B-2'> featureBFaultIsolation : CapabilityRequirement {
                doc
                /* The CSCI shall isolate Feature B processing faults such that
                 * a Feature B failure does not interrupt or corrupt Feature A
                 * operation.
                 */
                doc Rationale
                /* Independent fault domains prevent a single subsystem failure
                 * from cascading into a total system outage, maintaining partial
                 * mission capability when Feature B is unavailable.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::High;
                attribute :>> criticality    = CMNDEF::LevelKind::High;
                attribute :>> capabilityName = "FeatureB_FaultIsolation";
                attribute :>> performance    = "Feature B fault boundary enforced; zero Feature A impact on Feature B failure.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Inject a fatal fault into Feature B while Feature A is
                     * processing nominal load. PASS if Feature A continues
                     * without data loss or error.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "Feature A unaffected; 0 errors during Feature B fault";
                }
            }

            #derivation connection <'REQ-CAP-002-B-1-DRV'> drv_featureBHandoffFormat {
                end #original orig references integrationCapability::featureBIntegration;
                end #derive derv references integrationCapability::featureBIntegration::featureBHandoffFormat;
            }
            #derivation connection <'REQ-CAP-002-B-2-DRV'> drv_featureBFaultIsolation {
                end #original orig references integrationCapability::featureBIntegration;
                end #derive derv references integrationCapability::featureBIntegration::featureBFaultIsolation;
            }
        }

        #derivation connection <'REQ-CAP-002-A-DRV'> drv_featureAIntegration {
            end #original orig references integrationCapability;
            end #derive derv references integrationCapability::featureAIntegration;
        }
        #derivation connection <'REQ-CAP-002-B-DRV'> drv_featureBIntegration {
            end #original orig references integrationCapability;
            end #derive derv references integrationCapability::featureBIntegration;
        }
    }

    requirement <'REQ-IFC-001'> externalDataInterface
            : ExternalDataInterface_Def {
        doc
        /* The CSCI shall implement a binary message interface to the
         * external data source conforming to ICD-EXT-001 revision C.
         */
        doc Rationale
        /* ExternalDataSource uses a fixed binary protocol in ICD-EXT-001
         * that cannot be modified. Conformance is a contractual criterion.
         */
        subject featureA : FeatureA_Component;
        attribute :>> source          = "ICD-EXT-001 Rev C";
        attribute :>> priority        = CMNDEF::LevelKind::High;
        attribute :>> criticality     = CMNDEF::LevelKind::High;
        attribute :>> interfaceName   = "ExternalDataSource_Interface";
        attribute :>> primaryEntity   = "CoreCSCI";
        attribute :>> secondaryEntity = "ExternalDataSource";
        attribute :>> protocol        = "Binary framed message protocol per ICD-EXT-001";
        attribute :>> messageFormat   = "256-byte header + variable payload + 4-byte CRC";
        attribute :>> dataName        = "ExternalDataMessage";
        attribute :>> dataType        = "Binary framed message";
        part :>> criteria : VerificationCriteria {
            doc
            /* Exercise all ICD-EXT-001 §3 message types with nominal and
             * boundary values (10 000 total messages).
             * PASS if zero encoding or decoding errors observed.
             */
            attribute :>> verificationMethod = VerificationMethodKind::test;
            attribute :>> threshold          = "0 errors in 10 000 messages";
        }

        requirement <'REQ-IFC-001-A'> messageFraming : InterfaceRequirement {
            doc
            /* The CSCI shall frame all messages to and from ExternalDataSource
             * using the 256-byte fixed header and variable-length payload format
             * defined in ICD-EXT-001 §4.1.
             */
            doc Rationale
            /* ICD-EXT-001 §4.1 mandates the header layout as a contractual
             * interface commitment with the external data provider. Non-conforming
             * frames are silently discarded by the external system.
             */
            subject featureA : FeatureA_Component;
            attribute :>> priority        = CMNDEF::LevelKind::High;
            attribute :>> criticality     = CMNDEF::LevelKind::High;
            attribute :>> interfaceName   = "ExternalDataSource_FrameFormat";
            attribute :>> primaryEntity   = "CoreCSCI";
            attribute :>> secondaryEntity = "ExternalDataSource";
            attribute :>> messageFormat   = "256-byte fixed header + variable payload per ICD-EXT-001 §4.1";
            attribute :>> dataName        = "ExternalDataFrame";
            attribute :>> dataType        = "Binary framed message";
            part :>> criteria : VerificationCriteria {
                doc
                /* Send 1000 messages covering all message types from ICD-EXT-001 §3.
                 * PASS if the external source accepts all frames without format rejection.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::test;
                attribute :>> threshold          = "0 format rejections in 1000 frames";
            }

            requirement <'REQ-IFC-001-A-1'> headerFieldLayout : InterfaceRequirement {
                doc
                /* The CSCI shall populate all mandatory fields of the 256-byte
                 * message header in the byte order and at the offsets defined
                 * in ICD-EXT-001 §4.1 Table 4-1.
                 */
                doc Rationale
                /* The external system performs a direct memory mapping of the
                 * header; incorrect field order or offset causes silent
                 * misinterpretation of all subsequent header fields.
                 */
                subject featureA : FeatureA_Component;
                // derivation connection intentionally omitted — INCOMPLETE: awaiting ICD-EXT-001 Rev D update
                attribute :>> priority        = CMNDEF::LevelKind::High;
                attribute :>> criticality     = CMNDEF::LevelKind::High;
                attribute :>> interfaceName   = "ExternalDataSource_HeaderFields";
                attribute :>> primaryEntity   = "CoreCSCI";
                attribute :>> secondaryEntity = "ExternalDataSource";
                attribute :>> messageFormat   = "Mandatory fields at byte offsets per ICD-EXT-001 §4.1 Table 4-1";
                attribute :>> dataName        = "MessageHeader";
                attribute :>> dataType        = "256-byte binary fixed header";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Capture ten message headers and verify each field against
                     * ICD-EXT-001 §4.1 Table 4-1 using a protocol analyzer.
                     * PASS if all mandatory fields are at the correct offsets.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "100% field-offset conformance across 10 samples";
                }
            }

            requirement <'REQ-IFC-001-A-2'> payloadBoundaryEncoding : InterfaceRequirement {
                doc
                /* The CSCI shall encode the payload length in bytes at the
                 * header offset field defined in ICD-EXT-001 §4.1, allowing
                 * the receiver to correctly extract the variable-length payload.
                 */
                doc Rationale
                /* Without an accurate length field the receiver cannot determine
                 * payload boundaries, causing framing errors on all subsequent
                 * messages in the stream.
                 */
                subject featureA : FeatureA_Component;
                attribute :>> priority        = CMNDEF::LevelKind::High;
                attribute :>> criticality     = CMNDEF::LevelKind::High;
                attribute :>> interfaceName   = "ExternalDataSource_PayloadLength";
                attribute :>> primaryEntity   = "CoreCSCI";
                attribute :>> secondaryEntity = "ExternalDataSource";
                attribute :>> messageFormat   = "Payload length as 16-bit unsigned integer at header offset per ICD-EXT-001 §4.1";
                attribute :>> dataName        = "PayloadLengthField";
                attribute :>> dataType        = "16-bit unsigned integer";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Send messages with payloads of 0, 1, 127, 128, and 65535
                     * bytes. PASS if the receiver correctly extracts each payload
                     * using only the length field.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "Correct payload extraction at all boundary sizes";
                }
            }

            // headerFieldLayout (REQ-IFC-001-A-1): derivation intentionally omitted — INCOMPLETE
            #derivation connection <'REQ-IFC-001-A-2-DRV'> drv_payloadBoundaryEncoding {
                end #original orig references externalDataInterface::messageFraming;
                end #derive derv references externalDataInterface::messageFraming::payloadBoundaryEncoding;
            }
        }

        requirement <'REQ-IFC-001-B'> messageIntegrity : InterfaceRequirement {
            doc
            /* The CSCI shall append a 4-byte CRC-32 to each outbound message
             * and shall reject and log any inbound message whose CRC-32 does
             * not match the computed value.
             */
            doc Rationale
            /* ICD-EXT-001 §4.3 requires CRC-32 on all message exchanges.
             * Silent data corruption would propagate undetectable errors into
             * downstream processing pipelines.
             */
            subject featureA : FeatureA_Component;
            attribute :>> priority        = CMNDEF::LevelKind::High;
            attribute :>> criticality     = CMNDEF::LevelKind::High;
            attribute :>> interfaceName   = "ExternalDataSource_Integrity";
            attribute :>> primaryEntity   = "CoreCSCI";
            attribute :>> secondaryEntity = "ExternalDataSource";
            attribute :>> protocol        = "CRC-32 per ICD-EXT-001 §4.3";
            attribute :>> dataName        = "MessageCRC";
            attribute :>> dataType        = "32-bit CRC (ISO 3309)";
            part :>> criteria : VerificationCriteria {
                doc
                /* Inject 500 valid messages and 100 messages with deliberately
                 * corrupted CRCs. PASS if all valid messages are accepted and
                 * all corrupted messages are rejected and logged.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::test;
                attribute :>> threshold          = "100% corrupt-CRC rejection; 0 silent failures";
            }

            requirement <'REQ-IFC-001-B-1'> crcGeneration : InterfaceRequirement {
                doc
                /* The CSCI shall compute a CRC-32 using the ISO 3309 polynomial
                 * and append it to every outbound message before transmission.
                 */
                doc Rationale
                /* CRC-32 generation is mandated by ICD-EXT-001 §4.3. The ISO 3309
                 * polynomial is required by the external system's hardware decoder
                 * and cannot be substituted.
                 */
                subject featureA : FeatureA_Component;
                attribute :>> priority        = CMNDEF::LevelKind::High;
                attribute :>> criticality     = CMNDEF::LevelKind::High;
                attribute :>> interfaceName   = "ExternalDataSource_CRCGen";
                attribute :>> primaryEntity   = "CoreCSCI";
                attribute :>> secondaryEntity = "ExternalDataSource";
                attribute :>> protocol        = "CRC-32 per ISO 3309 polynomial appended to every outbound message";
                attribute :>> dataName        = "OutboundCRC";
                attribute :>> dataType        = "32-bit CRC (ISO 3309)";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Send 1000 known messages and verify CRC-32 of each using
                     * a reference implementation. PASS if all CRCs match.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "CRC-32 matches reference for all 1000 messages";
                }
            }

            requirement <'REQ-IFC-001-B-2'> crcRejectionLogging : InterfaceRequirement {
                doc
                /* The CSCI shall log every inbound message rejected for a CRC
                 * failure, recording the timestamp, source address, and the
                 * computed versus received CRC values.
                 */
                doc Rationale
                /* CRC failure records are required for post-event forensic
                 * analysis per COMPLIANCE-001 §5. Without a log, the source
                 * and frequency of data corruption cannot be determined.
                 */
                subject featureA : FeatureA_Component;
                attribute :>> priority        = CMNDEF::LevelKind::High;
                attribute :>> criticality     = CMNDEF::LevelKind::High;
                attribute :>> interfaceName   = "ExternalDataSource_CRCLog";
                attribute :>> primaryEntity   = "CoreCSCI";
                attribute :>> secondaryEntity = "ExternalDataSource";
                attribute :>> protocol        = "Structured CRC-failure log entry per COMPLIANCE-001 §5";
                attribute :>> dataName        = "CRCRejectionRecord";
                attribute :>> dataType        = "Structured log entry with timestamp, source address, and CRC mismatch detail";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Inject 50 messages with corrupted CRCs and inspect the log.
                     * PASS if every rejection is logged with timestamp, source
                     * address, computed CRC, and received CRC.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::inspect;
                    attribute :>> threshold          = "All 50 rejections logged with complete fields";
                }
            }

            #derivation connection <'REQ-IFC-001-B-1-DRV'> drv_crcGeneration {
                end #original orig references externalDataInterface::messageIntegrity;
                end #derive derv references externalDataInterface::messageIntegrity::crcGeneration;
            }
            #derivation connection <'REQ-IFC-001-B-2-DRV'> drv_crcRejectionLogging {
                end #original orig references externalDataInterface::messageIntegrity;
                end #derive derv references externalDataInterface::messageIntegrity::crcRejectionLogging;
            }
        }

        #derivation connection <'REQ-IFC-001-A-DRV'> drv_messageFraming {
            end #original orig references externalDataInterface;
            end #derive derv references externalDataInterface::messageFraming;
        }
        #derivation connection <'REQ-IFC-001-B-DRV'> drv_messageIntegrity {
            end #original orig references externalDataInterface;
            end #derive derv references externalDataInterface::messageIntegrity;
        }
    }

    requirement <'REQ-QUA-001'> systemAvailability
            : SystemAvailability_Def {
        doc
        /* The CSCI shall achieve a minimum operational availability of
         * 99.5% over any 30-day measurement period.
         */
        doc Rationale
        /* Mission profile requires near-continuous operation. Planned
         * maintenance windows must not exceed 0.5% of the measurement period.
         * Derived from SYS-RELY-001.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> source           = "SYS-RELY-001";
        attribute :>> priority         = CMNDEF::LevelKind::High;
        attribute :>> criticality      = CMNDEF::LevelKind::High;
        attribute :>> qualityAttribute = "Availability";
        part :>> criteria : VerificationCriteria {
            doc
            /* Reliability analysis using component MTBF data, 30-day window,
             * normal operating environment, planned maintenance excluded.
             * PASS if predicted availability >= 99.5%.
             */
            attribute :>> verificationMethod = VerificationMethodKind::analyze;
            attribute :>> threshold          = "99.5% over 30-day period";
        }

        requirement <'REQ-QUA-001-A'> plannedMaintenanceWindow : QualityRequirement {
            doc
            /* The CSCI shall require no more than 3.6 hours of total planned
             * downtime within any 30-day measurement period.
             */
            doc Rationale
            /* 3.6 hours per 30 days equals 0.5% of the period — the full
             * planned-maintenance allocation under the 99.5% availability
             * requirement. Exceeding this budget violates REQ-QUA-001.
             */
            subject sys : CoreSystem_Assembly;
            attribute :>> priority         = CMNDEF::LevelKind::High;
            attribute :>> criticality      = CMNDEF::LevelKind::High;
            attribute :>> qualityAttribute = "PlannedMaintenanceDowntime";
            part :>> criteria : VerificationCriteria {
                doc
                /* Analyze maintenance schedule records over a 90-day baseline.
                 * PASS if total planned downtime in each 30-day window <= 3.6 h.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::analyze;
                attribute :>> threshold          = "<= 3.6 hours planned downtime per 30-day period";
            }

            requirement <'REQ-QUA-001-A-1'> maintenanceWindowDuration : QualityRequirement {
                doc
                /* The CSCI shall complete each individual planned maintenance
                 * event within a maintenance window of no more than 2 hours.
                 */
                doc Rationale
                /* Limiting individual events to 2 hours allows at least one full
                 * maintenance event plus a 1.6-hour reserve within the 3.6-hour
                 * monthly budget, matching typical release-upgrade cadences.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority         = CMNDEF::LevelKind::Medium;
                attribute :>> criticality      = CMNDEF::LevelKind::Medium;
                attribute :>> qualityAttribute = "MaintenanceWindowDuration";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Review maintenance event records from the last 6 months.
                     * PASS if every individual maintenance event completed within
                     * 2 hours.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::analyze;
                    attribute :>> threshold          = "Every maintenance event <= 2 hours";
                }
            }

            requirement <'REQ-QUA-001-A-2'> maintenanceAdvanceNotice : QualityRequirement {
                doc
                /* The CSCI operator interface shall display a maintenance
                 * notification at least 24 hours before a scheduled maintenance
                 * window begins.
                 */
                doc Rationale
                /* 24-hour advance notice allows operational staff to adjust
                 * mission schedules to avoid the maintenance window impact and
                 * arrange any necessary handover.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority         = CMNDEF::LevelKind::Medium;
                attribute :>> criticality      = CMNDEF::LevelKind::Low;
                attribute :>> qualityAttribute = "MaintenanceAdvanceNotice";
                // criteria intentionally omitted — INCOMPLETE: operator interface not yet designed
            }

            #derivation connection <'REQ-QUA-001-A-1-DRV'> drv_maintenanceWindowDuration {
                end #original orig references systemAvailability::plannedMaintenanceWindow;
                end #derive derv references systemAvailability::plannedMaintenanceWindow::maintenanceWindowDuration;
            }
            #derivation connection <'REQ-QUA-001-A-2-DRV'> drv_maintenanceAdvanceNotice {
                end #original orig references systemAvailability::plannedMaintenanceWindow;
                end #derive derv references systemAvailability::plannedMaintenanceWindow::maintenanceAdvanceNotice;
            }
        }

        requirement <'REQ-QUA-001-B'> unplannedOutageBudget : QualityRequirement {
            doc
            /* The CSCI shall resume normal operation within 15 minutes of an
             * unplanned fault being isolated, bounding the contribution of any
             * single outage event to the availability budget.
             */
            doc Rationale
            /* Bounding MTTR to 15 minutes limits any single fault's availability
             * impact to 0.035% of a 30-day period, preserving headroom within
             * the 0.5% total unavailability budget for multiple concurrent events.
             */
            subject sys : CoreSystem_Assembly;
            attribute :>> priority         = CMNDEF::LevelKind::High;
            attribute :>> criticality      = CMNDEF::LevelKind::High;
            attribute :>> qualityAttribute = "MaxUnplannedOutageDuration";
            part :>> criteria : VerificationCriteria {
                doc
                /* Analyze MTTR data from fault injection testing over 20 fault
                 * scenarios. PASS if all recovery times are <= 15 minutes.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::analyze;
                attribute :>> threshold          = "Recovery within 15 minutes for all fault scenarios";
            }

            requirement <'REQ-QUA-001-B-1'> faultDetectionLatency : QualityRequirement {
                doc
                /* The CSCI built-in health monitor shall detect and raise an
                 * alarm for any processing fault within 5 seconds of the
                 * fault occurrence.
                 */
                doc Rationale
                /* 5-second detection is the prerequisite for meeting the 15-minute
                 * MTTR target; undetected faults consume the recovery time budget
                 * without triggering the automated recovery sequence.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority         = CMNDEF::LevelKind::High;
                attribute :>> criticality      = CMNDEF::LevelKind::High;
                attribute :>> qualityAttribute = "FaultDetectionLatency";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Inject 10 distinct fault types and measure time from fault
                     * injection to alarm raised. PASS if all detection times
                     * are <= 5 seconds.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "All 10 fault types detected within 5 seconds";
                }
            }

            requirement <'REQ-QUA-001-B-2'> faultRecoveryProcedure : QualityRequirement {
                doc
                /* The CSCI shall automatically attempt restart of any failed
                 * processing component and restore service without operator
                 * intervention within 15 minutes of fault detection.
                 */
                doc Rationale
                /* Automated recovery eliminates operator reaction time as a
                 * variable in the availability budget and ensures 24/7 uptime
                 * without continuous operator staffing requirements.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority         = CMNDEF::LevelKind::High;
                attribute :>> criticality      = CMNDEF::LevelKind::High;
                attribute :>> qualityAttribute = "AutomatedFaultRecovery";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Inject a fatal component fault with no operator present.
                     * PASS if the component restarts and normal operation resumes
                     * within 15 minutes without any operator action.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::test;
                    attribute :>> threshold          = "Service restored within 15 min; 0 operator actions";
                }
            }

            #derivation connection <'REQ-QUA-001-B-1-DRV'> drv_faultDetectionLatency {
                end #original orig references systemAvailability::unplannedOutageBudget;
                end #derive derv references systemAvailability::unplannedOutageBudget::faultDetectionLatency;
            }
            #derivation connection <'REQ-QUA-001-B-2-DRV'> drv_faultRecoveryProcedure {
                end #original orig references systemAvailability::unplannedOutageBudget;
                end #derive derv references systemAvailability::unplannedOutageBudget::faultRecoveryProcedure;
            }
        }

        #derivation connection <'REQ-QUA-001-A-DRV'> drv_plannedMaintenanceWindow {
            end #original orig references systemAvailability;
            end #derive derv references systemAvailability::plannedMaintenanceWindow;
        }
        #derivation connection <'REQ-QUA-001-B-DRV'> drv_unplannedOutageBudget {
            end #original orig references systemAvailability;
            end #derive derv references systemAvailability::unplannedOutageBudget;
        }
    }

    requirement <'REQ-DSN-001'> programmingLanguageConstraint
            : ProgrammingLanguageConstraint_Def {
        doc
        /* The CSCI shall be implemented in C++ (ISO/IEC 14882:2017) or
         * Python 3.10+ as specified in the Software Development Plan.
         */
        doc Rationale
        /* Organizational toolchain and code review processes support only
         * these languages. No waiver exists for other languages.
         * Derived from SDP-001 §4.2.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> source         = "SDP-001 §4.2";
        attribute :>> priority       = CMNDEF::LevelKind::Medium;
        attribute :>> criticality    = CMNDEF::LevelKind::Medium;
        attribute :>> constraintText = "C++ (ISO/IEC 14882:2017) or Python 3.10+ only.";
        part :>> criteria : VerificationCriteria {
            doc
            /* Code review at CDR confirms all source files use approved languages.
             * PASS if 100% of source files are in approved languages with no waivers.
             */
            attribute :>> verificationMethod = VerificationMethodKind::inspect;
            attribute :>> threshold          = "100% approved languages";
        }

        requirement <'REQ-DSN-001-A'> languageVersionCompliance : DesignConstraintRequirement {
            doc
            /* The CSCI implementation shall use only language features defined
             * in C++ ISO/IEC 14882:2017 or Python 3.10+; no deprecated features
             * or compiler-specific extensions shall be used.
             */
            doc Rationale
            /* Restricting to the defined standard version prevents portability
             * issues and ensures the code compiles correctly on all
             * project-approved build environments without modification.
             */
            subject sys : CoreSystem_Assembly;
            attribute :>> priority       = CMNDEF::LevelKind::Medium;
            attribute :>> criticality    = CMNDEF::LevelKind::Medium;
            attribute :>> constraintText = "C++ ISO/IEC 14882:2017 or Python 3.10+ features only; no deprecated or non-standard extensions.";
            part :>> criteria : VerificationCriteria {
                doc
                /* Inspect build logs and compiler flags for all source files.
                 * PASS if no deprecated feature warnings or extension flags
                 * appear in any build configuration.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::inspect;
                attribute :>> threshold          = "Zero deprecated-feature warnings; no extension flags";
            }

            requirement <'REQ-DSN-001-A-1'> cppStandardConformance : DesignConstraintRequirement {
                doc
                /* All C++ source files in the CSCI shall compile without warnings
                 * under the ISO/IEC 14882:2017 standard with -Wpedantic enabled
                 * and no compiler extension flags.
                 */
                doc Rationale
                /* Clean compilation under -Wpedantic with no extensions ensures
                 * strict standard conformance and catches non-portable constructs
                 * at compile time before they reach integration testing.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::Medium;
                attribute :>> criticality    = CMNDEF::LevelKind::Medium;
                attribute :>> constraintText = "C++ clean under -std=c++17 -Wpedantic with no extension flags.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Compile all C++ sources with -std=c++17 -Wpedantic -Werror.
                     * PASS if the build succeeds with zero warnings or errors.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::inspect;
                    attribute :>> threshold          = "Zero warnings under -std=c++17 -Wpedantic -Werror";
                }
            }

            requirement <'REQ-DSN-001-A-2'> pythonVersionConformance : DesignConstraintRequirement {
                doc
                /* All Python source files shall be syntactically and semantically
                 * compatible with Python 3.10 and shall not use any syntax or API
                 * deprecated in Python 3.10 or later.
                 */
                doc Rationale
                /* Python 3.10 is the project baseline runtime. Deprecated API
                 * usage breaks the build when the deprecated feature is removed
                 * in a subsequent Python release.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::Medium;
                attribute :>> criticality    = CMNDEF::LevelKind::Medium;
                attribute :>> constraintText = "Python 3.10 compatible; no deprecated syntax or API usage.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Run pyupgrade --py310-plus on all Python sources and verify
                     * no changes are required. PASS if pyupgrade reports zero
                     * deprecated constructs.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::inspect;
                    attribute :>> threshold          = "Zero deprecated constructs per pyupgrade --py310-plus";
                }
            }

            #derivation connection <'REQ-DSN-001-A-1-DRV'> drv_cppStandardConformance {
                end #original orig references programmingLanguageConstraint::languageVersionCompliance;
                end #derive derv references programmingLanguageConstraint::languageVersionCompliance::cppStandardConformance;
            }
            #derivation connection <'REQ-DSN-001-A-2-DRV'> drv_pythonVersionConformance {
                end #original orig references programmingLanguageConstraint::languageVersionCompliance;
                end #derive derv references programmingLanguageConstraint::languageVersionCompliance::pythonVersionConformance;
            }
        }

        requirement <'REQ-DSN-001-B'> staticAnalysisCompliance : DesignConstraintRequirement {
            doc
            /* All CSCI source code shall pass the project-approved static analysis
             * tool suite at the strictest applicable rule set with no unsuppressed
             * violations before delivery.
             */
            doc Rationale
            /* Automated static analysis gates enforce coding standards consistently
             * across all contributors and detect defect classes — null dereferences,
             * race conditions, resource leaks — not caught by compilation or test.
             */
            subject sys : CoreSystem_Assembly;
            attribute :>> priority       = CMNDEF::LevelKind::Medium;
            attribute :>> criticality    = CMNDEF::LevelKind::Medium;
            attribute :>> constraintText = "Static analysis clean at strictest applicable rule set per SDP-001 §4.3.";
            part :>> criteria : VerificationCriteria {
                doc
                /* Run the approved static analysis suite on the full codebase.
                 * PASS if zero unsuppressed violations are reported at the
                 * strictest rule level.
                 */
                attribute :>> verificationMethod = VerificationMethodKind::inspect;
                attribute :>> threshold          = "Zero unsuppressed violations at strictest rule level";
            }

            requirement <'REQ-DSN-001-B-1'> cppStaticAnalysis : DesignConstraintRequirement {
                doc
                /* All C++ source files shall pass MISRA C++:2023 Advisory level
                 * rules using the project-approved static analysis tool, with no
                 * suppressions lacking documented justification.
                 */
                doc Rationale
                /* MISRA C++:2023 is mandated by the program safety plan.
                 * Advisory-level compliance catches the majority of defect classes
                 * without undue constraint on idiomatic modern C++.
                 */
                subject sys : CoreSystem_Assembly;
                attribute :>> priority       = CMNDEF::LevelKind::Medium;
                attribute :>> criticality    = CMNDEF::LevelKind::Medium;
                attribute :>> constraintText = "MISRA C++:2023 Advisory clean via project-approved static analysis tool.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Run the approved C++ static analysis tool in MISRA C++:2023
                     * Advisory mode. PASS if zero unsuppressed findings remain
                     * in the pre-delivery build report.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::inspect;
                    attribute :>> threshold          = "Zero unsuppressed MISRA C++:2023 Advisory findings";
                }
            }

            requirement <'REQ-DSN-001-B-2'> pythonStaticAnalysis : DesignConstraintRequirement {
                doc
                /* All Python source files shall pass ruff at error and warning
                 * severity levels with no unsuppressed violations prior to delivery.
                 */
                doc Rationale
                /* ruff provides fast, comprehensive Python linting including type
                 * errors, unused imports, and common defect patterns. Error and
                 * warning level compliance is the minimum bar for deliverable code.
                 */
                subject sys : CoreSystem_Assembly;
                // derivation connection intentionally omitted — INCOMPLETE: tool selection pending SDP-001 Rev B
                attribute :>> priority       = CMNDEF::LevelKind::Medium;
                attribute :>> criticality    = CMNDEF::LevelKind::Medium;
                attribute :>> constraintText = "Python ruff clean at error and warning severity with no unsuppressed violations.";
                part :>> criteria : VerificationCriteria {
                    doc
                    /* Run ruff on all Python sources with --select E,W.
                     * PASS if the report shows zero violations with no
                     * suppression comments lacking justification.
                     */
                    attribute :>> verificationMethod = VerificationMethodKind::inspect;
                    attribute :>> threshold          = "Zero ruff E/W violations; no unjustified suppressions";
                }
            }

            #derivation connection <'REQ-DSN-001-B-1-DRV'> drv_cppStaticAnalysis {
                end #original orig references programmingLanguageConstraint::staticAnalysisCompliance;
                end #derive derv references programmingLanguageConstraint::staticAnalysisCompliance::cppStaticAnalysis;
            }
            // pythonStaticAnalysis (REQ-DSN-001-B-2): derivation intentionally omitted — INCOMPLETE
        }

        #derivation connection <'REQ-DSN-001-A-DRV'> drv_languageVersionCompliance {
            end #original orig references programmingLanguageConstraint;
            end #derive derv references programmingLanguageConstraint::languageVersionCompliance;
        }
        #derivation connection <'REQ-DSN-001-B-DRV'> drv_staticAnalysisCompliance {
            end #original orig references programmingLanguageConstraint;
            end #derive derv references programmingLanguageConstraint::staticAnalysisCompliance;
        }
    }

    // ════════════════════════════════════════════════════════════════════════
    // INCOMPLETE requirement — passes VALID checks but has completeness gaps.
    // @RiskItem demonstrates risk annotation on a requirement.
    // ════════════════════════════════════════════════════════════════════════

    @RiskItem {
        riskId      = "RISK-CORE-REQ-001";
        title       = "BIT requirement lacks acceptance criteria";
        category    = RiskCategory::Technical;
        probability = LevelKind::Medium;
        impact      = LevelKind::Medium;
        exposure    = 4;
        status      = RiskStatus::Open;
        description = "REQ-CAP-003 (incompleteReq) has no defined verification
                       criteria or threshold. Without these, acceptance testing
                       for the BIT capability cannot be objectively assessed.";
        mitigation  = "Complete the verification criteria for REQ-CAP-003 before CDR.
                       Assign to systems engineer to draft test procedure.";
        owner       = "Systems Engineer";
    }

    // INCOMPLETE requirement — passes VALID checks but has completeness gaps.
    // Missing: source, priority, criticality, criteria.
    // req_validate.py will report this as INCOMPLETE.
    // ════════════════════════════════════════════════════════════════════════

    requirement <'REQ-CAP-003'> incompleteReq
            : ProcessingCapability_Def {
        doc
        /* The CSCI shall provide a built-in self-test capability that
         * verifies all subsystem interfaces during initialization.
         */
        doc Rationale
        /* Early fault detection during initialization prevents the system
         * from entering operational mode with undetected hardware faults.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> capabilityName = "BuiltInSelfTest";
        attribute :>> timing         = "Completes within 30 seconds of power-on.";
        // source, priority, criticality intentionally omitted — INCOMPLETE demo
        // criteria intentionally omitted — INCOMPLETE demo
    }

    // ════════════════════════════════════════════════════════════════════════
    // INVALID requirements — fail VALID checks.
    // These demonstrate what req_validate.py catches.
    // ════════════════════════════════════════════════════════════════════════

    // INVALID: no short-name ID (HasId violation)
    requirement invalidReq_noId : ProcessingCapability_Def {
        doc
        /* The CSCI shall log all interface transactions with sufficient
         * detail to support post-event audit and replay.
         */
        doc Rationale
        /* Audit logs are required by the program compliance framework and
         * are essential for incident investigation.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> capabilityName = "AuditLogging";
        attribute :>> source         = "COMPLIANCE-001";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
    }

    // INVALID: no doc block (HasText violation)
    requirement <'REQ-CAP-005'> invalidReq_noDoc
            : ProcessingCapability_Def {
        doc Rationale
        /* Throughput is a contractual performance threshold derived from
         * the program operational concept document.
         */
        subject sys : CoreSystem_Assembly;
        attribute :>> capabilityName = "PeakThroughput";
        attribute :>> source         = "PA-OCD §4.2";
        attribute :>> priority       = CMNDEF::LevelKind::High;
        attribute :>> criticality    = CMNDEF::LevelKind::High;
        attribute :>> throughput     = "5000 messages/second minimum.";
    }

    // INVALID: no doc Rationale block (HasRationale violation)
    requirement <'REQ-QUA-002'> invalidReq_noRationale
            : SystemAvailability_Def {
        doc
        /* The CSCI shall support online diagnostics accessible to the
         * system administrator without interrupting operational processing.
         */
        // doc Rationale intentionally absent — INVALID demo
        subject sys : CoreSystem_Assembly;
        attribute :>> qualityAttribute = "Maintainability";
        attribute :>> source           = "SDP-001 §5.1";
        attribute :>> priority         = CMNDEF::LevelKind::Medium;
        attribute :>> criticality      = CMNDEF::LevelKind::Medium;
    }
}

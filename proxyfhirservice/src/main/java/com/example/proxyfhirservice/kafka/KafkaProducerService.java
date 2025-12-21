package com.example.proxyfhirservice.kafka;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;

@Service
public class KafkaProducerService {

    private static final Logger log =
            LoggerFactory.getLogger(KafkaProducerService.class);

    public static final String RAW_FHIR_TOPIC = "fhir.data.raw";

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public KafkaProducerService(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    /**
     * 🔹 Publie un EVENT FHIR (léger) vers Kafka
     */
    public void publishFhirRawEvent(Long bundleId, String patientId) {

        Map<String, Object> message = Map.of(
                "bundleId", bundleId,
                "patientId", patientId,
                "createdAt", Instant.now().toString()
        );

        kafkaTemplate.send(RAW_FHIR_TOPIC, patientId, message);

        log.info(
                "📤 FHIR RAW EVENT | topic={} | patientId={} | bundleId={}",
                RAW_FHIR_TOPIC,
                patientId,
                bundleId
        );
    }
}

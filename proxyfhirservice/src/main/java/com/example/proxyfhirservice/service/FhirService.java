package com.example.proxyfhirservice.service;

import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.rest.client.api.IGenericClient;
import ca.uhn.fhir.rest.gclient.ICriterion;
import com.example.proxyfhirservice.kafka.KafkaProducerService;
import com.example.proxyfhirservice.model.FhirBundleEntity;
import com.example.proxyfhirservice.repository.FhirBundleRepository;
import org.hl7.fhir.r4.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
public class FhirService {

    private static final Logger logger = LoggerFactory.getLogger(FhirService.class);

    private final FhirContext fhirContext;
    private final IGenericClient fhirClient;
    private final FhirBundleRepository repository;
    private final KafkaProducerService kafkaProducer;

    public FhirService(
            FhirContext fhirContext,
            IGenericClient fhirClient,
            FhirBundleRepository repository,
            KafkaProducerService kafkaProducer
    ) {
        this.fhirContext = fhirContext;
        this.fhirClient = fhirClient;
        this.repository = repository;
        this.kafkaProducer = kafkaProducer;
    }

    /**
     * 🔹 Fetch FHIR → store DB → publish Kafka EVENT
     */
    public FhirBundleEntity fetchAndStorePatientBundle(String patientId) {

        Optional<FhirBundleEntity> existing =
                repository.findByPatientRef(patientId);

        FhirBundleEntity entity;

        if (existing.isPresent()) {
            logger.info("Patient {} already in DB → reuse bundle", patientId);
            entity = existing.get();
        } else {
            logger.info("Fetching FHIR data for patient {}", patientId);

            Bundle bundle = buildPatientBundle(patientId);

            String bundleJson = fhirContext
                    .newJsonParser()
                    .encodeResourceToString(bundle);

            entity = new FhirBundleEntity();
            entity.setPatientRef(patientId);
            entity.setSource("HAPI_FHIR");
            entity.setBundleJson(bundleJson);

            entity = repository.save(entity);

            logger.info("FHIR bundle stored with ID {}", entity.getId());
        }

        // ✅ EVENT KAFKA (léger, métier)
        kafkaProducer.publishFhirRawEvent(
                entity.getId(),
                entity.getPatientRef()
        );

        logger.info("📤 Kafka event published for patient {}", patientId);

        return entity;
    }

    // ----------------------------------------------------

    private Bundle buildPatientBundle(String patientId) {

        Bundle bundle = new Bundle();
        bundle.setType(Bundle.BundleType.COLLECTION);
        bundle.setId("bundle-" + patientId);

        List<Bundle.BundleEntryComponent> entries = new ArrayList<>();

        try {
            Patient patient = fhirClient.read()
                    .resource(Patient.class)
                    .withId(patientId)
                    .execute();
            entries.add(entry(patient));

            addSearch(entries, Observation.class, Observation.SUBJECT.hasId(patientId));
            addSearch(entries, Condition.class, Condition.SUBJECT.hasId(patientId));
            addSearch(entries, MedicationRequest.class, MedicationRequest.SUBJECT.hasId(patientId));
            addSearch(entries, DiagnosticReport.class, DiagnosticReport.SUBJECT.hasId(patientId));

        } catch (Exception e) {
            logger.warn("FHIR fetch error for {}: {}", patientId, e.getMessage());
        }

        bundle.setEntry(entries);
        bundle.setTotal(entries.size());

        logger.info("FHIR bundle built → {} resources", entries.size());
        return bundle;
    }

    private <T extends Resource> void addSearch(
            List<Bundle.BundleEntryComponent> entries,
            Class<T> type,
            ICriterion<?> criterion
    ) {
        Bundle result = fhirClient.search()
                .forResource(type)
                .where(criterion)
                .count(100)
                .returnBundle(Bundle.class)
                .execute();

        if (result != null && result.hasEntry()) {
            for (Bundle.BundleEntryComponent e : result.getEntry()) {
                entries.add(entry(e.getResource()));
            }
        }
    }

    private Bundle.BundleEntryComponent entry(Resource resource) {
        Bundle.BundleEntryComponent e = new Bundle.BundleEntryComponent();
        e.setResource(resource);
        e.setFullUrl(resource.getResourceType() + "/" +
                resource.getIdElement().getIdPart());
        return e;
    }
}

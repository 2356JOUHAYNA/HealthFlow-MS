package com.example.proxyfhirservice.controller;

import com.example.proxyfhirservice.model.FhirBundleEntity;
import com.example.proxyfhirservice.service.FhirService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/fhir")
@CrossOrigin(origins = "*")
public class ProxyFhirController {

    private static final Logger logger = LoggerFactory.getLogger(ProxyFhirController.class);

    private final FhirService fhirService;

    public ProxyFhirController(FhirService fhirService) {
        this.fhirService = fhirService;
    }

    /**
     * 🔹 Synchroniser un patient (Patient + Observation + Condition + etc.)
     */
    @PostMapping("/sync/patient/{patientId}")
    public ResponseEntity<Map<String, Object>> syncPatient(@PathVariable String patientId) {

        logger.info("Sync FHIR patient {}", patientId);
        Map<String, Object> response = new HashMap<>();

        try {
            FhirBundleEntity entity = fhirService.fetchAndStorePatientBundle(patientId);

            if (entity == null) {
                response.put("status", "skipped");
                response.put("message", "Patient already synchronized");
                response.put("patientId", patientId);
                return ResponseEntity.ok(response);
            }

            response.put("status", "success");
            response.put("message", "Patient synchronized successfully");
            response.put("bundleId", entity.getId());
            response.put("patientId", patientId);
            response.put("timestamp", entity.getCreatedAt());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            logger.error("Error syncing patient {}", patientId, e);

            response.put("status", "error");
            response.put("message", e.getMessage());
            response.put("patientId", patientId);

            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    /**
     * 🔹 Synchronisation batch de plusieurs patients
     */
    @PostMapping("/sync/patients")
    public ResponseEntity<Map<String, Object>> syncPatients(@RequestBody Map<String, Object> request) {

        Map<String, Object> response = new HashMap<>();

        @SuppressWarnings("unchecked")
        List<String> patientIds = (List<String>) request.get("patientIds");

        if (patientIds == null || patientIds.isEmpty()) {
            response.put("status", "error");
            response.put("message", "patientIds is required");
            return ResponseEntity.badRequest().body(response);
        }

        int success = 0, skipped = 0, errors = 0;
        List<Map<String, Object>> results = new ArrayList<>();

        for (String patientId : patientIds) {
            try {
                FhirBundleEntity entity = fhirService.fetchAndStorePatientBundle(patientId);

                Map<String, Object> r = new HashMap<>();
                r.put("patientId", patientId);

                if (entity == null) {
                    r.put("status", "skipped");
                    skipped++;
                } else {
                    r.put("status", "success");
                    r.put("bundleId", entity.getId());
                    success++;
                }

                results.add(r);

            } catch (Exception e) {
                Map<String, Object> r = new HashMap<>();
                r.put("patientId", patientId);
                r.put("status", "error");
                r.put("error", e.getMessage());
                results.add(r);
                errors++;
            }
        }

        response.put("status", "completed");
        response.put("summary", Map.of(
                "total", patientIds.size(),
                "success", success,
                "skipped", skipped,
                "errors", errors
        ));
        response.put("results", results);

        return ResponseEntity.ok(response);
    }

    /**
     * 🔹 Health check
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "proxyfhir");
        response.put("status", "UP");
        response.put("timestamp", System.currentTimeMillis());
        return ResponseEntity.ok(response);
    }

    /**
     * 🔹 Informations service
     */
    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> info() {

        return ResponseEntity.ok(
                Map.of(
                        "service", "HealthFlow ProxyFHIR",
                        "version", "1.0.0",
                        "description", "FHIR ingestion & Kafka publisher",
                        "endpoints", List.of(
                                "POST /api/v1/fhir/sync/patient/{id}",
                                "POST /api/v1/fhir/sync/patients",
                                "GET  /api/v1/fhir/health",
                                "GET  /api/v1/fhir/info"
                        )
                )
        );
    }
}

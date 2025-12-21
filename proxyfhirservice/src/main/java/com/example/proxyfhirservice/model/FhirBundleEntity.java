package com.example.proxyfhirservice.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "fhir_bundles")
public class FhirBundleEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "patient_ref", nullable = false, unique = true)
    private String patientRef;

    @Column(name = "source")
    private String source;

    @Column(name = "bundle_type")
    private String bundleType;

    @Column(name = "received_at", nullable = false)
    private Instant receivedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "bundle_data", columnDefinition = "TEXT", nullable = false)
    private String bundleJson;

    @PrePersist
    public void prePersist() {
        Instant now = Instant.now();
        this.receivedAt = now;
        this.createdAt = now;
    }

    // ===== GETTERS & SETTERS =====

    public Long getId() {
        return id;
    }

    public String getPatientRef() {
        return patientRef;
    }

    public void setPatientRef(String patientRef) {
        this.patientRef = patientRef;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getBundleType() {
        return bundleType;
    }

    public void setBundleType(String bundleType) {
        this.bundleType = bundleType;
    }

    public Instant getReceivedAt() {
        return receivedAt;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public String getBundleJson() {
        return bundleJson;
    }

    public void setBundleJson(String bundleJson) {
        this.bundleJson = bundleJson;
    }
}

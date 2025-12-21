package com.example.proxyfhirservice.repository;

import com.example.proxyfhirservice.model.FhirBundleEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface FhirBundleRepository
        extends JpaRepository<FhirBundleEntity, Long> {

    // 🔹 Vérifie si un patient est déjà synchronisé
    boolean existsByPatientRef(String patientRef);

    // 🔹 Récupère le bundle existant (pour republier Kafka)
    Optional<FhirBundleEntity> findByPatientRef(String patientRef);
}

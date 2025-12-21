package com.example.proxyfhirservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class ProxyFhirApplication {
	public static void main(String[] args) {
		SpringApplication.run(ProxyFhirApplication.class, args);
	}
}
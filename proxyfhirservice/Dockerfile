# =========================
# STAGE 1 : Build avec Maven
# =========================
FROM maven:3.9.9-eclipse-temurin-17 AS build

WORKDIR /build

COPY pom.xml .
RUN mvn dependency:go-offline

COPY src ./src
RUN mvn package -DskipTests


# =========================
# STAGE 2 : Runtime
# =========================
FROM eclipse-temurin:17-jdk

WORKDIR /app

COPY --from=build /build/target/*.jar app.jar

EXPOSE 8081

ENTRYPOINT ["java", "-jar", "app.jar"]

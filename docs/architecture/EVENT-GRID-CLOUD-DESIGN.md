# Diseño Declarativo de Azure Event Grid en Cloud (AegisBank)

---

## 1. Topología de Distribución de Eventos en Azure

Este documento describe la arquitectura declarativa de **Azure Event Grid** para la plataforma AegisBank en la nube de Microsoft Azure. **No realiza aprovisionamiento ni despliegues reales de infraestructura.**

```mermaid
graph TD
    Publisher[Mock Core Banking / Outbox Publisher] -->|CloudEvents 1.0 HTTPS POST| Topic[Event Grid Custom Topic:<br/>aegisbank-domain-events]

    subgraph Event Subscriptions & Advanced Filters
        Topic -->|Filter: type=*.created.v1 & subject=service-requests/*| Sub1[Subscription: sub-audit-compliance]
        Topic -->|Filter: type=*.created.v1 & amount > 10000| Sub2[Subscription: sub-high-value-analytics]
    end

    Sub1 -->|Push Delivery / EventGrid Trigger| FunctionApp1[Azure Function: ServiceRequestEventHandler]
    Sub2 -->|Push Delivery / EventGrid Trigger| FunctionApp2[Azure Function: HighValueRiskAnalyzer]

    Sub1 -.->|Max Retries Exceeded (24h) / HTTP 500| DLQ[Dead-Letter Container:<br/>eventgrid-deadletter/sub-audit]
```

---

## 2. Definición Declarativa de Recursos Cloud

### 2.1. Event Grid Custom Topic
- **Nombre:** `aegisbank-domain-events-topic`
- **Ubicación:** `eastus2` (o región secundaria)
- **Esquema de Entrada (*Input Schema*):** `CloudEventSchemaV1_0`
- **Aislamiento de Red:** Private Endpoint exclusivo en la VNet de AegisBank.

### 2.2. Suscripción Canónica: `sub-audit-compliance`
- **Destino (*Endpoint*):** Azure Function `service_request_event_handler`.
- **Filtros Avanzados (*Advanced Filters*):**
  - **Por Tipo de Evento:** `includedEventTypes = ["com.aegisbank.service-request.created.v1"]`
  - **Por Prefijo de Asunto:** `subjectBeginsWith = "service-requests/"`
  - **Filtro de Datos:** `NumberIn` o `StringContains` en atributos de `data`.

### 2.3. Política de Reintentos (*Retry Policy*)
- **Intentos Máximos de Entrega (*Max Delivery Attempts*):** 30.
- **Tiempo de Vida del Evento (*Event Time-To-Live*):** 1440 minutos (24 horas).
- **Algoritmo de Reintento:** *Exponential Backoff* administrado automáticamente por el servicio de Event Grid.

### 2.4. Destino de Mensajes Muertos (*Dead-Letter Destination*)
- **Almacén:** Azure Storage Account (Blob Container).
- **Contenedor:** `eventgrid-deadletter/sub-audit-compliance/`
- **Propósito:** Almacenar eventos que fallaron permanentemente tras agotar los 30 intentos o 24 horas, permitiendo auditoría forense y reprocesamiento manual.

---

## 3. Estado de Madurez de la Capacidad

- **Diseño Declarativo de Suscripciones y Filtros:** `EVENTGRID-CLOUD-PENDING`.
- **Destino Dead-Letter en Almacenamiento Azure:** `EVENTGRID-DEADLETTER-CLOUD-PENDING`.
- **Políticas de Reintento del Servicio Cloud:** `EVENTGRID-SERVICE-RETRY-CLOUD-PENDING`.
- **Handler de Azure Functions en Local:** `LOCAL-FUNCTIONS-COVERED`.

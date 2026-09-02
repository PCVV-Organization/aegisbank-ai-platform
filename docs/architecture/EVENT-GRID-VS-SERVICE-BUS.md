# Event Grid vs Service Bus in AegisBank v0.13

> **Milestone:** `v0.13.0 — Azure Functions + Event Grid Local Serverless Foundation`
> **Propósito:** Definir la separación formal de responsabilidades entre Azure Event Grid (serverless push notifications vía HTTP) y Azure Service Bus (brokered, durable, command-style messaging). Ambos coexisten en la arquitectura AegisBank; ninguno reemplaza al otro.

---

## 1. Comparativa Canónica (Microsoft Learn revisado 2026-09-02)

| Dimensión | Azure Event Grid | Azure Service Bus |
|---|---|---|
| **Patrón arquitectónico** | Event notification / push-push HTTP | Brokered queue / topic-subscription |
| **Transporte** | HTTP + CloudEvents 1.0 (recomendado) o Event Grid schema (legacy) | AMQP 1.0 + HTTP |
| **Semántica de entrega** | **At-least-once**, **sin garantía de orden** | **At-least-once**, **FIFO con sesiones**, **duplicate detection** nativo |
| **Modelo de consumo** | Push (webhook HTTPS) | Pull / push con settlement (`complete`, `abandon`, `dead-letter`) |
| **Persistencia** | Sin cola persistente — los eventos se reintentan con backoff exponencial hasta TTL/DLQ | Mensajes persistidos en storage del broker hasta `complete` |
| **Retención** | Reintentos 1–30 intentos, TTL 1–1440 min; DLQ a blob storage | Mensajes hasta expirar por TTL o completarse; DLQ integrada |
| **Filtrado** | Tipos, `subject begins-with/ends-with`, advanced filters (números, strings, boolean) | SQL filters sobre `application_properties`; correlation filters |
| **Casos de uso típicos** | Notificaciones reactivas, fan-out, integraciones SaaS, reactividad declarativa | Comandos transaccionales, orquestación de workflows, settlement |
| **Estado Azure** | GA (Basic y Standard tiers) | GA (Basic, Standard, Premium) |

---

## 2. Posición en AegisBank

```
       +-------------------+
       | HITL APPROVED     |
       | (v0.7 contract)   |
       +---------+---------+
                 |
                 v
       +-------------------+
       | create_service_   |
       | request (v0.6)    |
       +---------+---------+
                 |
                 v
       +-------------------+
       | SQL Transaction   | <-- Atomicidad con Outbox (v0.8)
       | INSERT outbox     |
       +---------+---------+
                 |
        +--------+--------+
        |                 |
        v                 v
+------------------+   +----------------------+
| OutboxProcessor  |   | CloudEvents Mapper   |
| (v0.8 / v0.11)   |   | (v0.13 ADR-028)      |
+--------+---------+   +----------+-----------+
         |                        |
         v                        v
+------------------+   +----------------------+
| LocalMessageBus  |   | HTTP POST a Azure    |
| AzureServiceBus  |   | Event Grid (futuro)  |
| Emulator adapter |   | (CloudEvents 1.0)    |
+--------+---------+   +----------+-----------+
         |                        |
         v                        v
+------------------+   +----------------------+
| Durable consumer |   | Azure Function       |
| Idempotent +     |   | (v0.13)              |
| DLQ              |   | Idempotent + Audit   |
+------------------+   +----------------------+
```

| Responsabilidad | Owner canónico |
|---|---|
| **Comandos transaccionales de larga vida** (HITL approvals, settlement, command queues) | Service Bus (v0.11) |
| **DLQ de mensajes envenenados** | Service Bus DLQ (v0.8) |
| **Notificación reactiva `ServiceRequestCreated` → function serverless** | **Event Grid (v0.13)** |
| **Eventos `disparar-y-olvidar` para proyecciones / auditoría reactiva** | **Event Grid (v0.13)** |
| **Reintentos con backoff exponencial y entrega al menos una vez** | **Event Grid nativo (1–30 intentos)** |
| **FIFO estricto y sesiones** | Service Bus (sin reemplazo) |
| **Fan-out masivo (>5 consumers)** | **Event Grid topic + suscripciones múltiples** |

---

## 3. Reglas de Selección (cuándo usar uno u otro)

| Si necesitas… | Usa |
|---|---|
| Garantía de orden estricta (FIFO) entre eventos del mismo `aggregate_id` | Service Bus con `sessions` |
| Settlement manual (`complete` / `abandon` / `dead-letter`) por handler | Service Bus |
| Push HTTP nativo a un webhook HTTPS sin acoplar al SDK del broker | Event Grid |
| Suscripciones múltiples al mismo evento con filtros independientes | Event Grid topic |
| Reintentos administrados por la nube sin lógica de reintentos en el handler | Event Grid |
| Integración SaaS / system topic (`Microsoft.Storage.BlobCreated`, etc.) | Event Grid |
| Cola durable con mensajes persistidos por días | Service Bus |
| Dead-letter integrado en el broker con semántica `dead-letter` | Service Bus |
| Mensajes > 1 MB | Service Bus (Event Grid ≤ 1 MB por evento) |

---

## 4. Estado de Madurez en AegisBank

| Capacidad | Estado local | Estado cloud Azure |
|---|---|---|
| **Service Bus Emulator (AMQP)** | `LAB-COVERED` (v0.11) | `CLOUD-PENDING` (Namespace Estándar/Premium) |
| **Adapter `AzureServiceBusMessageBus`** | `LAB-COVERED` (v0.11) | Mismo adapter con token Entra ID |
| **Event Grid service** | `EVENT_GRID_SERVICE_EMULATED = NO` | Microsoft no publica emulador oficial; el runtime del servicio solo es cloud (Basic/Standard) |
| **Event Grid handler local (Azure Function v2)** | `EVENT_GRID_HANDLER_LOCAL = COVERED` (v0.13) | Mismo handler, Function App deployada |
| **CloudEvents 1.0 envelope** | `LAB-COVERED` (v0.13, schema estricto) | Idéntico en cloud |

---

## 5. Razones para no reemplazar Service Bus

1. Service Bus ya implementa FIFO con sesiones, duplicate detection nativo y settlement manual; **Event Grid no garantiza orden**.
2. Service Bus tiene DLQ integrada en el broker; **Event Grid usa blob storage como DLQ**, lo que requiere un consumer adicional para procesarla.
3. Service Bus permite sesiones y transacciones (`transactional client`); **Event Grid es estrictamente at-least-once sin settlement**.
4. El modelo de `ServiceRequestCreated` en AegisBank es **dual**: necesita (a) notificación reactiva fan-out → Event Grid, y (b) command queue durable con settlement → Service Bus. Ambos siguen siendo válidos.

---

## 6. Decisión final

**AegisBank mantiene ambos** canales. El **Outbox transaccional canónico** (v0.8) es la única fuente de publicación; un **OutboxProcessor** reparte cada evento a los dos transportes según su `event_type`. Para `ServiceRequestCreated`:

- **Event Grid** → Azure Function serverless (v0.13) — handler fino, idempotente, auditable.
- **Service Bus** → consumers durables existentes (v0.8 / v0.11) — sin cambios.

Ningún handler, bus, outbox, audit logger o metrics framework paralelo se introduce. Toda duplicación `NEW TRUE_DUPLICATION = 0`.

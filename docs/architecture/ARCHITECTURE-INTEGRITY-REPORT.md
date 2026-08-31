# AegisBank — Architecture Integrity & Code Duplication Report

> **Hito:** v0.10.1 — Architecture Integrity + Cross-Session Coordination  
> **Herramienta Auditora:** Pylint 4.0.8 (Checker: `R0801` / `duplicate-code`)  
> **Calificación General del Código:** **9.98 / 10**  
> **Evaluación de Deriva Arquitectónica:** 0 duplicaciones verdaderas de lógica de negocio (*0 TRUE_DUPLICATION*).

---

## 1. Clasificación y Análisis de Hallazgos Pylint R0801

| ID | Módulos Involucrados | Líneas Afectadas | Patrón Detectado | Clasificación | Decisión & Justificación |
|---|---|---|---|---|---|
| **DUP-001** | `aegisbank_rag.generation_evaluation` vs `aegisbank_rag.retriever` | 139-150 / 67-78 | Mapeo e instanciación de dataclass `RetrievalHit` con atributos de chunk. | `INTENTIONAL_SCHEMA_SIMILARITY` | **Mantener:** Son dominios separados (pipeline de evaluación de generación vs motor de recuperación en vivo). Mapean el mismo contrato canónico. |
| **DUP-002** | `aegisbank_rag.dense_local` vs `aegisbank_rag.lexical` | 61-70 / 42-51 | Ordenamiento por `cosine_similarity` y filtrado de chunks con score > 0.0. | `INTENTIONAL_SCHEMA_SIMILARITY` | **Mantener:** Motores de similitud independientes (léxico vs denso) que operan sobre matrices de scikit-learn. Abstraerlos aumentaría acoplamiento innecesario. |
| **DUP-003** | `aegisbank_intent_classifier.constants` vs `aegisbank_rag.lexical` | 45-55 / 13-24 | Diccionario de hiperparámetros de `TfidfVectorizer` (`ngram_range`, `min_df`, `norm`). | `INTENTIONAL_SCHEMA_SIMILARITY` | **Mantener:** `ml/intent-classifier` está congelado bajo contrato de dataset sintético v0.3. No se deben compartir constantes entre paquetes independientes. |
| **DUP-004** | `aegisbank_rag.evaluation` vs `aegisbank_rag.generation_evaluation` | 225-235 / 383-393 | Renderizado de cabecera markdown para reportes de evaluación. | `TEST_FIXTURE_SIMILARITY` | **Mantener:** Formateadores de texto independientes para reportes de evaluación de retrieval vs evaluación de respuestas generadas. |
| **DUP-005** | `aegisbank_rag.evaluation` vs `aegisbank_rag.generation_evaluation` | 218-224 / 376-382 | Serialización JSON con formato identado de métricas evaluativas. | `TEST_FIXTURE_SIMILARITY` | **Mantener:** Escritura estándar de artefactos en disco. Crear un "JsonHelper" violaría el principio de cohesión. |
| **DUP-006** | `aegisbank_rag.context` vs `aegisbank_rag.generation_evaluation` | 14-19 / 78-83 | Declaración de campos de dataclass (`document_id`, `version`, `chunk_id`, `source`, `status`). | `INTENTIONAL_SCHEMA_SIMILARITY` | **Mantener:** Definición canónica de atributos para el contexto de citas documentales. |

---

## 2. Auditoría de Deriva Arquitectónica (*Architecture Drift*)

| Responsabilidad | Implementación Canónica | Sospecha de Duplicación | Decisión | Acción | Evidencia |
|---|---|---|---|---|---|
| **Orquestación del Agente** | `AgentOrchestrator` (`ai/agent/src/aegisbank_agent/agent.py`) | Ninguna | `REUSE` | Mantener única fuente de verdad | 0 orquestadores paralelos encontrados. |
| **Registro de Herramientas** | `ToolRegistry` (`ai/agent/src/aegisbank_agent/tools/registry.py`) | Ninguna | `REUSE` | Mantener registro central | Exporta esquemas OpenAI y MCP sin diccionarios ad-hoc. |
| **Políticas de Enrutamiento** | `requires_account_data` / `requires_banking_read` | Ninguna | `REUSE` | Mantener reglas deterministas | Separado limpiamente de inferencia estocástica. |
| **Gestión HITL** | `HITLApprovalManager` (`ai/agent/src/aegisbank_agent/hitl.py`) | Ninguna | `REUSE` | Mantener gestor único | Cero duplicaciones tipo `HumanApprovalService`. |
| **Límite MCP** | `AegisBank Local MCP` (`ai/agent/src/aegisbank_agent/mcp_boundary.py`) | Ninguna | `REUSE` | Mantener transporte stdio | Servidor oficial `mcp==2.1.1` protocolo `2026-07-28`. |
| **Resiliencia (Retry / CB / Idemp)** | `RetryPolicy`, `CircuitBreaker`, `IdempotencyGuard` | Ninguna | `REUSE` | Mantener módulo `reliability` | Reutilizado en Core Banking y llamadas de herramientas. |
| **Mensajería / Outbox / DLQ** | `LocalMessageBus`, `OutboxProcessor`, `IdempotentConsumer` | Ninguna | `REUSE` | Mantener abstracción desacoplada | Cero conexiones directas sin pasar por broker. |
| **Observabilidad / Auditoría** | `StructuredLogger`, `AuditLogger`, `TracerProvider`, `HOTLSupervisor` | Ninguna | `REUSE` | Mantener módulo `observability` | Redacción de secretos y registro WORM centralizado. |

---

## 3. Conclusión de la Auditoría

* **TRUE DUPLICATIONS:** 0
* **INTENTIONAL SCHEMA SIMILARITIES:** 4
* **TEST FIXTURE SIMILARITIES:** 2
* **REFACTORS REQUERIDOS:** 0 (el código mantiene alta cohesión y bajo acoplamiento sin introducir abstracciones prematuras ni *god objects*).

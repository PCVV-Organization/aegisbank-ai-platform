# AegisBank Canonical Component Catalog

> **Purpose:** Identify the canonical implementations in this repository.
> Consult this catalog before creating code. Do not duplicate an existing
> responsibility.

## Responsibilities and extension points

| Responsibility | Canonical component | Canonical path | Main interface | Consumers | Extension point and constraint |
|---|---|---|---|---|---|
| Agent orchestration | `AgentOrchestrator` | `ai/agent/src/aegisbank_agent/agent.py` | `run(prompt, customer_id, correlation_id) -> AgentExecutionResult` | CLI, evaluators, E2E tests | Add lifecycle handlers or stop policies. Do not create a parallel orchestrator or `ChatbotManager`. |
| Tool registry | `ToolRegistry` | `ai/agent/src/aegisbank_agent/tools/registry.py` | `register(tool)`, `get(name)`, `list_tools()`, `export_openai_tools()` | Agent orchestrator, MCP server | Register `BaseTool` subclasses. Do not keep ad-hoc tool dictionaries in the orchestrator. |
| Banking routing policy | `requires_account_data`, `requires_banking_read` | `ai/agent/src/aegisbank_agent/agent.py`; see also `knowledge_routing.py` | `requires_account_data(prompt) -> bool`, `build_banking_routing_plan()` | Agent orchestrator | Add deterministic intent rules. Never let the LLM decide whether private banking data may be accessed. |
| RAG retrieval | `Retriever`, `PgVectorRetriever`, `SearchKnowledgeTool` | `ai/rag/src/aegisbank_rag/`; `ai/agent/src/aegisbank_agent/tools/knowledge_tools.py` | `search(query, top_k) -> list[RetrievalHit]`; `SearchKnowledgeTool.execute(args)` | Agent orchestrator, RAG pipeline | Add storage adapters behind `Retriever`. Do not create another RAG pipeline, chunker, or evaluation. Preserve frozen filters and qrels. |
| LLM provider adapter | Provider clients and `FoundryLocalAdapter` | `ai/agent/src/aegisbank_agent/` | Provider chat-completion API | Agent orchestrator, evaluators | Add provider support behind the adapter. Do not mix direct HTTP calls with provider integration. |
| Human approval (HITL) | `HITLApprovalManager` | `ai/agent/src/aegisbank_agent/hitl.py` | `create_request()`, `approve()`, `reject()`, `validate_tampering()` | Agent orchestrator, MCP server, CLI | Integrate approval channels through this manager. Do not create parallel approval managers. |
| MCP server and boundary | Local AegisBank MCP server, `create_mcp_server` | `ai/agent/src/aegisbank_agent/mcp_boundary.py` | `create_mcp_server(db, ctx, hitl_manager)`, `run_stdio_async()` | MCP clients and subprocesses | Register banking tools with annotations. Do not implement a parallel MCP server. |
| Idempotency | `IdempotencyGuard` | `ai/agent/src/aegisbank_agent/reliability/idempotency.py` | `execute(key, operation, *args) -> tuple[Any, bool]` | `CreateServiceRequestTool`, Core Banking | Adapt storage for distributed deployments. Do not duplicate idempotency hashing in tools. |
| Bounded retries | `RetryPolicy` | `ai/agent/src/aegisbank_agent/reliability/retry.py` | `execute(fn, *args, **kwargs) -> T` | HTTP clients, MCP calls, database clients | Extend transient-error classification. Do not add ad-hoc retry loops. |
| Circuit breaker | `CircuitBreaker` | `ai/agent/src/aegisbank_agent/reliability/circuit_breaker.py` | `execute(operation, *args, **kwargs) -> T`, `state` | Core Banking clients, external adapters | Configure thresholds and cooldown. Do not ignore cascading failures or add a second implementation. |
| Timeout handling | `with_timeout`, `TimeoutException` | `ai/agent/src/aegisbank_agent/reliability/timeout.py` | `@with_timeout(seconds)`, `execute_with_timeout(fn, seconds)` | LLM calls, database queries | Integrate native socket timeouts. Never add unbounded wait loops. |
| Transactional outbox | `OutboxRepository`, `OutboxEvent` | `services/mock-core-banking/src/mock_core_banking/persistence/` | `save(event)`, `list_pending(limit)`, `mark_published(event_id)` | Service-request tool, outbox processor | Add domain event types. Do not publish to a broker before the database transaction commits. |
| Message bus and consumers | `LocalMessageBus`, `IdempotentConsumer`, `DeadLetterQueue` | `ai/agent/src/aegisbank_agent/reliability/messaging.py` | `publish(topic, msg)`, `subscribe(topic, handler)`, `handle(msg)` | Background workers, event consumers | Add transport drivers behind existing abstractions. Do not couple consumers directly to producers. |
| OpenTelemetry tracing | `TracerProvider`, `get_tracer` | `ai/agent/src/aegisbank_agent/observability/tracer.py` | `start_as_current_span(name, attributes)`, `trace_span()` | Agent modules and tools | Add exporters as adapters. Do not use `print` for execution tracing. |
| Structured logging | `StructuredLogger` | `ai/agent/src/aegisbank_agent/observability/logging.py` | `info(msg, **extra)`, `error(msg, **extra)`, `redact(text)` | Application components | Extend redaction patterns. Do not bypass redaction with ad-hoc logging configuration. |
| Operational metrics | `OperationalMetrics` | `ai/agent/src/aegisbank_agent/observability/metrics.py` | `increment_counter()`, `record_timing()`, `get_percentiles()` | Agent orchestrator, evaluators | Add exporters through the existing metrics boundary. Do not calculate percentiles independently in modules. |
| Audit records | `AuditLogger` | `ai/agent/src/aegisbank_agent/observability/audit.py` | See the class API and tests | HITL manager, HOTL supervisor | Add durable storage through an adapter. Keep audit records separate from operational logs. |
| Human-on-the-loop supervision (HOTL) | `HOTLSupervisor` | `ai/agent/src/aegisbank_agent/observability/hotl.py` | `engage_kill_switch(reason)`, `disengage_kill_switch()`, `is_write_allowed` | Agent orchestrator, admin CLI | Add supervisory rules. Every write must check `is_write_allowed`. |
| Quality gates | `scripts/quality_gate.py` | `scripts/quality_gate.py` | `run_quality_gates() -> int` | Local developers, CI | Add deterministic quality or security checks. Do not silence failures. |
| Cosmos DB and change feed | `CosmosRepository`, `CosmosChangeFeedProcessor` | `ai/agent/src/aegisbank_agent/cosmos.py` | `create_item()`, `read_item()`, `query_items()`, `read_change_feed()`, `process_latest_changes()` | Agent, reactive workers | Integrate event triggers through this boundary. Do not duplicate document persistence or event processing. |
| Redis cache and vector search | `RedisCacheManager`, `RedisVectorRetriever` | `ai/rag/src/aegisbank_rag/cache.py`, `redis_retriever.py` | `get()`, `set()`, `invalidate_prefix()`, `execute_single_flight()`, `search()` | RAG and knowledge retrieval | Add managed Redis adapters. Do not duplicate cache abstractions or cache private customer financial data. |
| Serverless event handling | `ServiceRequestEventHandler`, `function_app` | `functions/aegisbank-events/function_app.py`, `service_request_handler.py` | `handle_cloud_event(raw_event) -> EventProcessingResult` | Azure Functions host, Event Grid | Add triggers through the existing Function App and validate shared contracts. Do not create a Function App per event. |
| Configuration and secrets | `ConfigurationProvider`, `SecretProvider`, `KeyVaultReferenceResolver` | `ai/agent/src/aegisbank_agent/configuration/` | `get()`, `get_optional()`, `require()`, `refresh()`, `resolve()` | Agent, infrastructure, adapters | Add providers behind these interfaces. Never put secrets in ordinary configuration. |
| AI evaluation and MLOps | `FoundryEvaluators`, `MLflowTracker`, `DriftDetector`, `ABExperimentHarness` | `ai/agent/src/aegisbank_agent/evaluation/`, `mlops/` | `evaluate_variant()`, `run_evaluation_gate()`, `start_run()`, `detect_data_drift()` | Agent traces, experiment reports, promotion gates | Add integrations behind existing interfaces. Never modify frozen holdouts or create duplicate metrics systems. |

## Discover before create

Before creating a file, function, or class:

1. Search the code graph for symbols and relationships. Use `rg` for literal
   text, configuration, or when graph results are insufficient.
2. Check this catalog and the [ownership map](../engineering/OWNERSHIP-MAP.md).
3. Record one of these decisions in the change description:
   - `REUSE`: use the existing canonical component.
   - `EXTEND`: add behavior at its supported extension point without breaking
     its contract.
   - `NEW_COMPONENT_JUSTIFIED`: explain why the responsibility is genuinely
     new and does not overlap another component.

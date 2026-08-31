# ADR-025: Local Containers and Service Bus Adapter

- **Status:** Accepted for v0.11 lab
- **Context:** AegisBank must learn container images, Compose networking and Azure-style messaging without cloud cost.
- **Decision:** Containerize Core Banking first; run the official Service Bus emulator with its SQL Server dependency in one canonical Compose file; implement an Azure adapter behind the existing MessageBus contract and use one queue.
- **Consequences:** The lab demonstrates AMQP, queue settlement and network boundaries without claiming cloud parity. Topics/subscriptions, managed identity and Azure Service Bus production remain future work. The adapter does not own retries, idempotency, HITL or business rules.
- **Alternatives rejected:** A second domain MessageBus, direct cloud deployment, topics before a fan-out requirement, and AKS for the first target.

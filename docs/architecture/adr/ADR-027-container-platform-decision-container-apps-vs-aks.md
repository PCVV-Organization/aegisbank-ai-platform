# ADR-027: Cloud Container Platform Decision — Azure Container Apps First vs. AKS Deferred

- **Status:** Accepted
- **Context:**
  Microsoft AI-200 and enterprise banking architectures evaluate both Azure Container Apps (ACA) and Azure Kubernetes Service (AKS). AegisBank must select a target cloud container platform for future cloud deployment (v0.12+) without incurring unnecessary operational complexity.
- **Decision:**
  Adopt **Azure Container Apps (ACA)** as the primary cloud container platform target for AegisBank AI Platform. Defer **Azure Kubernetes Service (AKS)** to future phases when multi-node GPU clusters or complex custom network meshes are explicitly required.
- **Consequences:**
  - **Positive:** Serverless operations, native KEDA event-driven autoscaling based on Service Bus queue depth, automatic TLS ingress, and zero idle cost via scale-to-zero.
  - **Positive:** Drastically reduced operational maintenance compared to managing AKS node pools, control planes, and Ingress controllers.
  - **Neutral:** Pedagogical Kubernetes manifests (`deploy/kubernetes/`) are retained in the repository to maintain Microsoft AI-200 and Mibanco 2026 competency alignment without requiring live AKS infrastructure today.
- **Alternatives Rejected:**
  - Deploying full AKS cluster initially for a single-agent modular monolith.
  - Using Azure App Service Linux (lacks native KEDA autoscaling and microservices composition).

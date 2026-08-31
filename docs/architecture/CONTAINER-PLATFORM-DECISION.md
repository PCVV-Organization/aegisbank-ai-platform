# Container Platform Decision

Status: design only. No Azure resource or deployment is created in v0.11.

| Concern | Azure Container Apps | AKS |
|---|---|---|
| Operating model | Managed/serverless containers and revisions | Managed Kubernetes cluster |
| Scaling | KEDA-based event scalers and replicas | KEDA plus Kubernetes controllers |
| Control | Lower operational overhead | Pods, Deployments, Services, ConfigMaps and Secrets with deeper control |
| Cost/complexity | Better first target for this modular monolith | Higher cluster and platform burden |
| AegisBank status | Future first cloud target | Deferred learning/deployment target |

Recommendation: Container Apps first, because AegisBank needs managed revisions,
ingress and event scaling without operating a cluster. AKS remains a deliberate future
target for AI-200 and workloads needing Kubernetes-level scheduling, policy or topology
control. Neither recommendation is a deployment claim.

# 018 — AegisBank v0.11.1 Local Kubernetes Runtime + Orchestration Acceptance

Continúa exclusivamente v0.11.1 — Local Kubernetes Runtime + Orchestration Acceptance.

Proyecto: C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform

0. Teaching Contract + Architecture Integrity

Lee primero y respeta:
- `docs/learning/TEACHING-CONTRACT.md`
- `docs/architecture/CANONICAL-COMPONENTS.md`
- `docs/engineering/OWNERSHIP-MAP.md`
- `docs/architecture/ARCHITECTURE-INTEGRITY-REPORT.md`

Aplica siempre ONE WRITER, MANY READERS, DISCOVER BEFORE CREATE y clasifica cualquier componente como REUSE, EXTEND o NEW_COMPONENT_JUSTIFIED.

Explica desde cero y documenta: Kubernetes/K8s, cluster, control plane, node, Pod, Deployment, ReplicaSet, Service, Namespace, ConfigMap, Secret, kubeconfig, context, readiness probe, liveness probe, rollout, rollback, replica, resource request, resource limit, securityContext, imagePullPolicy, port-forward, AKS, Azure Container Apps y KEDA.

Para cada concepto: nombre/sigla, traducción, significado, problema que resuelve, funcionamiento interno, por qué AegisBank lo necesita, ejemplo, alternativa, riesgos, relación Mibanco, relación AI-200 y maturity status.

Guarda este prompt como docs/chatgpt-prompts/018_PROMPT.md.

1. Reconciliar baseline Git — READ ONLY

El cierre v0.11 reportó:
- `2819e29`
- corrección posterior `6ced3c3`

Ejecuta:
```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git log -5 --oneline
git show --stat --oneline 2819e29
git show --stat --oneline 6ced3c3
git merge-base --is-ancestor 2819e29 6ced3c3
git diff --name-status 2819e29 6ced3c3
```

Si 6ced3c3 existe, es descendiente de 2819e29, HEAD coincide y el working tree está limpio, usar CANONICAL_V011_HEAD=6ced3c3.
Si no está claro: AEGISBANK_V0.11_1_BASELINE_AMBIGUOUS y STOP.
No reset, rebase, amend ni reescritura de historia.

2. Session Guard

Después de reconciliar Git:
```powershell
.venv\Scripts\python.exe scripts\session_guard.py acquire --session-id "opencode-v0111" --milestone "v0.11.1" --allowed-paths "deploy/kubernetes/**,docs/**,scripts/**,ai/agent/tests/kubernetes/**,.github/**,README.md"
```

Si existe otro writer: AEGISBANK_CROSS_SESSION_WRITER_ACTIVE y STOP.
Antes de staging/commit: session_guard check.

3. Preflight Kubernetes — no tocar cluster desconocido

Ejecutar solo lectura:
```powershell
kubectl version --client
kubectl config current-context
kubectl config get-contexts
kubectl cluster-info
kubectl get nodes -o wide
```

Continuar SOLO si el contexto es inequívocamente local de Docker Desktop/Kind para desarrollo.

Si apunta a AKS/EKS/GKE/corporativo/remoto o no puede probarse que es local:
AEGISBANK_V0.11_1_UNSAFE_KUBE_CONTEXT y STOP.

NO cambiar automáticamente el kubectl context.
NO habilitar Kubernetes en Docker Desktop automáticamente.
NO instalar Kind/Minikube/K3d automáticamente.

Si no hay cluster local:
AEGISBANK_V0.11_1_LOCAL_K8S_REQUIRED y STOP, explicando al usuario cómo habilitarlo manualmente.

4. Objetivo

Demostrar realmente:
Docker image -> Kubernetes Deployment -> Pod -> Service -> probes -> rolling update -> rollback -> scale -> logs/events/troubleshooting

Sin Azure cloud, AKS real ni Container Apps real.

5. Discover Before Create

Inspeccionar `deploy/kubernetes/`.
Reutilizar `aegisbank/mock-core-banking:0.11.0`.
No crear un segundo set de manifests si los existentes pueden extenderse.
No crear Helm/Kustomize salvo necesidad demostrable.

6. Namespace

Usar namespace `aegisbank-local`.
No desplegar en default.
Explicar que Namespace = aislamiento lógico, no frontera de seguridad completa.

7. Deployment hardening

Revisar/EXTENDER el Deployment existente con:
- replicas 1 inicial;
- image versionada;
- imagePullPolicy apropiada al laboratorio;
- port 8000;
- readiness /health/ready;
- liveness /health/live;
- requests/limits;
- runAsNonRoot;
- UID 10001 cuando aplique;
- allowPrivilegeEscalation false;
- readOnlyRootFilesystem cuando sea compatible;
- drop capabilities ALL;
- seccomp RuntimeDefault si el cluster lo soporta.

No inventar secrets.

8. ConfigMap

ConfigMap solo para configuración NO secreta.
Explicar ConfigMap vs Secret.
No guardar credenciales reales.
Documentar como futuros equivalentes: Managed Identity + Key Vault + App Configuration.

9. Image availability

Detectar cómo el cluster local obtiene `aegisbank/mock-core-banking:0.11.0`.
No hacer push Docker Hub/ACR.
Si aparece ImagePullBackOff, diagnosticarlo sin cambiar a latest ni instalar herramientas globales.
Si no existe mecanismo local seguro: AEGISBANK_V0.11_1_LOCAL_IMAGE_UNAVAILABLE.

10. Apply + Rollout

Aplicar manifests al namespace local y validar:
```powershell
kubectl apply -n aegisbank-local -f deploy/kubernetes/
kubectl rollout status deployment/mock-core-banking -n aegisbank-local
kubectl get pods -n aegisbank-local -o wide
kubectl get service -n aegisbank-local
kubectl describe deployment mock-core-banking -n aegisbank-local
```

No aceptar solo Running; debe estar Ready.

11. Service + Port Forward

Preferir ClusterIP.
No usar LoadBalancer/NodePort sin necesidad.
Probar con port-forward local:
- `/health/live`
- `/health/ready`
- un endpoint Core Banking READ.
Finalizar port-forward tras la prueba.

12. Rolling Update

Demostrar Deployment, ReplicaSet, rolling update y revision history.
Usar un cambio inocuo de Pod template, no lógica bancaria.
Validar rollout sin romper readiness.

13. Rollback

Ejecutar `kubectl rollout undo`, esperar rollout y validar health.
Explicar por qué rollback no sustituye backward compatibility ni migrations.

14. Manual Horizontal Scale

Demostrar replicas 1 -> 2 -> 1.
Validar Pods Ready y Service.
No instalar HPA/metrics-server si no existe.

15. Troubleshooting

Crear `docs/operations/KUBERNETES-TROUBLESHOOTING.md`.
Enseñar kubectl get, describe, logs, eventos y estados Pending, CrashLoopBackOff, ImagePullBackOff.
No provocar fallos destructivos innecesarios.

16. Acceptance Tests

Crear suite separada para Kubernetes. Validar:
- context safety;
- namespace;
- Deployment;
- image/tag;
- Pod Ready;
- probes;
- securityContext;
- requests/limits;
- Service ClusterIP;
- health vía port-forward;
- rollout;
- rollback;
- scale 1->2->1;
- no production secrets;
- no nuevas WRITE tools;
- new TRUE_DUPLICATION = 0.

Los tests normales NO deben depender de Kubernetes.
Crear gate separado kubernetes/integration.

17. AI-200 Mapping

Actualizar notas/matriz distinguiendo:
- `LOCAL-K8S-COVERED`
  - Deployment
  - Service
  - Namespace
  - probes
  - resources
  - rollout
  - rollback
  - scaling
  - logs/events
- `AKS-CLOUD-PENDING`
  - node pools reales
  - Managed Identity
  - ACR
  - networking
  - Azure Monitor
  - autoscaling productivo
- `CONTAINER-APPS-CLOUD-PENDING`
  - revisions reales
  - ingress real
  - KEDA real
  - Managed Identity
  - traffic splitting

Nunca convertir Kubernetes local en AKS-COVERED.

18. Container Apps + KEDA design

NO desplegar.
Extender documentación con revision, replica, ingress, scale-to-zero, KEDA, Service Bus scaler y Managed Identity.
No instalar Azure CLI.

19. Quality + Duplication

Ejecutar Kubernetes integration gate, suite completa, contracts, E2E, fast quality gate, container gate, Ruff, format, compileall, Bandit, pip-audit, secret scan, Pylint R0801 y git diff --check.

Debe mantenerse NEW TRUE_DUPLICATION = 0.

20. Cleanup

Eliminar aegisbank-local solo si lo creó esta sesión y no existe uso legítimo.
Cerrar port-forward.
Confirmar sin workloads de prueba y Compose v0.11 apagado.
No borrar imágenes/caches globales.

21. Git

Antes de staging:
- `session_guard check`
- `git rev-parse HEAD`
- `git status --porcelain=v2`
- `git diff --name-status`

PROHIBIDO: worktrees, git add ., git add -A, reset, rebase, amend, push.

Stagear exclusivamente archivos legítimos v0.11.1.
Antes de commit repetir session_guard check.

Si todo pasa:
`feat(v0.11): validate local Kubernetes orchestration`

Liberar session guard después.

# Rollback Runbook

1. Stop promotion and capture the failing gate output and commit SHA.
2. Keep the current artifact immutable for diagnosis; do not rewrite history.
3. Disable unsafe WRITE execution with `HOTLSupervisor` when applicable.
4. Restore the last locally verified commit or artifact using the repository's
   normal review process. No remote push or cloud deployment is implied here.
5. Re-run contracts, critical E2E, evaluation gate, security gates, and the
   performance baseline before declaring recovery.

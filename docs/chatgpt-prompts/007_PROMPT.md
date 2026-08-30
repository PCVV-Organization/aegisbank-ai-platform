# Cierre v0.5 — Staging y commit local

Cierra exclusivamente `v0.5.0 — Grounded Generation & LLM Evaluation`.

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

NO ejecutar nuevamente smoke ni held-out live. NO modificar `rag-answer-v001`,
corpus, qrels, retrieval v0.4 ni métricas observadas. NO iniciar v0.6, NO hacer
push y NO usar worktrees.

Verifica Git en `master` con HEAD
`1e92a6223bc5a96890f8b0d7ca5be43cb7e35bc2`, revisa `git status --short`,
`git diff` y `git diff --check`. Confirma que los artefactos congelados de v0.4
no cambiaron: corpus, queries, qrels, corpus manifest y retrieval reports.

No modifiques los archivos preexistentes de `docs/research/` responsables del
root format check; el scoped format check es la validación autorizada.

Ejecuta sin inferencia live: tests v0.5, regresiones v0.4 `36 passed`, v0.3
`17 passed`, v0.2 `55 passed`, Ruff, scoped format, compileall, secret scan y
`git diff --check`.

Si todo pasa, usa únicamente `git add` con rutas explícitas, nunca `git add .`
ni `git add -A`. Revisa `git diff --cached --name-only`, `--stat` y el diff.

Si el staging contiene solo archivos legítimos v0.5, crea exactamente:

`feat(v0.5): establish grounded generation and LLM evaluation`

No hagas push. Verifica `git log -1 --oneline`, `git show --stat --oneline HEAD`
y `git status --short`. Entrega commit, archivos, validaciones, métricas y
estado final sin secretos. No iniciar v0.6.

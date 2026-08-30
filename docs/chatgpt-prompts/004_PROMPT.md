# Continuar v0.5 - detectar LLM autorizado

Ejecuta esta tarea con el agente primario `orchestrator` de OpenCode. Carga y
aplica las skills pertinentes como apoyo operativo, sin implementar capacidades
de Agent, MCP o HITL en el producto.

Para esta ejecucion no interactiva:

* usa `Glob`, `Grep` y `Read` para descubrir y leer archivos;
* no uses `ls`, `dir`, `Get-ChildItem`, pipelines de shell ni comandos de
  descubrimiento equivalentes;
* ejecuta Git, Python, pytest y Ruff con los comandos directos ya autorizados;
* para inspeccionar el entorno, invoca `powershell -NoProfile -Command` y reporta
  solo presencia/ausencia y nombres no sensibles, nunca valores de credenciales;
* carga `find-docs` solo si hace falta conectar el provider y verificar la API
  estable actual;
* considera el marcador de configuracion requerida como un estado terminal
  correcto, no como motivo para modificar o stagear codigo.

Continua exclusivamente `v0.5.0 - Grounded Generation & LLM Evaluation`.

Proyecto:

`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

NO crear recursos Azure, NO desplegar modelos, NO generar costos, NO Agent/MCP/HITL
y NO iniciar v0.6.

Primero verifica el estado Git y preserva todo el trabajo v0.5 actual sin staging.

Despues detecta unicamente si ya existe configuracion valida de Microsoft Foundry
mediante variables de entorno/configuracion local autorizada para:

* endpoint;
* deployment/model;
* autenticacion.

NO imprimas secretos.

Usa la API estable `OpenAI/v1` / Responses API; NO uses el Azure AI Inference beta
SDK.

Modelo preferido para el baseline si ya esta desplegado:

`gpt-5-mini`

pero utiliza el deployment realmente configurado si es compatible.

Si NO existe endpoint/modelo autorizado, no cambies codigo innecesariamente y
finaliza:

`AEGISBANK_V0.5_FOUNDRY_CONFIGURATION_REQUIRED`

indicando unicamente que configuracion falta, sin crearla.

Si SI existe configuracion valida:

1. conecta el `LLMProvider` existente;
2. ejecuta primero una unica llamada smoke de bajo costo;
3. si funciona, ejecuta los 6 casos held-out una sola vez;
4. registra provider, deployment/model, prompt version y metricas;
5. no ajustes el prompt despues de observar held-out;
6. ejecuta todos los tests y regresiones v0.2/v0.3/v0.4/v0.5;
7. ejecuta Ruff, format, compileall, secret check y `git diff --check`;
8. stagea solo archivos legitimos v0.5;
9. crea:

`feat(v0.5): establish grounded generation and LLM evaluation`

No push.

Finaliza con:

`AEGISBANK_V0.5_GROUNDED_GENERATION_READY`

y STOP.

# Repositorio de aplicación y entorno de desarrollo

Este Git contiene la aplicación bancaria educativa AegisBank: código, contratos,
pruebas, datos sintéticos y documentación del producto.

El repositorio separado `aegisbank-ai-platform-ai-env` contiene herramientas e
instrucciones para desarrollar el producto. El agente de desarrollo utiliza
ambos proyectos; el asistente bancario Aegis pertenece solo a esta aplicación.

En el workspace local, esta aplicación está clonada en una subcarpeta de ai-env.
La carpeta padre la ignora por completo en su Git. Cada repositorio tiene su
propio historial y no hay submódulo ni gitlink.

Esta aplicación puede clonarse sola y conserva sus instrucciones en AGENTS.md.
Las instrucciones de ai-env no se presuponen cargadas automáticamente. Si el
trabajo usa ese entorno, consultar sus reglas y su manifiesto de workspace.

Los cambios bancarios y su aprobación pertenecen a este repositorio. Los cambios
en tooling y configuración del agente de desarrollo pertenecen a ai-env.
Un cambio transversal se revisa en ambos y registra sus dependencias.

La separación no modifica el hito bancario, no crea recursos de nube y no
convierte permisos del agente de desarrollo en autorización bancaria.

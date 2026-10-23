# Skills personales para Claude Code

[Seguro] Se copiaron el **23/10/2026** las **14 skills personales activas** de la instalación local de Claude: directorios de primer nivel con un `SKILL.md` directo. Se excluyeron `.trash` y `synced`. En esta versión cada skill tiene únicamente su `SKILL.md`; no había archivos de apoyo adicionales.

[Seguro] Los archivos de [`.claude/skills/`](../.claude/skills/) conservan exactamente los bytes de sus originales. El [manifiesto](../.claude/skills-manifest.json) registra rutas relativas, tamaños y hashes SHA256 de cada copia. No contiene rutas personales absolutas.

| Skill | Uso |
|---|---|
| `auditoria` | Auditoría integral con evidencia y plan priorizado. |
| `cierre` | Cierre de sesión, documentación y comprobaciones. |
| `contexto` | Apertura de sesión y estado real del proyecto. |
| `delegar` | Preparar un handoff para otro modelo. |
| `estudio` | Estudio y resolución razonada de ejercicios. |
| `ganar-contexto` | Nombre alternativo de `contexto`. |
| `limpieza` | Ordenar carpetas personales o Drive con revisión previa. |
| `mis-pasos` | Documentar los pasos que debe hacer el usuario. |
| `nueva-fuente` | Investigar e integrar una fuente de datos externa. |
| `ordenar` | Ordenar documentación y plan de un repositorio. |
| `portfolio` | Preparar material del proyecto para búsquedas laborales. |
| `rescate` | Retomar trabajo interrumpido sin rehacer lo completado. |
| `research` | Investigación con fuentes primarias y niveles de confianza. |
| `segunda-opinion` | Contrastar propuestas o entregas de otro modelo. |

## Uso y actualización

- Leer [`.claude/CLAUDE.md`](../.claude/CLAUDE.md) para las preferencias y restricciones del proyecto. Tener las skills disponibles no ordena ejecutarlas.
- Las copias están versionadas en este repositorio. La computadora y `~/investigathon` reciben la misma versión al sincronizar Git; el procedimiento operativo está en [GPU.md](GPU.md).
- Para actualizar una skill, copiar explícitamente su versión personal al directorio correspondiente, verificar igualdad de bytes, recalcular el manifiesto y revisar el diff antes de sincronizar.
- Mantener los originales personales intactos y registrar cambios propios por separado. No volver a copiar todo el perfil personal como método de actualización.

[Seguro] Este paquete incluye instrucciones personales en Markdown. No incluye credenciales, settings, conexiones MCP, plugins, conectores ni herramientas externas; su disponibilidad se comprueba por separado cuando haga falta.

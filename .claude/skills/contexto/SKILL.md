---
name: contexto
description: Ritual de apertura de sesión para cualquier proyecto — lee lo que haya de contexto (CLAUDE.md/AGENTS.md/memory.md/README/TODO), mide el estado real del repo con git, reporta dónde estamos y qué sigue, y cierra proponiendo arreglar lo raro y rescatar lo cortado. Usar cuando el usuario pide "dame contexto", "ganá/gana contexto (del proyecto)", "ganar contexto", "en qué estábamos", "leete el repo", "leete todo el repo", "sabés de qué va el proyecto", "por dónde íbamos", "qué falta acá", "poneme al día", "decime cómo seguimos con el plan", "qué te toca hacer hoy", o abre sesión sin más indicación en un proyecto ya empezado.
---

# /contexto — arrancar sabiendo dónde estamos

El objetivo no es resumir el proyecto: es poder responder **"estamos acá, sigue esto"** con datos
medidos, no recordados.

**Lo propio del proyecto manda.** Si `AGENTS.md` o `CLAUDE.md` dice qué archivos son las fuentes
de verdad y qué buscar en cada uno, seguí eso por encima del orden genérico de acá.

Argumentos: `$ARGUMENTS` (si trae algo, es el foco; igual mirá todo lo demás).

## 1. Encontrar qué contexto existe

No asumas que hay nada. Buscá, en este orden, y usá lo que aparezca:

1. `CLAUDE.md` / `AGENTS.md` en la raíz — instrucciones del proyecto para agentes.
2. `memory.md`, `MEMORY.md`, `NOTES.md` en la raíz — bitácora de decisiones.
3. Si este entorno tiene el sistema de memoria automática mencionado en tu system prompt (una
   carpeta `memory/` con `MEMORY.md` fuera del proyecto, indexada por directorio de trabajo),
   revisala.
4. Un plan o backlog: `TODO.md`, `PLAN.md`, `*plan*.md`, `TASKS.md`, o issues abiertos si hay un
   tracker configurado.
5. `README.md` — sólo para entender qué es el proyecto si no hay nada de lo anterior.

Si no hay ninguno de estos archivos, decilo explícitamente en el reporte en vez de inventar
contexto — "este proyecto todavía no tiene bitácora" es información real y útil.

Archivos largos: no los leas enteros de una. Sacá el mapa con `grep -n "^#\{1,3\} "` y leé sólo
la tabla de estado y la sección "Dónde retomar", que es donde vive el estado real.

## 2. Medir el estado real, no confiar en lo que dicen los docs

Los docs se escriben antes del merge y quedan viejos. Si algo escrito contradice lo que ves en el
árbol, **gana lo que ves** — y decilo en el reporte.

Si es un repo git (comprobalo primero, no asumas):
```bash
git log --oneline -5
git status -sb
git branch --no-merged main 2>/dev/null || git branch --no-merged master 2>/dev/null
git worktree list 2>/dev/null
```

Si NO es un repo git, saltealo entero y decí en el reporte que no hay control de versiones acá —
no es un error, es un dato.

Mirá también qué tipo de proyecto es (`package.json`, `pyproject.toml`, `requirements.txt`, o
ninguno — carpeta de archivos sueltos) para saber qué comandos de verificación tendrían sentido
más adelante, sin ejecutarlos todavía.

## 3. Reportar

Cuatro cosas, cortito:

1. **Dónde estamos** — qué es este proyecto (una línea, si no era obvio), estado del repo si hay
   uno (commit, sincronizado o no, conteo de tests si la bitácora lo lleva).
2. **Qué quedó abierto** — pendientes que encontraste en los docs o en el árbol (ramas sin
   mergear, cambios sin commitear, TODOs, etapas con lo que las bloquea).
3. **Qué recomendás arrancar hoy** — una sola cosa, con el motivo.
4. **Si hay algo raro** — docs desactualizados respecto al árbol, archivos de contexto ausentes,
   worktrees colgados, trabajo cortado a mitad.

## 4. Cerrar con la propuesta, lista para un "dale"

Después de `/contexto` el usuario casi siempre sigue con "fixeá lo raro" y "rescatá". Terminá el
reporte proponiéndolo concreto, en una o dos líneas:
- **Lo raro que arreglaría:** la lista corta de lo del punto 4 que tiene arreglo (docs a equiparar,
  worktrees a limpiar, ramas a mergear).
- **Lo que rescataría:** si hay trabajo cortado (cambios sin commitear, ramas a mitad, agentes
  muertos), que lo retomás con `/rescate`.

Y preguntá si le das. Si no hay nada raro ni cortado, decilo en una línea.

## Lo que NO hay que hacer

- **No arranques a codear.** Reportá, proponé y esperá el "dale".
- No repitas de vuelta palabra por palabra lo que ya dice la bitácora — el usuario la escribió.
  Resumí lo que importa para arrancar hoy.

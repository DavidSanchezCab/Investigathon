---
name: auditoria
description: Auditoría integral de un proyecto o app — mide antes de afirmar, puntúa cada dimensión (correctitud, datos, performance, tests, código, seguridad, UI, operación, largo plazo) con nivel de confianza [Seguro]/[Probable]/[Adivinando] y termina en un plan priorizado; no toca nada hasta el "dale". Usar siempre que el usuario pida "auditá la app", "auditoría integral/profunda", "la auditoría de siempre", "cambiaron muchas cosas, actualizá la auditoría", "qué opinás de la app hasta ahora", "qué le falta para ponerla en prod", "qué mejorarías", "leete todo el repo y analizalo de punta a punta", "revisá todo el código y la bdd", "¿es demasiado ambicioso?", o "compará contra apps existentes", aunque no diga la palabra auditoría. No es para diagnosticar un bug puntual ni para escribir tests.
---

# /auditoria — la auditoría de siempre, sin mega-prompt

Argumentos: `$ARGUMENTS` — foco o dimensión (opcional). Sin argumento: todas.

**Es análisis: no se edita nada ni se larga ningún agente hasta el "dale".** Arrancar a corregir en
medio de una auditoría es la queja más repetida del usuario ("no te dije que te pusieras a hacer
nada…"). Lo que haya que cambiar va como propuesta.

## 0. Antes de auditar

- Leé el contexto del proyecto: `CLAUDE.md`/`AGENTS.md`, la memoria o bitácora, y los docs de
  decisiones y lecciones si existen. Sirve para no proponer lo que ya se descartó ni lo que ya está
  construido: antes de proponer algo, grepeá si existe.
- **¿Hay una auditoría anterior** en el repo? Entonces es una auditoría delta: partí de ella y decí
  qué se arregló, qué empeoró y qué es nuevo ("cambiaron muchas cosas, actualizá la auditoría").
- Medí el tamaño real: archivos y líneas (los más grandes primero), tests (cantidad y duración),
  dependencias. Esos números van al reporte.

## 1. Dimensiones

| # | Dimensión | Qué mirar |
|---|---|---|
| 1 | Correctitud | reglas de negocio, cálculos de plata y fechas, casos borde, literales |
| 2 | Datos | normalización, índices, integridad, migraciones, backups que se puedan restaurar |
| 3 | Performance | latencias reales contra el objetivo que fijó el usuario, lecturas O(historia), N+1, fetch externos sin caché |
| 4 | Tests | lo crítico cubierto, flakes, tiempos, tests que fijan conducta vieja |
| 5 | Código | archivos gigantes, duplicación, código escrito y nunca llamado |
| 6 | Seguridad y privacidad | secretos, superficie expuesta, permisos, datos sensibles en logs |
| 7 | UI/UX | consistencia, estados vacíos y de error (si hay UI) |
| 8 | Operación | qué corre solo, qué falla en silencio, qué avisa y qué no |
| 9 | Largo plazo | escala (años de datos), retención (lo que crece sin barrido), bombas de tiempo (cupos, modelos o APIs que vencen, formatos que cambian), mantenimiento cerca de cero, costo (gratis vs pago) |
| 10 | Producto (si lo pide) | qué falta para usarlo de verdad todos los días; competencia: qué copiarle y qué fortalecer de lo propio |

**Tests:** si el proyecto tiene una skill de testing (por ejemplo `/testing`), delegale esa dimensión
y usá su resultado. Si no tiene, cubrila acá.

La dimensión 9 es la que más pesa para el usuario: ir más allá de sus ejemplos y buscar lo que se
rompe a los meses o años, no sólo hoy.

## 2. Reglas de evidencia

- Cada hallazgo lleva la evidencia (`path:línea`, el comando y su salida, el número medido) y su
  etiqueta: **[Seguro]** medido o visto, **[Probable]** inferencia sólida, **[Adivinando]**.
- Un número dicho sin medirlo es un error esperando. Si no se puede medir, decilo.
- La premisa del usuario no es un hecho: si dice "X no anda", verificalo antes de construir encima.
- No concluyas desde una sola capa (código, datos, logs y config pueden contar historias distintas).
- Puntaje 0-10 por dimensión, con una línea de por qué. Lo que se puede medir no lleva puntaje
  [Probable]: medilo, o decí qué falta para medirlo. Pasó el 16/08 en otro proyecto: "no me gustan
  esos probable en los puntajes".

## 3. Entregable

Usá esta estructura:

```markdown
# Auditoría — <proyecto> — <fecha>
**La verdad incómoda primero** (1-3 líneas).

| Dimensión | Puntaje | vs. anterior | Lo más grave |
|---|---|---|---|

## Hallazgos (por severidad × costo de no hacerlo)
- [Seguro] <hallazgo> — <evidencia> → <propuesta>

## Plan propuesto
Olas chicas: objetivo, archivos, verificación y tamaño de cada una.
Lo que NO conviene hacer, y por qué (así no se vuelve a proponer).

## Qué no pude medir
```

Va en el chat. Si el proyecto guarda sus auditorías en el repo, ofrecé guardarla ahí; no la
escribas sin el ok.

## 4. Después del "dale"

Las olas van al plan del proyecto y se largan con su skill de olas si existe. Lo descartado queda
anotado donde el proyecto registra las decisiones.

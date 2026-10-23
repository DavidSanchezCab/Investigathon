---
name: ordenar
description: Pone en orden la documentación y el plan de un repo — poda a un tope de líneas, marca lo hecho y registra lo descartado (para no re-proponerlo), equipara docs contra código (gana el código), rehace diagramas desactualizados y saca basura del repo (archivos vacíos o sin uso, logs viejos). Usar siempre que el usuario diga "el plan es un caos", "compactá/resumí la documentación", "no debería tener más de N líneas", "quedó largo y desprolijo", "actualizá todos los docs", "que los docs coincidan con el código", "rehacé los diagramas/el DER", "limpiá el repo", o "corregí la deuda técnica de docs". No es el cierre de sesión (/cierre) ni la limpieza de carpetas personales o Drive (/limpieza).
---

# /ordenar — docs y plan que se puedan leer

Argumentos: `$ARGUMENTS` — qué ordenar (plan, docs, diagramas, repo) y el tope de líneas, si lo dio.

**Un plan que nadie puede leer no guía nada.** Pasó varias veces en otro proyecto:
- el 07/08: "ya no entiendo una goma el plan, lo hiciste de más de mil líneas";
- el 02/09: "más de 2k líneas, no debería tener más de 100";
- otra vez se pidieron ~100 líneas y llegaron 1007.

## 0. El tope

- Si el usuario dio un número, es un tope, no una sugerencia.
- Si el contenido no entra, decilo ANTES de escribir y proponé el corte: qué pasa a un archivo
  histórico.
- Sin número: el plan vivo tiene que entrar en una pantalla por sección.

## 1. Inventario

- Listá los docs (los `.md` de la raíz y de `docs/`): líneas, última modificación y de qué habla
  cada uno.
- Marcá los duplicados (el mismo tema en dos lados) y las contradicciones.
- En el plan o la bitácora, cada ítem queda como hecho, en curso, pendiente o descartado.

## 2. El código gana

- Contrastá con el código cada afirmación verificable de los docs: archivos, comandos, flujos,
  números.
- Si no coinciden, se corrige el papel, no el código. La excepción: si el doc registra una decisión
  que el código violó, eso se reporta; no se "arregla" en silencio.
- Los diagramas (DER, flujos, dependencias) se regeneran desde el código: con la herramienta del
  repo si la hay, o a mano desde el schema y los imports reales.
- Las flechas no se cruzan ni atraviesan cajas (pasó el 30/09).

## 3. Podar sin perder

- **Lo hecho:** una línea con fecha o commit, o directo al histórico. El porqué de una decisión no
  se borra: va al doc de decisiones.
- **Lo descartado:** una línea con el motivo, en un lugar fijo. Así no se vuelve a proponer.
- **Lo pendiente:** todo junto, ordenado, sin referencias cruzadas a puntos de otros documentos.
- **Un solo "Dónde retomar":** se reemplaza en cada pasada, no se apila.
- Lo que sale del plan vivo va a un snapshot histórico fechado, nunca a la papelera.

## 4. Basura del repo

- **Candidatos:** archivos de 0 bytes, carpetas fuera de lugar, logs viejos, temporales, copias
  `-old` o `-v2`, artefactos generados que quedaron trackeados.
- **Antes de borrar cada uno:**
  - quién lo usa: grep del nombre;
  - por qué existe: `git log`;
  - si se regenera. En ese caso se arregla el origen y se agrega al `.gitignore`.
- Mostrá la lista y borrá con el ok del usuario. Ante la duda, mové al histórico.

## 5. Cerrar

- Ningún link interno roto: grepeá las rutas mencionadas que ya no existen.
- Un commit propio, separado de cualquier cambio de código, que diga qué se podó y adónde fue.
  Respetá el protocolo de commits y push del proyecto.

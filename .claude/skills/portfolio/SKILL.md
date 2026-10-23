---
name: portfolio
description: Convierte un proyecto en material para conseguir laburo — README de GitHub, bullets de CV con impacto medible, post de LinkedIn y respuestas para entrevistas — con una evaluación honesta de cuánto suma para el puesto buscado. Usar siempre que el usuario pregunte "¿lo pongo en el CV?", "¿me sirve para venderme como junior/jr de data o dev?", "haceme la descripción para el README de GitHub", "armame el post de LinkedIn de este proyecto", o "¿cómo lo cuento en una entrevista?".
---

# /portfolio — que el proyecto cuente

Argumentos: `$ARGUMENTS` — qué pieza quiere (README, CV, LinkedIn, entrevista) y para qué puesto.

Si pide sólo el texto, devolvé sólo el texto y no toques el repo. Pasó el 19/04: "solamente
devolveme el texto, que el resto lo hago yo".

## 1. Medir lo que hay, sin inflar

- **Del repo, sólo lo verificable:** stack, tamaño, tests, decisiones técnicas, problemas reales
  resueltos y métricas (R², latencia, volumen de datos, cantidad de tests). Nada de features que no
  existen.
- **La respuesta honesta va primero:**
  - ¿suma para ese puesto?
  - qué le falta para sumar más: deploy público, demo, tests, un README claro.

## 2. Las piezas que pida

- **README:**
  - qué es (una línea) y por qué existe;
  - demo o capturas;
  - stack y arquitectura (con diagrama si hay);
  - cómo correrlo;
  - decisiones y resultados;
  - autor.
- **CV:** 2 a 4 bullets de acción + tecnología + resultado medible.
- **LinkedIn:** un post corto, con un gancho en la primera línea y sin humo.
- **Entrevista:** 3 a 5 preguntas probables y cómo contestarlas con lo que hizo: los tradeoffs y qué
  haría distinto.

## 3. Privacidad

Si el proyecto maneja datos personales (por ejemplo, finanzas reales), el material público usa datos
de ejemplo. No expone cuentas, montos, nombres ni capturas con datos reales.

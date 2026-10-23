---
name: estudio
description: Ayuda para estudiar materias de la facu (UBA) — ejercicios resueltos con el razonamiento, corrección del intento propio, código Haskell que compile y pase sus casos, demostraciones de álgebra y lógica paso a paso, y repaso para parciales. Usar siempre que el usuario pegue un ejercicio o una consigna, pregunte "¿esto compila en haskell?", "solucioname los parse error", "¿es lo mismo decir…?", "explicame X para el parcial", "armame ejercicios de práctica", "¿cómo lo resuelvo?", o mencione IP, Álgebra, una guía, un parcial, un final o la facu.
---

# /estudio — para aprender, no sólo para la respuesta

Argumentos: `$ARGUMENTS` — el ejercicio, la consigna o el tema.

El objetivo es aprobar sabiéndolo: en el parcial no hay a quién preguntarle, así que la solución sin
el razonamiento no sirve.

## Ejercicios

1. **Leé la consigna entera y las reglas de la materia.**
   - Usá sólo lo que se puede usar. En IP: lo visto (recursión, guardas, pattern matching), nada de
     funciones de librería que la cátedra no permita.
   - Respetá la signatura dada (`Integer` no es `Int`) y el formato de especificación si lo piden
     (requiere / asegura).
   - Si no sabés qué se vio, preguntá en una línea.
2. **Primero la idea** (cómo se piensa), **después la solución**, **después por qué anda**: casos
   base, casos borde, terminación.
3. **Haskell:** si hay `ghc`/`ghci`, compilalo y correlo con casos, incluidos los borde. Si no hay,
   decilo y marcá lo que quedó sin verificar.
4. **Álgebra y lógica:** demostración paso a paso, justificando cada paso. Si es falso, un
   contraejemplo concreto.

## Si pega su intento

Corregí sobre lo suyo, sin reescribir de cero:
- qué está bien;
- dónde está el error y por qué falla;
- la versión corregida, con el cambio mínimo.

## Repaso para un parcial

- Temas → ejercicios tipo, del más fácil al más difícil.
- Si quiere practicar, la solución va aparte y no se muestra de entrada.
- Los errores típicos de cada tema.

## Archivos

Si trabaja en un repo de la materia, respetá su estructura (un archivo por guía o ejercicio) y no
commitees ni subas nada sin que lo pida.

---
name: mis-pasos
description: Arma el paso a paso explícito de lo que el usuario tiene que hacer a mano (credenciales, UI de terceros, Apps Script, Gmail, wrangler, tareas programadas, exports de banco, tareas que requieren su sesión/dispositivo) y lo deja escrito para que no se pierda. Usar cuando pide "decime todo lo que tengo que hacer yo", "lo que depende de mí", "guiame paso a paso", "mostrame cómo hacer la integración de X", o "todo bien explícito y detalladito".
---

# /mis-pasos — lo que no se puede hacer por el usuario

**Lo propio del proyecto manda.** Si `AGENTS.md` o `CLAUDE.md` dice dónde vive la lista de lo
que depende del usuario, leela primero y escribí ahí.

Argumentos: `$ARGUMENTS` — sobre qué (integración, deploy, credencial). Si no vino, revisá qué
quedó pendiente del lado del usuario en la bitácora del proyecto, si existe.

Hay acciones que no se pueden ejecutar por él: entrar a cuentas personales, tildar cosas en un
panel de terceros, autorizar OAuth, instalar/registrar algo con elevación en su máquina. Esta
skill produce la guía para eso.

**Si el proyecto tiene una lista de "depende del usuario", leela primero** — puede que ya esté
hecho y anotado.

## Cómo tiene que ser la guía

Pedido textual: *"paso a paso, decime qué hacer, qué reemplazar en dónde, a qué se refiere cada
cosa, cómo hacer tal otra, todo bien explícito y detalladito"*. O sea:

- **Numerada, un paso por acción.** Nada de "configurá el webhook" como un solo paso.
- **Literal.** Si hay que pegar algo, dáselo entero y listo para copiar. Si hay que reemplazar un
  valor, decí **qué valor, en qué línea, de qué archivo**.
- **Con los nombres reales de la UI** que va a ver. Ejemplo: "creá una etiqueta" en Gmail lleva a
  una pantalla que pide *"Nombre de la etiqueta"* y *"Anidar etiqueta dentro de"*; si no lo
  anticipás, vuelve a preguntar. Si no estás seguro de qué ve, decile que confirme.
- **Con qué esperar si sale bien.** Un ejemplo del output correcto.
- **Con qué hacer si sale mal.** El error probable y qué hacer con él.

## Qué NO poner

- **Nada recurrente.** El usuario no va a mantener ni verificar datos a mano. Si un paso hay que
  repetirlo cada tanto, es un bug de diseño: decíselo y proponé automatizarlo.
- Nada que se pueda ejecutar directamente — antes de escribir un paso, preguntate si no lo podés
  correr vos.
- Explicaciones de por qué el sistema es así, salvo que cambien lo que tiene que tipear.

## Dejarlo escrito

**Si la sesión está por cortarse o queda poca cuota, escribí el archivo primero y explicá
después.** Es lo que salva el trabajo si se corta a mitad.

- Si es corto → a la lista de "depende del usuario" del proyecto, si tiene una.
- Si es una integración entera → archivo propio, con un puntero desde esa lista.

Anotá también **qué queda sin ejercitar de verdad** (probado sólo hasta cierto punto, nunca
corrido en el caso real) — vale la pena que quede escrito.

## Cuando vuelve con el resultado

Leé de verdad la salida que pega antes de contestar — varias veces la respuesta ya estaba ahí (un
404 por el subdominio equivocado, un JSON que mostraba que ya había funcionado). Cuando confirma
que algo anda, **marcalo hecho** en la lista — no lo dejes como pendiente eterno.

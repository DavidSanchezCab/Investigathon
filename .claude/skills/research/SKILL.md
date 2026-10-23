---
name: research
description: Investigación en serio — lee fuentes primarias (documentación oficial, términos, tarifarios, normativa), contrasta, fecha todo y etiqueta cada afirmación con [Seguro]/[Probable]/[Adivinando], con contexto argentino cuando aplica (bancos, billeteras, impuestos, ARCA, BCRA). Usar siempre que el usuario diga "investigá", "investigame sobre X", "hacé research", "buscá en internet", "investigá BIEN", "fijate si es gratis/legal/seguro", "¿con qué me conviene pagar…?", "¿qué banco o cuenta me conviene?", "¿me cobran impuestos si…?", "¿vale la pena…?", "¿se podría vender/monetizar?", "¿quién es el dueño de…?", o cuando una respuesta de memoria no alcanza. Si el objetivo es construir una integración con esa fuente, usar /nueva-fuente.
---

# /research — investigar, no recordar

Argumentos: `$ARGUMENTS` — la pregunta.

Dos frases del usuario marcan la vara:
- "No me sirve 'hay webhooks': leete las documentaciones de todo lo que encuentres, fijate si son
  gratuitas, si son muy laboriosas, si se integran fácil… investigá BIEN" (01/09).
- "Veo que no hiciste research para respaldar tus respuestas" (16/08).

Una respuesta de memoria no es research.

## 1. Encuadrar

- Reformulá la pregunta en una línea, junto con la decisión que destraba.
- Si falta un dato que cambia la respuesta (banco, monto, plazo, provincia), preguntalo en una
  línea. Si se puede asumir razonablemente, asumilo y decilo.
- Lo que vale es lo vigente hoy: promos, tasas, precios, modelos y normas cambian. Todo va fechado.

## 2. Buscar y leer

- **Fuentes primarias primero:** documentación oficial, términos y condiciones, tarifarios,
  normativa (BCRA, ARCA, Boletín Oficial), la página del servicio. Después prensa seria. Los foros
  sólo cuentan como señal.
- **Leé la página, no el snippet.** De cada fuente anotá qué dice (cita corta) y su fecha.
- **Contrastá:** lo que decide plata o riesgo necesita al menos dos fuentes. Si se contradicen, se
  dice.
- **Costo:** si es gratis, hasta dónde llega (cupos, free tier, vencimiento) y qué pasa al pasarse.
- **Riesgo:**
  - legal y términos de uso;
  - seguridad: qué datos o permisos se entregan;
  - solidez del proveedor: regulación y respaldo;
  - qué pasa si deja de existir.

## 3. Responder

Usá esta estructura:

```markdown
**Respuesta corta** — lo que haría, en la primera línea. Lo incómodo primero.

- [Seguro] <afirmación> — <fuente con link> (<fecha>)
- [Probable] …

**Opciones** (si hay más de una): tabla con costo, esfuerzo, riesgo y limitaciones.

**Lo que no pude confirmar**, y cómo se confirmaría.
```

## Límites

- **Plata personal** (bancos, inversiones, billeteras, impuestos): información con fuentes y
  tradeoffs. La decisión es del usuario; no es asesoramiento financiero personalizado.
- **Personas:** sólo información pública y relevante para el pedido (por ejemplo, el dueño de un
  negocio con el que va a reunirse). Nada de juntar datos personales sensibles.

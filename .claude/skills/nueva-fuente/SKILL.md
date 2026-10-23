---
name: nueva-fuente
description: Integra una fuente de datos externa a un proyecto — API oficial, reporte programado, mail, webhook, notificaciones del celular o, como último recurso y sólo donde los términos lo permiten, scraping — con el checklist completo (costo y cupos, auth, límites, términos de uso, ingesta idempotente, reconciliación con otros canales, monitoreo de último éxito y los pasos manuales del usuario). Usar siempre que el usuario diga "conectá X a la app", "¿hay API de…?", "quiero que se carguen solos los movimientos/las promos/los precios de…", "fetcheá esto", "scrapeemos…", "te pego los requests/el cURL que vi en DevTools", "me llegó un mail de X, ¿nos sirve?", o "integrá el reporte de…". Para sólo averiguar algo sin construir nada, /research.
---

# /nueva-fuente — traer datos de afuera sin que se rompa en silencio

Argumentos: `$ARGUMENTS` — la fuente y qué datos se quieren traer.

**Lo caro no es el primer fetch: es la fuente que deja de andar sin que nadie se entere.** Pasó en
otro proyecto: avisos mudos durante semanas sin un solo error en los logs, porque un `for` sobre
una lista vacía no falla. La integración está terminada recién cuando se sabe sola si anda.

## 1. Elegir el canal

De más estable a menos:
1. **API oficial documentada**, con su free tier.
2. **Reportes programados del servicio**, por mail, SFTP o webhook.
3. **Un mail que el usuario ya recibe**, reenviado por una regla o un Apps Script.
4. **Notificaciones del celular**: inmediatas, pero traen pocos datos.
5. **Endpoints internos de la web** (los que se ven en DevTools): frágiles. Sólo como plan B y si los
   términos no lo prohíben.
6. **Scraping:** último recurso, sólo donde los términos lo permitan y con un ritmo educado. Nada de
   evadir anti-bots, CAPTCHAs, bloqueos o baneos (tampoco con VPN): si la fuente lo impide, es la
   señal de no usarla.

Para cada canal candidato, una fila con:
- costo y cupos;
- auth: qué credencial hace falta y quién la genera;
- límites: rate limit y ventana de datos;
- términos de uso;
- latencia: inmediata o diaria;
- esfuerzo;
- qué se rompe si la fuente cambia.

Verificá contra la documentación real, y con una llamada real si se puede, no contra lo que
"debería" haber.

## 2. Diseñar la ingesta

- **Idempotencia:** cada ítem con una clave natural (el id de la fuente, o un hash). Reprocesar el
  mismo archivo no duplica nada.
- **Guardar el payload crudo**, para diagnosticar después sin volver a pedirlo.
- **Normalizar:**
  - fechas con zona explícita, distinguiendo la fecha de la operación de la de liquidación o
    acreditación;
  - montos en la unidad del proyecto, con su moneda.
- **Reconciliar con los otros canales.** La misma operación puede llegar por aviso, por reporte y por
  comprobante. Matcheá por monto, fecha con ventana y contraparte, sin crear duplicados.
- **Cachear todo fetch y respetar su TTL:** nunca pedir dos veces el mismo dato.
- **Fallas:** reintento con backoff. Lo que no se pudo leer queda en cola; no se pierde.

## 3. Monitoreo (sin esto no está terminada)

- Marca de último éxito y de último error por fuente, visible donde el usuario la vea.
- Umbral de "demorado" según la cadencia real de la fuente.
- Un aviso activo cuando pasa el umbral, no sólo un renglón de log.

## 4. Lo que depende del usuario

Credenciales, apps de developer, permisos OAuth, configurar el celular o Gmail: armalo con
`/mis-pasos`.
- **Los secretos los carga el usuario** en el `.env` o en su gestor, nunca pegados en el chat.
- **Explicá qué permiso concede y por qué.** Es su pregunta de siempre: "¿qué estoy autorizando?".

## 5. Verificación

- Un test con un payload real de la fuente, anonimizado.
- Una corrida real de punta a punta, con el dato visible donde corresponde.
- Documentarla en el repo:
  - canal y cadencia;
  - nombres de las variables (nunca sus valores);
  - formato;
  - trampas encontradas.

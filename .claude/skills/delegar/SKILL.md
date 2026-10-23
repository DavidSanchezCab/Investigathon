---
name: delegar
description: Arma el prompt de handoff para que otro modelo (ChatGPT, Codex, Gemini, etc.) ejecute una parte del trabajo con sus propios agentes, sin ver este repo ni este historial, y define qué conviene delegar y qué no. Usar cuando el usuario dice "tirame un prompt para chatgpt/gemini/codex", "dame el prompt para que se ponga a laburar", "qué le podemos delegar a otro modelo/a chatgpt", "voy a poner al gpt con algunas", o "voy a poner a X con esto". La vuelta (revisar lo que entregó) es /segunda-opinion.
---

# /delegar — pasarle trabajo a otro modelo

**Lo propio del proyecto manda.** Si `AGENTS.md` o `CLAUDE.md` define cómo se delega ahí (rama,
trampas del entorno, verificación, qué no se delega), usalo para llenar el prompt.

Argumentos: `$ARGUMENTS` — qué delegar. Si no vino, recomendá vos qué pieza tiene sentido. Si el
plan del proyecto ya reparte trabajo por ejecutor (una columna "Ejecutor" o similar), respetalo.

## Qué conviene delegar

Lo que **más se delega bien**: alcance cerrado y territorio disjunto de lo que se está tocando acá
— un módulo aislado, higiene/lint, una auditoría de lectura. Verificación clara, poca
conversación necesaria.

Lo que **no** conviene delegar: cualquier cosa que toque el núcleo de datos/lógica crítica del
proyecto (esquema de base de datos, cálculos de plata, seguridad). Ahí el costo de un malentendido
es alto y el ida y vuelta es caro cuando el otro modelo no ve el repo.

Si hay poca cuota o poco tiempo para armar el handoff: priorizá delegar lo que **menos** dependa
de leer contexto extenso del repo.

## El prompt del handoff

El otro modelo **no ve el repo ni el historial**. Todo lo que necesita tiene que estar en el
prompt o ser algo que pueda leer de un archivo que le indiques. Estructura que funciona:

1. **Qué es** — una o dos líneas de qué proyecto es y qué parte le toca.
2. **Qué leer primero** — si el proyecto tiene un plan/contrato de trabajo (`CLAUDE.md`,
   `AGENTS.md`, un plan de acción), nombralo y aclarale que es **el contrato, no un resumen**.
3. **Rama** — si hay git, qué rama usar y desde dónde parte.
4. **Archivos que posee y prohibidos** — lista explícita, no genérica.
5. **Trampas del entorno** — lo que rompe si no lo sabe (comandos que fallan en cierto contexto,
   pasos irreversibles, archivos que nunca hay que tocar).
6. **Verificación** — el comando exacto de test/build de este proyecto.
7. **Conducta** — convenciones del proyecto (idioma, estilo, stack), commitear cada paso, sin
   línea `Co-Authored-By` en los commits.
8. **Cierre** — qué hacer al terminar: commits en su rama, **sin push ni merge**, y que la primera
   línea del reporte diga si tocó algo sensible (esquema, datos).

Dáselo en un solo bloque, listo para pegar, sin preámbulo tuyo adentro del bloque.

## Cuando vuelve

Eso es `/segunda-opinion`. Lo mínimo:

- **No rehagas lo que hizo.** Verificá contra el árbol real (`git log`, `git diff`) antes de
  confiar en lo que dice que hizo.
- Si dice que no tocó algo sensible, comprobalo con un diff acotado a ese archivo.
- El merge, si corresponde, lo hacés vos según el protocolo del proyecto — no lo delegués.
- Si el usuario dice "de acá no hagas nada nuevo, sólo mergeá/corroborá", es al pie de la letra.

---
name: rescate
description: Retoma un trabajo que quedó a mitad — sesión cortada por límite, API error, compu apagada o cierre inesperado, o un agente que murió — sin rehacer lo que ya se hizo. Usar cuando el usuario dice "rescatá", "rescatá todo porfa", "rescatemos", "se cortó la sesión anterior", "se cortó todo", "murió la sesión/el agente", "quedó (todo) a la mitad", "terminá lo que había quedado pendiente", "terminá lo que te había asignado", "seguí/continuá donde quedaste", "reanudemos", "volvé a lanzar los agentes para que sigan donde quedaron", o "relanzá el agente para que siga".
---

# /rescate — cerrar lo que quedó a mitad

**Lo propio del proyecto manda.** Si `AGENTS.md` o `CLAUDE.md` tiene instrucciones para agentes
(worktrees, contrato de una tarea, protocolo de merge), el reemplazo del §4 las sigue.

Argumentos: `$ARGUMENTS` — qué se cortó (tarea, rama, agente). Si no vino, averigualo primero.

**El error caro no es que se corte el trabajo: es rehacer lo que ya existía.** Antes de dar algo
por pendiente, comprobalo en el árbol — el plan o las instrucciones originales pueden pedir cosas
que ya se hicieron antes del corte. Pasó: leer el plan al pie de la letra habría tirado 2.170
líneas que el agente muerto ya había escrito.

## 1. Primero: encontrar qué quedó vivo

**No arranques a tocar código hasta terminar este paso.**

Si hay git:
```bash
git worktree list 2>/dev/null      # ¿había un worktree separado?
git log --oneline -10              # ¿qué llegó a commitear?
git status --porcelain             # ¿hay cambios sin commitear?
git diff                           # ¿qué dicen esos cambios?
```

Tres estados, cada uno se trata distinto:

| Estado | Qué significa | Qué hacer |
|---|---|---|
| Commits + árbol limpio | Terminó un paso y se cortó antes del siguiente | Seguí desde el paso siguiente |
| Commits + cambios sueltos | Se cortó a mitad de una edición | Leé el diff archivo por archivo antes de tocar nada |
| Sin commits, cambios sueltos | Se cortó temprano; el árbol es el único registro | Leé todo el diff |

El caso peligroso es el del medio: puede haber código escrito y **sin cablear** — una función que
todavía nadie llama. Grepeá lo que agregó el diff para ver si tiene llamador.

## 2. Leer el reporte del trabajo cortado, si lo hay

Si fue un subagente lanzado desde esta misma herramienta, el transcript vive bajo
`~/.claude/projects/<proyecto-mangled>/<sesión>/subagents/agent-<id>.jsonl`, con un
`agent-<id>.meta.json` al lado (`description`, `model`, `agentType`, rama/worktree) — es la forma
más barata de identificar cuál murió sin abrir el jsonl entero. El último mensaje de asistente con
texto suele ser el último reporte parcial; si dice que llegó al límite, el árbol es la única
fuente.

## 3. ¿Retomarlo o reemplazarlo? Medí su contexto primero

Retomar un subagente con SendMessage conserva su transcript entero. Eso tiene un costo:
- cada vuelta lo relee completo;
- cada consulta al `advisor` lo reenvía entero.

Con un contexto grande, el agente retomado se vuelve a morir por el mismo límite. Pasó el
2026-10-04: dos agentes con ~470 mil y ~750 mil tokens, sin compactar, murieron tres veces
seguidas. El tamaño sale del último mensaje de asistente del jsonl:

```bash
node - "<ruta>/subagents/agent-<id>.jsonl" <<'EOF'
const lineas = require('fs').readFileSync(process.argv[2], 'utf8').trim().split('\n')
let t = 0
for (const l of lineas) {
  try {
    const u = JSON.parse(l).message?.usage
    if (u) t = (u.input_tokens || 0) + (u.cache_read_input_tokens || 0) + (u.cache_creation_input_tokens || 0) || t
  } catch {}
}
console.log(`contexto ≈ ${Math.round(t / 1000)} mil tokens`)
EOF
```

| Contexto | Qué hacer |
|---|---|
| < ~200 mil tokens | Retomalo con SendMessage: sabe lo que hizo y no re-deriva nada |
| ≥ ~200 mil tokens | Agente nuevo con el prompt de reemplazo del §4, más las reglas de frugalidad |

Un subagente no puede compactarse a sí mismo. La compactación automática salta recién cerca del
tope de la ventana, demasiado tarde para el cupo. Lo que la reemplaza son dos cosas:
- **no dejar crecer el contexto**, con las reglas de frugalidad del §4;
- **cortar el trabajo largo en postas:** cada agente cierra un tramo, commitea, reporta corto y
  termina, y el siguiente arranca de cero con ese reporte.

## 4. Si hace falta relanzar el trabajo

No siempre hace falta un agente nuevo: a veces conviene terminarlo directamente. Si hace falta,
el prompt del reemplazo tiene que abrir dejando claro:

> Continúa un trabajo interrumpido. Ya se hizo casi todo y se cortó por límite/error. La tarea es
> **cerrarlo, no rehacerlo**. Primero verificá en el código lo que ya está hecho (commits + diff)
> antes de asumir algo pendiente.
>
> Lo que sé que llegó a hacer: `<lista concreta>`
> Lo que falta, hasta donde puedo ver: `<lista concreta>`

**Si el trabajo vive en un worktree y una rama que ya existen**, el reemplazo va **sin
`isolation: "worktree"`**: una rama que ya está en un worktree no la puede tomar uno nuevo, y se
perdería el setup. Por eso:
- el prompt fija la ruta absoluta del worktree;
- todos los comandos van como `cd "<worktree>" && …` o `git -C "<worktree>" …`;
- antes de cada commit, el agente confirma la rama con `git branch --show-current`.

**Las reglas de frugalidad van textuales en el prompt:**

> Tu contexto se relee entero en cada vuelta: que no crezca.
> - Los tests con el reporter más corto y la salida siempre por `| tail`.
> - Los logs sólo por `grep` o `tail`, nunca enteros.
> - Los archivos por rango de líneas, nunca el mismo entero dos veces, con `grep -n` antes de abrir.
> - Nada de exploración que la tarea no necesite.
> - El `advisor` una sola vez, al final, con todo commiteado.
> - Commiteá cada paso apenas termina.

Después, el resto de las instrucciones normales del proyecto para ese tipo de tarea (setup,
archivos, verificación, conducta) si existen.

## 5. Prevención

- Si el trabajo cortado no venía commiteando por paso, decíselo al usuario en el reporte:
  commitear seguido es lo que evita este trabajo.
- Si murió con un contexto enorme, la prevención es la misma frugalidad desde el prompt original,
  y las postas si el trabajo es largo. Si el proyecto tiene un skill para largar agentes, ahí
  tiene que estar.

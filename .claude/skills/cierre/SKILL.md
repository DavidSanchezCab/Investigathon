---
name: cierre
description: Ritual de cierre de sesión para cualquier proyecto — deja anotado lo que se hizo y por qué, verifica que el proyecto esté en verde con sus propios comandos, y commitea/pushea si corresponde. Usar cuando el usuario dice "pusheá todo", "pushea todo porfa", "anotá lo hecho", "actualizá el plan/la bitácora", "actualizá el plan con lo que se hizo y comiteá", "me voy", "me voy a dormir", "me quedo sin sesión/cuota", "corré la skill de cierre", o "fijate si hace falta pushear o terminar de escribir algo antes de cortar".
---

# /cierre — que la sesión que viene no empiece de cero

El riesgo real no es no commitear: es que el **por qué** de lo que se hizo se pierda y la sesión
siguiente lo re-litigue.

**Lo propio del proyecto manda.** Si `AGENTS.md` o `CLAUDE.md` tiene una sección de rituales o de
cierre (qué archivos anotar, comando de verificación, protocolo de ramas), leela primero y seguila
por encima de lo genérico de acá.

Argumentos: `$ARGUMENTS` (contexto de qué se hizo; verificalo igual, no lo des por sentado).

**Si el usuario avisa que se queda sin sesión o cuota: escribí primero, verificá después.**
Anotar el por qué es lo que no se puede recuperar después; correr tests se puede hacer mañana.

## 1. Qué se hizo realmente

No lo reconstruyas de memoria — mirá el árbol si es un repo git:
```bash
git status --porcelain
git log --oneline origin/HEAD..HEAD 2>/dev/null || git log --oneline -10
git diff --stat
```

## 2. Anotar

Si el proyecto tiene una bitácora (`memory.md`, `MEMORY.md`, `NOTES.md`, o el sistema de memoria
automática si este entorno lo tiene activo): agregá lo que se hizo con el **por qué** de lo no
obvio, no una repetición del diff.
- **Marcá hecho, no borres el rastro.** Lo completado queda registrado como completado.
- Si el proyecto tiene un plan con estados de tareas/etapas, actualizalo si cambió algo.
- Si quedó algo a medias, dejá una sección **"Dónde retomar"** con fecha. Si ya existe una,
  **reemplazala** en vez de apilar otra debajo (antes de pisarla, archivá la vieja si el proyecto
  tiene un histórico): apiladas, los planes crecen a miles de líneas.
- Sé breve. "Quedó muy largo y desprolijo" es una corrección frecuente.

Si el proyecto **no tiene ninguno de estos archivos todavía**, no inventes una convención nueva sin
avisar: preguntale al usuario si quiere que arranques una bitácora, o simplemente resumiselo en el
chat.

## 3. Verificar antes de commitear

Derivá el comando de verificación del propio proyecto en vez de asumir uno fijo:
- Node: revisá `scripts` en `package.json` (`test`, `build`, `typecheck`, `lint`).
- Python: `pyproject.toml` / `Makefile` / `tox.ini`.
- Otro stack: lo que use el proyecto — si no está claro, preguntá antes de asumir.

Si algo falla de forma ya conocida y documentada (flake bajo carga, etc.), corré ese test aislado
antes de tratarlo como regresión, y decilo en el reporte.

## 4. Commitear y pushear

Sólo si es un repo git y el usuario lo pidió (o ya es la convención establecida). Mensajes en el
idioma del proyecto, **sin línea `Co-Authored-By`**. Para mensajes multilínea en Bash, heredoc:
```bash
git commit -m "$(cat <<'EOF'
tipo(alcance): qué cambió

Por qué, si no es obvio.
EOF
)"
```
En PowerShell, here-string simple-quoted (`@'...'@`), nunca de comillas dobles.

Si estás en una rama de feature y el proyecto tiene su propio protocolo de merge, no lo pisés:
commit sí, merge según ese protocolo.

## 5. Cerrar

Decile al usuario en dos o tres líneas: qué quedó commiteado, qué quedó anotado y dónde, y qué es
lo primero para agarrar la próxima vez.

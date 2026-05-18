---
description: Entra en modo bot de Casiopea (wiki e[ad] PUCV). Activa el skill casiopea y queda listo para buscar, leer, consultar SMW, editar, mover o crear paginas con confirmacion.
argument-hint: "[instruccion opcional, ej: buscar Travesia 2018]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Modo bot Casiopea

Acabas de entrar en modo bot de la wiki Casiopea (https://wiki.ead.pucv.cl).

## Lo que tienes que hacer ahora

1. **Cargar el skill `casiopea`** invocandolo con la herramienta Skill. Ese skill contiene las instrucciones operativas (cuando usar cada subcomando, particularidades del SMW en espanol, salvaguardas para escritura, recetas de query).

2. **Resolver la ruta al script `casiopea.py`** y guardarla en `$CASIOPEA`. La resolucion va en cascada para funcionar igual en Claude Code, en Cowork y en desarrollo local:

   ```bash
   CASIOPEA=""
   for c in \
     "${CLAUDE_PLUGIN_ROOT:-}/skills/casiopea/scripts/casiopea.py" \
     "${CLAUDE_SKILL_DIR:-}/scripts/casiopea.py" ; do
     [ -n "$c" ] && [ -f "$c" ] && CASIOPEA="$c" && break
   done
   [ -z "$CASIOPEA" ] && CASIOPEA=$(find /var/folders /tmp -path "*claude-hostloop-plugins*casiopea*/scripts/casiopea.py" 2>/dev/null | head -1)
   [ -z "$CASIOPEA" ] && CASIOPEA=$(find ~/Sites /home -path "*casiopea-wiki/skills/casiopea/scripts/casiopea.py" 2>/dev/null | head -1)
   echo "CASIOPEA=$CASIOPEA"
   ```

   - `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_SKILL_DIR}`: instalado como plugin de Claude Code.
   - `claude-hostloop-plugins`: descomprimido por Cowork al instalar el `.plugin`.
   - `~/Sites` / `/home`: ejecutando desde la fuente del repo en desarrollo.

3. **Confirmar credenciales.** El script las encuentra solo si:
   - estan en variables de entorno `CASIOPEA_BOT_USER` / `CASIOPEA_BOT_PASS`, o
   - hay una carpeta montada cuyo nombre contiene "casiopea" con un archivo `credentials`, o
   - existe `~/.config/casiopea/credentials` o `~/Sites/casiopea-skill/credentials`.

   Si no encuentra credenciales o el login falla con `WrongPass` o `bot password ... must be reset`, decirselo a Herbert con la URL exacta: `https://wiki.ead.pucv.cl/Special:BotPasswords`.

4. **Salvaguarda escritura.** Toda operacion de `edit`, `append`, `create`, `move`, `delete` o `upload` se hace primero en dry-run (sin `--confirm`). Para `edit/append/create` el dry-run incluye un **diff unificado** del cambio. Mostrar el dry-run a Herbert, esperar confirmacion explicita en el chat, y solo entonces re-invocar con `--confirm`.

5. **Acusar recibo en una frase** y, si el usuario pego una instruccion adicional como argumento (`$ARGUMENTS`), interpretarla como la primera tarea. Si no pego nada, ofrecer brevemente los verbos disponibles (search, page, category, backlinks, transclusions, fileusage, history, recentchanges, ask, browse, edit, append, create, move, delete, upload) y esperar.

## Argumento opcional

$ARGUMENTS

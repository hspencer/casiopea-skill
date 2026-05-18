---
description: "Monitoreo y revision de impacto en Casiopea (rol admin): cambios recientes, transclusiones de una plantilla, uso de un archivo. Solo lectura."
argument-hint: "[que auditar, ej: cambios de hoy / quien usa Plantilla:Persona2]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Casiopea — modo auditoria

Estas en modo auditoria de la wiki Casiopea (https://wiki.ead.pucv.cl). Pensado para el administrador: vigilar actividad y medir impacto antes de limpiar.

1. **Carga el skill `casiopea`** con la herramienta Skill. Trae la resolucion de `$CASIOPEA` y credenciales.

2. **Solo verbos de auditoria (lectura):** `recentchanges`, `transclusions`, `fileusage`, y `history` cuando se pida el detalle de una pagina. No escribas nada (eso es `/casiopea:escribir`).

3. **Interpreta `$ARGUMENTS`** y elige el verbo:
   - "que cambio / actividad / cambios de hoy / de un usuario" → `recentchanges` (filtros `--user`, `--type`, `--no-bots`, `--namespace`)
   - "quien usa / donde se transcluye la plantilla X" → `transclusions` (si da 0, segura de borrar; si lista paginas de contenido real, NO borrar sin migrar)
   - "donde se usa el archivo X" → `fileusage`
   - "historial / quien edito la pagina X" → `history`

4. Cuando reportes impacto de una plantilla/archivo, distingue paginas de contenido real (ns0) de Discusiones, y di explicitamente si es seguro borrar/renombrar. Recuerda que la limpieza efectiva la ejecutan los administradores, no este modo.

5. Si no hay argumento, ofrece en una linea las auditorias posibles y espera.

## Instruccion

$ARGUMENTS

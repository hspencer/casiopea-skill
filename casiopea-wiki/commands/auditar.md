---
description: "Monitoreo, diagnostico e impacto en Casiopea: recentchanges, history, compare, transclusions, fileusage, whoami, siteinfo, doctor. Rol admin, solo lectura."
argument-hint: "[que auditar, ej: que cambio hoy / quien usa la Plantilla:Persona2]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Casiopea — modo auditoria

Estas en modo administracion de la wiki Casiopea. Todo aca es solo lectura: sirve para entender el estado y el impacto de las cosas antes de tocarlas.

1. **Carga el skill `casiopea`** con la herramienta Skill.

2. **Verbos:** `recentchanges`, `history`, `compare`, `transclusions`, `fileusage`, `backlinks`, `whoami`, `siteinfo`, `doctor`.

3. **Interpreta `$ARGUMENTS`:**
   - "que cambio hoy / actividad reciente" → `recentchanges` (con `--no-bots` si interesa la actividad humana)
   - "quien edito X" → `history`
   - "que cambio entre estas dos versiones" → `compare`
   - "quien usa la plantilla X" → `transclusions`
   - "quien usa el archivo X" → `fileusage`
   - "se puede borrar X" → `transclusions` o `fileusage` segun corresponda, y responde con el numero
   - "que permisos tengo / con que cuenta estoy" → `whoami`
   - "que version de MediaWiki / que extensiones hay" → `siteinfo`
   - "por que no funciona el skill" → `doctor`

4. **Responde con el numero, no con una impresion.** "Se puede borrar" no es una respuesta: "0 paginas la transcluyen, se puede borrar" o "37 paginas la transcluyen, borrarla rompe esas 37" si lo es.

5. Si no hay argumento, ofrece en una linea las auditorias disponibles.

## Instruccion

$ARGUMENTS

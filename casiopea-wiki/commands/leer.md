---
description: "Lee, busca o trae contenido de la wiki Casiopea (e[ad] PUCV). Solo lectura: search, page, category, backlinks, browse, history. No modifica nada."
argument-hint: "[que leer, ej: trae la pagina Amereida]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Casiopea — modo lectura

Estas en modo lectura de la wiki Casiopea (https://wiki.ead.pucv.cl).

1. **Carga el skill `casiopea`** con la herramienta Skill. El skill trae la resolucion en cascada de la ruta a `$CASIOPEA`, el manejo de credenciales y la referencia del esquema SMW.

2. **Solo verbos de lectura.** En este modo usa unicamente: `search`, `page`, `category`, `backlinks`, `browse`, `history`. Nunca `ask` (eso es `/casiopea:consultar`), nunca escritura (eso es `/casiopea:escribir`).

3. **Interpreta `$ARGUMENTS`** como lo que el usuario quiere leer y elige el verbo adecuado:
   - "trae/lee la pagina X" → `page`
   - "busca / paginas sobre X" → `search`
   - "lista la categoria X" / "paginas de X" → `category`
   - "que enlaza a X" → `backlinks`
   - "que propiedades tiene X" → `browse`
   - "quien edito X / historial de X" → `history`

   Resume o cita selectivamente; no vuelques wikitexto crudo al chat.

4. Si no hay argumento, ofrece en una linea los verbos de lectura y espera.

## Instruccion

$ARGUMENTS

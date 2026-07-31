---
description: "Lee, busca o trae contenido de la wiki Casiopea (e[ad] PUCV). Solo lectura: search, prefix, page, pages, sections, revision, category, browse. No modifica nada."
argument-hint: "[que leer, ej: trae la pagina Amereida]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Casiopea — modo lectura

Estas en modo lectura de la wiki Casiopea (https://wiki.ead.pucv.cl). Nada de lo que hagas aca deja rastro en la wiki.

1. **Carga el skill `casiopea`** con la herramienta Skill. Trae la resolucion en cascada de la ruta a `$CASIOPEA`, el manejo de credenciales y la referencia del esquema SMW.

2. **Solo verbos de lectura.** En este modo usa unicamente: `search`, `prefix`, `page`, `pages`, `sections`, `revision`, `category`, `backlinks`, `browse`, `history`. Las consultas semanticas `#ask` son `/casiopea:consultar`; la escritura es `/casiopea:escribir`.

3. **Interpreta `$ARGUMENTS`** y elige el verbo adecuado:
   - "trae/lee la pagina X" → `page` (si es larga: `sections` primero, luego `page --section N`)
   - "busca / paginas sobre X" → `search` (busca en el contenido)
   - "como se llama la pagina que empieza con X" / "subpaginas de X" → `prefix` (busca en los titulos)
   - "trae estas cinco plantillas" → `pages` (hasta 50 de una vez)
   - "la version anterior de X" → `history` y luego `revision <revid>`
   - "lista la categoria X" → `category`
   - "que enlaza a X" → `backlinks`
   - "que propiedades tiene X" → `browse`

4. Resume o cita selectivamente. **No vuelques wikitexto crudo al chat**: es ruido, gasta contexto y nadie lo lee.

5. Si `page` avisa que trunco, no finjas que eso era toda la pagina: usa el indice de secciones que imprime.

6. Si no hay argumento, ofrece en una linea los verbos de lectura y espera.

## Instruccion

$ARGUMENTS

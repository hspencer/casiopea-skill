---
description: "Consulta semantica SMW sobre Casiopea y exportacion a CSV/JSON: ask, properties, browse. Solo lectura."
argument-hint: "[que consultar, ej: travesias por ano con destino, a CSV]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Casiopea — modo consulta semantica

Estas en modo consulta de la wiki Casiopea. Casiopea es Semantic MediaWiki: cada pagina lleva propiedades tipadas y se pueden consultar como una base de datos.

1. **Carga el skill `casiopea`** con la herramienta Skill.

2. **Carga `references/recetas.md`** antes de improvisar una consulta. Muchas ya estan escritas y probadas. Para el esquema completo, `references/esquema-casiopea.md`.

3. **Verbos:** `ask` (la consulta), `properties` (que propiedades existen), `browse` (que propiedades tiene una pagina concreta).

4. **Las tildes importan y el silencio engana.** Una propiedad mal escrita no da error: devuelve columnas vacias. Ante columnas vacias inesperadas, la primera hipotesis es siempre el nombre:

   ```bash
   python "$CASIOPEA" properties --grep coleccion   # responde: Colección
   ```

   La segunda hipotesis es `browse` sobre un ejemplar representativo.

5. **Exporta cuando corresponda.** `--format csv` produce algo que abre en Excel o Numbers; `--format json` conserva la estructura completa. `--max` controla el tope al paginar (500 por defecto): subelo si la categoria es grande, o el resultado miente por omision.

6. Si no hay argumento, pregunta que se quiere consultar y sobre que clase.

## Instruccion

$ARGUMENTS

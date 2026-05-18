---
description: "Query semantica SMW sobre Casiopea y exporta a CSV/JSON (verbo ask). Para datos tabulares por categoria y propiedades, paginado automatico."
argument-hint: "[consulta, ej: travesias por anio a CSV]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Casiopea — modo consulta semantica (SMW)

Estas en modo consulta semantica de la wiki Casiopea (https://wiki.ead.pucv.cl).

1. **Carga el skill `casiopea`** con la herramienta Skill. Trae la resolucion de `$CASIOPEA`, credenciales y las particularidades de SMW en espanol.

2. **Lee `references/recetas.md` y `references/esquema-casiopea.md`** del skill antes de armar la query: las propiedades de Casiopea llevan tildes y mayusculas exactas (`Colección`, `Año`, `Destino`) y SMW esta localizado al espanol. Una propiedad mal escrita devuelve columnas vacias.

3. **Usa el verbo `ask`.** Sintaxis SMW: `[[Category:X]][[Prop::Val]]|?Prop1|?Prop2`. Pagina solo por offset hasta `--max`. Elige `--format`:
   - el usuario pide CSV / Excel / Numbers → `--format csv`
   - quiere mirar el resultado → `--format table` (default)
   - necesita datos completos / anidados → `--format json`

   Si el resultado sale tabular y largo, propon guardarlo a un archivo `.csv`.

4. Si la query devuelve columnas vacias, corre `browse` sobre una pagina representativa para descubrir los nombres reales y reintenta.

5. Si no hay argumento, pide en una linea que categoria/propiedades consultar.

## Instruccion

$ARGUMENTS
